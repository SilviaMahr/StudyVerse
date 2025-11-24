"""
Integriertes RAG-System: Kombiniert Query Parsing, Hybrid Retrieval und LLM-Planung
End-to-End Pipeline für Studienplanung.
"""

from typing import Dict, List, Any, Optional
from .query_parser import parse_user_query, build_metadata_filter, extract_completed_lvas
from .hybrid_retriever import HybridRetriever
from .semester_planner import SemesterPlanner


class StudyPlanningRAG:
    """
    End-to-End RAG-System für Studienplanung:
    1. Query Parsing (User Input → Structured Parameters)
    2. Hybrid Retrieval (Metadata Filter + Vector Search)
    3. LLM Planning (Semester Plan Generation)
    """

    def __init__(self):
        self.retriever = HybridRetriever()
        self.planner = SemesterPlanner()

    def create_semester_plan(
        self,
        user_query: str,
        top_k: int = 20,
    ) -> Dict[str, Any]:
        """
        Hauptfunktion: Erstellt einen Semesterplan aus natürlichsprachlicher Query.

        Args:
            user_query: Natürlichsprachliche User-Anfrage
            top_k: Anzahl LVAs für Retrieval

        Returns:
            Dictionary mit Plan, retrieved LVAs und Debug-Info
        """
        # 1. Parse User Query
        print("1. Parsing User Query...")
        parsed_query = parse_user_query(user_query)
        completed_lvas = extract_completed_lvas(user_query)

        print(f"   ECTS-Ziel: {parsed_query['ects_target']}")
        print(f"   Semester: {parsed_query['semester']}")
        print(f"   Tage: {parsed_query['preferred_days']}")
        print(f"   Gewünschte LVAs: {parsed_query['desired_lvas']}")
        print(f"   Absolvierte LVAs: {completed_lvas}")

        # 2. Build Metadata Filter
        print("\n2. Building Metadata Filter...")
        metadata_filter = build_metadata_filter(parsed_query)
        print(f"   Filter: {metadata_filter}")

        # 3. Hybrid Retrieval
        print("\n3. Performing Hybrid Retrieval...")
        retrieved_lvas = self.retriever.retrieve(
            query=parsed_query["free_text"],
            metadata_filter=metadata_filter,
            top_k=top_k,
        )
        print(f"   Retrieved {len(retrieved_lvas)} LVAs")

        # 4. LLM Planning
        print("\n4. Generating Semester Plan...")
        semester_plan = self.planner.create_semester_plan(
            user_query=user_query,
            retrieved_lvas=retrieved_lvas,
            ects_target=parsed_query["ects_target"] or 15,  # Default 15 ECTS
            preferred_days=parsed_query["preferred_days"],
            completed_lvas=completed_lvas,
            desired_lvas=parsed_query["desired_lvas"],
        )

        # 5. Return Results
        return {
            "plan": semester_plan,
            "retrieved_lvas": retrieved_lvas,
            "parsed_query": parsed_query,
            "metadata_filter": metadata_filter,
        }

    def answer_question(
        self,
        question: str,
        top_k: int = 10,
    ) -> str:
        """
        Beantwortet allgemeine Studienfragen (keine Semesterplanung).

        Args:
            question: User-Frage
            top_k: Anzahl LVAs für Kontext

        Returns:
            Antwort als String
        """
        print(f"Answering question: {question}")

        # Retrieval ohne harte Filter (semantische Suche)
        retrieved_lvas = self.retriever.retrieve(
            query=question,
            metadata_filter=None,
            top_k=top_k,
        )

        print(f"Retrieved {len(retrieved_lvas)} LVAs for context")

        # LLM Answer
        answer = self.planner.answer_study_question(
            question=question,
            context_lvas=retrieved_lvas,
        )

        return answer

    def search_lva_by_name(self, lva_name: str) -> List[Dict[str, Any]]:
        """
        Sucht eine spezifische LVA nach Name oder Alias.

        Args:
            lva_name: Name oder Alias (z.B. "SOFT1", "Softwareentwicklung")

        Returns:
            Liste von gefundenen LVAs
        """
        return self.retriever.retrieve_by_lva_name(lva_name)


# Main CLI für Testing
if __name__ == "__main__":
    print("="*60)
    print("StudyVerse - RAG-basierte Studienplanung")
    print("="*60)

    rag = StudyPlanningRAG()

    # Beispiel-Queries
    test_queries = [
        "Ich möchte 15 ECTS im SS26 machen, an Montag und Mittwoch. Ich möchte unbedingt SOFT1 machen.",
        "12 ECTS im Wintersemester, nur Dienstag und Donnerstag",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"USER QUERY: {query}")
        print("="*60)

        result = rag.create_semester_plan(query)

        print("\n" + "="*60)
        print("SEMESTER PLAN:")
        print("="*60)
        print(result["plan"])
        print()

    # Beispiel: Allgemeine Frage
    print("\n" + "="*60)
    print("EXAMPLE: General Question")
    print("="*60)

    question = "Muss ich in Softwareentwicklung eine Klausur schreiben?"
    answer = rag.answer_question(question)

    print(f"\nFRAGE: {question}")
    print(f"\nANTWORT:\n{answer}")
