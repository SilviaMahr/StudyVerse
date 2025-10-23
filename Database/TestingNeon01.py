import psycopg
import os

# ⚠️ FÜGEN SIE IHREN VOLLSTÄNDIGEN CONNECTION STRING HIER EIN
DB_URL = "postgresql://neondb_owner:npg_Hv7VAhfpR1dc@ep-patient-mode-a9dvojnm-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require"


def test_neon_connection(db_url):
    """Prüft die Verbindung, pgvector und führt eine Testabfrage aus."""
    if not db_url:
        print("❌ Fehler: DB_URL ist leer. Bitte den Connection String im Skript eintragen.")
        return

    # Extrahiert den Hostnamen für die Ausgabe
    host = db_url.split('@')[-1].split('/')[0]
    print(f"🔗 Versuche Verbindung zu Host: {host}...")

    try:
        # Verbindung herstellen
        with psycopg.connect(db_url) as conn:

            # Cursor für Abfragen erstellen
            with conn.cursor() as cur:

                # 1. Test: Prüfen, ob pgvector aktiv ist
                cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                pgvector_installed = cur.fetchone()

                print("---")
                if pgvector_installed:
                    print("✅ 'pgvector' Vektor-Erweiterung ist installiert und aktiv.")
                else:
                    print("⚠️ 'pgvector' ist nicht installiert. Bitte mit 'CREATE EXTENSION IF NOT EXISTS vector;' installieren.")

                # 2. Test: Abrufen der aktuellen Datenbank-Zeit
                cur.execute("SELECT now()")
                db_time = cur.fetchone()[0]
                print(f"⏰ Datenbank-Zeit erfolgreich abgerufen: {db_time}")

                # --- 3. TEST: DATENABRUF ---
                print("\n📖 **3. Test: Abruf der ersten 10 LVA-Datensätze**")

                # Führt die Abfrage aus
                cur.execute("SELECT id, name, ects FROM lvas LIMIT 10;")
                lva_records = cur.fetchall()

                if lva_records:
                    print("ID | LVA Name | ECTS")
                    print("---|---|---")
                    for record in lva_records:
                        # Formatiert die Ausgabe sauber
                        print(f"{record[0]:2} | {record[1]:45} | {record[2]}")
                    print(f"\n✅ Datenabruf erfolgreich. {len(lva_records)} Datensätze angezeigt.")
                else:
                    print("⚠️ Die Tabelle 'lvas' ist leer oder existiert nicht.")
                # ---------------------------

                print(f"⏰ Datenbank-Zeit erfolgreich abgerufen: {db_time}")
                print("---")
                print("🥳 **VERBINDUNG ERFOLGREICH!**")

    except psycopg.OperationalError as e:
        print(f"❌ Verbindungsfehler (OperationalError): Die Verbindung konnte nicht hergestellt werden.")
        print("Mögliche Ursachen: falsches Passwort, falscher Hostname, oder Ihre IP ist nicht freigegeben.")
        print(f"Fehlerdetails: {e}")

    except Exception as e:
        print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    # Benötigter PostgreSQL-Treiber installieren (falls noch nicht geschehen)
    try:
        import psycopg
    except ImportError:
        print("Installiere 'psycopg[binary]'...")
        os.system("pip install psycopg[binary]")
        # Muss neu importiert werden, daher Neustart-Empfehlung
        print("Bitte starten Sie das Skript erneut.")
        exit(1)

    test_neon_connection(DB_URL)