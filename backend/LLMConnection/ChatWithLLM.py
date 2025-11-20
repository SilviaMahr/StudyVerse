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
async def store_prompt_into_db_async(prompt, question, planning_id=None):
    """
    Stores the prompt into the database asynchronously.
    Returns the inserted chat_id.
    """
    try:
        pool = await init_db_pool()
        async with pool.acquire() as conn:
            # Store the user's question (prompt)
            chat_id = await conn.fetchval(
                """
                INSERT INTO chat_messages (planning_id, role, content, timestamp)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                planning_id, 'user', question, datetime.utcnow()
            )
            print(f"✅ Prompt stored with chat_id: {chat_id}")
            return chat_id
    except Exception as e:
        print(f"❌ Error storing prompt: {e}")
        return None


async def store_response_into_db_async(response_text, planning_id=None):
    """
    Stores the LLM response into the database asynchronously.
    """
    try:
        pool = await init_db_pool()
        async with pool.acquire() as conn:
            # Store the assistant's response
            chat_id = await conn.fetchval(
                """
                INSERT INTO chat_messages (planning_id, role, content, timestamp)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                planning_id, 'assistant', response_text, datetime.utcnow()
            )
            print(f"✅ Response stored with chat_id: {chat_id}")
            return chat_id
    except Exception as e:
        print(f"❌ Error storing response: {e}")
        return None


async def send_prompt_to_LLM(question):
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")

    context = retrieve_lvadata()

    prompt = f"""
    Du bist ein **hilfsbereiter und präziser Assistent**, der alle Fragen zu den folgenden Lehrveranstaltungs-Daten (LVA) beantwortet.

    **WICHTIGE REGELN:**
    1. **Antworte AUSSCHLIESSLICH** basierend auf dem bereitgestellten Kontext. Erfinde **keine** Informationen.
    2. Erkläre, wie du zu dieser Antwort gekommen bist.

    **KONTEXT (LVA-Daten):**
    {context}

    **FRAGE:**
    {question}

    **ANTWORT:**
    """
    print(prompt)
    await store_prompt_into_db_async(prompt, question)

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.1}
    )

    await store_response_into_db_async(response.text)
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