import os
from dotenv import load_dotenv
from typing import List
from langchain.schema import Document

from data_ingestion.extractor import load_all_curriculum_data
from data_ingestion.processor import process_documents

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector

load_dotenv()

NEON_COLLECTION_NAME = "studyverse_curriculum_data"
# im Backend auch den GLEICHEN Embedding-Dienst verwenden
# Der "text-embedding-004" ist Googles neuestes Embedding-Modell
EMBEDDING_MODEL = GoogleGenerativeAIEmbeddings(model="text-embedding-004")

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

    raw_documents = load_all_curriculum_data()

    if not raw_documents:
        print("Pipeline beendet: Keine Quelldokumente gefunden.")
        return

    processed_chunks = process_documents(raw_documents)

    if not processed_chunks:
        print("Pipeline beendet: Nach der Verarbeitung keine Chunks übrig.")
        return

    load_data_into_vector_store(processed_chunks)

    print("\n--> ETL-PIPELINE beendet! <--")


if __name__ == "__main__":
    load_dotenv()

    run_etl_pipeline()