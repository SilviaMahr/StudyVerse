"""
Semester Planner: LLM-basierte Logik für Semesterplanungsvorschläge
Nutzt Gemini für intelligente Kursauswahl und Konfliktauflösung.
"""

import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from .ideal_plan_loader import IdealPlanLoader

load_dotenv()

# ============================================================================
# DEBUG TOGGLE: Set to True to save prompts to Desktop, False to disable
# ============================================================================
#SAVE_PROMPTS_TO_FILE = False  # Change to True to enable prompt logging
SAVE_PROMPTS_TO_FILE = True

class SemesterPlanner:
    """
    LLM-basierter Semester-Planer:
    - Analysiert retrieved LVAs
    - Prüft Voraussetzungen
    - Löst Zeitkonflikte
    - Erstellt optimierte Semesterpläne mit Begründungen
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")

        genai.configure(api_key=api_key)

        # ============================================================================
        # TODO: Talk as a team which Gemini model should be used
        # Silvia: my key only works with gemini-2.5-flash-lite
        # Marlene: Currently using gemini-2.0-flash-exp (only model available with this API key)
        # NOTE: This model has strict free-tier limits (15 requests/min, 1500/day)
        # If you hit quota errors during testing, wait ~15 seconds between runs
        # Other models (gemini-1.5-flash, gemini-1.5-pro) return 404 with this API key
        # ============================================================================
        self.model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")

        # Load ideal study plan for LLM context
        self.ideal_plan_loader = IdealPlanLoader()
        self.ideal_plan_context = self.ideal_plan_loader.format_ideal_plan_for_llm()

    # Todo! Test-code from claude, to check if lvas without all prerequists can be eliminated before consulting the llm.
    def create_chat_answer(
        self,
        user_query: str,
        retrieved_lvas: List[Dict[str, Any]],
        ects_target: int,
        preferred_days: List[str],
        completed_lvas: Optional[List[str]],
        desired_lvas: Optional[List[str]],
        existing_plan_json: Dict[str, Any],
        filtered_lvas: Optional[List[Dict[str, Any]]] = None,  # NEU
    ) -> str:
        """
        Erstellt eine Text-Antwort für das Chat-Fenster basierend auf einem existierenden Semesterplan.
        Diese Methode wird nach create_semester_plan_json() aufgerufen.

        Args:
            user_query: Original User Query
            retrieved_lvas: Liste von LVA-Dictionaries aus Retrieval
            ects_target: Gewünschte ECTS-Anzahl
            preferred_days: Liste bevorzugter Wochentage
            existing_plan_json: Bereits erstellter Semesterplan aus create_semester_plan_json() (REQUIRED)
            completed_lvas: Bereits absolvierte LVAs
            desired_lvas: Explizit gewünschte LVAs
            filtered_lvas: LVAs die aufgrund fehlender Voraussetzungen gefiltert wurden (optional)

        Returns:
            Chat-Antwort als String basierend auf dem existierenden Plan
        """
        # Format LVA-Liste für Prompt
        lva_list = self._format_lvas_for_prompt(retrieved_lvas)

        # Build Prompt
        prompt = self._build_planning_prompt(
            user_query=user_query,
            lva_list=lva_list,
            ects_target=ects_target,
            preferred_days=preferred_days,
            completed_lvas=completed_lvas or [],
            desired_lvas=desired_lvas or [],
            existing_plan_json=existing_plan_json,
            filtered_lvas=filtered_lvas or [],  # NEU
        )

        # Save prompt to file for debugging/testing in other LLMs
        self._save_prompt_to_file(prompt, user_query, len(retrieved_lvas))

        # Generate Plan
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.3}
            )
            return response.text

        except Exception as e:
            return f"Fehler bei der Planungserstellung: {e}"

    def create_semester_plan_json(
        self,
        user_query: str,
        retrieved_lvas: List[Dict[str, Any]],
        ects_target: int,
        preferred_days: List[str],
        completed_lvas: Optional[List[str]] = None,
        desired_lvas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Erstellt einen Semesterplan als JSON für die Planning-Detail-Ansicht.
        Wird aufgerufen wenn "Planung starten" Button geklickt wird.

        Args:
            user_query: Original User Query
            retrieved_lvas: Liste von LVA-Dictionaries aus Retrieval
            ects_target: Gewünschte ECTS-Anzahl
            preferred_days: Liste bevorzugter Wochentage
            completed_lvas: Bereits absolvierte LVAs
            desired_lvas: Explizit gewünschte LVAs

        Returns:
            Dictionary mit Semesterplan-Daten (JSON-kompatibel)
        """
        import json

        # Format LVA-Liste für Prompt
        lva_list = self._format_lvas_for_prompt(retrieved_lvas)

        # Build Prompt mit JSON output format
        prompt = self._build_planning_prompt_json(
            user_query=user_query,
            lva_list=lva_list,
            ects_target=ects_target,
            preferred_days=preferred_days,
            completed_lvas=completed_lvas or [],
            desired_lvas=desired_lvas or [],
        )

        # Save prompt to file for debugging/testing in other LLMs
        self._save_prompt_to_file(prompt, user_query, len(retrieved_lvas))

        # Generate Plan
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.3}
            )

            # Parse JSON response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Parse JSON
            plan_json = json.loads(response_text)
            return plan_json

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse LLM response as JSON: {e}")
            print(f"[ERROR] Response was: {response.text[:500]}")
            return {
                "error": "JSON parsing failed",
                "raw_response": response.text[:500]
            }
        except Exception as e:
            print(f"[ERROR] Error generating semester plan: {e}")
            return {
                "error": str(e)
            }

    def _save_prompt_to_file(self, prompt: str, user_query: str, lva_count: int) -> None:
        """
        Saves the generated prompt to a .txt file for debugging and testing in other LLMs.
        Only saves if SAVE_PROMPTS_TO_FILE is True.

        Args:
            prompt: The full LLM prompt
            user_query: The original user query
            lva_count: Number of retrieved LVAs
        """
        # Check if prompt saving is enabled
        if not SAVE_PROMPTS_TO_FILE:
            return

        try:
            from datetime import datetime
            from pathlib import Path

            # Calculate prompt size
            prompt_length = len(prompt)
            prompt_tokens_approx = prompt_length // 4  # Rough estimate: 1 token ≈ 4 chars

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llm_prompt_{timestamp}.txt"

            # Get Desktop path (works on Windows, macOS, Linux)
            desktop_path = Path.home() / "Desktop"
            filepath = desktop_path / filename

            # Write to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("="*60 + "\n")
                f.write("LLM PROMPT FOR SEMESTER PLANNING\n")
                f.write("="*60 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"User Query: {user_query}\n")
                f.write(f"Retrieved LVAs: {lva_count}\n")
                f.write(f"Character count: {prompt_length:,}\n")
                f.write(f"Estimated tokens: ~{prompt_tokens_approx:,}\n")
                f.write("\n" + "="*60 + "\n")
                f.write("ACTUAL PROMPT:\n")
                f.write("="*60 + "\n\n")
                f.write(prompt)

            print(f"[DEBUG] Prompt saved to Desktop: {filepath}")
            print(f"[DEBUG] Prompt size: {prompt_length:,} chars (~{prompt_tokens_approx:,} tokens)")

        except Exception as e:
            print(f"[WARNING] Could not save prompt to file: {e}")

    def _format_lvas_for_prompt(self, lvas: List[Dict[str, Any]]) -> str:
        """Formatiert LVA-Liste für LLM-Prompt."""
        formatted = []

        for lva in lvas:
            metadata = lva.get("metadata", {})
            content = lva.get("content", "")

            # Extrahiere wichtige Info
            lva_info = {
                "Nr": metadata.get("lva_nr", "N/A"),
                "Name": metadata.get("lva_name", "N/A"),
                "Type": metadata.get("lva_type", "N/A"),
                "ECTS": metadata.get("ects", "N/A"),
                "Semester": metadata.get("semester", "N/A"),
                "Tag": metadata.get("tag", "N/A"),
                "Uhrzeit": metadata.get("uhrzeit", "N/A"),
                "Leiter": metadata.get("lva_leiter", "N/A"),
                "Voraussetzungen": metadata.get("anmeldevoraussetzungen", "Keine"),
            }

            # Format als Stichpunkte mit vollständigem Content
            formatted_lva = f"""
LVA {lva_info['Nr']}: {lva_info['Name']} ({lva_info['Type']})
  - ECTS: {lva_info['ECTS']}
  - Semester: {lva_info['Semester']}
  - Wochentag: {lva_info['Tag']} um {lva_info['Uhrzeit']}
  - LVA-Leiter: {lva_info['Leiter']}
  - Voraussetzungen: {lva_info['Voraussetzungen']}

  DETAILLIERTE INFORMATIONEN AUS STUDIENHANDBUCH:
  {content if content else "Keine weiteren Details verfügbar."}
"""
            formatted.append(formatted_lva.strip())

        return "\n\n".join(formatted)

    def _build_planning_prompt(
        self,
        user_query: str,
        lva_list: str,
        ects_target: int,
        preferred_days: List[str],
        completed_lvas: List[str],
        desired_lvas: List[str],
        existing_plan_json: Dict[str, Any],
    ) -> str:
        """
        Erstellt den LLM-Prompt für Chat-Antworten basierend auf einem existierenden Semesterplan.

        Args:
            user_query: User-Anfrage
            lva_list: Formatierte LVA-Liste für Kontext
            ects_target: ECTS-Ziel
            preferred_days: Bevorzugte Tage
            completed_lvas: Absolvierte LVAs
            desired_lvas: Gewünschte LVAs
            existing_plan_json: Bereits erstellter Semesterplan (REQUIRED)

        Returns:
            LLM-Prompt als String
        """
        import json
        plan_str = json.dumps(existing_plan_json, indent=2, ensure_ascii=False)

        prompt = f"""Du bist UNI, ein **Studienplanungs-Assistent** für Bachelor Wirtschaftsinformatik an der JKU.

**USER-ANFRAGE:**
{user_query}

**BEREITS ERSTELLTER SEMESTERPLAN:**
Der User hat bereits folgenden Semesterplan erstellt:

```json
{plan_str}
```
**ZIEL-PARAMETER:**
- ECTS-Ziel: {ects_target} ECTS
- Bevorzugte Tage: {", ".join(preferred_days) if preferred_days else "Keine Angabe"}
- Bereits absolvierte LVAs: {", ".join(completed_lvas) if completed_lvas else "Keine"}
- Gewünschte LVAs: {", ".join(desired_lvas) if desired_lvas else "Keine spezifischen Wünsche"}

**VERFÜGBARE LVAs (aus Vector-Search für Kontext):**
{lva_list}

**DEINE AUFGABEN:**
- Beantworte die User-Anfrage im Kontext des bereits existierenden Planes oben
- Beantworte die Frage **ausschließlich** aufgrund der Informationen des Kontexts
- Wenn du etwas nicht weißt, verweise auf https://studienhandbuch.jku.at/?lang=de

**OUTPUT-FORMAT:**
Antworte in natürlicher Sprache und beantworte die Frage des Users.
Formuliere deine Antwort **kurz** und freundlich.
"""
        return prompt

    def _build_planning_prompt_json(
        self,
        user_query: str,
        lva_list: str,
        ects_target: int,
        preferred_days: List[str],
        completed_lvas: List[str],
        desired_lvas: List[str],
    ) -> str:
        """Erstellt den LLM-Prompt für Semesterplanung mit JSON-Output."""

        prompt = f"""Du bist UNI, ein **Studienplanungs-Assistent** für Bachelor Wirtschaftsinformatik an der JKU.

{self.ideal_plan_context}

**USER-ANFRAGE:**
{user_query}

**ZIEL-PARAMETER:**
- ECTS-Ziel: {ects_target} ECTS
- Bevorzugte Tage: {", ".join(preferred_days) if preferred_days else "Keine Angabe"}
- Bereits absolvierte LVAs: {", ".join(completed_lvas) if completed_lvas else "Keine"}
- Gewünschte LVAs: {", ".join(desired_lvas) if desired_lvas else "Keine spezifischen Wünsche"}

**VERFÜGBARE LVAs (aus Vector-Search):**
{lva_list}

**DEINE AUFGABEN:**
1. **Wähle die optimalen LVAs** aus der Liste, die:
   - Das ECTS-Ziel erreichen, eine Unterschreitung um 3 ECTS ist möglich, eine Überschreitung nicht
   - An den bevorzugten Tagen stattfinden
   - Voraussetzungen erfüllen
   - Bereits absolvierte Kurse dürfen **keinesfalls** im Plan vorkommen
   - jede LVA darf im Plan nur **einmal** vorkommen, LVA+Type ist die LVA id
   - Gewünschte LVAs priorisieren

2. **Prüfe Voraussetzungen GRÜNDLICH**:
   - Nutze die DETAILLIERTEN INFORMATIONEN AUS STUDIENHANDBUCH für jede LVA
   - Prüfe "Anmeldevoraussetzungen" UND "Erwartete Vorkenntnisse"
   - Falls Voraussetzungen NICHT erfüllt: NICHT vorschlagen
   - berücksichtige den idealtypischen Studienverlauf

3. **Prüfe Zeitkonflikte**:
   - Keine zwei LVAs dürfen zur selben Zeit stattfinden

**OUTPUT-FORMAT:**
Antworte AUSSCHLIESSLICH mit einem gültigen JSON-Objekt in folgendem Format (KEIN anderer Text):

{{
  "semester": "{user_query.split()[0] if 'SS' in user_query or 'WS' in user_query else 'SS26'}",
  "total_ects": 0,
  "uni_days": [],
  "lvas": [
    {{
      "name": "Voller LVA-Name",
      "type": "VL/UE/PR",
      "ects": 0,
      "day": "Mo./Di./Mi./Do./Fr.",
      "time": "HH:MM - HH:MM",
      "instructor": "Name des Leiters",
      "reason": "Kurze Begründung"
    }}
  ],
  "summary": "Zusammenfassung der Planungsentscheidungen",
  "warnings": "Hinweise oder leerer String"
}}

WICHTIG:
- Antworte NUR mit dem JSON-Objekt
- Kein Text vor oder nach dem JSON
- Alle String-Werte in Anführungszeichen
- Zahlen ohne Anführungszeichen
"""

        return prompt

    def answer_study_question(self, question: str, context_lvas: List[Dict[str, Any]]) -> str:
        """
        Beantwortet allgemeine Studienfragen basierend auf LVA-Daten.

        Args:
            question: User-Frage (z.B. "Muss ich in BWL eine Klausur schreiben?")
            context_lvas: Relevante LVAs aus Retrieval

        Returns:
            Antwort als String
        """
        # Format LVAs
        lva_context = self._format_lvas_for_prompt(context_lvas)

        prompt = f"""Du bist UNI, ein **Studienplanungs-Assistent** für Bachelor Wirtschaftsinformatik an der JKU.

**FRAGE:**
{question}

**KONTEXT (Relevante LVA-Daten):**
{lva_context}

**WICHTIG:**
- Antworte AUSSCHLIESSLICH basierend auf den bereitgestellten Daten
- Wenn die Info nicht verfügbar ist, sage das klar
- Sei präzise und hilfsbereit

**ANTWORT:**
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.1}
            )
            return response.text

        except Exception as e:
            return f"Fehler bei der Beantwortung: {e}"


# Test
if __name__ == "__main__":
    print("=== Semester Planner Test ===\n")

    planner = SemesterPlanner()

    # Mock-Daten für Test
    mock_lvas = [
        {
            "metadata": {
                "lva_nr": "256.100",
                "lva_name": "Einführung in die Softwareentwicklung",
                "lva_type": "VL",
                "ects": 3.0,
                "semester": "SS",
                "tag": "Mo.",
                "uhrzeit": "08:30 - 10:00",
                "lva_leiter": "Wieland Schwinger",
                "anmeldevoraussetzungen": None,
            }
        },
        {
            "metadata": {
                "lva_nr": "256.101",
                "lva_name": "Einführung in die Softwareentwicklung",
                "lva_type": "UE",
                "ects": 3.0,
                "semester": "SS",
                "tag": "Mo.",
                "uhrzeit": "10:15 - 11:45",
                "lva_leiter": "Wieland Schwinger",
                "anmeldevoraussetzungen": None,
            }
        },
        {
            "metadata": {
                "lva_nr": "258.100",
                "lva_name": "Prozess- und Kommunikationsmodellierung",
                "lva_type": "VL",
                "ects": 3.0,
                "semester": "SS",
                "tag": "Mi.",
                "uhrzeit": "13:45 - 15:15",
                "lva_leiter": "Udo Kannengiesser",
                "anmeldevoraussetzungen": None,
            }
        },
    ]

    test_query = "15 ECTS im SS26, Montag und Mittwoch, ich möchte SOFT1 machen"

    plan = planner.create_chat_answer(
        user_query=test_query,
        retrieved_lvas=mock_lvas,
        ects_target=15,
        preferred_days=["Mo.", "Mi."],
        completed_lvas=[],
        desired_lvas=["Einführung in die Softwareentwicklung"],
    )

    print("USER QUERY:")
    print(test_query)
    print("\n" + "="*60)
    print("GENERATED PLAN:")
    print("="*60)
    print(plan)
