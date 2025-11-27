"""
RAG routes for semester plan generation
Endpoints for: Generate semester plan, Answer study questions
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import jwt
from datetime import datetime
from ..models import ChatSendRequest
from ..db import init_db_pool
from ..auth import JWT_SECRET, JWT_ALGORITHM
from fastapi.security import OAuth2PasswordBearer
from ..retrieval.rag_pipeline import StudyPlanningRAG


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
    dependencies=[Depends(oauth2_scheme)]
)

rag_system = StudyPlanningRAG()

# ========== Helper Functions ==========

async def get_current_user_email(authorization: str = Header(None)) -> str:
    """
    Extracts the user email from the JWT token in the Authorization header
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

@router.post("/{planning_id}/generate-plan")
async def generate_semester_plan(
    planning_id: int,
    user_email: str = Depends(get_current_user_email)
):
    """
    Generates a semester plan using RAG pipeline based on planning preferences.

    Steps:
    1. Gets user_id from email
    2. Gets planning details (semester, ECTS, preferred days, mandatory courses)
    3. Builds query from planning data
    4. Calls RAG Pipeline with user_id to fetch completed LVAs from DB
    5. Returns generated plan with retrieved LVAs
    """
    print(f"📊 Generating semester plan for planning_id={planning_id}, user={user_email}")

    pool = await init_db_pool()

    try:
        async with pool.acquire() as conn:
            # 1. Get user_id from email
            user_id = await conn.fetchval(
                "SELECT id FROM users WHERE email = $1",
                user_email
            )

            if not user_id:
                raise HTTPException(status_code=404, detail="User not found")

            # 2. Get planning details
            planning = await conn.fetchrow(
                """
                SELECT semester, target_ects, preferred_days, mandatory_courses
                FROM plannings
                WHERE id = $1 AND user_email = $2
                """,
                planning_id,
                user_email
            )

            if not planning:
                raise HTTPException(
                    status_code=404,
                    detail="Planning not found or access denied"
                )

        # 3. Build query from planning data
        semester = planning['semester']
        target_ects = planning['target_ects']
        preferred_days = planning['preferred_days'] or []
        mandatory_courses = planning['mandatory_courses']

        # Convert preferred_days list to readable format
        days_str = ", ".join(preferred_days) if preferred_days else "keine Einschränkungen"

        # Build natural language query
        query = f"Ich möchte {target_ects} ECTS im {semester} machen"

        if preferred_days:
            query += f", an {days_str}"

        if mandatory_courses:
            query += f". Ich möchte unbedingt folgende LVAs machen: {mandatory_courses}"

        print(f"📝 Built query: {query}")
        print(f"👤 User ID: {user_id}")

        # 4. Call RAG Pipeline with user_id
        result = rag_system.create_semester_plan(
            user_query=query,
            user_id=user_id,
            top_k=20
        )

        print(f"✅ Plan generated successfully")

        # 5. Return result
        return {
            "success": True,
            "planning_id": planning_id,
            "plan": result["plan"],
            "retrieved_lvas": result["retrieved_lvas"],
            "metadata_filter": result["metadata_filter"],
            "parsed_query": result["parsed_query"]
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in generate_semester_plan: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating semester plan: {str(e)}"
        )


@router.post("/ask")
async def ask_study_question(
    request: ChatSendRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Answers general study questions using RAG (without planning context).

    Example questions:
    - "Welchen Prüfungsmodus hat Datenmodellierung?"
    - "Was sind die Voraussetzungen für Software Engineering?"
    - "Wann findet EWIN statt?"
    """
    print(f"❓ Answering study question from {user_email}: {request.message}")

    try:
        # Call RAG Pipeline for Q&A (no user_id needed, no completed LVAs filter)
        answer = rag_system.answer_question(
            question=request.message,
            top_k=10
        )

        print(f"✅ Answer generated successfully")

        return {
            "success": True,
            "question": request.message,
            "answer": answer
        }

    except Exception as e:
        print(f"❌ Error in ask_study_question: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error answering question: {str(e)}"
        )
