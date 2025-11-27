"""
Ergänzt fehlende SS-Daten in der Datenbank
"""

import os
from dotenv import load_dotenv
from typing import List
from langchain_core.documents import Document
import data_ingestion.extractor as extractor
import data_ingestion.processor as processor
import psycopg2
import psycopg2.extras
import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

GOOGLE_EMBEDDING_MODEL = "models/text-embedding-004"
GEMINI_API_KEY_VALUE = os.getenv("GEMINI_API_KEY")

model = GoogleGenerativeAIEmbeddings(
    model=GOOGLE_EMBEDDING_MODEL,
    google_api_key=GEMINI_API_KEY_VALUE
)


def store_html_chunks(conn, chunks, url: str):
    try:
        cur = conn.cursor()

        insert_query = """
                       INSERT INTO studyverse_data
                           (content, metadata, embedding, url)
                       VALUES (%s, %s, %s, %s); \
                       """

        data_to_insert = []
        for chunk in chunks:
            metadata_dict = chunk.get("metadata", {})

            if not metadata_dict:
                metadata_value = None
            else:
                metadata_value = json.dumps(metadata_dict)

            data_to_insert.append((
                chunk.get("text"),
                metadata_value,
                chunk.get("embedding"),
                url
            ))

        cur.executemany(insert_query, data_to_insert)

        conn.commit()
        print(f"--> {len(data_to_insert)} Chunks gespeichert.")

    except psycopg2.Error as e:
        print(f"PostgreSQL Fehler: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Fehler: {e}")


def complete_ss_data():
    """Ergänzt fehlende SS-Daten"""
    neon_db_url = os.getenv("DATABASE_URL")

    print("=" * 80)
    print("ERGÄNZE FEHLENDE SS-DATEN")
    print("=" * 80)

    conn = psycopg2.connect(neon_db_url)
    conn.autocommit = True

    # Extrahiere SS-Daten mit Playwright
    (root_html, root_url) = extractor.extract_win_bsc_info_with_semester("SS")

    if not root_html:
        print("FEHLER: Konnte SS-Daten nicht laden!")
        return

    semester = extractor.extract_semester_info(root_html)
    course_links = extractor.extract_links(html=root_html)

    print(f"Gefunden: {len(course_links)} Kurse")

    successful = 0
    failed = 0

    for i, course_url in enumerate(course_links, 1):
        print(f"\n[{i}/{len(course_links)}] Bearbeite Kurs...")

        try:
            subject_links = extractor.extract_links(url=course_url)

            if not subject_links or len(subject_links) < 2:
                print(f"  WARNUNG: Keine Links gefunden. Ueberspringe...")
                failed += 1
                continue

            subject_url = subject_links[0]
            study_manual_url = subject_links[1]
            subject_html = extractor.fetch_content_from_div(subject_url)
            sm_subject_html = extractor.fetch_content_from_div(study_manual_url)
            course_data = extractor.extract_lva_links_for_course(subject_html)
            lva_links = course_data["lva_links"]
            semester_msg = course_data["semester_msg"]

            if lva_links:
                for lva_url in lva_links:
                    lva_html = extractor.fetch_content_from_div(lva_url)
                    lva_chunks = processor.process_html_page(lva_html, sm_subject_html, semester, model)
                    store_html_chunks(conn=conn, chunks=lva_chunks, url=lva_url)
                successful += 1
            elif semester_msg:
                # Kurs wird nur im WS angeboten
                other_semester = "WS"
                lva_chunks = processor.process_html_page(subject_html, sm_subject_html, other_semester, model)
                store_html_chunks(conn=conn, chunks=lva_chunks, url=subject_url)
                successful += 1

        except Exception as e:
            print(f"  FEHLER bei Kurs {i}: {e}")
            failed += 1
            continue

    print("\n" + "=" * 80)
    print("FERTIG!")
    print(f"Erfolgreich: {successful}, Fehler: {failed}")
    print("=" * 80)


if __name__ == "__main__":
    load_dotenv()
    complete_ss_data()
