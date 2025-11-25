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
import data_ingestion.extractor as extractor


load_dotenv()

GOOGLE_EMBEDDING_MODEL = "models/text-embedding-004"
GEMINI_API_KEY_VALUE = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY_VALUE:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY_VALUE
else:
    pass

model = GoogleGenerativeAIEmbeddings(
    model=GOOGLE_EMBEDDING_MODEL,
    google_api_key=GEMINI_API_KEY_VALUE
)
NEON_COLLECTION = "studymanual_data"

def check_env_variables(neon_db_url: str) -> bool:
    is_valid = True

    if not GEMINI_API_KEY_VALUE or not GEMINI_API_KEY_VALUE.strip():
        print("GEMINI_API_KEY ist leer oder nicht gesetzt. Pipeline abgebrochen.")
        is_valid = False

    if not neon_db_url or not neon_db_url.strip():
        print("DATABASE_URL (NEON_DB_URL) ist leer oder nicht gesetzt. Pipeline abgebrochen.")
        is_valid = False

    return is_valid

def load_data_into_vector_store(conn, chunks: List[Document], embeddings, doc_url):
    try:
        cur = conn.cursor()

        insert_query = """
                       INSERT INTO studyverse_data
                           (content, metadata, embedding, url)
                       VALUES (%s, %s, %s, %s); \
                       """

        data_to_insert = []
        for i, chunk in enumerate(chunks):
            metadata_dict = chunk.metadata
            metadata_value = json.dumps(metadata_dict)

            data_to_insert.append((
                chunk.page_content,
                metadata_value,
                embeddings[i],
                doc_url
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
    neon_db_url = os.getenv("DATABASE_URL")

    if not check_env_variables(neon_db_url):
        return

    print("--> ETL-PIPELINE gestartet... <--")

    conn = psycopg2.connect(neon_db_url)
    conn.autocommit = True

    ### IDEAL_PLAN DATA ETL (already manually done)

    ### CURRICULUM DATA ETL
    (curriculum_data, doc_url) = extractor.load_curriculum_data()
    if not curriculum_data:
        print("Pipeline beendet: Keine Quelldokumente gefunden.")
        return

    (processed_curriculum_chunks, curriculum_embeddings) = processor.process_documents(curriculum_data, model)
    if not processed_curriculum_chunks:
        print("Pipeline beendet: Nach der Verarbeitung keine Chunks übrig.")
        return

    load_data_into_vector_store(conn, processed_curriculum_chunks, curriculum_embeddings, doc_url)


    ### KUSSS DATA ETL - BEIDE SEMESTER (WS + SS)
    semesters_to_process = ["WS", "SS"]

    for current_semester in semesters_to_process:
        print(f"\n{'='*80}")
        print(f"EXTRAHIERE DATEN FÜR {current_semester}")
        print(f"{'='*80}\n")

        # Nutze Playwright um das richtige Semester zu laden
        (root_html, root_url) = extractor.extract_win_bsc_info_with_semester(current_semester)

        if not root_html:
            print(f"FEHLER: Konnte {current_semester}-Daten nicht laden. Überspringe...")
            continue

        semester = extractor.extract_semester_info(root_html)
        chunks = processor.process_main_page(root_html, model)
        store_html_chunks(conn=conn, chunks=chunks, url=f"{root_url}?semester={current_semester}")
        course_links = extractor.extract_links(html=root_html)

        print(f"Gefunden: {len(course_links)} Kurse für {current_semester}")

        for course_url in course_links:
            # the one middle page
            subject_links = extractor.extract_links(url=course_url)

            # Prüfe ob Links extrahiert wurden
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
                for lva_url in lva_links:
                    lva_html = extractor.fetch_content_from_div(lva_url)
                    lva_chunks = processor.process_html_page(lva_html, sm_subject_html, semester, model)
                    store_html_chunks(conn=conn, chunks=lva_chunks, url=lva_url)
            elif semester_msg:
                # Kurs wird in diesem Semester nicht angeboten
                # Markiere mit dem anderen Semester
                other_semester = "SS" if current_semester == "WS" else "WS"
                lva_chunks = processor.process_html_page(subject_html, sm_subject_html, other_semester, model)
                store_html_chunks(conn=conn, chunks=lva_chunks, url=subject_url)

        print(f"\n{current_semester}-Daten erfolgreich extrahiert!\n")

    ### STUDY MANUAL DATA ETL (part 2)
    study_manual_links = extractor.get_links_from_study_manual()
    for url in study_manual_links:
        subject_html = extractor.fetch_content_from_div(url)
        subject_chunks = processor.process_sm_html(subject_html, model)
        store_html_chunks(conn=conn, chunks=subject_chunks, url=url)

    print("\n--> ETL-PIPELINE beendet! <--")


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
                chunk.get("text"),  # content (TEXT)
                metadata_value,  # metadata (JSONB or NULL)
                chunk.get("embedding"),  # embedding (VECTOR)
                url  # url (VARCHAR)
            ))

        cur.executemany(insert_query, data_to_insert)

        conn.commit()
        print(f"--> {len(data_to_insert)} Chunks für {url} gespeichert.")

    except psycopg2.Error as e:
        print(f"PostgreSQL Fehler beim Speichern: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Allgemeiner Fehler beim Speichern: {e}")


def print_debug(chunks, url):
    # DEBUG PRINT BEFORE STORING
    print("\n================ DEBUG ================")
    print("URL:", url)
    print("Number of chunks:", len(chunks))
    print("---------------------------------------")

    for i, chunk in enumerate(chunks):
        print(f"\n--- CHUNK {i} ---")
        print(chunk)  # first 500 chars to keep log readable
        print("---------------------------------------")

    #print("Embeddings shape:", embeddings.shape)
    #print("=======================================\n")

if __name__ == "__main__":
    load_dotenv()

    run_etl_pipeline()