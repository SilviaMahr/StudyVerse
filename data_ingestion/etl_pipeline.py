import os
from dotenv import load_dotenv
from typing import List
from langchain.schema import Document
import data_ingestion.extractor as extractor
import data_ingestion.processor as processor
from langchain_community.vectorstores.pgvector import PGVector
import psycopg2
import psycopg2.extras
import json

load_dotenv()

NEON_COLLECTION = "studyverse_data"

def check_env_variables(neon_db_url: str, gemini_api_key: str) -> bool:
    is_valid = True

    if not gemini_api_key or not gemini_api_key.strip():
        print("GEMINI_API_KEY ist leer oder nicht gesetzt. Pipeline abgebrochen.")
        is_valid = False

    if not neon_db_url or not neon_db_url.strip():
        print("DATABASE_URL (NEON_DB_URL) ist leer oder nicht gesetzt. Pipeline abgebrochen.")
        is_valid = False

    return is_valid

def load_data_into_vector_store(chunks: List[Document], db_url):
    try:
        # 1. Erstellung der Embeddings für jeden Chunk mit EMBEDDING_MODEL
        # 2. Verbindung zur DB über NEON_DB_URL
        # 3. Speichern der Vektoren und Metadaten in der Tabelle (Collection)
        PGVector.from_documents(
            documents=chunks,
            embedding=processor.model,
            connection_string=db_url,
            collection_name=NEON_COLLECTION,
        )
        print(f"--> {len(chunks)} Chunks in Neon DB geladen und vektorisiert.")

    except Exception as e:
        print(f"FATALER FEHLER beim Laden in PGVector: {e}")
        print("Stellen Sie sicher, dass die 'pgvector' Extension in Ihrer Neon DB aktiviert ist.")


def run_etl_pipeline():
    gemini_key = os.getenv("GEMINI_API_KEY")
    neon_db_url = os.getenv("DATABASE_URL")

    if not check_env_variables(neon_db_url, gemini_key):
        return

    print("--> ETL-PIPELINE gestartet... <--")

    conn = psycopg2.connect(neon_db_url)
    conn.autocommit = True

    ### IDEAL_PLAN DATA ETL (already manually done)

    ### CURRICULUM DATA ETL
    curriculum_data = extractor.load_curriculum_data()
    if not curriculum_data:
        print("Pipeline beendet: Keine Quelldokumente gefunden.")
        return

    processed_curriculum_chunks = processor.process_documents(curriculum_data)
    if not processed_curriculum_chunks:
        print("Pipeline beendet: Nach der Verarbeitung keine Chunks übrig.")
        return

    load_data_into_vector_store(processed_curriculum_chunks, neon_db_url)

    ### KUSSS DATA ETL
    (root_html, root_url) = extractor.extract_win_bsc_info()
    semester = extractor.extract_semester_info(root_html)
    chunks = processor.process_main_page(root_html)
    store_html_chunks(conn=conn, chunks=chunks, url=root_url)
    course_links = extractor.extract_links(html=root_html)

    for course_url in course_links:
        # the one middle page
        subject_links = extractor.extract_links(url=course_url)
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
                lva_chunks = processor.process_html_page(lva_html, sm_subject_html, semester)
                store_html_chunks(conn=conn, chunks=lva_chunks, url=lva_url)
        elif semester_msg:
            if semester == "WS":
                semester = "SS"

            if semester == "SS":
                semester = "WS"

            lva_chunks = processor.process_html_page(subject_html, sm_subject_html, semester)
            store_html_chunks(conn=conn, chunks=lva_chunks, url=subject_url)

    ### STUDY MANUAL DATA ETL (part 2)
    study_manual_links = extractor.get_links_from_study_manual()
    for url in study_manual_links:
        subject_html = extractor.fetch_content_from_div(url)
        subject_chunks = processor.process_sm_html(subject_html)
        store_html_chunks(conn=conn, chunks=subject_chunks, url=url)

    print("\n--> ETL-PIPELINE beendet! <--")

'''
def store_html_chunks(db_url, chunks, metadata, embeddings, url):
    with conn.cursor() as cursor:
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            row_id = f"{url}_chunk_{i}"

            cursor.execute(
                """
                INSERT INTO rag_documents (id, url, chunk_text, embedding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
                """,
                (
                    row_id, url, chunk, emb.toList(),
                )
            )
'''

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