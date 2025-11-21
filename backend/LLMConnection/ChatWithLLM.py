import os
import asyncio
from datetime import datetime
import google.generativeai as genai

from backend.app.db import init_db_pool

# API-Key aus Umgebungsvariable
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# ========== Get Info ========== ##
def retrieve_lvadata():
    context = "Die LVA hat den Namen Softwareentwicklung1 und wird im Sommersemester von Hrn. Schwinger abgehalten." # for 1st testing
    return context

# ========== Database Storage ========== ##
async def _store_message_into_db_async(role: str, content: str, planning_id=None):
    """
    Helper function to store a chat message into the database asynchronously.

    Args:
        role: The role of the message sender ('user' or 'assistant')
        content: The message content
        planning_id: Optional planning session ID to associate with the message

    Returns:
        The inserted chat_id or None if an error occurred
    """
    try:
        pool = await init_db_pool()
        async with pool.acquire() as conn:
            chat_id = await conn.fetchval(
                """
                INSERT INTO chat_messages (planning_id, role, content, timestamp)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                planning_id, role, content, datetime.utcnow()
            )
            print(f"✅ {role.capitalize()} message stored with chat_id: {chat_id}")
            return chat_id
    except Exception as e:
        print(f"❌ Error storing {role} message: {e}")
        return None


async def store_question_into_db_async(question, planning_id=None):
    """
    Stores the user's prompt into the database asynchronously.
    Returns the inserted chat_id.
    """
    return await _store_message_into_db_async('user', question, planning_id)


async def store_response_into_db_async(response_text, planning_id=None):
    """
    Stores the LLM response into the database asynchronously.
    Returns the inserted chat_id.
    """
    return await _store_message_into_db_async('assistant', response_text, planning_id)


async def send_prompt_to_LLM(question):
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")

    context = retrieve_lvadata()

    prompt = f"""
    Du bist ein **hilfsbereiter und präziser Assistent**, der alle Fragen zu den folgenden Lehrveranstaltungs-Daten (LVA) beantwortet.

    **WICHTIGE REGELN:**
    1. **Antworte AUSSCHLIESSLICH** basierend auf dem bereitgestellten Kontext. Erfinde **keine** Informationen.
    2. Erkläre kurz, wie du zu dieser Antwort gekommen bist.

    **KONTEXT (LVA-Daten):**
    {context}

    **FRAGE:**
    {question}

    **ANTWORT:**
    """
    print(prompt)
    # Note: Database storage is now handled by chat_routes.py to ensure planning_id is included

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.1}
    )

    # Note: Database storage is now handled by chat_routes.py to ensure planning_id is included
    return response.text


# ========== Receive answer ========== ##

async def main():
    """Main async function to run the chatbot."""
    print("=== ECTS planner ===\n")

    # Get question from user
    question = input("\nAsk something: ").strip()

    if not question:
        question = "How many ects has this LVA?"

    # Run RAG
    answer = await send_prompt_to_LLM(question)

    print("\n=== Answer ===")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())