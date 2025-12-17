"""
Ideal Study Plan Loader: Lädt den idealtypischen Studienplan aus der DB
Der idealtypische Plan wird dem LLM als Kontext übergeben für bessere Entscheidungen.
"""

import os
import psycopg2
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class IdealPlanLoader:
    """
    Lädt den idealtypischen Studienplan aus der Datenbank.
    Dieser Plan gibt die empfohlene Reihenfolge der LVAs pro Semester an.
    """

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL not set in environment")

    def load_ideal_plan(self) -> List[Dict[str, Any]]:
        """
        Lädt den kompletten idealtypischen Studienplan aus der DB.

        Returns:
            Liste von Dictionaries mit LVA-Zuordnungen zu Semestern
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            # Hole alle Daten aus ideal_study_plan
            cur.execute("""
                SELECT DISTINCT *
                FROM ideal_study_plan
                WHERE study_mode = 'Teilzeit' AND study_start_mode = 'Start_WS'
                ORDER BY semester_num, lva_name
            """)

            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            ideal_plan = []
            for row in rows:
                ideal_plan.append(dict(zip(columns, row)))

            cur.close()
            conn.close()

            return ideal_plan

        except Exception as e:
            print(f"Error loading ideal study plan: {e}")
            return []

    def format_ideal_plan_for_llm(self) -> str:
        """
        Formatiert den idealtypischen Studienplan für LLM-Kontext.

        Returns:
            Formatierter String für LLM-Prompt
        """
        ideal_plan = self.load_ideal_plan()

        if not ideal_plan:
            return "Kein idealtypischer Studienplan verfügbar."

        # Gruppiere nach Semester
        by_semester = {}
        for entry in ideal_plan:
            semester = entry.get('semester_num', 'Unknown')
            if semester not in by_semester:
                by_semester[semester] = []
            by_semester[semester].append(entry)

        # Formatiere als Text
        formatted = "=== IDEALTYPISCHER STUDIENVERLAUF ===\n\n"

        for semester in sorted(by_semester.keys()):
            formatted += f"**Semester {semester}:**\n"
            lvas = by_semester[semester]

            for lva in lvas:
                lva_name = lva.get('lva_name', 'N/A')
                formatted += (f"  - {lva_name} \n")

            formatted += "\n"

        formatted += """
**HINWEIS:**
Dieser idealtypische Verlauf ist eine Empfehlung. Studierende können davon abweichen,
sollten aber Voraussetzungen und Abhängigkeiten beachten.
"""

        return formatted

