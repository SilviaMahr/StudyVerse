"""
Query Parser: Extrahiert strukturierte Informationen aus User Queries
Wandelt natürlichsprachliche Eingaben in Filter-Dictionaries um.
"""

import re
from typing import Dict, List, Optional, Any


# Mapping für LVA-Aliase (Soft1, Soft2, etc.)
LVA_ALIASES = {
    "soft1": ["Einführung in die Softwareentwicklung"],
    "esoft": ["Einführung in die Softwareentwicklung"],
    "soft2": ["Vertiefung Softwareentwicklung"],
    "algo" : ["Algorithmen und Datenstrukturen"],
    "algodat" : ["Algorithmen und Datenstrukturen"],
    "ewin": ["Einführung in die Wirtschaftsinformatik"],
    "bwl": ["Betriebswirtschaftslehre"],
    "dm": ["Datenmodellierung"],
    "dke": ["Data and Knowledge Engineering"],
}

# Semester-Patterns (für Freitext-Parsing als Fallback)
# Normalerweise kommen Semester-Werte direkt vom Frontend
SEMESTER_PATTERNS = {
    r"SS\s*\d{2}": "SS",  # SS26, SS 26
    r"WS\s*\d{2}": "WS",  # WS25, WS 25
    r"Sommersemester": "SS",
    r"Wintersemester": "WS",
}


def parse_user_query(query: str) -> Dict[str, Any]:
    """
    Parsed eine User Query und extrahiert:
    - ECTS-Ziel
    - Semester (SS/WS)
    - Bevorzugte Tage
    - Gewünschte LVAs
    - Freitext für semantische Suche

    Args:
        query: Natürlichsprachliche User-Anfrage

    Returns:
        Dictionary mit parsed parameters
    """
    query_lower = query.lower()

    result = {
        "ects_target": None,
        "semester": None,
        "preferred_days": [],
        "desired_lvas": [],
        "free_text": query,  # Originaler Text für semantische Suche
    }

    # 1. ECTS extrahieren
    ects_match = re.search(r"(\d{1,2})\s*ects", query_lower)
    if ects_match:
        result["ects_target"] = int(ects_match.group(1))

    # 2. Semester extrahieren
    for pattern, semester_code in SEMESTER_PATTERNS.items():
        if re.search(pattern, query, re.IGNORECASE):
            result["semester"] = semester_code
            break

    # 3. Wochentage extrahieren (nur als Fallback, Frontend liefert normalerweise direkt)
    # Die Werte kommen vom Frontend bereits formatiert als ["Mo.", "Di.", etc.]
    day_patterns = {
        r"\bmo\.?\b": "Mo.",
        r"\bdi\.?\b": "Di.",
        r"\bmi\.?\b": "Mi.",
        r"\bdo\.?\b": "Do.",
        r"\bfr\.?\b": "Fr.",
        r"montag": "Mo.",
        r"dienstag": "Di.",
        r"mittwoch": "Mi.",
        r"donnerstag": "Do.",
        r"freitag": "Fr.",
    }
    for pattern, day_code in day_patterns.items():
        if re.search(pattern, query_lower):
            if day_code not in result["preferred_days"]:
                result["preferred_days"].append(day_code)

    # 4. LVA-Aliase matchen
    for alias, lva_names in LVA_ALIASES.items():
        if alias in query_lower:
            result["desired_lvas"].extend(lva_names)

    return result


def build_metadata_filter(parsed_query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Erstellt ein Metadata-Filter-Dictionary für pgvector
    basierend auf der parsed query.

    Args:
        parsed_query: Output von parse_user_query()

    Returns:
        Filter-Dictionary für vector search
    """
    filter_conditions = []

    # 1. Semester-Filter
    if parsed_query["semester"]:
        # Suche nach LVAs die entweder im gewünschten Semester ODER ganzjährig angeboten werden
        semester_filter = {
            "$or": [
                {"semester": {"$eq": parsed_query["semester"]}},
                {"semester": {"$eq": f"{parsed_query['semester']}+"}},  # Ganzjährig
            ]
        }
        filter_conditions.append(semester_filter)

    # 2. Tage-Filter (wenn Tage angegeben wurden)
    if parsed_query["preferred_days"]:
        days_filter = {
            "tag": {"$in": parsed_query["preferred_days"]}
        }
        filter_conditions.append(days_filter)

    # 3. ECTS-Filter (optional: filtere nur LVAs mit <= target ECTS)
    if parsed_query["ects_target"]:
        ects_filter = {
            "ects": {"$lte": parsed_query["ects_target"]}
        }
        filter_conditions.append(ects_filter)

    # Kombiniere alle Filter mit AND
    if filter_conditions:
        if len(filter_conditions) == 1:
            return filter_conditions[0]
        else:
            return {"$and": filter_conditions}

    return {}


def extract_completed_lvas(user_input: str) -> List[str]:
    """
    Extrahiert bereits absolvierte LVAs aus User Input.

    Args:
        user_input: Text mit bereits absolvierten LVAs

    Returns:
        Liste von LVA-Namen/Codes
    """
    completed = []

    # Pattern: "absolviert: EWIN, SOFT1, BWL"
    absolviert_match = re.search(r"absolviert[e]?:?\s*([^.]+)", user_input, re.IGNORECASE)
    if absolviert_match:
        lva_string = absolviert_match.group(1)
        # Split by comma or "und"
        lvas = re.split(r",\s*|und\s+", lva_string)
        for lva in lvas:
            lva = lva.strip().lower()
            if lva in LVA_ALIASES:
                completed.extend(LVA_ALIASES[lva])
            else:
                completed.append(lva)

    return completed


# Test
if __name__ == "__main__":
    test_queries = [
        "Ich möchte 15 ECTS im SS26 machen, an Montag und Mittwoch. Ich möchte unbedingt SOFT1 machen.",
        "12 ECTS, WS25, nur Dienstag und Donnerstag",
        "Sommersemester, 18 ECTS, Mo Di Mi, SOFT2 und BWL",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        parsed = parse_user_query(query)
        print("\nParsed Result:")
        for key, value in parsed.items():
            print(f"  {key}: {value}")

        filter_dict = build_metadata_filter(parsed)
        print("\nMetadata Filter:")
        print(f"  {filter_dict}")
