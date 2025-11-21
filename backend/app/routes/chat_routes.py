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
import sys
import os

# Import ChatWithLLM module
# Add the backend directory to path to access LLMConnection
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)
from backend.LLMConnection.ChatWithLLM import send_prompt_to_LLM

# OAuth2 for session management
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

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
    Sends a message to the LLM and returns the response.
    Stores both the user message and LLM response in the database.
    """
    print(f"📩 Received chat message from {user_email}: {request.message}")
    print(f"Planning ID: {planning_id}")

    pool = await init_db_pool()

    try:
        # Verify planning_id exists and belongs to user if provided
        if planning_id is not None:
            async with pool.acquire() as conn:
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

        # Save user message to database
        timestamp = datetime.utcnow()
        user_message_id = None

        if planning_id is not None:
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
                print(f"💾 Saved user message with ID: {user_message_id}")

        # Call the LLM with the user's message
        print("🔄 Calling LLM...")
        llm_response = await send_prompt_to_LLM(request.message)
        print(f"✅ LLM response received: {llm_response[:100]}...")

        # Save assistant response to database
        assistant_message_id = None

        if planning_id is not None:
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
                print(f"💾 Saved assistant message with ID: {assistant_message_id}")

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
        print(f"❌ Error in send_chat_message: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")


@router.get("/history/{planning_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    planning_id: int,
    limit: int = 50,
    user_email: str = Depends(get_current_user_email)
):
    """
    Retrieves the chat history for a specific planning session.
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
