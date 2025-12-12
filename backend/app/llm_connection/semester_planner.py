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

    def create_chat_answer(
        self,
        user_query: str,
        retrieved_lvas: List[Dict[str, Any]] = None,
        ects_target: int = None,
        preferred_days: List[str] = None,
        completed_lvas: Optional[List[str]] = None,
        desired_lvas: Optional[List[str]] = None,
        filtered_lvas: Optional[List[Dict[str, Any]]] = None,
        planning_context: Optional[str] = None,
    ) -> str:
        """
        Erstellt eine Text-Antwort für das Chat-Fenster.

        Args:
            user_query: Original User Query
            retrieved_lvas: Liste von LVA-Dictionaries aus Retrieval (optional wenn planning_context vorhanden)
            ects_target: Gewünschte ECTS-Anzahl (optional wenn planning_context vorhanden)
            preferred_days: Liste bevorzugter Wochentage (optional wenn planning_context vorhanden)
            completed_lvas: Bereits absolvierte LVAs (optional)
            desired_lvas: Explizit gewünschte LVAs (optional)
            filtered_lvas: LVAs die aufgrund fehlender Voraussetzungen gefiltert wurden (optional)
            planning_context: Gespeicherter Planning-Context aus DB (bevorzugt, wenn vorhanden)

        Returns:
            Chat-Antwort als String
        """
        # Use stored planning_context if available, otherwise build new one
        if planning_context:
            # Use the stored context from DB (best option - exact parameters from plan creation)
            context = planning_context
        else:
            # Fallback: Build new context from parameters (for backwards compatibility)
            if retrieved_lvas is None or ects_target is None or preferred_days is None:
                return "Fehler: Entweder planning_context oder alle Parameter (retrieved_lvas, ects_target, preferred_days) müssen angegeben werden."

            lva_list = self._format_lvas_for_prompt(retrieved_lvas)
            context = self._build_planning_context(
                user_query=user_query,
                lva_list=lva_list,
                ects_target=ects_target,
                preferred_days=preferred_days,
                completed_lvas=completed_lvas or [],
                desired_lvas=desired_lvas or [],
                filtered_lvas=filtered_lvas or [],
            )

        # Build chat prompt using the planning context
        prompt = self._build_planning_prompt(
            user_query=user_query,
            planning_context=context,
        )

        # Save prompt to file for debugging/testing in other LLMs
        if retrieved_lvas:
            self._save_prompt_to_file(prompt, user_query, len(retrieved_lvas))

        # Generate Answer
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
        filtered_lvas: Optional[List[Dict[str, Any]]] = None,  # NEU
    ) -> tuple[Dict[str, Any], str]:
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
            filtered_lvas: LVAs die aufgrund fehlender Voraussetzungen gefiltert wurden (optional)

        Returns:
            Tuple: (plan_json, planning_context)
            - plan_json: Dictionary mit Semesterplan-Daten (JSON-kompatibel)
            - planning_context: String mit Planning-Context (für DB-Speicherung und Chat)
        """
        import json

        # Format LVA-Liste für Prompt
        lva_list = self._format_lvas_for_prompt(retrieved_lvas)

        # Build Planning Context (wird in DB gespeichert für Chat-Antworten)
        planning_context = self._build_planning_context(
            user_query=user_query,
            lva_list=lva_list,
            ects_target=ects_target,
            preferred_days=preferred_days,
            completed_lvas=completed_lvas or [],
            desired_lvas=desired_lvas or [],
            filtered_lvas=filtered_lvas or [],
        )

        # Build Prompt mit JSON output format
        prompt = self._build_planning_prompt_json(
            user_query=user_query,
            lva_list=lva_list,
            ects_target=ects_target,
            preferred_days=preferred_days,
            completed_lvas=completed_lvas or [],
            desired_lvas=desired_lvas or [],
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
            return plan_json, planning_context

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse LLM response as JSON: {e}")
            print(f"[ERROR] Response was: {response.text[:500]}")
            return {
                "error": "JSON parsing failed",
                "raw_response": response.text[:500]
            }, planning_context
        except Exception as e:
            print(f"[ERROR] Error generating semester plan: {e}")
            return {
                "error": str(e)
            }, planning_context

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

            # Get Desktop path (handles OneDrive and other configurations)
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                    r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
                desktop_path = Path(winreg.QueryValueEx(key, 'Desktop')[0])
            except:
                # Fallback to standard path
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
================================================================\n
LVA {lva_info['Nr']}: {lva_info['Name']} ({lva_info['Type']})
================================================================\n
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
        planning_context: str,
    ) -> str:
        """
        Erstellt den LLM-Prompt für Chat-Antworten basierend auf dem Planning-Context.

        Args:
            user_query: User-Anfrage
            planning_context: Der Planning-Context (von _build_planning_context oder aus DB)

        Returns:
            LLM-Prompt als String
        """
        prompt = f"""{planning_context}

**AKTUELLE USER-ANFRAGE (zu beantworten):**
{user_query}

**OUTPUT-FORMAT:**
Beantworte die Frage des Users in natürlicher Sprache.
Antworte **ausschließlich** aufgrund Informationen, die dir zur Verfügung stehen. Wenn du Fragen zum Studium Bachelor
Wirtschaftinformatik nicht weißt, verweise auf das Studienhandbuch der JKU für unter https://studienhandbuch.jku.at/curr/1193 und
für allgemeine Fragen zum Studium an der JKU auf https://www.jku.at/
Formuliere deine Antwort **kurz** und freundlich.
"""
        return prompt

    def _build_planning_context(
        self,
        user_query: str,
        lva_list: str,
        ects_target: int,
        preferred_days: List[str],
        completed_lvas: List[str],
        desired_lvas: List[str],
        filtered_lvas: List[Dict[str, Any]] = None,
    ) -> str:
        """
        Erstellt den Planning-Context (ohne Output-Format-Anweisungen).
        Dieser Context wird in DB gespeichert und für Chat-Antworten wiederverwendet.
        """
        # Baue Filtered-LVAs-Section
        filtered_info = ""
        if filtered_lvas:
            for item in filtered_lvas:
                lva_name = item["lva"]["metadata"].get("lva_name", "Unknown")
                filtered_info += f"- {lva_name} \n"

        context = f"""Du bist UNI, ein **Studienplanungs-Assistent** für Bachelor Wirtschaftsinformatik an der JKU.

**USER-ANFRAGE:**
{user_query}

**ZIEL-PARAMETER:**
- maximales ECTS-Ziel: {ects_target} ECTS
- Bevorzugte Tage: {", ".join(preferred_days) if preferred_days else "Keine Angabe"}
- Bereits absolvierte LVAs: {", ".join(completed_lvas) if completed_lvas else "Keine"}
- Gewünschte LVAs: {", ".join(desired_lvas) if desired_lvas else "Keine spezifischen Wünsche"}

**VERFÜGBARE LVAs:**
{lva_list}

**Blacklist: diese LVAs dürfen NICHT im Plan aufscheinen: **\n
{filtered_info}

**DEINE AUFGABEN:**
1. **Wähle die optimalen LVAs** aus der Liste VERFÜGBARE LVAs, die:
   - Das ECTS-Ziel erreichen, eine Unterschreitung ist möglich, eine Überschreitung KEINESFALLS
   - An den bevorzugten Tagen stattfinden
   - plane den Typ "VL" und "UE" einer LVA **immer** im selben Semester
   - Bereits absolvierte Kurse dürfen **keinesfalls** im Plan vorkommen
   - jede LVA darf im Plan nur **einmal** vorkommen, LVA+Type ist die LVA id
   - priorisiere gewünschte LVAs

2. **Prüfe Voraussetzungen GRÜNDLICH**:
   - Nutze die DETAILLIERTEN INFORMATIONEN AUS STUDIENHANDBUCH für jede LVA
   - Prüfe "Anmeldevoraussetzungen" UND "Erwartete Vorkenntnisse"
   - Falls Voraussetzungen NICHT erfüllt: NICHT vorschlagen

3. **Prüfe Zeitkonflikte**:
   - Keine zwei LVAs dürfen zur selben Zeit stattfinden

4. **Priorität der Kurse im Plan**
    - falls die Kurse der STEOP (Studien Eingangs Orientierungs Phase) noch nicht absoviert wurden, müssen diese geplant werden:
        Einführung in die Softwareentwicklung UE, Einführung in die Softwareentwicklung VL, Grundlagen der BWL, Einführung in die Wirtschaftsinformatik
    - priorisiere Kurse, die im idealtypischen Studienplan in niedrigeren Semestern vorkommen
    \n {self.ideal_plan_context}
"""
        return context

    #changes made by Marlene -> because delivered data changed (due to pre-filtering)
    def _build_planning_prompt_json(
        self,
        user_query: str,
        lva_list: str,
        ects_target: int,
        preferred_days: List[str],
        completed_lvas: List[str],
        desired_lvas: List[str],
        filtered_lvas: List[Dict[str, Any]] = None,  # NEU
    ) -> str:
        """Erstellt den LLM-Prompt für Semesterplanung mit JSON-Output."""

        # Get the planning context (reusable part)
        context = self._build_planning_context(
            user_query=user_query,
            lva_list=lva_list,
            ects_target=ects_target,
            preferred_days=preferred_days,
            completed_lvas=completed_lvas,
            desired_lvas=desired_lvas,
            filtered_lvas=filtered_lvas,
        )

        # Add JSON output format instructions
        output_format = f"""
**OUTPUT-FORMAT:**
Antworte AUSSCHLIESSLICH mit einem gültigen JSON-Objekt in folgendem Format (KEIN anderer Text):

{{
  "semester": "{user_query.split()[0] if 'SS' in user_query or 'WS' in user_query else 'SS26'}",
  "total_ects": 0,
  "uni_days": [],
  "lvas": [
    {{
      "name": "Voller LVA-Name",
      "type": "VL|UE|PR|SE|KS|KV|PS|PE|PJ|KT",
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

        return context + output_format

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
