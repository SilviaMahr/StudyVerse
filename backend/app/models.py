# all modules (e.g. entities) go here

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ========== Planning Models ==========
# TODO extend this model when RAG can be implemented
#  (AFTER ETL Component is done)

class PlanningBase(BaseModel):
    #base model for inheritance
    title: str

class PlanningCreate(PlanningBase):
    #inherits from PlanningBase - nothing else to do!
    #used to create a planning session
    #later: POST/plannings/{id} in routes
    pass

#Necessary??? Should it be possible to edit recent plannings?
class PlanningUpdate(BaseModel):
    #to enable editing exisiting plannings
    title: Optional[str] = None

class Planning(PlanningBase):
    #extract the planning data from DB and insert here:
    id: int
    user_email: str
    created_at: datetime
    last_modified: datetime

    class Config:
        from_attributes = True

class PlanningResponse(BaseModel):
    #Sends data to client
    #GET /plannings/{id} in routes
    id: int
    title: str
    created_at: datetime
    last_modified: datetime

class RecentPlanningsResponse(BaseModel):
    #for side bar memory -> shows recent plannings
    #GET /plannings/recent in routes
    plannings: list[PlanningResponse]
    total: int