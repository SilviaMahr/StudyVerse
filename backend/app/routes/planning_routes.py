# Planning routes for sidebar
# Endpoints for: Recent Plannings, New planning-session, planning-details
#TODO extension might be necessary after final rag implementation

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import jwt
from datetime import datetime
from ..models import (
    PlanningCreate, PlanningResponse, RecentPlanningsResponse,
    PlanningUpdate, RAGStartRequest, RAGStartResponse, DayOfWeek
)
from ..db import init_db_pool
from ..auth import JWT_SECRET, JWT_ALGORITHM
from fastapi.security import OAuth2PasswordBearer


#necessary for session management in every routes file
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

#all endpoints in this router need a valid token!
router = APIRouter(
    prefix="/plannings",
    tags=["Plannings"],
    dependencies=[Depends(oauth2_scheme)]
)

# ========== Helper Functions ==========

async def get_current_user_email(authorization: str = Header(None)) -> str:
    """
    Extrahiert die User-Email aus dem JWT-Token im Authorization-Header
    Format: "Bearer <token>"
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ========== API Endpoints ==========

@router.get("/recent", response_model=RecentPlanningsResponse)
async def get_recent_plannings(
        limit: int = 5,
        user_email: str = Depends(get_current_user_email)
):
    """
    Gibt die letzten Planning-Sessions des eingeloggten Users zurück.

    """
    pool = await init_db_pool()

    async with pool.acquire() as conn:
        # Extract planning data from DB
        rows = await conn.fetch(
            """
            SELECT id, title, semester, target_ects, preferred_days,
                   mandatory_courses, created_at, last_modified
            FROM plannings
            WHERE user_email = $1
            ORDER BY last_modified DESC
                LIMIT $2
            """,
            user_email,
            limit
        )

        # count total plannings for user
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM plannings WHERE user_email = $1",
            user_email
        )

    # convert for response model (for client transfer)
    plannings = [
        PlanningResponse(
            id=row["id"],
            title=row["title"],
            semester=row["semester"],
            target_ects=row["target_ects"],
            preferred_days=row["preferred_days"] or [],
            mandatory_courses=row["mandatory_courses"],
            created_at=row["created_at"],
            last_modified=row["last_modified"]
        )
        for row in rows
    ]
    return RecentPlanningsResponse(plannings=plannings, total=total or 0)


@router.post("/new", response_model=PlanningResponse)
async def create_new_planning(
        planning_data: PlanningCreate,
        user_email: str = Depends(get_current_user_email)
):
    """
    Erstellt eine neue Planning-Session für den eingeloggten User.

    """
    pool = await init_db_pool()
    now = datetime.utcnow()

    # automatic title (semester and ects)
    if planning_data.semester and planning_data.target_ects is not None:
        title = f"{planning_data.semester} - {planning_data.target_ects} ECTS"
    else:
        # Fallback if somehow no data provided
        title = f"Planning {now.strftime('%Y-%m-%d')}"

    async with pool.acquire() as conn:
        # add new planning in DB
        row = await conn.fetchrow(
            """
            INSERT INTO plannings
            (title, user_email, semester, target_ects, preferred_days, mandatory_courses, created_at, last_modified)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, title, semester, target_ects, preferred_days, mandatory_courses, created_at, last_modified
            """,
            title,
            user_email,
            planning_data.semester,
            planning_data.target_ects,
            planning_data.preferred_days,
            planning_data.mandatory_courses,
            now,
            now
        )

    return PlanningResponse(
        id=row["id"],
        title=row["title"],
        semester=row["semester"],
        target_ects=row["target_ects"],
        preferred_days=row["preferred_days"] or [],
        mandatory_courses=row["mandatory_courses"],
        created_at=row["created_at"],
        last_modified=row["last_modified"]
    )


@router.get("/{planning_id}", response_model=PlanningResponse)
async def get_planning(
        planning_id: int,
        user_email: str = Depends(get_current_user_email)
):
    """
    Gibt die Details einer bestimmten Planning zurück.
    """
    pool = await init_db_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, title, semester, target_ects, preferred_days,
                   mandatory_courses, created_at, last_modified
            FROM plannings
            WHERE id = $1 AND user_email = $2
            """,
            planning_id,
            user_email
        )

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Planning not found or you don't have access"
        )

    return PlanningResponse(
        id=row["id"],
        title=row["title"],
        semester=row["semester"],
        target_ects=row["target_ects"],
        preferred_days=row["preferred_days"] or [],
        mandatory_courses=row["mandatory_courses"],
        created_at=row["created_at"],
        last_modified=row["last_modified"]
    )

#todo check if planning update is wanted!
@router.put("/{planning_id}", response_model=PlanningResponse)
async def update_planning(
        planning_id: int,
        planning_data: PlanningUpdate,
        user_email: str = Depends(get_current_user_email)
):
    """
    Aktualisiert eine Planning.
    """
    pool = await init_db_pool()
    now = datetime.utcnow()

    async with pool.acquire() as conn:
        # Prüfe ob Planning existiert
        exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM plannings
                WHERE id = $1 AND user_email = $2
            )
            """,
            planning_id,
            user_email
        )

        if not exists:
            raise HTTPException(
                status_code=404,
                detail="Planning not found or you don't have access"
            )

        # Baue dynamisches UPDATE Statement
        update_fields = []
        params = []
        param_count = 1

        if planning_data.title is not None:
            update_fields.append(f"title = ${param_count}")
            params.append(planning_data.title)
            param_count += 1

        if planning_data.semester is not None:
            update_fields.append(f"semester = ${param_count}")
            params.append(planning_data.semester)
            param_count += 1

        if planning_data.target_ects is not None:
            update_fields.append(f"target_ects = ${param_count}")
            params.append(planning_data.target_ects)
            param_count += 1

        if planning_data.preferred_days is not None:
            update_fields.append(f"preferred_days = ${param_count}")
            params.append(planning_data.preferred_days)
            param_count += 1

        if planning_data.mandatory_courses is not None:
            update_fields.append(f"mandatory_courses = ${param_count}")
            params.append(planning_data.mandatory_courses)
            param_count += 1

        # Füge last_modified hinzu
        update_fields.append(f"last_modified = ${param_count}")
        params.append(now)
        param_count += 1

        # Füge WHERE-Bedingungen hinzu
        params.append(planning_id)
        where_clause = f"WHERE id = ${param_count}"

        # Führe UPDATE aus
        if update_fields:
            query = f"UPDATE plannings SET {', '.join(update_fields)} {where_clause}"
            await conn.execute(query, *params)

        # Hole aktualisierte Planning
        row = await conn.fetchrow(
            """
            SELECT id, title, semester, target_ects, preferred_days,
                   mandatory_courses, created_at, last_modified
            FROM plannings
            WHERE id = $1
            """,
            planning_id
        )
    return PlanningResponse(
        id=row["id"],
        title=row["title"],
        semester=row["semester"],
        target_ects=row["target_ects"],
        preferred_days=row["preferred_days"] or [],
        mandatory_courses=row["mandatory_courses"],
        created_at=row["created_at"],
        last_modified=row["last_modified"]
    )

@router.put("/{planning_id}/access")
async def update_planning_access(
        planning_id: int,
        user_email: str = Depends(get_current_user_email)
):
    """Aktualisiert last_modified beim Zugriff."""
    pool = await init_db_pool()
    now = datetime.utcnow()

    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM plannings
                WHERE id = $1 AND user_email = $2
            )
            """,
            planning_id,
            user_email
        )

        if not exists:
            raise HTTPException(
                status_code=404,
                detail="Planning not found or you don't have access"
            )

        await conn.execute(
            "UPDATE plannings SET last_modified = $1 WHERE id = $2",
            now,
            planning_id
        )

    return {"status": "success", "message": "Planning access updated"}

@router.delete("/{planning_id}")
async def delete_planning(
        planning_id: int,
        user_email: str = Depends(get_current_user_email)
):
    """
    Löscht eine Planning.

    Parameters:
    - planning_id: ID der Planning
    - Authorization Header mit JWT-Token wird automatisch verarbeitet
    """
    pool = await init_db_pool()

    async with pool.acquire() as conn:
        # Prüfen ob Planning existiert und User Zugriff hat
        exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM plannings
                WHERE id = $1 AND user_email = $2
            )
            """,
            planning_id,
            user_email
        )

        if not exists:
            raise HTTPException(
                status_code=404,
                detail="Planning not found or you don't have access"
            )

        # delete planning
        await conn.execute(
            "DELETE FROM plannings WHERE id = $1",
            planning_id
        )

    return {"status": "success", "message": "Planning deleted"}
