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
from ..retrieval.rag_pipeline import StudyPlanningRAG
from ..retrieval.query_parser import parse_user_query, build_metadata_filter
import json


#necessary for session management in every routes file
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Initialize RAG system
rag_system = StudyPlanningRAG()

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

    """
    pool = await init_db_pool()

    async with pool.acquire() as conn:
        # Extract planning data from DB
        rows = await conn.fetch(
            """
            SELECT id, title, semester, target_ects, preferred_days,
                   mandatory_courses, semester_plan_json, created_at, last_modified
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
            semester_plan_json=json.loads(row["semester_plan_json"]) if row["semester_plan_json"] else None,
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
    Generiert automatisch einen Semesterplan mit LLM beim Erstellen.

    """
    pool = await init_db_pool()
    now = datetime.utcnow()

    # automatic title (semester and ects)
    if planning_data.semester and planning_data.target_ects is not None:
        title = f"{planning_data.semester} - {planning_data.target_ects} ECTS"
    else:
        # Fallback if somehow no data provided
        title = f"Planning {now.strftime('%Y-%m-%d')}"

    print(f"[PLANNING] Creating new planning for {user_email}: {title}")

    # Get user_id for RAG system
    async with pool.acquire() as conn:
        user_id = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1",
            user_email
        )

        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")

    # Build query for RAG
    days_str = ", ".join(planning_data.preferred_days) if planning_data.preferred_days else "keine Einschränkungen"
    query = f"Ich möchte {planning_data.target_ects} ECTS im {planning_data.semester} machen"
    if planning_data.preferred_days:
        query += f", an {days_str}"
    if planning_data.mandatory_courses:
        query += f". Ich möchte unbedingt folgende LVAs machen: {planning_data.mandatory_courses}"

    print(f"[PLANNING] RAG Query: {query}")

    # Generate semester plan with RAG
    try:
        # Parse query
        parsed_query = parse_user_query(query)

        # Get completed LVAs
        completed_lvas = rag_system.retriever.get_completed_lvas_for_user(user_id)

        # Build metadata filter
        metadata_filter = build_metadata_filter(parsed_query)

        # Retrieve relevant LVAs
        retrieved_lvas = rag_system.retriever.retrieve(
            query=parsed_query["free_text"],
            metadata_filter=metadata_filter,
            top_k=20,
        )

        print(f"[PLANNING] Retrieved {len(retrieved_lvas)} LVAs")

        # Todo! Test-code from claude, to check if lvas without all prerequists can be eliminated before consulting the llm.
        # Filter basierend auf Voraussetzungen
        filter_result = rag_system.retriever.filter_by_prerequisites(
            retrieved_lvas=retrieved_lvas,
            completed_lvas=completed_lvas,
            target_semester=parsed_query.get("semester"),
            user_query=query  # NEU: User-Query für Wahlfach-Erkennung
        )

        eligible_lvas = filter_result["eligible"]
        filtered_lvas = filter_result["filtered"]

        print(f"[PLANNING] Eligible: {len(eligible_lvas)} LVAs")
        print(f"[PLANNING] Filtered: {len(filtered_lvas)} LVAs (missing prerequisites)")

        # Generate JSON semester plan (returns tuple: plan_json, planning_context)
        semester_plan_json, planning_context = rag_system.planner.create_semester_plan_json(
            user_query=query,
            retrieved_lvas=eligible_lvas,  # Nur eligible LVAs
            ects_target=parsed_query["ects_target"] or planning_data.target_ects,
            preferred_days=parsed_query["preferred_days"],
            completed_lvas=completed_lvas,
            desired_lvas=parsed_query["desired_lvas"],
            filtered_lvas=filtered_lvas,  # NEU: für Erklärungen
        )

        print(f"[PLANNING] Generated semester plan JSON: {semester_plan_json.keys()}")
        print(f"[PLANNING] Planning context length: {len(planning_context)} chars")

    except Exception as e:
        print(f"[PLANNING ERROR] Failed to generate semester plan: {e}")
        import traceback
        traceback.print_exc()
        semester_plan_json = {"error": str(e)}
        planning_context = ""  # Empty context on error

    # Insert planning with semester_plan_json and planning_context
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO plannings
            (title, user_email, semester, target_ects, preferred_days, mandatory_courses, semester_plan_json, planning_context, created_at, last_modified)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10)
                RETURNING id, title, semester, target_ects, preferred_days, mandatory_courses, semester_plan_json, created_at, last_modified
            """,
            title,
            user_email,
            planning_data.semester,
            planning_data.target_ects,
            planning_data.preferred_days,
            planning_data.mandatory_courses,
            json.dumps(semester_plan_json),  # Convert dict to JSON string for PostgreSQL
            planning_context,  # Store planning context for chat reuse
            now,
            now
        )

    print(f"[PLANNING] Created planning with ID: {row['id']}")

    # Parse JSON string back to dict for response
    semester_plan_dict = json.loads(row["semester_plan_json"]) if row["semester_plan_json"] else None

    return PlanningResponse(
        id=row["id"],
        title=row["title"],
        semester=row["semester"],
        target_ects=row["target_ects"],
        preferred_days=row["preferred_days"] or [],
        mandatory_courses=row["mandatory_courses"],
        semester_plan_json=semester_plan_dict,
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
                   mandatory_courses, semester_plan_json, created_at, last_modified
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
        semester_plan_json=json.loads(row["semester_plan_json"]) if row["semester_plan_json"] else None,
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
                   mandatory_courses, semester_plan_json, created_at, last_modified
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
        semester_plan_json=json.loads(row["semester_plan_json"]) if row["semester_plan_json"] else None,
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
