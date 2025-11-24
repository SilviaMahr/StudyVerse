"""
Skript zum Anpassen der Vektordimension in der Datenbank von 1536 auf 768.
Google's text-embedding-004 Modell liefert 768-dimensionale Embeddings.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

neon_db_url = os.getenv("DATABASE_URL")

if not neon_db_url:
    print("ERROR: DATABASE_URL nicht gesetzt!")
    exit(1)

try:
    conn = psycopg2.connect(neon_db_url)
    cur = conn.cursor()

    print("Verbunden mit der Datenbank.")
    print("\n=== Aktuelle Tabellen-Struktur prüfen ===")

    # Check if table exists and get current structure
    cur.execute("""
        SELECT column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_name = 'studyverse_data'
        ORDER BY ordinal_position;
    """)

    columns = cur.fetchall()
    print(f"Gefundene Spalten in studyverse_data:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]} ({col[2]})")

    print("\n=== Lösung: Tabelle neu erstellen mit 768 Dimensionen ===")

    # Backup old data if exists
    print("1. Backup der alten Daten...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS studyverse_data_backup AS
        SELECT * FROM studyverse_data;
    """)
    print("   [OK] Backup erstellt: studyverse_data_backup")

    # Drop old table
    print("2. Alte Tabelle loeschen...")
    cur.execute("DROP TABLE IF EXISTS studyverse_data CASCADE;")
    print("   [OK] Tabelle geloescht")

    # Create new table with 768 dimensions
    print("3. Neue Tabelle mit 768 Dimensionen erstellen...")
    cur.execute("""
        CREATE TABLE studyverse_data (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB,
            embedding VECTOR(768),
            url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("   [OK] Neue Tabelle erstellt mit VECTOR(768)")

    # Create index for vector similarity search
    print("4. Index fuer Vektor-Suche erstellen...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS studyverse_data_embedding_idx
        ON studyverse_data
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    print("   [OK] Index erstellt")

    conn.commit()
    print("\n[ERFOLG] Datenbank wurde auf 768 Dimensionen angepasst.")
    print("\nHinweis: Die alten Daten wurden in 'studyverse_data_backup' gesichert.")
    print("Zum Löschen: DROP TABLE studyverse_data_backup; - wenn gewollt")

except psycopg2.Error as e:
    print(f"[FEHLER] PostgreSQL Fehler: {e}")
    if conn:
        conn.rollback()
except Exception as e:
    print(f"[FEHLER] Allgemeiner Fehler: {e}")
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
