"""
Test-Skript für einen einzelnen Semester-Plan Test
Nutzt nur 1 LLM-Request, um Quota zu schonen
"""

import sys
sys.path.append(".")

from backend.app.retrieval import StudyPlanningRAG


def test_single_semester_plan():
    """Testet die Semester-Planung mit nur einer Query."""
    print("=" * 80)
    print("SINGLE TEST: SEMESTER PLANUNG")
    print("=" * 80)

    rag = StudyPlanningRAG()

    test_query = {
        "query": "Ich möchte 15 ECTS im SS26 machen, an Montag und Mittwoch. Ich möchte unbedingt SOFT1 machen.",
        "description": "Semester-Planung mit Tagen und gewünschter LVA"
    }

    print(f"\nQUERY: {test_query['query']}")
    print(f"DESCRIPTION: {test_query['description']}")
    print(f"\n{'-' * 80}\n")

    try:
        result = rag.create_semester_plan(test_query["query"], top_k=15)

        print("\n" + "=" * 80)
        print("SEMESTER PLAN:")
        print("=" * 80)
        print(result["plan"])

        print(f"\n{'-' * 80}")
        print(f"DEBUG INFO:")
        print(f"  - Retrieved LVAs: {len(result['retrieved_lvas'])}")
        print(f"  - Parsed ECTS Target: {result['parsed_query']['ects_target']}")
        print(f"  - Parsed Semester: {result['parsed_query']['semester']}")
        print(f"  - Parsed Days: {result['parsed_query']['preferred_days']}")

        print("\n" + "=" * 80)
        print("SUCCESS! Komplettes RAG-System funktioniert!")
        print("=" * 80)

    except Exception as e:
        print(f"FEHLER: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_single_semester_plan()
