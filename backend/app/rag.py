# This will be the main file - code follows here

import os
import google.generativeai as genai
#from google import genai

#DUMMYCODE! TESTING ONLY - AI GENERATED
# API-Key aus Umgebungsvariable
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)


# LVAs dummy - retrieve component later
LVAs = {
    "ewin": (6, "ES", 1),
    "soft1": (6, "SS", 1),
    "bwl": (6, "ES", 1),
    "dm": (6, "WS", 2),
    "betriebssysteme": (3, "SS", 1),
}

def retrieve_lvadata(lva):
    """Retrieve lva data"""

    # 1. Hole die ECTS und den Semester-Code aus LVAs
    ects, semester_code, reihung = LVAs.get(lva, (None, None, None))


    # 2. Formatiere die Semesterangabe
    if semester_code == "SS":
        semester = "ausschließlich im Sommersemster"
    elif semester_code == "WS":
        semester = "ausschließlich im Wintersemster"
    elif semester_code == "ES":
        semester = "in jedem Semester"
    else:
        # Falls ein unerwarteter Code auftaucht
        semester = "nicht"

    context = f"""Die LVA hat den Namen {lva}, sie hat {ects} ECTS und wird {semester} angeboten. Sie hat die Reihung {reihung}.

    """


    return context


def store_prompt_into_db(prompt):
    pass


def store_response_into_db(response):
    pass


def rag_query(question, lva, ects, semester):
    """RAG: Retrieve LVA Data and generate answer"""

    # Step 1: Retrieve
    print("\nRetrieving lva data...")
    context = retrieve_lvadata(lva)
    print(context)

    # Step 2: Generate
    print("\nGenerating answer...")
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")

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
    store_prompt_into_db(prompt)

    model.generate_content()

    response = model.generate_content(
        prompt,
        # no hallus
        #temperature=0.0,
    )


    store_response_into_db(response)
    return response.text

if __name__ == "__main__":
    print("=== ECTS planner ===\n")

    # Get LVA from User
    print("Available LVAs:", ", ".join(LVAs.keys()))
    lva_input = input("\nEnter LVA name: ").strip().lower()

    if lva_input not in LVAs:
        print(f"LVA '{lva_input}' not found. Using EWIN as default.")
        lva_input = "ewin"

    ects, semester, reihung = LVAs[lva_input]

    # Get question from user
    question = input("\nAsk how many ects or in witch Semester LVA has/is: ").strip()

    if not question:
        question = "How many ects has this LVA?"

    # Run RAG
    answer = rag_query(question, lva_input, ects, semester)

    print("\n=== Answer ===")
    print(answer)