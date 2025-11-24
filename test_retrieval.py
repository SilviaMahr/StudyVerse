"""
Test-Skript für das komplette Retrieval-System
Testet Query Parsing, Retrieval und Semester Planning
"""

import sys
sys.path.append(".")

from backend.app.retrieval import StudyPlanningRAG


def test_semester_planning():
    """Testet die komplette Semester-Planung Pipeline."""
    print("="*80)
    print("TEST 1: SEMESTER PLANUNG")
    print("="*80)

    rag = StudyPlanningRAG()

    test_queries = [
        {
            "query": "Ich möchte 15 ECTS im SS26 machen, an Montag und Mittwoch. Ich möchte unbedingt SOFT1 machen.",
            "description": "Semester-Planung mit Tagen und gewünschter LVA"
        },
        {
            "query": "12 ECTS im Wintersemester, nur Dienstag und Donnerstag",
            "description": "Einfache Semester-Planung"
        },
        {
            "query": "18 ECTS SS26, Mo Di Mi, ich habe bereits BWL und EWIN absolviert",
            "description": "Mit bereits absolvierten LVAs"
        },
    ]

    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {test_case['description']}")
        print(f"{'='*80}")
        print(f"\nQUERY:\n{test_case['query']}")
        print(f"\n{'-'*80}\n")

        try:
            result = rag.create_semester_plan(test_case["query"], top_k=15)

            print("SEMESTER PLAN:")
            print("-"*80)
            print(result["plan"])

            print(f"\n{'-'*80}")
            print(f"DEBUG INFO:")
            print(f"  - Retrieved LVAs: {len(result['retrieved_lvas'])}")
            print(f"  - Parsed ECTS Target: {result['parsed_query']['ects_target']}")
            print(f"  - Parsed Semester: {result['parsed_query']['semester']}")
            print(f"  - Parsed Days: {result['parsed_query']['preferred_days']}")

        except Exception as e:
            print(f"FEHLER: {e}")
            import traceback
            traceback.print_exc()

        print("\n")


def test_question_answering():
    """Testet das Beantworten von allgemeinen Studienfragen."""
    print("\n" + "="*80)
    print("TEST 2: FRAGE BEANTWORTEN")
    print("="*80)

    rag = StudyPlanningRAG()

    test_questions = [
        "Muss ich in Softwareentwicklung eine Klausur schreiben?",
        "Wer unterrichtet Betriebssysteme?",
        "Wie viele ECTS hat Datenmodellierung?",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'-'*80}")
        print(f"FRAGE {i}: {question}")
        print(f"{'-'*80}")

        try:
            answer = rag.answer_question(question, top_k=5)
            print(f"\nANTWORT:\n{answer}")

        except Exception as e:
            print(f"FEHLER: {e}")
            import traceback
            traceback.print_exc()


def test_lva_search():
    """Testet die Suche nach spezifischen LVAs."""
    print("\n" + "="*80)
    print("TEST 3: LVA-SUCHE")
    print("="*80)

    rag = StudyPlanningRAG()

    search_terms = [
        "Softwareentwicklung",
        "BWL",
        "Datenmodellierung",
    ]

    for term in search_terms:
        print(f"\n{'-'*80}")
        print(f"SUCHE NACH: {term}")
        print(f"{'-'*80}")

        try:
            results = rag.search_lva_by_name(term)
            print(f"\nGefunden: {len(results)} LVAs\n")

            for i, lva in enumerate(results[:3], 1):  # Zeige nur Top 3
                metadata = lva.get("metadata", {})
                print(f"{i}. {metadata.get('lva_name', 'N/A')} ({metadata.get('lva_nr', 'N/A')})")
                print(f"   ECTS: {metadata.get('ects', 'N/A')}, Semester: {metadata.get('semester', 'N/A')}")
                print(f"   Tag: {metadata.get('tag', 'N/A')}, Zeit: {metadata.get('uhrzeit', 'N/A')}")
                print()

        except Exception as e:
            print(f"FEHLER: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         StudyVerse - Retrieval System Test Suite             ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    try:
        # Test 1: Semester Planning
        test_semester_planning()

        # Test 2: Question Answering
        test_question_answering()

        # Test 3: LVA Search
        test_lva_search()

        print("\n" + "="*80)
        print("ALLE TESTS ABGESCHLOSSEN!")
        print("="*80)

    except KeyboardInterrupt:
        print("\n\nTests abgebrochen durch User.")
    except Exception as e:
        print(f"\n\nFATALER FEHLER: {e}")
        import traceback
        traceback.print_exc()
