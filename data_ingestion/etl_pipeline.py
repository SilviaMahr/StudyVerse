import os
from dotenv import load_dotenv
from typing import List
from langchain.schema import Document
import data_ingestion.extractor as extractor
import data_ingestion.processor as processor

#from langchain_google_genai import GoogleGenerativeAIEmbeddings
#from langchain_community.vectorstores.pgvector import PGVector
#import psycopg2
#import psycopg2.extras

load_dotenv()

NEON_COLLECTION_NAME = "studyverse_curriculum_data"
# im Backend auch den GLEICHEN Embedding-Dienst verwenden
# "text-embedding-004" ist Googles neuestes Embedding-Modell
#EMBEDDING_MODEL = GoogleGenerativeAIEmbeddings(model="text-embedding-001")

def check_env_variables(neon_db_url: str, gemini_api_key: str) -> bool:
    is_valid = True

    if not gemini_api_key or not gemini_api_key.strip():
        print("GEMINI_API_KEY ist leer oder nicht gesetzt. Pipeline abgebrochen.")
        is_valid = False

    if not neon_db_url or not neon_db_url.strip():
        print("DATABASE_URL (NEON_DB_URL) ist leer oder nicht gesetzt. Pipeline abgebrochen.")
        is_valid = False

    return is_valid

def load_data_into_vector_store(chunks: List[Document]):
    try:
        # 1. Erstellung der Embeddings für jeden Chunk mit EMBEDDING_MODEL
        # 2. Verbindung zur DB über NEON_DB_URL
        # 3. Speichern der Vektoren und Metadaten in der Tabelle (Collection)
        PGVector.from_documents(
            documents=chunks,
            embedding=EMBEDDING_MODEL,
            connection_string=NEON_DB_URL,
            collection_name=NEON_COLLECTION_NAME,
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

    #conn = psycopg2.connect(neon_db_url)
    #conn.autocommit = True

    curriculum_data = extractor.load_curriculum_data()
    if not curriculum_data:
        print("Pipeline beendet: Keine Quelldokumente gefunden.")
        return

    processed_chunks = processor.process_documents(curriculum_data)

    (root_html, root_url) = extractor.extract_win_bsc_info()
    (chunks, html_url) = processor.process_main_page(root_url, root_html)
    #store_html_chunks(chunks=chunks, embeddings=embeddings, url=root_url)
    course_links = extractor.extract_links(html=root_html)

    for course_url in course_links:
        subject_links = extractor.extract_links(url=course_url)
        subject = subject_links[0]
        subject_html = extractor.fetch_content_from_div(subject)
        course_data = extractor.extract_lva_links_for_course(subject_html)
        lva_links = course_data["lva_links"]
        semester_msg = course_data["semester_msg"]

        if lva_links:
            for lva_url in lva_links:
                print(f"--> LVA page: {lva_url}")
                lva_html = extractor.fetch_content_from_div(lva_url)
                semester = extractor.extract_semester_info(root_html)
                (lva_chunks, lva_url) = processor.process_html_page(lva_url, lva_html, semester)
                #store_html_chunks(chunks=lva_chunks, embeddings=lva_embeddings, url=lva_url)
        elif semester_msg:
            semester = extractor.extract_semester_info(root_html)
            if semester == "WS":
                semester = "SS"

            if semester == "SS":
                semester = "WS"

            processor.process_html_page(subject, subject_html, semester)

    study_manual_links = extractor.get_links_from_study_manual()
    last_two_links = study_manual_links[-2:]
    for link in last_two_links:
       subject_html = extractor.fetch_content_from_div(link)

    if not processed_chunks:
        print("Pipeline beendet: Nach der Verarbeitung keine Chunks übrig.")
        return

    #load_data_into_vector_store(processed_chunks)

    print("\n--> ETL-PIPELINE beendet! <--")


def store_html_chunks(chunks, embeddings, url):
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