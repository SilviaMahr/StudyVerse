"""
Vereinfachter Test für das Retrieval-System
"""

import sys
sys.path.append(".")

from backend.app.retrieval import StudyPlanningRAG


def test_semester_planning():
    """Testet die komplette Semester-Planung Pipeline."""
    print("=" * 80)
    print("TEST: SEMESTER PLANUNG")
    print("=" * 80)

    rag = StudyPlanningRAG()

    test_query = "Ich moechte 15 ECTS im SS26 machen, an Montag und Mittwoch. Ich moechte unbedingt SOFT1 machen."

    print(f"\nQUERY: {test_query}")
    print(f"\n{'-' * 80}\n")

    try:
        result = rag.create_semester_plan(test_query, top_k=15)

        print("SEMESTER PLAN:")
        print("-" * 80)
        print(result["plan"])

        print(f"\n{'-' * 80}")
        print(f"DEBUG INFO:")
        print(f"  - Retrieved LVAs: {len(result['retrieved_lvas'])}")
        print(f"  - Parsed ECTS Target: {result['parsed_query']['ects_target']}")
        print(f"  - Parsed Semester: {result['parsed_query']['semester']}")
        print(f"  - Parsed Days: {result['parsed_query']['preferred_days']}")

        # Zeige die ersten 2 retrieved LVAs mit Content
        print(f"\n{'-' * 80}")
        print("BEISPIEL: ERSTE 2 RETRIEVED LVAs MIT CONTENT")
        print("-" * 80)
        for i, lva in enumerate(result['retrieved_lvas'][:5], 1):
            metadata = lva.get("metadata", {})
            content = lva.get("content", "")

            print(f"\nLVA {i}:")
            print(f"  Name: {metadata.get('lva_name', 'N/A')}")
            print(f"  Nr: {metadata.get('lva_nr', 'N/A')}")
            print(f"  ECTS: {metadata.get('ects', 'N/A')}")
            print(f"  Content-Laenge: {len(content)} Zeichen")
            print(f"  Content (erste 300 Zeichen):")
            print(f"  {content[:300]}...")

    except Exception as e:
        print(f"FEHLER: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\nStudyVerse - Retrieval System Test\n")

    try:
        test_semester_planning()
        print("\n" + "=" * 80)
        print("TEST ABGESCHLOSSEN!")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nTest abgebrochen durch User.")
    except Exception as e:
        print(f"\n\nFATALER FEHLER: {e}")
        import traceback
        traceback.print_exc()
