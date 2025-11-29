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
    title: Optional[str] = None #optional since auto generation
    semester: str = Field(..., pattern="^(SS|WS)\\d{2}$", description="Semester im Format SS26 oder WS25")
    target_ects: float = Field(..., ge=1, le=60, description="Geplante ECTS-Punkte")
    preferred_days: List[DayOfWeek] = Field(default=[DayOfWeek.ANY], description="Bevorzugte Tage")
    mandatory_courses: Optional[str] = Field(None, description="Freitext für obligatorische LVAs")

#Necessary??? Should it be possible to edit recent plannings?
class PlanningUpdate(BaseModel):
    #to enable editing exisiting plannings
    title: Optional[str] = None
    semester: Optional[str] = Field(None, pattern="^(SS|WS)\\d{2}$")
    target_ects: Optional[float] = Field(None, ge=1, le=60)
    preferred_days: Optional[List[DayOfWeek]] = None
    mandatory_courses: Optional[str] = None

class PlanningResponse(BaseModel):
    #Sends data to client
    #GET /plannings/{id} in routes
    id: int
    title: str
    semester: str
    target_ects: float #war int
    preferred_days: List[str]
    mandatory_courses: Optional[str]
    semester_plan_json: Optional[dict] = None  # LLM-generated semester plan as JSON
    created_at: datetime
    last_modified: datetime

    class Config:
        from_attributes = True

class RecentPlanningsResponse(BaseModel):
    #for side bar memory -> shows recent plannings
    #GET /plannings/recent in routes
    plannings: List[PlanningResponse]
    total: int #total number of plannings - can stay int

# To start RAG
#TODO: adapt if necessary as soon as RAG is ready for further implementation
#starts a RAG session
class RAGStartRequest(BaseModel):
    planning_id: int
    user_query: Optional[str] = None

#response model (contains all the data that the backend sends to the client when
# interacting with the rag
#TODO: adapt if necessary as soon as RAG is ready for further implementation
class RAGStartResponse(BaseModel):
    success: bool
    planning_id: int
    message: str
    session_id: Optional[str] = None

# Chat models
#TODO: maybe changes necessry later in process
# ========== Chat Models ==========

class ChatMessage(BaseModel):
    """Eine Chat-Nachricht"""
    id: int
    role: str  # 'user' oder 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[dict] = None

class ChatSendRequest(BaseModel):
    """Request zum Senden einer Nachricht"""
    message: str

class ChatHistoryResponse(BaseModel):
    """Response mit Chat-History"""
    planning_id: int
    messages: List[ChatMessage]
    total: int

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    studiengang: str ="Bachelor Wirtschaftsinformatik"
# ========== Profile models ==========

#user data
class UserProfile(BaseModel):
    id: int
    username: Optional[str] = None
    email: str
    studiengang: str = "Bachelor Wirtschaftsinformatik"
    #hard-coded - only one to be served right now

#update profile if username or email changes.
class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    studiengang: Optional[str] = None #optional - inculded for possible enhancement

# ========== LVA models ==========

#single lva
class LVA(BaseModel):
    id: int
    hierarchielevel0: str  # Pflichtfach/Wahlfach
    hierarchielevel1: str  # Modul
    hierarchielevel2: str  # Kurs-Name
    type: str              # VL, UE, PR, etc.
    name: str              # Voller Name
    ects: float               # war vorher int
    is_completed: bool = False  # completed by user?

#module inkluding it´s lvas: zB Grundlagen der Informatik with
# Einf. Inf, Operational Systems, Soft1 VL + UE
class LVAModule(BaseModel):
    module_name: str        # hierarchielevel1
    lvas: List[LVA]
    total_ects: float       # war vorher int

#hierarchie sends a liste of all modules with it´s courses
class LVAHierarchy(BaseModel):
    category: str           # Pflichtfach oder Wahlfach
    modules: List[LVAModule]

#response for client - deliveres entire lva-structure
class PflichtfaecherResponse(BaseModel):
    pflichtfaecher: List[LVAModule]

#response for client - deliveres entire lva-structure
class WahlfaecherResponse(BaseModel):
    wahlfaecher: List[LVAModule]

#client request -> sends updated completed_lva data
class CompletedLVAsUpdate(BaseModel):
    lva_ids: List[int]
