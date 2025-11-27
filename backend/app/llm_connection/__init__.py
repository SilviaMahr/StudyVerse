"""
LLM Connection Package: LLM-based logic for semester planning

Components:
- semester_planner: LLM-based semester planning
- ideal_plan_loader: Loads ideal study plan for LLM context
"""

from .semester_planner import SemesterPlanner
from .ideal_plan_loader import IdealPlanLoader

__all__ = [
    "SemesterPlanner",
    "IdealPlanLoader",
]
