import sqlite3
import hashlib

conn = sqlite3.connect('studyverse.db')
cursor = conn.cursor()

cursor.execute('''
               CREATE TABLE IF NOT EXISTS users (
                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                    email TEXT UNIQUE NOT NULL,
                                                    password TEXT NOT NULL --will be hashed
               )
               ''')

cursor.execute('''
               CREATE TABLE IF NOT EXISTS lvas (
                                                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                   name TEXT UNIQUE NOT NULL,
                                                   ects INTEGER NOT NULL
               )
               ''')

cursor.execute('''
               CREATE TABLE IF NOT EXISTS completed_lvas (
                                                             user_id INTEGER,
                                                             lva_id INTEGER,
                                                             PRIMARY KEY (user_id, lva_id),
                                                             FOREIGN KEY (user_id) REFERENCES users(id),
                                                             FOREIGN KEY (lva_id) REFERENCES lvas(id)
                   )
               ''')

#Hashing function and dummy data

# hashing function - AI generated
def hash_password(password: str) -> str:
    """Erstellt einen SHA256-Hash für das Passwort."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# insert dummy-users
dummy_users = [
    ("a", hash_password("a")),
    ("silvia.mahringer@study.com", hash_password("silvia")),
    ("johanna.ferstl@study.com", hash_password("johanna")),
    ("sabiha.moradi@study.com", hash_password("sabiha")),
    ("marlene.huber@study.com", hash_password("marlene"))
]

cursor.executemany('''
                   INSERT OR IGNORE INTO users (email, password)
VALUES (?, ?)
                   ''', dummy_users)

# insert LVAs
lvas = [
    ("VL Einführung in die Wirtschaftsinformatik", 3.0),
    ("UE Einführung in die Wirtschaftsinformatik", 3.0),
    ("VL Algorithmen und Datenstrukturen", 3.0),
    ("UE Algorithmen und Datenstrukturen", 3.0),
    ("VL Datenmodellierung", 3.0),
    ("UE Datenmodellierung", 3.0),
    ("VL Prozess- und Kommunikationsmodellierung", 3.0),
    ("UE Prozess- und Kommunikationsmodellierung", 3.0),
    ("KS Grundlagen der Betriebswirtschaftslehre", 3.0),
    ("KS Grundlagen des integrierten Managements", 3.0),
    ("KS Grundlagen der Kostenrechnung", 3.0),
    ("KS Buchhaltung nach UGB", 3.0),
    ("KS Einführung in Marketing", 3.0),
    ("KS Grundlagen des Supply Chain Management", 3.0),
    ("VL Einführung in die Informatik", 3.0),
    ("VL Operating Systems", 3.0),
    ("VL Einführung in die Softwareentwicklung", 3.0),
    ("UE Einführung in die Softwareentwicklung", 3.0),
    ("VL Vertiefung Softwareentwicklung", 3.0),
    ("UE Vertiefung Softwareentwicklung", 3.0),
    ("KV Mathematik und Logik", 6.0),
    ("VL Formale Grundlagen der Wirtschaftsinformatik", 4.5),
    ("UE Formale Grundlagen der Wirtschaftsinformatik", 1.5),
    ("KV Statistik", 3.0),
    ("KV Privatrecht für Wirtschaftsinformatik", 4.5),
    ("KV Öffentliches Recht für Wirtschaftsinformatik", 1.5),
    ("KS Kommunikative Fertigkeiten Englisch (B2)", 3.0),
    ("SE Fachsprache Englisch", 3.0),
    ("KS Soziale Auswirkungen der IT", 3.0),
    ("KS Einführung in IKT, Gesellschaft, Gender und Diversity", 3.0),
    ("VL IT-Project Engineering & Management", 3.0),
    ("UE IT-Project Engineering & Management", 3.0),
    ("VL Informationsmanagement", 3.0),
    ("UE Informationsmanagement", 3.0),
    ("VL Software Engineering", 3.0),
    ("UE Software Engineering", 3.0),
    ("PR Software Engineering", 6.0),
    ("VL Data & Knowledge Engineering", 3.0),
    ("UE Data & Knowledge Engineering", 3.0),
    ("PR Data & Knowledge Engineering", 6.0),
    ("VL Communications Engineering", 3.0),
    ("UE Communications Engineering", 3.0),
    ("KT Communications Engineering (Kompetenztraining)", 3.0),
    ("SE Anwendungen des Communications Engineering", 3.0),
    ("PJ IT-Projekt Wirtschaftsinformatik", 6.0),
    ("PS Information Engineering", 3.0),
    ("PS Software Engineering", 3.0),
    ("PS Data & Knowledge Engineering", 3.0),
    ("PS Communications Engineering", 3.0),
    ("PE Spezielle Wirtschaftsinformatik - Theorie und Praxis, inklusive Bachelorarbeit", 12.0),
    ("Wahlfach Wirtschaftsinformatik1", 3.0),
    ("Wahlfach Wirtschaftsinformatik2", 3.0),
    ("Wahlfach Wirtschaftswissenschaften1", 3.0),
    ("Wahlfach Wirtschaftswissenschaften2", 3.0),

    ("Freie Studienleistungen1", 3.0),
    ("Freie Studienleistungen2", 3.0),
    ("Freie Studienleistungen3", 3.0)
]

# insert
cursor.executemany('''
                   INSERT OR IGNORE INTO lvas (name, ects)
VALUES (?, ?)
                   ''', lvas)

# example -> first user (a) already completed some lvas
cursor.executemany('''
                   INSERT INTO completed_lvas (user_id, lva_id)
                   VALUES (?, ?)
                   ''', [
                       (1, 1),  # VL EWIN
                       (1, 2)   # UW EWIN
                   ])

conn.commit()
conn.close()

print("✅ Datenbank studyplanner.db wurde erstellt!")
