# Chat routes for LLM interaction
# Endpoints for: Send message, Get chat history

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import jwt
from datetime import datetime
from ..models import ChatSendRequest, ChatMessage, ChatHistoryResponse
from ..db import init_db_pool
from ..auth import JWT_SECRET, JWT_ALGORITHM
from fastapi.security import OAuth2PasswordBearer
from ..retrieval.rag_pipeline import StudyPlanningRAG

# OAuth2 for session management
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Initialize RAG system
rag_system = StudyPlanningRAG()

# All endpoints in this router need a valid token!
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    dependencies=[Depends(oauth2_scheme)]
)

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

@router.post("/send")
async def send_chat_message(
        request: ChatSendRequest,
        planning_id: Optional[int] = None,
        user_email: str = Depends(get_current_user_email)
):
    """
    Sends a message to the RAG system and returns the response.

    Flow:
    1. First message in a planning session -> Generate semester plan with RAG
    2. Follow-up messages -> Answer questions with RAG Q&A

    Stores both the user message and assistant response in the database.
    """
    print(f"[CHAT] Received message from {user_email}: {request.message}")
    print(f"[CHAT] Planning ID: {planning_id}")

    pool = await init_db_pool()

    try:
        if planning_id is None:
            raise HTTPException(status_code=400, detail="planning_id is required")

        async with pool.acquire() as conn:
            # 1. Get user_id from email
            user_id = await conn.fetchval(
                "SELECT id FROM users WHERE email = $1",
                user_email
            )

            if not user_id:
                raise HTTPException(status_code=404, detail="User not found")

            # 2. Verify planning exists and belongs to user
            planning = await conn.fetchrow(
                """
                SELECT semester, target_ects, preferred_days, mandatory_courses, semester_plan_json, planning_context
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

            # 3. Check if this is the first user message (only greeting exists or no messages)
            message_count = await conn.fetchval(
                "SELECT COUNT(*) FROM chat_messages WHERE planning_id = $1 AND role = 'user'",
                planning_id
            )

        # Save user message to database
        timestamp = datetime.utcnow()
        user_message_id = None

        async with pool.acquire() as conn:
            user_message_id = await conn.fetchval(
                """
                INSERT INTO chat_messages (planning_id, role, content, timestamp)
                VALUES ($1, $2, $3, $4)
                    RETURNING id
                """,
                planning_id,
                'user',
                request.message,
                timestamp
            )
            print(f"[CHAT] Saved user message with ID: {user_message_id}")

        # 4. Get existing semester plan JSON from database
        semester_plan_json_raw = planning.get('semester_plan_json')

        if not semester_plan_json_raw:
            raise HTTPException(
                status_code=400,
                detail="No semester plan found. Please click 'Planung starten' first."
            )

        # Parse JSON string to dict if needed
        import json
        if isinstance(semester_plan_json_raw, str):
            semester_plan_json = json.loads(semester_plan_json_raw)
        else:
            semester_plan_json = semester_plan_json_raw

        print(f"[CHAT] Using existing semester plan with {len(semester_plan_json.get('lvas', []))} LVAs")

        # Get planning_context from planning (for optimal chat answers)
        planning_context = planning.get('planning_context')
        if planning_context:
            print(f"[CHAT] Using stored planning_context ({len(planning_context)} chars)")
        else:
            print("[CHAT] No planning_context found, will build from scratch")

        # 5. Answer question based on existing plan
        try:
            llm_response = rag_system.answer_question_with_plan(
                question=request.message,
                existing_plan_json=semester_plan_json,
                user_id=user_id,
                planning_context=planning_context,  # Pass stored context for exact parameters
                top_k=10
            )
            print(f"[CHAT] Generated answer (length: {len(llm_response)})")
        except Exception as e:
            print(f"[CHAT ERROR] {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

        # Save assistant response to database
        async with pool.acquire() as conn:
            assistant_message_id = await conn.fetchval(
                """
                INSERT INTO chat_messages (planning_id, role, content, timestamp)
                VALUES ($1, $2, $3, $4)
                    RETURNING id
                """,
                planning_id,
                'assistant',
                llm_response,
                datetime.utcnow()
            )
            print(f"[CHAT] Saved assistant message with ID: {assistant_message_id}")

        return {
            "success": True,
            "message": llm_response,
            "timestamp": timestamp.isoformat(),
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHAT ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get("/history/{planning_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
        planning_id: int,
        limit: int = 50,
        user_email: str = Depends(get_current_user_email)
):
    """
    Retrieves the chat history for a specific planning session.
    If no messages exist yet, creates and stores the initial greeting message.
    """
    pool = await init_db_pool()

    async with pool.acquire() as conn:
        # Verify that the planning belongs to the user
        planning_exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM plannings
                WHERE id = $1 AND user_email = $2
            )
            """,
            planning_id,
            user_email
        )

        if not planning_exists:
            raise HTTPException(status_code=404, detail="Planning not found or access denied")

        # Check if there are any messages
        message_count = await conn.fetchval(
            "SELECT COUNT(*) FROM chat_messages WHERE planning_id = $1",
            planning_id
        )

        # If no messages exist, create and store the greeting message
        if message_count == 0:
            greeting_message = "Hallo! Ich bin UNI, dein Planungsassistent. Du kannst mir Fragen zum Plan oder den LVAs stellen."
            greeting_id = await conn.fetchval(
                """
                INSERT INTO chat_messages (planning_id, role, content, timestamp)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                planning_id,
                'assistant',
                greeting_message,
                datetime.utcnow()
            )
            print(f"[CHAT] Created initial greeting message with ID: {greeting_id}")

        # Get chat messages
        rows = await conn.fetch(
            """
            SELECT id, role, content, timestamp
            FROM chat_messages
            WHERE planning_id = $1
            ORDER BY timestamp ASC
                LIMIT $2
            """,
            planning_id,
            limit
        )

        messages = [
            ChatMessage(
                id=row['id'],
                role=row['role'],
                content=row['content'],
                timestamp=row['timestamp']
            )
            for row in rows
        ]

        total = await conn.fetchval(
            "SELECT COUNT(*) FROM chat_messages WHERE planning_id = $1",
            planning_id
        )

        return ChatHistoryResponse(
            planning_id=planning_id,
            messages=messages,
            total=total
        )
