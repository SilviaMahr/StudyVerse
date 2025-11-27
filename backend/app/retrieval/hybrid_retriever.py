"""
Hybrid Retrieval System: Kombiniert Metadata-Filtering mit Vector Similarity Search
Nutzt pgvector für effiziente semantische Suche in der Neon DB.
"""

import os
import psycopg2
from typing import List, Dict, Any, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


class HybridRetriever:
    """
    Hybrid Retrieval to combine:
    1. Metadata-Filtering (hard constraints: Semester, days, ECTS)
    2. Vector Similarity Search (for free text field)
    """

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL not set in environment")

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")

        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=gemini_api_key
        )

    def _build_metadata_sql_filter(self, filter_dict: Dict[str, Any]) -> tuple:
        """
        Build SQL-Where-Clause -> Filer-Dict = Key = String
                                               Value = Any
        Returns a tuple eg. "Semester = ? AND ECTS = ?", ["SS", 15]
        """

        conditions = [] #for SQL-conditions like "Semester = ?"
        params = [] #values for sql placeholders e.g. "SS"

        if not filter_dict: #if no filter needed, WHERE clause is empty
            return "", []

        # if filter conditions connect with $and eg. {$and: [{"Semester: "SS"}, {"ECTS": 15}]}
        if "$and" in filter_dict:
            and_conditions = []
            for condition in filter_dict["$and"]:
                clause, param = self._parse_condition(condition) #builds sql-condition as tuple
                if clause:
                    and_conditions.append(clause)
                    params.extend(param)
            if and_conditions:
                conditions.append(f"({' AND '.join(and_conditions)})")
                #parse into useful where clause with all AND conditions

        #same for $or conditions
        elif "$or" in filter_dict:
            or_conditions = []
            for condition in filter_dict["$or"]:
                clause, param = self._parse_condition(condition)
                if clause:
                    or_conditions.append(clause)
                    params.extend(param)
            if or_conditions:
                conditions.append(f"({' OR '.join(or_conditions)})")

        # single condition
        else:
            clause, param = self._parse_condition(filter_dict)
            if clause:
                conditions.append(clause)
                params.extend(param)

        where_clause = " AND ".join(conditions) if conditions else ""
        return where_clause, params


    def _parse_condition(self, condition: Dict[str, Any]) -> tuple:
        """
            helper function for _build_metadata_sql_filter
            - called for every single condition in $and, $or or standalone condition
            - parses one condition at a time
        """
        if not condition:
            return "", []

        conditions = []
        params = []

        for field, constraint in condition.items():
            if field in ["$and", "$or"]: #$and and $or can are not handled here - will be
                continue                #returning once in for loop treated as single cond.

            #case A: constraint is a dictionary
            if isinstance(constraint, dict):
                for operator, value in constraint.items():
                    if operator == "$eq": # eg. metadata -> Semester & params = SS
                        conditions.append(f"metadata->>'{field}' = %s")
                        params.append(str(value))
                    elif operator == "$in":
                        placeholders = ", ".join(["%s"] * len(value))
                        conditions.append(f"metadata->>'{field}' IN ({placeholders})")
                        params.extend([str(v) for v in value])
                    elif operator == "$lte":
                        # cast ECTS into float
                        conditions.append(f"(metadata->>'{field}')::float <= %s")
                        params.append(float(value))
                    elif operator == "$gte":
                        conditions.append(f"(metadata->>'{field}')::float >= %s")
                        params.append(float(value))
            else:
                # Case B: constraint is not a dict -> equality given
                conditions.append(f"metadata->>'{field}' = %s")
                params.append(str(constraint))

        where_clause = " AND ".join(conditions) if conditions else ""
        return where_clause, params

    def retrieve(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        #TODO Check if top k none would make sense, try out later when LLM is ready to go

        """
        Haupt-Retrieval-Funktion: Hybrid Search

        Args:
            query: User query für semantische Suche
            metadata_filter: Filter-Dict für Metadaten (Semester, Tage, etc.)
            top_k: Anzahl der Top-Ergebnisse (unique LVAs)

        Returns:
            Liste von LVA-Dictionaries mit content, metadata, similarity
        """
        # 1. generate emedding from user query
        query_embedding = self.embedding_model.embed_query(query)

        # 2. generate query from metadata filter and embedding (hybrid - metadata + similarity)
        where_clause, params = self._build_metadata_sql_filter(metadata_filter or {})

        base_query = """
            SELECT
                id,
                content,
                metadata,
                url,
                1 - (embedding <=> %s::vector) AS similarity  
            FROM studyverse_data
        """
                #similarty = 1 - distance
        if where_clause:
            base_query += f" WHERE {where_clause}"

        base_query += """
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        # if top k is limited to eg. 15 best lvas - then generate more lvas to provide the llm
        #with more context, if we chose none, do nothing other then get the retrieved lvas
        if top_k is not None:
            fetch_limit = top_k * 20
        else:
            fetch_limit = None


# Parameters: [query_embedding, ...metadata_params..., query_embedding, fetch_limit]
        final_params = [query_embedding] + params + [query_embedding, fetch_limit]

        # 3. Query ausführen
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            cur.execute(base_query, final_params)
            rows = cur.fetchall()

            # 4. Duplikate entfernen (basierend auf lva_nr)
            # Behalte nur den besten (ersten) Chunk pro LVA
            seen_lvas = set()
            unique_results = []

            for row in rows:
                metadata = row[2]
                lva_nr = metadata.get("lva_nr")

                # Wenn lva_nr nicht existiert, trotzdem aufnehmen (z.B. Curriculum-Chunks)
                if lva_nr is None or lva_nr not in seen_lvas:
                    if lva_nr:
                        seen_lvas.add(lva_nr)

                    unique_results.append({
                        "id": row[0],
                        "content": row[1],
                        "metadata": metadata,
                        "url": row[3],
                        "similarity": float(row[4]) if row[4] else 0.0,
                    })

                    # Stop wenn wir genug unique LVAs haben
                    if len(unique_results) >= top_k:
                        break

            cur.close()
            conn.close()

            return unique_results

        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []

    def retrieve_by_lva_name(self, lva_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Sucht LVAs nach Name (für Aliase wie "SOFT1" → "Einführung in die Softwareentwicklung")

        Args:
            lva_name: Name oder Alias der LVA
            top_k: Maximale Anzahl Ergebnisse

        Returns:
            Liste von LVA-Dictionaries
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            # Suche nach LVA-Namen im content ODER in metadata
            query = """
                SELECT
                    id,
                    content,
                    metadata,
                    url
                FROM studyverse_data
                WHERE
                    content ILIKE %s
                    OR metadata->>'lva_name' ILIKE %s
                    OR metadata->>'lva_code' ILIKE %s
                LIMIT %s
            """

            search_pattern = f"%{lva_name}%"
            cur.execute(query, [search_pattern, search_pattern, search_pattern, top_k])
            rows = cur.fetchall()

            results = []
            for row in rows:
                results.append({
                    "id": row[0],
                    "content": row[1],
                    "metadata": row[2],
                    "url": row[3],
                })

            cur.close()
            conn.close()

            return results

        except Exception as e:
            print(f"Error during LVA name search: {e}")
            return []

