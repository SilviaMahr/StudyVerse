
import os
import psycopg2
from typing import List, Dict, Any, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
# Todo! Test-code from claude, to check if lvas without all prerequists can be eliminated before consulting the llm.
from difflib import SequenceMatcher
import re

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


# Parameters: [query_embedding + metadata_params + query_embedding, fetch_limit (Order by clause]
        final_params = [query_embedding] + params + [query_embedding, fetch_limit]

        # run query
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            cur.execute(base_query, final_params)
            rows = cur.fetchall()

            # remove duplicates and only keep the first (best) chunk from each lva
            # to keep it clear
            seen_lvas = set()
            unique_results = []

            for row in rows:
                metadata = row[2]
                lva_nr = metadata.get("lva_nr")

                # also keep chunks without lva nr (e.g. vor Curicculum data)
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

                    # stop, if enough unique lvas were retrieved
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
        retrieve lva by name or alias (if alias is already defined, otherwise LLM must
        ask user to specify lva name
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            # check content or metadata for lva name
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

    # Todo! Test-code from claude, to check if lvas without all prerequists can be eliminated before consulting the llm.
    def _fuzzy_match(self, text1: str, text2: str, threshold: float = 0.80) -> bool:
        """
        Fuzzy String Matching mit konfigurierbarem Threshold.

        Args:
            text1: Erster String
            text2: Zweiter String
            threshold: Minimum Similarity Score (0.0 - 1.0)

        Returns:
            True wenn Similarity >= threshold
        """
        # Normalisiere für besseres Matching
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        ratio = SequenceMatcher(None, text1, text2).ratio()
        return ratio >= threshold

    # Todo! Test-code from claude, to check if lvas without all prerequists can be eliminated before consulting the llm.
    def _extract_prerequisite_names(self, anmeldevoraussetzungen: str) -> List[str]:
        """
        Extrahiert LVA-Namen aus dem Freitext-Feld 'anmeldevoraussetzungen'.

        Beispiele:
        - "positive Absolvierung von SOFT1 VL" → ["SOFT1"]
        - "VL Einführung in die Softwareentwicklung" → ["VL Einführung in die Softwareentwicklung"]

        Returns:
            Liste von extrahierten LVA-Namen/Codes
        """
        if not anmeldevoraussetzungen or anmeldevoraussetzungen.strip().lower() == "keine":
            return []

        prerequisites = []

        # Pattern für LVA-Codes (z.B. SOFT1, ALGO, DKE)
        lva_code_pattern = r'\b([A-Z]{2,6}\d?)\b'
        codes = re.findall(lva_code_pattern, anmeldevoraussetzungen)
        prerequisites.extend(codes)

        # Pattern für vollständige LVA-Namen (z.B. "VL Softwareentwicklung")
        # Suche nach "VL/UE/PR/..." gefolgt von Text
        lva_name_pattern = r'((?:VL|UE|PR|SE|KS|KV|PS|PE|PJ|KT)\s+[A-ZÄÖÜ][a-zäöüß\s]+)'
        names = re.findall(lva_name_pattern, anmeldevoraussetzungen)
        prerequisites.extend(names)

        return prerequisites

    # Todo! Test-code from claude, to check if lvas without all prerequists can be eliminated before consulting the llm.
    def _check_prerequisites_met(
        self,
        prerequisite_names: List[str],
        completed_lvas: List[str]
    ) -> Dict[str, bool]:
        """
        Prüft ob Voraussetzungen erfüllt sind via Fuzzy Matching.

        Args:
            prerequisite_names: Liste von benötigten LVA-Namen/Codes
            completed_lvas: Liste von absolvierten LVA-Namen

        Returns:
            Dict mit {prerequisite_name: is_met}
        """
        results = {}

        print(f"[PREREQ DEBUG] Checking prerequisites: {prerequisite_names}")

        for prereq in prerequisite_names:
            is_met = False
            best_match = None
            best_score = 0.0

            # Prüfe gegen jede completed LVA
            for completed in completed_lvas:
                # Fuzzy Match (Threshold 75%)
                ratio = SequenceMatcher(None, prereq.lower(), completed.lower()).ratio()
                if ratio > best_score:
                    best_score = ratio
                    best_match = completed

                if ratio >= 0.75:
                    is_met = True
                    print(f"[PREREQ DEBUG]   ✓ '{prereq}' MATCHED '{completed}' (score: {ratio:.2f})")
                    break

                # Falls prereq ein Code ist (z.B. "SOFT1"), checke ob in completed enthalten
                if len(prereq) <= 6 and prereq.upper() in completed.upper():
                    is_met = True
                    print(f"[PREREQ DEBUG]   ✓ '{prereq}' FOUND IN '{completed}' (substring match)")
                    break

            if not is_met:
                print(f"[PREREQ DEBUG]   ✗ '{prereq}' NOT MATCHED (best: '{best_match}', score: {best_score:.2f})")

            results[prereq] = is_met

        return results

    # Todo! Test-code from claude, to check if lvas without all prerequists can be eliminated before consulting the llm.
    def filter_by_prerequisites(
        self,
        retrieved_lvas: List[Dict[str, Any]],
        completed_lvas: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filtert LVAs basierend auf Voraussetzungen UND bereits absolvierten LVAs.

        Args:
            retrieved_lvas: Retrieved documents von retrieve()
            completed_lvas: Absolvierte LVAs des Users

        Returns:
            {
                "eligible": [...],  # LVAs die alle Voraussetzungen erfüllen
                "filtered": [       # LVAs die Voraussetzungen NICHT erfüllen
                    {
                        "lva": {...},
                        "missing_prerequisites": ["SOFT1", "ALGO"],
                        "reason": "Fehlende Voraussetzungen: SOFT1, ALGO"
                    },
                    ...
                ]
            }
        """
        eligible_lvas = []
        filtered_lvas = []

        print(f"[FILTER DEBUG] Starting filter with {len(completed_lvas)} completed LVAs:")
        for comp_lva in completed_lvas:
            print(f"  ✓ {comp_lva}")

        for lva_doc in retrieved_lvas:
            metadata = lva_doc.get("metadata", {})
            lva_name = metadata.get("lva_name", "Unknown")
            lva_nr = metadata.get("lva_nr", "")
            anmeldevoraussetzungen = metadata.get("anmeldevoraussetzungen", "")

            # Todo! Test-code from claude, to check if lvas without all prerequists can be eliminated before consulting the llm.
            # 1. CHECK: Ist die LVA bereits absolviert?
            is_already_completed = False
            for completed in completed_lvas:
                # Fuzzy Match gegen completed LVAs
                if self._fuzzy_match(lva_name, completed, threshold=0.75):
                    is_already_completed = True
                    break
                # Exakte Substring-Prüfung für LVA-Nr
                if lva_nr and lva_nr in completed:
                    is_already_completed = True
                    break

            if is_already_completed:
                print(f"[FILTER DEBUG] ❌ FILTERED (bereits absolviert): {lva_name} ({lva_nr})")
                filtered_lvas.append({
                    "lva": lva_doc,
                    "missing_prerequisites": [],
                    "reason": f"Bereits absolviert"
                })
                continue

            # 2. CHECK: Voraussetzungen prüfen
            # Falls keine Voraussetzungen oder "keine" → direkt eligible
            if not anmeldevoraussetzungen or anmeldevoraussetzungen.strip().lower() == "keine":
                print(f"[FILTER DEBUG] ✅ ELIGIBLE (keine Voraussetzungen): {lva_name} ({lva_nr})")
                eligible_lvas.append(lva_doc)
                continue

            # Extrahiere benötigte LVAs
            prerequisite_names = self._extract_prerequisite_names(anmeldevoraussetzungen)

            if not prerequisite_names:
                # Konnte nichts parsen → erstmal eligible (sicherer)
                print(f"[FILTER DEBUG] ✅ ELIGIBLE (Voraussetzungen nicht parsebar): {lva_name} ({lva_nr})")
                eligible_lvas.append(lva_doc)
                continue

            # Prüfe welche Voraussetzungen erfüllt sind
            prereq_check = self._check_prerequisites_met(prerequisite_names, completed_lvas)

            missing = [name for name, met in prereq_check.items() if not met]

            if missing:
                # Nicht alle Voraussetzungen erfüllt
                print(f"[FILTER DEBUG] ❌ FILTERED (fehlende Voraussetzungen): {lva_name} ({lva_nr})")
                print(f"              Fehlend: {', '.join(missing)}")
                filtered_lvas.append({
                    "lva": lva_doc,
                    "missing_prerequisites": missing,
                    "reason": f"Fehlende Voraussetzungen: {', '.join(missing)}"
                })
            else:
                # Alle Voraussetzungen erfüllt
                print(f"[FILTER DEBUG] ✅ ELIGIBLE (Voraussetzungen erfüllt): {lva_name} ({lva_nr})")
                eligible_lvas.append(lva_doc)

        return {
            "eligible": eligible_lvas,
            "filtered": filtered_lvas
        }

    def get_completed_lvas_for_user(self, user_id: int) -> List[str]:
        """
        Gets all completed LVA names for a user from the database.
        Returns a l ist of completed LVA names (e.g., ["Einführung in die Softwareentwicklung", "BWL"])
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            query = """
                    SELECT l.name, l.ects, l.hierarchielevel2
                    FROM completed_lvas cl
                             JOIN lvas l ON cl.lva_id = l.id
                    WHERE cl.user_id = %s \
                    """

            cur.execute(query, [user_id])
            rows = cur.fetchall()

            # Return list of LVA names
            completed_lva_names = [row[0] for row in rows]

            cur.close()
            conn.close()

            return completed_lva_names

        except Exception as e:
            print(f"Error fetching completed LVAs: {e}")
            return []
