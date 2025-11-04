# all modules (e.g. entities) go here

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

# ========== Planning Models ==========
# TODO extend this model when RAG can be implemented
#  (AFTER ETL Component is done)

class DayOfWeek(str, Enum):
    ANY = "keine Einschränkungen"
    MONDAY = "Montag"
    TUESDAY = "Dienstag"
    WEDNESDAY = "Mittwoch"
    THURSDAY = "Donnerstag"
    FRIDAY = "Freitag"


class PlanningCreate(BaseModel):
    title: str = Field(..., description="Titel der Planning-Session")
    semester: str = Field(..., pattern="^(SS|WS)\\d{2}$", description="Semester im Format SS26 oder WS25")
    target_ects: int = Field(..., ge=1, le=60, description="Geplante ECTS-Punkte")
    preferred_days: List[DayOfWeek] = Field(default=[DayOfWeek.ANY], description="Bevorzugte Tage")
    mandatory_courses: Optional[str] = Field(None, description="Freitext für obligatorische LVAs")

#Necessary??? Should it be possible to edit recent plannings?
class PlanningUpdate(BaseModel):
    #to enable editing exisiting plannings
    title: Optional[str] = None
    semester: Optional[str] = Field(None, pattern="^(SS|WS)\\d{2}$")
    target_ects: Optional[int] = Field(None, ge=1, le=60)
    preferred_days: Optional[List[DayOfWeek]] = None
    mandatory_courses: Optional[str] = None

class PlanningResponse(BaseModel):
    #Sends data to client
    #GET /plannings/{id} in routes
    id: int
    title: str
    semester: str
    target_ects: int
    preferred_days: List[str]
    mandatory_courses: Optional[str]
    created_at: datetime
    last_modified: datetime

    class Config:
        from_attributes = True

class RecentPlanningsResponse(BaseModel):
    #for side bar memory -> shows recent plannings
    #GET /plannings/recent in routes
    plannings: List[PlanningResponse]
    total: int

# To start RAG
#TODO maybe some editin necessary later when RAG is being implemented!
class RAGStartRequest(BaseModel):
    planning_id: int

class RAGStartResponse(BaseModel):
    status: str
    message: str
    session_id: Optional[str] = None