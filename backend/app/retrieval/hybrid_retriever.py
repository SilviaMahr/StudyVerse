
import os
import psycopg2
from typing import List, Dict, Any, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from difflib import SequenceMatcher
import re

load_dotenv()


class HybridRetriever:
    """
    Hybrid Retrieval to combine:
    1. Metadata-Filtering (hard constraints: Semester, days, ECTS)
    2. Vector Similarity Search (for free text field)
    """

    # Fallback: Bekannte Voraussetzungsketten (falls Metadaten fehlen/falsch sind)
    KNOWN_PREREQUISITES = {
        # SOFT-Kette
        "Vertiefung Softwareentwicklung": ["Einführung in die Softwareentwicklung"],
        "Software Engineering": ["Vertiefung Softwareentwicklung"],
        "PR Software Engineering": ["Software Engineering"],

        # DKE-Kette
        "Data & Knowledge Engineering": ["Datenmodellierung"],
        "PR Data & Knowledge Engineering": ["Data & Knowledge Engineering"],

        # COMM-Kette
        "Communications Engineering": ["Prozess- und Kommunikationsmodellierung"],

        # INFO-Kette
        "Informationsmanagement": ["Einführung in die Wirtschaftsinformatik"],
        "IT-Project Engineering & Management": ["Einführung in die Wirtschaftsinformatik"],

        # Weitere bekannte Ketten können hier hinzugefügt werden
    }

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
        top_k: int = 100,
    ) -> List[Dict[str, Any]]:
        #TODO Check if top k none would make sense, try out later when all Data is available

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

        # For semester planning: We want ALL LVAs matching the metadata filter, not just the most similar ones
        # So we sort by similarity but don't limit too aggressively
        base_query += """
            ORDER BY embedding <=> %s::vector
        """

        # Determine fetch limit
        # For semester planning we need ALL matching LVAs, so use a very high limit or no limit
        if top_k is not None:
            # Fetch many more to ensure we get all matching LVAs
            # After deduplication (by lva_name+type), we'll have fewer anyway
            fetch_limit = max(top_k * 50, 5000)  # At least 5000 to get comprehensive results
        else:
            fetch_limit = 10000  # Very high default to get all matches

        base_query += " LIMIT %s"

        # Parameters: [query_embedding + metadata_params + query_embedding + fetch_limit]
        final_params = [query_embedding] + params + [query_embedding, fetch_limit]

        # run query
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            cur.execute(base_query, final_params)
            rows = cur.fetchall()

            print(f"[RETRIEVAL DEBUG] Fetched {len(rows)} documents from Vector DB (before deduplication)")

            # remove duplicates and only keep the first (best) chunk from each (lva_name, lva_type)
            # Different time slots (different lva_nr) of the same course should be deduplicated
            seen_lvas = set()  # stores (lva_name, lva_type) tuples
            unique_results = []

            for row in rows:
                metadata = row[2]

                # FIX: Prüfe ob metadata ein gültiges Dictionary ist
                if not isinstance(metadata, dict):
                    # Skip Einträge mit fehlerhaftem metadata (None oder String)
                    print(f"[RETRIEVAL WARNING] Skipping entry with invalid metadata (ID: {row[0]}, type: {type(metadata).__name__})")
                    continue

                lva_name = metadata.get("lva_name")
                lva_type = metadata.get("lva_type")
                lva_nr = metadata.get("lva_nr")

                # Create unique key: (lva_name, lva_type)
                # This ensures we only get ONE entry per course type (e.g. only one "VL Datenmodellierung")
                # regardless of different time slots (lva_nr 258.100, 258.101, etc.)
                if lva_name and lva_type:
                    lva_key = (lva_name, lva_type)
                else:
                    # For entries without name/type (curriculum docs), use lva_nr or ID
                    lva_key = lva_nr if lva_nr else row[0]

                # Only add if we haven't seen this (name, type) combination yet
                if lva_key not in seen_lvas:
                    seen_lvas.add(lva_key)

                    unique_results.append({
                        "id": row[0],
                        "content": row[1],
                        "metadata": metadata,
                        "url": row[3],
                        "similarity": float(row[4]) if row[4] else 0.0,
                    })

                    # Don't break early - we want ALL matching LVAs for comprehensive semester planning
                    # The top_k limit is only for the initial fetch, not for the final results

            cur.close()
            conn.close()

            print(f"[RETRIEVAL DEBUG] After deduplication: {len(unique_results)} unique LVAs")
            print(f"[RETRIEVAL DEBUG] Seen combinations: {len(seen_lvas)}")

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

        # Stopwörter die KEINE LVA-Codes sind
        STOPWORDS = {"ODER", "UND", "IT", "VO", "VL", "UE", "PR", "SE", "KS", "KV", "PS", "PE", "PJ", "KT", "IN", "AN", "IM"}

        # Pattern für LVA-Codes MIT Nummer (z.B. SOFT1, ALGO2, DKE3)
        lva_code_with_number = r'\b([A-Z]{2,6}\d+)\b'
        codes_with_number = re.findall(lva_code_with_number, anmeldevoraussetzungen)
        prerequisites.extend(codes_with_number)

        # Pattern für bekannte LVA-Codes OHNE Nummer (z.B. SOFT, ALGO, DKE, BWL)
        # Nur wenn sie 3-6 Buchstaben haben und NICHT in Stopwords sind
        lva_code_pattern = r'\b([A-Z]{3,6})\b'
        codes = re.findall(lva_code_pattern, anmeldevoraussetzungen)
        for code in codes:
            if code not in STOPWORDS:
                prerequisites.append(code)

        # Pattern für vollständige LVA-Namen (z.B. "VL Softwareentwicklung")
        # Suche nach "VL/UE/PR/..." gefolgt von Text
        lva_name_pattern = r'((?:VL|UE|PR|SE|KS|KV|PS|PE|PJ|KT)\s+[A-ZÄÖÜ][a-zäöüß\s]+)'
        names = re.findall(lva_name_pattern, anmeldevoraussetzungen)
        prerequisites.extend(names)

        print(f"[EXTRACT DEBUG] Raw: '{anmeldevoraussetzungen}' → Extracted: {prerequisites}")

        return prerequisites

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
                # Fuzzy Match (Threshold 70% für Namen, 75% für Codes)
                ratio = SequenceMatcher(None, prereq.lower(), completed.lower()).ratio()
                if ratio > best_score:
                    best_score = ratio
                    best_match = completed

                # Threshold abhängig von prereq-Länge (Namen sind länger als Codes)
                threshold = 0.65 if len(prereq) > 10 else 0.75

                if ratio >= threshold:
                    is_met = True
                    print(f"[PREREQ DEBUG]   ✓ '{prereq}' MATCHED '{completed}' (score: {ratio:.2f})")
                    break

                # Falls prereq ein Code ist (z.B. "SOFT1"), checke ob in completed enthalten
                if len(prereq) <= 6 and prereq.upper() in completed.upper():
                    is_met = True
                    print(f"[PREREQ DEBUG]   ✓ '{prereq}' FOUND IN '{completed}' (substring match)")
                    break

                # Checke auch ob completed den prereq enthält (für volle Namen)
                if len(prereq) > 10 and prereq.lower() in completed.lower():
                    is_met = True
                    print(f"[PREREQ DEBUG]   ✓ '{prereq}' SUBSTRING IN '{completed}'")
                    break

            if not is_met:
                print(f"[PREREQ DEBUG]   ✗ '{prereq}' NOT MATCHED (best: '{best_match}', score: {best_score:.2f})")

            results[prereq] = is_met

        return results

    def filter_by_prerequisites(
        self,
        retrieved_lvas: List[Dict[str, Any]],
        completed_lvas: List[str],
        target_semester: Optional[str] = None,
        user_query: Optional[str] = None,
        excluded_wahlfaecher: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filtert LVAs basierend auf Voraussetzungen, bereits absolvierten LVAs, Wahlfächern UND Semester.

        Filterkriterien (in dieser Reihenfolge):
        0. FALSCHES SEMESTER → wird gefiltert (falls target_semester angegeben)
        1. WAHLFACH → wird gefiltert (nicht vorgeschlagen)
           AUSNAHME: Wahlfächer in excluded_wahlfaecher oder im user_query erwähnt werden NICHT gefiltert
        2. Bereits absolviert → wird gefiltert
        3. Voraussetzungen nicht erfüllt → wird gefiltert

        Args:
            retrieved_lvas: Retrieved documents von retrieve()
            completed_lvas: Absolvierte LVAs des Users
            target_semester: Gewünschtes Semester (z.B. "SS", "WS") - optional
            user_query: User-Query um explizit gewünschte Wahlfächer zu erkennen - optional
            excluded_wahlfaecher: Liste von Wahlfach-Namen, die NICHT gefiltert werden sollen - optional

        Returns:
            {
                "eligible": [...],  # LVAs die alle Kriterien erfüllen
                "filtered": [       # LVAs die gefiltert wurden
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

        if target_semester:
            print(f"[FILTER DEBUG] Target semester: {target_semester}")

        # Lade alle Wahlfächer aus der Datenbank (einmalig für alle LVAs)
        print(f"[FILTER DEBUG] Loading Wahlfächer from database...")
        wahlfaecher_names = self._get_wahlfaecher_names()

        # Baue Liste von Wahlfächern, die NICHT gefiltert werden sollen
        final_excluded_wahlfaecher = []
        if excluded_wahlfaecher:
            final_excluded_wahlfaecher.extend(excluded_wahlfaecher)

        # Extrahiere Wahlfach-Namen aus user_query (falls vorhanden)
        if user_query:
            user_query_lower = user_query.lower()
            for wahlfach_name in wahlfaecher_names:
                # Checke ob der Wahlfach-Name im User-Query vorkommt
                if wahlfach_name.lower() in user_query_lower:
                    final_excluded_wahlfaecher.append(wahlfach_name)
                    print(f"[FILTER DEBUG] User erwähnt Wahlfach '{wahlfach_name}' → wird NICHT gefiltert")

        if final_excluded_wahlfaecher:
            print(f"[FILTER DEBUG] Wahlfächer die NICHT gefiltert werden: {final_excluded_wahlfaecher}")

        for lva_doc in retrieved_lvas:
            metadata = lva_doc.get("metadata", {})

            # FIX: Prüfe ob metadata ein gültiges Dictionary ist
            if not isinstance(metadata, dict):
                print(f"[FILTER WARNING] Skipping LVA with invalid metadata (type: {type(metadata).__name__})")
                continue

            lva_name = metadata.get("lva_name", "Unknown")
            lva_nr = metadata.get("lva_nr", "")
            lva_semester = metadata.get("semester", None)
            anmeldevoraussetzungen = metadata.get("anmeldevoraussetzungen", "")

            # CHECK -1: SEMESTER-Filter (falls target_semester angegeben)
            if target_semester:
                # Falls die LVA einen Namen hat (ist eine konkrete LVA):
                if lva_name and lva_name != "Unknown":
                    # Fall A: LVA hat KEIN Semester-Feld → Curriculum-Eintrag → FILTERN
                    if not lva_semester:
                        print(f"[FILTER DEBUG] ❌ FILTERED (kein Semester-Info): {lva_name} - Curriculum-Eintrag")
                        filtered_lvas.append({
                            "lva": lva_doc,
                            "missing_prerequisites": [],
                            "reason": f"Kein Semester-Info (Curriculum-Eintrag, nicht für konkrete Planung)"
                        })
                        continue

                    # Fall B: LVA hat falsches Semester → FILTERN
                    if lva_semester != target_semester and lva_semester != f"{target_semester}+":
                        print(f"[FILTER DEBUG] ❌ FILTERED (falsches Semester): {lva_name} ({lva_nr}) - Semester: {lva_semester}, Target: {target_semester}")
                        filtered_lvas.append({
                            "lva": lva_doc,
                            "missing_prerequisites": [],
                            "reason": f"Nur für {lva_semester} verfügbar (nicht {target_semester})"
                        })
                        continue

            # CHECK 0: Ist die LVA ein WAHLFACH?
            if self._is_wahlfach(lva_name, wahlfaecher_names, final_excluded_wahlfaecher):
                print(f"[FILTER DEBUG] ❌ FILTERED (Wahlfach): {lva_name} ({lva_nr})")
                filtered_lvas.append({
                    "lva": lva_doc,
                    "missing_prerequisites": [],
                    "reason": "Wahlfächer werden nicht vorgeschlagen"
                })
                continue

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
            prerequisite_names = []

            # Zuerst: Versuche aus Metadaten zu extrahieren
            if anmeldevoraussetzungen and anmeldevoraussetzungen.strip().lower() != "keine":
                prerequisite_names = self._extract_prerequisite_names(anmeldevoraussetzungen)

            # Fallback: Falls nichts extrahiert wurde, checke gegen bekannte Voraussetzungsketten
            if not prerequisite_names and lva_name in self.KNOWN_PREREQUISITES:
                prerequisite_names = self.KNOWN_PREREQUISITES[lva_name]
                print(f"[FILTER DEBUG] 🔄 Using KNOWN prerequisites for '{lva_name}': {prerequisite_names}")

            # Falls immer noch keine Voraussetzungen → eligible
            if not prerequisite_names:
                print(f"[FILTER DEBUG] ✅ ELIGIBLE (keine Voraussetzungen): {lva_name} ({lva_nr})")
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

    def _get_wahlfaecher_names(self) -> List[str]:
        """
        Holt alle Wahlfach-Namen aus der wahlfach Tabelle.

        Returns:
            Liste von Wahlfach-Namen (z.B., ["Data Mining", "Service Engineering"])
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            query = """
                SELECT lva_name
                FROM wahlfach
            """
            cur.execute(query)
            rows = cur.fetchall()

            # Return list of Wahlfach names
            wahlfaecher = [row[0] for row in rows]

            cur.close()
            conn.close()

            print(f"[WAHLFACH DEBUG] Loaded {len(wahlfaecher)} Wahlfächer from wahlfach table")
            return wahlfaecher

        except Exception as e:
            print(f"Error fetching Wahlfächer from wahlfach table: {e}")
            return []

    def _is_wahlfach(self, lva_name: str, wahlfaecher_names: List[str], excluded_wahlfaecher: Optional[List[str]] = None) -> bool:
        """
        Checkt ob eine LVA ein Wahlfach ist via LIKE-ähnlichem Substring-Matching.
        Verwendet KEIN Fuzzy Matching mehr für präziseres Filtern.

        Args:
            lva_name: Name der zu prüfenden LVA
            wahlfaecher_names: Liste aller Wahlfach-Namen aus der DB
            excluded_wahlfaecher: Liste von Wahlfächern, die NICHT gefiltert werden sollen
                                  (vom User explizit gewünscht)

        Returns:
            True wenn die LVA ein Wahlfach ist UND NICHT in excluded_wahlfaecher
        """
        lva_name_lower = lva_name.lower().strip()

        # Check 0: Ist dieses Wahlfach vom User explizit gewünscht?
        if excluded_wahlfaecher:
            for excluded in excluded_wahlfaecher:
                excluded_lower = excluded.lower().strip()
                # Exakte Übereinstimmung oder Substring-Match
                if excluded_lower in lva_name_lower or lva_name_lower in excluded_lower:
                    print(f"[WAHLFACH DEBUG]   [!] '{lva_name}' ist vom User gewuenscht -> NICHT filtern")
                    return False

        # Check 1: Direkt "Wahlfach" oder "Freie Studienleistungen" im Namen
        if "wahlfach" in lva_name_lower or "freie studienleistungen" in lva_name_lower:
            print(f"[WAHLFACH DEBUG]   [+] '{lva_name}' MATCHED (contains 'wahlfach' or 'freie studienleistungen')")
            return True

        # Check 2: LIKE-ähnliches Substring-Matching gegen Wahlfach-Namen aus DB
        # Nur noch präzises Substring-Matching, KEIN Fuzzy Matching
        for wahlfach_name in wahlfaecher_names:
            wahlfach_lower = wahlfach_name.lower().strip()

            # Exakte Übereinstimmung
            if lva_name_lower == wahlfach_lower:
                print(f"[WAHLFACH DEBUG]   [+] '{lva_name}' MATCHED as Wahlfach: '{wahlfach_name}' (exact match)")
                return True

            # Substring-Match (ähnlich zu SQL LIKE '%name%')
            # LVA-Name enthält Wahlfach-Name ODER umgekehrt
            if wahlfach_lower in lva_name_lower or lva_name_lower in wahlfach_lower:
                print(f"[WAHLFACH DEBUG]   [+] '{lva_name}' MATCHED as Wahlfach: '{wahlfach_name}' (substring/LIKE)")
                return True

        return False
