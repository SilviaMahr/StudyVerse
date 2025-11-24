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
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

        # Load ideal study plan for LLM context
        self.ideal_plan_loader = IdealPlanLoader()
        self.ideal_plan_context = self.ideal_plan_loader.format_ideal_plan_for_llm()

    def create_semester_plan(
        self,
        user_query: str,
        retrieved_lvas: List[Dict[str, Any]],
        ects_target: int,
        preferred_days: List[str],
        completed_lvas: Optional[List[str]] = None,
        desired_lvas: Optional[List[str]] = None,
    ) -> str:
        """
        Erstellt einen Semesterplan basierend auf retrieved LVAs und User-Präferenzen.

        Args:
            user_query: Original User Query
            retrieved_lvas: Liste von LVA-Dictionaries aus Retrieval
            ects_target: Gewünschte ECTS-Anzahl
            preferred_days: Liste bevorzugter Wochentage
            completed_lvas: Bereits absolvierte LVAs
            desired_lvas: Explizit gewünschte LVAs

        Returns:
            Formatierter Semesterplan als String
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
        )

        # Generate Plan
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.3}
            )
            return response.text

        except Exception as e:
            return f"Fehler bei der Planungserstellung: {e}"

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

            # Format als Stichpunkte
            formatted_lva = f"""
LVA {lva_info['Nr']}: {lva_info['Name']} ({lva_info['Type']})
  - ECTS: {lva_info['ECTS']}
  - Semester: {lva_info['Semester']}
  - Wochentag: {lva_info['Tag']} um {lva_info['Uhrzeit']}
  - LVA-Leiter: {lva_info['Leiter']}
  - Voraussetzungen: {lva_info['Voraussetzungen']}
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
    ) -> str:
        """Erstellt den LLM-Prompt für Semesterplanung."""

        prompt = f"""Du bist ein **Studienplanungs-Assistent** für Bachelor Wirtschaftsinformatik an der JKU.

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
   - Das ECTS-Ziel erreichen oder nah dran sind (max. ±3 ECTS Abweichung)
   - An den bevorzugten Tagen stattfinden
   - Keine zeitlichen Überschneidungen haben
   - Voraussetzungen erfüllen (bereits absolvierte LVAs beachten!)
   - Gewünschte LVAs priorisieren
   - Den idealtypischen Studienverlauf berücksichtigen (welche LVAs werden typischerweise in welchem Semester empfohlen?)

2. **Prüfe Voraussetzungen**:
   - Wenn eine LVA Voraussetzungen hat, prüfe ob diese erfüllt sind
   - Falls nicht erfüllt: NICHT vorschlagen und erklären warum

3. **Prüfe Zeitkonflikte**:
   - Keine zwei LVAs dürfen zur selben Zeit stattfinden
   - Berücksichtige Pufferzeiten zwischen LVAs (min. 15 Min)

4. **Erstelle einen strukturierten Semesterplan** mit:
   - Liste der vorgeschlagenen LVAs (Name, ECTS, Tag, Uhrzeit, Leiter)
   - Gesamte ECTS-Summe
   - Kurze Begründung pro LVA (warum vorgeschlagen?)
   - Hinweise zu nicht berücksichtigten gewünschten LVAs

**OUTPUT-FORMAT:**
Hier ist dein Plan für das [Semester] mit [X] ECTS. Deine Uni-Tage sind [Tage]:

- [LVA-Name] [Typ] - [ECTS] ECTS, [Tag] [Uhrzeit] ([Leiter])
- [LVA-Name] [Typ] - [ECTS] ECTS, [Tag] [Uhrzeit] ([Leiter])
...

**Gesamt: [X] ECTS**

**Begründung:**
[Erkläre kurz warum diese LVAs gewählt wurden und ob alle Wünsche erfüllt werden konnten]

**Hinweise:**
[Falls gewünschte LVAs nicht berücksichtigt wurden, erkläre warum (Voraussetzungen, Zeitkonflikte, etc.)]
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

        prompt = f"""Du bist ein **Studienberater** für Bachelor Wirtschaftsinformatik an der JKU.

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

    plan = planner.create_semester_plan(
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
