"""
This script serves as the main orchestrator for the StudyVerse data ingestion process.
It coordinates the extraction, transformation, and loading (ETL) of curriculum PDFs,
KUSSS course data (via web scraping), and Study Manual information into a
PostgreSQL/Neon vector database.

Writes to studyverse_data_new
SKIPS courses with a semester_msg (instead of saving them with the wrong semester)
NOTE: Still not bug-free, but the metadata is complete everywhere.
"""

import os
from dotenv import load_dotenv
from typing import List
from langchain_core.documents import Document
import data_ingestion.extractor as extractor
import data_ingestion.processor as processor
from langchain_community.vectorstores.pgvector import PGVector
import psycopg2
import psycopg2.extras
import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings


load_dotenv()

# Specifies the Google AI model used to generate 768-dim vectors.
GOOGLE_EMBEDDING_MODEL = "models/text-embedding-004"
GEMINI_API_KEY_VALUE = os.getenv("GEMINI_API_KEY")

# Ensures the Google API key is available in the environment for the generative AI client.
if GEMINI_API_KEY_VALUE:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY_VALUE
else:
    pass

# The initialized embedding engine used throughout the pipeline.
model = GoogleGenerativeAIEmbeddings(
    model=GOOGLE_EMBEDDING_MODEL,
    google_api_key=GEMINI_API_KEY_VALUE
)

# Table name: The database table where all processed chunks are stored.
TARGET_TABLE = "studyverse_data_new"

def check_env_variables(neon_db_url: str) -> bool:
    """
    Validates that required environment variables are present before starting.
    INPUT: neon_db_url (String).
    OUTPUT: bool - True if both API key and Database URL are found, else False.
    """
    is_valid = True

    if not GEMINI_API_KEY_VALUE or not GEMINI_API_KEY_VALUE.strip():
        print("GEMINI_API_KEY ist leer oder nicht gesetzt. Pipeline abgebrochen.")
        is_valid = False

    if not neon_db_url or not neon_db_url.strip():
        print("DATABASE_URL (NEON_DB_URL) ist leer oder nicht gesetzt. Pipeline abgebrochen.")
        is_valid = False

    return is_valid

def load_data_into_vector_store(conn, chunks: List[Document], embeddings, doc_url):
    """
    Loads curriculum data into the table
    Performs bulk insertion of PDF-derived chunks into the vector database.
    INPUT: conn (Database connection), chunks (List of Documents), embeddings (List of vectors), doc_url (Source URL/path).
    """
    try:
        cur = conn.cursor()

        insert_query = f"""
                       INSERT INTO {TARGET_TABLE}
                           (content, metadata, embedding, url)
                       VALUES (%s, %s, %s, %s);
                       """

        data_to_insert = []
        for i, chunk in enumerate(chunks):
            metadata_dict = chunk.metadata
            metadata_value = json.dumps(metadata_dict)

            data_to_insert.append((
                chunk.page_content, # Content from the PDF page segment
                metadata_value, # Serialized JSON metadata
                embeddings[i], # Pre-calculated vector embedding
                doc_url # Reference URL/File path
            ))

        cur.executemany(insert_query, data_to_insert)

        conn.commit()
        print(f"--> {len(data_to_insert)} Chunks für {doc_url} gespeichert.")

    except psycopg2.Error as e:
        print(f"PostgreSQL Fehler beim Speichern: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Allgemeiner Fehler beim Speichern: {e}")



def run_etl_pipeline():
    """
    The main control loop that executes the three ETL steps:
    1. PDF Curriculum processing.
    2. Dynamic KUSSS scraping for Winter and Summer semesters.
    3. Study Manual web scraping.
    """
    neon_db_url = os.getenv("DATABASE_URL")

    if not check_env_variables(neon_db_url):
        return

    print(f"\n{'='*80}")
    print(f"ETL-PIPELINE (FIXED VERSION) gestartet")
    print(f"Target Table: {TARGET_TABLE}")
    print(f"{'='*80}\n")

    conn = psycopg2.connect(neon_db_url)
    conn.autocommit = True

    ### IDEAL_PLAN DATA ETL (already manually done)

    ### CURRICULUM DATA ETL
    print("\n[1/3] Processing CURRICULUM data...")
    (curriculum_data, doc_url) = extractor.load_curriculum_data()
    if not curriculum_data:
        print("Pipeline beendet: Keine Quelldokumente gefunden.")
        return

    (processed_curriculum_chunks, curriculum_embeddings) = processor.process_documents(curriculum_data, model)
    if not processed_curriculum_chunks:
        print("Pipeline beendet: Nach der Verarbeitung keine Chunks übrig.")
        return

    load_data_into_vector_store(conn, processed_curriculum_chunks, curriculum_embeddings, doc_url)


    ### KUSSS DATA ETL - BOTH SEMESTERS (WS + SS)
    print("\n[2/3] Processing KUSSS data for both semesters...")
    semesters_to_process = ["WS", "SS"]

    for current_semester in semesters_to_process:
        print(f"\n{'='*80}")
        print(f"EXTRAHIERE DATEN FÜR {current_semester}")
        print(f"{'='*80}\n")

        # Use Playwright to extract the correct semester
        (root_html, root_url) = extractor.extract_win_bsc_info_with_semester(current_semester)

        if not root_html:
            print(f"FEHLER: Konnte {current_semester}-Daten nicht laden. Überspringe...")
            continue

        semester = extractor.extract_semester_info(root_html)
        chunks = processor.process_main_page(root_html, model)
        store_html_chunks(conn=conn, chunks=chunks, url=f"{root_url}?semester={current_semester}")
        course_links = extractor.extract_links(html=root_html)

        print(f"Gefunden: {len(course_links)} Kurse für {current_semester}")

        # Navigates from course overview to specific subject and manual pages.
        for course_url in course_links:
            # The one middle page
            subject_links = extractor.extract_links(url=course_url)

            # Check if the links are extracted
            if not subject_links or len(subject_links) < 2:
                print(f"WARNUNG: Konnte keine Links für {course_url} extrahieren. Überspringe...")
                continue

            subject_url = subject_links[0]
            study_manual_url = subject_links[1]
            subject_html = extractor.fetch_content_from_div(subject_url)
            ### STUDY MANUAL DATA ETL (part 1)
            sm_subject_html = extractor.fetch_content_from_div(study_manual_url)
            course_data = extractor.extract_lva_links_for_course(subject_html)
            lva_links = course_data["lva_links"]
            semester_msg = course_data["semester_msg"]

            if lva_links:
                # Course is offered in this semester -> process all LVAs
                for lva_url in lva_links:
                    lva_html = extractor.fetch_content_from_div(lva_url)
                    lva_chunks = processor.process_html_page(lva_html, sm_subject_html, semester, model)
                    store_html_chunks(conn=conn, chunks=lva_chunks, url=lva_url)
            elif semester_msg:
                # Course NOT offered in this semester -> SKIP
                # It will be crawled when processing the correct semester
                print(f"  [SKIP] Kurs nicht im {current_semester} angeboten: {subject_url}")
                continue  # Skip this course

        print(f"\n{current_semester}-Daten erfolgreich extrahiert!\n")

    ### STUDY MANUAL DATA ETL (part 2)
    print("\n[3/3] Processing STUDY MANUAL data...")
    study_manual_links = extractor.get_links_from_study_manual()
    for url in study_manual_links:
        subject_html = extractor.fetch_content_from_div(url)
        subject_chunks = processor.process_sm_html(subject_html, model)
        store_html_chunks(conn=conn, chunks=subject_chunks, url=url)

    print(f"\n{'='*80}")
    print("ETL-PIPELINE beendet!")
    print(f"{'='*80}\n")


def store_html_chunks(conn, chunks, url: str):
    """
    Store chunks in the table:
    Specialized loader for web-derived data chunks that already include embeddings.
    INPUT: conn (Database connection), chunks (List of dictionaries), url (String).
    """
    try:
        cur = conn.cursor()

        insert_query = f"""
                       INSERT INTO {TARGET_TABLE}
                           (content, metadata, embedding, url)
                       VALUES (%s, %s, %s, %s);
                       """

        data_to_insert = []
        for chunk in chunks:
            metadata_dict = chunk.get("metadata", {})

            # Maps Python None to SQL NULL if metadata dictionary is empty.
            if not metadata_dict:
                metadata_value = None
            else:
                metadata_value = json.dumps(metadata_dict)

            data_to_insert.append((
                chunk.get("text"),  # Main text content converted from HTML (TEXT)
                metadata_value,  # Serialized metadata (JSONB or NULL)
                chunk.get("embedding"),  # Pre-embedded (VECTOR)
                url  # Web source url (VARCHAR)
            ))

        cur.executemany(insert_query, data_to_insert)

        conn.commit()
        print(f"--> {len(data_to_insert)} Chunks für {url} in {TARGET_TABLE} gespeichert.")

    except psycopg2.Error as e:
        print(f"PostgreSQL Fehler beim Speichern: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Allgemeiner Fehler beim Speichern: {e}")


if __name__ == "__main__":
    load_dotenv()
    run_etl_pipeline()
