# End-To-End Prozess

## 1. Basics
- RAG-System, für die Semesterplanung (Bachelor-Wirtschaftsinformatik)
- Das System erstellt Pläne, die gespeichert werden und später wieder aufgerufen/bearbeitet werden können.
- Input: 
    - ECTS-Ziel (z.B. 15 ECTS) 
    - bereits absolvierte LVAs (z.B. VL + UE EWIN, E-INF, BWL, Integriertes Management, Statistik)  
    - zu planendes Semester (z.B. SS26)
    - bevorzugte Tage (z.B. MO und MI). 
    - Optionaler Freitext für LVAs die der Studierende unbedingt besuchen möchte (z.B. Soft2) 
- Output:
    - Semesterplan mit Begründung
    - Beispiel:
      Hier ist dein Plan für das SS26 mit 15 ECTS. Deine Uni-Tage sind Montag und Mittwoch (in der Planungsübersicht):  
      - Prozess- und Kommunikationsmodellierung VL - 3 ECTS, Mi 13:45 - 15:15 Uhr (Udo Kannengiesser) 
      - Prozess- und Kommunikationsmodellierung UE - 3 ECTS, Mi 15:30 - 17:00 Uhr (Thomas Jost)
      - Einführung in die Softwareentwicklung VL - 3 ECTS, Mo 8:30 - 10:00 Uhr (Wieland Schwinger)
      - Einführung in die Softwareentwicklung UE - 3 ECTS, Mo 10:15 - 11:45 Uhr (Wieland Schwigner) 
      - Kommunikative Fertigkeiten Englisch KS - 3 ECTS, Mo 13:45 - 15:15 Uhr (Nina Einzinger)
     
        
      Du hast angegeben, dass du SOFT2 machen möchtest, ich interpretiere SOFT 2 als VL + UE Vertiefung Softwareentwicklung. Stimmt das?
      Ich empfehle dir den Besuch dieser Lehrveranstaltung noch nicht, du solltest zuerst unbedingt VL + UE Einführung in die Softwareentwicklung absolvieren.

- Zusatzfunktionen:
    - Generelle Fragen zum Studium stellen:
        - z.B. Student: Weißt zu ob ich in Prozess- und Kommunikationsmodellierung eine Klausur absolvieren muss?
        - Uni: Ja, in dem Kurs ist eine Klausur vorgesehen!
          
        - z.B. Student: Welcher LVA-Leiter unterrichtet Soft1?
        - Uni: Meinst du mit Soft1 VL Einführung in die Softwareentwicklung? Im Sommersemester wird VL Einführung in die Softwareentwicklung von Wieland Schwinger unterrichtet, im Wintersemester von Johannes Sametinger. 
  - Nachfragen und Planänderungen im Chatfenster möglich
  - Beispiel:
      -  Student: Ich habe Einf. in die Softwareentwicklung angerechnet bekommen, da ich HTL Absolvent bin. Ich möchte bitte SOFT2 machen.
      - Uni: Alles klar ich ändere deinen Plan, bitte gib auch angerechnete Lehrveranstaltungen als absolviert an! Soll ich das für dich übernehmen? Gibt es noch andere Kurse, die dir angerechnet wurden? 
 ❗ -> TEAM Discussion (soll das möglich sein)
      - Student: Ja bitte. Nein nur SOFT1!
      - Uni: Verstanden, ich habe deinen Plan angepasst, du findest ihn in der Planungsübersicht!
          - Prozess- und Kommunikationsmodellierung VL - 3 ECTS, Mi 13:45 - 15:15 Uhr (Udo Kannengiesser) 
          - Prozess- und Kommunikationsmodellierung UE - 3 ECTS, Mi 15:30 - 17:00 Uhr (Thomas Jost)
          - Algorithmen und Datenstrukturen VL - 3 ECTS, Mi 10:15 - 11:45 Uhr (Wolfgang Narzt)
          - Algorithmen und Datenstrukturen UE - 3 ECTS, Mi 12:00 - 13:30 Uhr (Dominik Lamprecht) 
          - Kommunikative Fertigkeiten Englisch KS - 3 ECTS, Mo 13:45 - 15:15 Uhr (Nina Einzinger)
    
      Du möchtest VL + UE Vertiefung in die Softwareentwicklung absolvieren, leider findet dieser Kurs aber immer nur am Dienstag statt. Du hast nur die Tage Montag und Mittwoch ausgewählt. Möchtest du Dienstag doch in deine Planung integrieren?
  
## 2. Datenquelle und ETL-Pipleline 

###  Phase 1. Vorbereitung der Wissensbasis für spätere Anfragen   

- Dokumente, Datenbanken und Websiteinformarionen sammeln
    - Curriculum (PDF) 
        - Format: PDF-Dokument
        - Inhalt:
             - STEOP-Kurse
             - Pflichtmodule
             - Modulbeschreibungen & -Struktur
             - Zuordnung LVAs zu Modulen
             - ECTS Verteilung pro Modul
             - Prüfungsordnung/Studienordnung 
        - Aktualisierung: Jährlich (sofern RAG weitergeführt werden würde)
        - **Extraktionsmethode: PyPDFLoader**
    - KUSSS LVA-Suche
        - Format: Webseite (strukturiert)
        - Inhalt:   
              - LVA-Details (LVA Nr, LVA, Titel, ECTS, SSt, WS/SS)    
              - Termine (Tag, Uhrzeit❗Cave: Uhrzeit beim ersten Termin oft abweichend zu den restlichen Terminen!)        
              - LVA-Leiter       
              - Abhaltungsart (Präsenz, Remote, Hybrid)      
              - Zusatzinformationen (Anwesenheitspflicht, Literatur, etc.)      
              - Link zum Studienhandbuch     
        - Aktualisierung: Semesterweise (sofern RAG weitergeführt werden würde)
        - **Extraktionsmethode: UnstructuredURLLoader -> HTML-Parsing-Strukturierte Felder**     
    - Studienhandbuch (❗pro LVA)
        - Format: Webseiten (pro LVA)
        - Inhalt:    
              - erwartete Vorkenntnisse (⚠️ Wichtig für Planungslogik)    
              - Beurteilungskriterien    
              - Zu erberbende Kompetenzen & Lernegebnisse (Nützlich für Chatfunktion wie: Was lerne ich in Einf. Inf -> ❗Team Discussion: sinnvoll?).    
              - Beurteilungkriterium (z.B. Klausur)    
              - Abhaltungssprache    
              - Sonstige Informationen (❗Hier befinden sich wichtige Informationen, wie z.B. VL + UE müssen gemeinsam absolviert werden).     
        - Aktualisierung: Semesterweise (sofern RAG weitergeführt werden würde)    
        - **Extraktionsmethode: UnstructuredURLLoader -> Studienhandbuchlink vom KUSSS -> Strukturierung**     
    - Idealtypischer Studienplan    
        - Format: Relationale Datenbank    
        - Inhalt: Empfohlene Semester-Reihenfolge    
        - Aktualisierung: Statisch    
        - **Extraktionsmethode: Relationale DB mit direct Query, kein Embedding nötig**    

*⚠️Anmerkung: Die Aktualisierungshinweise sind nur dazu gedacht, darzustellen wie bei einer "tatsächlichen" Inbetriebnahme mit laufender Wartung aussehen würde. Relevant, fall Chatbot z.B. für BSc/Masterarbeit weiterentwickelt werden soll. 

### Phase 2. ETL-Pipeline (Extract, Transform, Load) 

**2.1. Extract**

KI generierter Beispielcode! Dient nur der Veranschaulichung: 

````python    
def load_all_curriculum_data() -> List[Document]:
    documents = []
    
    # 1. Curriculum PDF
    pdf_docs = load_curriculum_pdf()
    documents.extend(pdf_docs)
    
    # 2. KUSSS LVA-Seiten (Liste aller LVA-URLs)
    kusss_docs = load_kusss_lva_pages()
    documents.extend(kusss_docs)
    
    # 3. Studienhandbuch-Seiten (pro LVA)
    studienhandbuch_docs = load_studienhandbuch_pages()
    documents.extend(studienhandbuch_docs)
    
    return documents
 ```` 
  
**Tools:**
- PyPDFLoader
- UnstructuredURLLoader
- Custom Scraper für strukturierte KUSSS Felder   
-> Siehe auch Phase 1 Extaktionsmethode

**2.2. Transform**
⚠️ @Team: Bitte um Input ob ihr mit der Strategie einverstanden seid!    

**Chunking-Strategie:** 

Ein Chunk = eine LVA (Jede LVA wird als ein vollständiges Dokument gespeichert. 

KI-generierter Beispeil-Chunk

```
=== LVA-Nummer: 123.456 ===
Titel: Einführung in die Wirtschaftsinformatik
Modul: Wirtschaftsinformatik Grundlagen
STEOP: Nein
Idealtypisches Semester: 1

=== Organisatorisches ===
LVA-Leiter: Prof.in Dr.in Barbara Krumay
Semester: Wintersemester (WS)
Tag: Di, 12:00 - 15:15 Uhr
Art: Präsenz
ECTS: 3,00
Semesterwochenstunden: 2,00

=== Voraussetzungen ===
Erwartete Vorkenntnisse: Keine (STEOP-Kurs)
Didaktische Einheit: Diese VL muss mit "UE Einführung in die WI" (LVA-Nr: 123.457) kombiniert werden.

=== Prüfung & Sprache ===
Beurteilungskriterium: Schriftliche Klausur
Abhaltungssprache: Deutsch
Klausurstoff: Buch "Wirtschaftsinformatik" (Heinrich et al.) + Folien
Zusatzinfo: Anwesenheitspflicht in UE

=== Kompetenzen & Lernergebnisse ===
Die Studierenden können:
- Den Gegenstandsbereich der WI systemtheoretisch erklären (K2)
- Systemdenken zur Analyse von WI-Problemstellungen anwenden (K3)
- Auswirkungen von IT auf Organisationen analysieren (K2)
- Wissenschaftliche Vorgehensweisen zur Problemlösung anwenden (K3)
``` 

Falls Metadaten verwendet werden sollen (um Filterung und Retrieval zu erleichtern), dann könnten diese folgende Struktur aufweisen:
(KI generierte Beispiel-Metadaten):#

```
metadata = {
    "lva_nr": "123.456",
    "lva_name": "Einführung in die Wirtschaftsinformatik",
    "ects": 3.0,
    "semester": "WS+SS"  # WS / SS / WS+SS
    "steop": TRUE,
    "modul": "Wirtschaftsinformatik Grundlagen",
    "idealtypisches_semester": 1,
    "erwartete_vorkenntnisse": [],  # Liste von LVA-Nummern oder Namen
    "verknuepfte_lvas": ["123.457"],  # z.B. UE, die dazu gehört
    "lva_leiter": "Barbara Krumay",
    "tag": "Di",
    "uhrzeit": "12:00-15:15"
}
```

**2.3. Load**    
Speicherung der Daten in der Vektor Datenbank.   
KI-generierter Beispiel-Code:

````python

def load_data_into_vector_store(chunks: List[Document]):
    """
    Erstellt Embeddings und speichert Chunks in Neon DB.
    """
    PGVector.from_documents(
        documents=chunks,
        embedding=EMBEDDING_MODEL,  # Google text-embedding-004 
        connection_string=NEON_DB_URL,
        collection_name="studyverse_curriculum_data",
    )

````

### Bestehende Unklarheiten: ⚠️ Team-Discussion!

**3.1. Datenstruktur in Vector-DB**     
Wie werden die Daten in der Vector-DB organisiert?     
Metadaten sinnvoll oder wird das zu viel? 

**3.2. Kritische Designentscheidungen** 

_3.2.1 Freitext-Suche_

- User Input: Soft1, Soft2
- Anforderung: RAG muss Soft1 zu Einfürhung in die Softwareentwicklung (VL + UE) matchen. 
- Mögliche Umsetzung: Vergabe von Aliases (zumindest wurde das in einem Reddit-Beitrag so genannt) -> lt. Reddit würde das so aussehen können (angepasst an unser Beispiel natürlich): 

````python
metadata = {
    "lva_aliases": ["SOFT1", "Soft1", "Software 1", "Einführung SE"],
}
````

_3.2.2 Verknüpfte Einheiten (VL + UE)_
- Variante A (Abklären, ob das klappt): Evlt.  es ist möglich, das LLM anzuweisen VL und UE aus demselben Modul mit demselben Namen immer gemeinsam vorzuschlagen.
- Variante B (Sicherstellung mit Metadaten) man erstellt quasi "Constraints", indem wir Verknüpfungen wählen und den RAG anweisen Verknpüfungen IMMER gemeinsam vorzuschlagen:

````python
metadata = {
    "verknuepfte_lvas": ["123.457"],  # UE zur VL 
    "verknuepfung_typ": "mandatory",  # mandatory / recommended
}
````

## 3. Retrieval/LLM 

**Grundprinzip** 

Die Gesamte Retrieval-Komponente baut darauf auf, dass im ETL-Teil tatsächlich, wie von Sabiha vorgeschlagen, eine Metadatenfilter verwendet wird. 
Dieser soll dazu verwendet werden, die Suche insgesamt einzugrenzen z.B. wenn der User SS auswählt, werden ausschließlich Kurse, die im SS oder im WS+SS besucht werden können durchsucht, etc. 
 

## Phase 1: Hybrid-Retrieval
1. Metadaten-Filter (Harte Constraints wie bspw. Semester werden direkt überliefert) - Reduziert Vector-Search 

   Beispiel:

   ````python
   filter_dict = {
    "semester": {"$in": ["SS", "WS+SS"]},  # User wählt Sommersemester
    "ects": {"$lte": 18},                   # Max 18 ECTS
    "steop": False
    }
    ```` 
Die Metadatenfilterung liefert eine Menge an gültigen LVA-Kandidaten, diese müssen dann noch mittels semantischer Suche durchsucht werden.
- Input = User-Query
- Output = Top-K LVA Chunks aus der gefilterten Menge z.B. TOP 15 LVAs mit denen das LLM dann arbeiten kann. 
Beispiel:

````python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 15,  # Top 15 Ergebnisse
        "filter": filter_dict
    }
)

results = retriever.get_relevant_documents(user_query)

```` 


### Phase 2: LLM Logik

Aufgaben für das LLM
1. Voraussetzungen prüfen
   - Wurden die vorausgesetzten LVAs bereits abgeschlossen?
   - Input:  
         - Verknüpfte LVAs (lt. Metadaten)    
         - Bereits abgeschlossene LVAs     
     
         ```sql
             SELECT lva_id
             FROM completed_lvas
             WHERE user = ?
         ```

2. Konflikte/Zeitplanung auflösen
    - LLM Prompting (Keine Überschneidungen erlaubt)
3. Begründung generieren
    - Text für User, warum eine LVA vorgeschlagen oder abgelehnt wurde. 


**Beispielhafter LLM Prompt:**

```
Du bist ein Studienplanungs-Assistent.
Die User-Query: "Semester: SS26, ECTS: 9, Tage: Mo, Mi, Gewünschte LVAs: BWL"
Liste der relevanten LVAs (aus Retriever):
- SOFT2 VL (3 ECTS, Mo 08:30-10:00)
- SOFT2 UE (3 ECTS, Mo 10:15-11:45)
- Operational Systems VL (3 ECTS, Mo 12:00-13:30)
- BWL2 VL (3 ECTS, Mi 14:00-15:30)
Prüfe:
- Überschneidungen der Uhrzeiten
- Max 9 ECTS dieses Semester
- Bereits absolvierte LVAs
Erstelle einen **optimierten Semesterplan** mit kurzer Begründung pro Kurs.
```
    
================================================================================

### Workflow-Darstellung:

1. User Query empfangen 
    - ECTS-Ziel, Semester, Tage, freie Textangaben (z. B. „Soft2“)

2. Metadaten-Filter anwenden
    - SQL/PGVector Filter auf LVA-Chunks

3. Vector Retrieval durchführen
    - Semantische Suche innerhalb der gefilterten Kandidaten

4. LLM-Postprocessing
   - Prüfung von Voraussetzungen
   - Konfliktlösung (Tage/Uhrzeiten)
   - Generierung von Plan & Begründungen

5. Ausgabe an User
   - Semesterplan + Kommentare
   - Möglichkeit für Nachfragen / Anpassungen






  
