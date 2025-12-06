"""
Extract user query information and transfers it into filter-dictionaries
"""

import re
from typing import Dict, List, Optional, Any


# Mapping for known LVA-aliase (Soft1, Soft2, etc.)
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

# semster patterns (for manual chat input)
SEMESTER_PATTERNS = {
    r"SS\s*\d{2}": "SS",  # SS26, SS 26
    r"WS\s*\d{2}": "WS",  # WS25, WS 25
    r"Sommersemester": "SS",
    r"Wintersemester": "WS",
}


def parse_user_query(query: str) -> Dict[str, Any]:
    """
    paring and extracting the following information:
    - ECTS
    - Semester (SS/WS)
    - preferred days
    - desired lvas (free text)
    - Free text für semantic search
    returns dictionary with parsed params
    """

    query_lower = query.lower()

    result = {
        "ects_target": None,
        "semester": None,
        "preferred_days": [],
        "desired_lvas": [],
        "free_text": query,
    }

    # 1. extract ECTS
    ects_match = re.search(r"(\d{1,2})\s*ects", query_lower)
    if ects_match:
        result["ects_target"] = int(ects_match.group(1))

    # 2. extract semester
    for pattern, semester_code in SEMESTER_PATTERNS.items():
        if re.search(pattern, query, re.IGNORECASE):
            result["semester"] = semester_code
            break

    # 3. extract weekdays
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

    # 4. match aliases (if necessary)
    for alias, lva_names in LVA_ALIASES.items():
        if alias in query_lower:
            result["desired_lvas"].extend(lva_names)

    return result


def build_metadata_filter(parsed_query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates meta-data filter based on user query
    returns filter dictionary
    """
    filter_conditions = []

    # 1. filter semester
    if parsed_query["semester"]:
        # only lvas happening in the chosen semester or in both eg (SS, SS+WS, not WS)
        semester_filter = {
            "$or": [
                {"semester": {"$eq": parsed_query["semester"]}},
                {"semester": {"$eq": f"{parsed_query['semester']}+"}},  # Ganzjährig
            ]
        }
        filter_conditions.append(semester_filter)

    # 2.filter days
    if parsed_query["preferred_days"]:
        days_filter = {
            "tag": {"$in": parsed_query["preferred_days"]}
        }
        filter_conditions.append(days_filter)

    # 3. ects - lva must have less ects than target
    if parsed_query["ects_target"]:
        ects_filter = {
            "ects": {"$lte": parsed_query["ects_target"]}
        }
        filter_conditions.append(ects_filter)

    # combine and use and filter condition
    if filter_conditions:
        if len(filter_conditions) == 1:
            return filter_conditions[0]
        else:
            return {"$and": filter_conditions}

    return {}


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
