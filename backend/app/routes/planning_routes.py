# Planning routes for sidebar
# Endpoints for: Recent Plannings, New planning-session, planning-details
#TODO extend when RAG can be implemented

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import jwt
from datetime import datetime
from ..models import PlanningCreate, PlanningResponse, RecentPlanningsResponse, PlanningUpdate
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
        limit: int = 10,
        user_email: str = Depends(get_current_user_email)
):
    """
    Gibt die letzten Planning-Sessions des eingeloggten Users zurück.
    Sortiert nach last_modified (neueste zuerst).

    Parameters:
    - limit: Maximale Anzahl der zurückgegebenen Plannings (default: 10)
    - Authorization Header mit JWT-Token wird automatisch verarbeitet
    """
    pool = await init_db_pool()

    async with pool.acquire() as conn:
        # Extract planning data from DB
        rows = await conn.fetch(
            """
            SELECT id, title, user_email, created_at, last_modified
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

    Parameters:
    - planning_data: JSON Body mit "title" der neuen Planning
    - Authorization Header mit JWT-Token wird automatisch verarbeitet
    """
    pool = await init_db_pool()

    now = datetime.utcnow()

    async with pool.acquire() as conn:
        # add new planning in DB
        row = await conn.fetchrow(
            """
            INSERT INTO plannings (title, user_email, created_at, last_modified)
            VALUES ($1, $2, $3, $4)
                RETURNING id, title, created_at, last_modified
            """,
            planning_data.title,
            user_email,
            now,
            now
        )

    return PlanningResponse(
        id=row["id"],
        title=row["title"],
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
    Nur der Besitzer kann auf seine Planning zugreifen.

    Parameters:
    - planning_id: ID der Planning
    - Authorization Header mit JWT-Token wird automatisch verarbeitet
    """
    pool = await init_db_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, title, user_email, created_at, last_modified
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
        created_at=row["created_at"],
        last_modified=row["last_modified"]
    )


@router.put("/{planning_id}/access")
async def update_planning_access(
        planning_id: int,
        user_email: str = Depends(get_current_user_email)
):
    """
    Aktualisiert die last_modified Zeit einer Planning.
    Wird aufgerufen wenn User auf eine Planning zugreift.
    Hilft dabei die Reihenfolge der "Recent Plannings" aktuell zu halten.

    Parameters:
    - planning_id: ID der Planning
    - Authorization Header mit JWT-Token wird automatisch verarbeitet
    """
    pool = await init_db_pool()

    now = datetime.utcnow()

    async with pool.acquire() as conn:
        # check if planning exists and access is allowd
        #TODO check if recent plannings can be edited
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

        # if edited: update last_modified
        await conn.execute(
            """
            UPDATE plannings
            SET last_modified = $1
            WHERE id = $2
            """,
            now,
            planning_id
        )

    return {"status": "success", "message": "Planning access updated"}


@router.put("/{planning_id}", response_model=PlanningResponse)
async def update_planning(
        planning_id: int,
        planning_data: PlanningUpdate,
        user_email: str = Depends(get_current_user_email)
):
    """
    Aktualisiert eine Planning (z.B. Titel ändern).

    Parameters:
    - planning_id: ID der Planning
    - planning_data: JSON Body mit zu aktualisierenden Feldern
    - Authorization Header mit JWT-Token wird automatisch verarbeitet
    """
    pool = await init_db_pool()

    now = datetime.utcnow()

    async with pool.acquire() as conn:
        # Check if planning exists and user can access
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

        # update planning
        if planning_data.title is not None:
            await conn.execute(
                """
                UPDATE plannings
                SET title = $1, last_modified = $2
                WHERE id = $3
                """,
                planning_data.title,
                now,
                planning_id
            )

        # retrieve updated planning
        row = await conn.fetchrow(
            """
            SELECT id, title, created_at, last_modified
            FROM plannings
            WHERE id = $1
            """,
            planning_id
        )

    return PlanningResponse(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        last_modified=row["last_modified"]
    )


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