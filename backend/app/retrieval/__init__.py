"""
Retrieval Package: Hybrid RAG-System für Studienplanung

Komponenten:
- query_parser: Parsed natürlichsprachliche User Queries
- hybrid_retriever: Kombiniert Metadata-Filtering mit Vector Search
- semester_planner: LLM-basierte Semesterplanung
- rag_pipeline: End-to-End RAG Pipeline
"""

from .query_parser import (
    parse_user_query,
    build_metadata_filter,
    LVA_ALIASES,
)

from .hybrid_retriever import HybridRetriever

from .semester_planner import SemesterPlanner

from .ideal_plan_loader import IdealPlanLoader

from .rag_pipeline import StudyPlanningRAG


__all__ = [
    # Query Parser
    "parse_user_query",
    "build_metadata_filter",
    "LVA_ALIASES",

    # Retriever
    "HybridRetriever",

    # Planner
    "SemesterPlanner",

    # Ideal Plan
    "IdealPlanLoader",

    # Pipeline
    "StudyPlanningRAG",
]
