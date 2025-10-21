# Konzept STUDYverse 

## WHY - Problemstellung    
Studierende haben oft Schwierigkeiten, ihr Semester oder das Studium optimal zu planen: Sie wissen nicht genau, welche Lehrveranstaltungen im kommenden Semester sinnvoll sind.  

Voraussetzungsketten (z. B. SOFT1 → SOFT2 → PR SE) sind im Studienhandbuch zwar dokumentiert, aber schwer überschaubar.
Der Studienfortschritt (bereits absolvierte Kurse) wird selten automatisch berücksichtigt. Viele Studierende arbeiten nebenher und/oder haben Betreuungspflichten und haben somit Ressourcen für unter 30 ECTS.  

Der STUDYverse soll Studierende bei der individuellen Semesterplanung unterstützen, indem er basierend auf bisherigen Leistungen, ECTS-Zielvorgaben und Curriculumsdaten ein ideales Semester vorschlägt.  

Retrieval-Augmented Generation (RAG)-System ist hier die ideale Lösung, weil hier der Zugriff auf aktuelle und korrekte curriculare Daten essentiell ist, mit Halluzinationen würde das System sinnlos sein. Aktualität, Zuverlässigkeit, Wissenstransparenz und Kontrollierbarkeit sind Vorraussetzung. Durch das Einfügen der Constraints (bisher absolvierte Kurse, Voraussetzungskette, ECTS-Vorgabe) im Abfragekontext wird vom LLM eine gute Antwort generiert.   

RAG verbindet die Verlässlichkeit und Spezifität der Studienordnung (durch den Retrieval-Teil) mit der Flexibilität, Personalisierungsfähigkeit und Kommunikationsstärke des LLMs (durch den Generation-Teil). Es ist die effektivste Methode, um eine individuelle, korrekte und gut begründete Semesterplanung zu erstellen.

## WHAT - Ziel des Systems  
Scope: Bachelor Wirtschaftsinformatik  

Der Study Planner soll automatisch für Studierende im Bachelorstudium Wirtschaftsinformatik ein Semester mit passenden LVAs zusammenstellen.
Er berücksichtigt dabei:
- Die gewünschte Anzahl an ECTS (z. B. max. 24 ECTS)
- Bereits absolvierte LVAs
- Berücksichtigung Idealtypischer Studienplan

Optional: Empfehlungen für alternative LVAs, wenn kein ideales Semester möglich ist
Optional: Vermeidung - LVAs die basierend auf dem Kursverlauf noch nicht ratsam sind
Optional: Erklärung warum bestimmte LVAs nicht gewählt wurden z.B. "Da du Soft1 noch nicht absolviert hast, ist Soft2, obwohl im Idealtypischen Studienplan sinnvoll, in deinem Plan noch nicht inkludiert."

### Funktionen:
#### ECTS-Zielvorgabe:   
min - Eingabe für maximale ECTS-Anzahl, Chat fragt nach, solange er die Information nicht hat
NiceToHave - Schieberegler  
#### Studienfortschritt:
min - Erfassung und Speicherung der absolvierten LVAs, Memory Funktion für Folgeplanungen, Abänderungen möglich  
NiceToHave - Importmöglichkeit der absolvieren Kurse vom .pdf "Ausfüllhilfe Prüfungsraster"  
#### Planungslogik:
min - Generierung eines gültigen Plans (Achtung WS/SS), der: 1. Die Voraussetzungsketten einhält. 2. Die Maximal-ECTS nicht überschreitet.  
NiceToHave - Optimierung nach idealtypischem Studienplan (Priorisierung der Kurse).  
#### Erklärung: 
min - Klare Begründung, warum vorgeschlagene Kurse gewählt wurden und warum wichtige Kurse ausgeschlossen wurden (z.B. fehlende Voraussetzung).  
NiceToHave - Empfehlungen für alternative LVAs (z.B. Wahlfächer), wenn der Pflichtplan nicht ideal gefüllt werden kann.  

### Benutzerinteraktion (LLM-Dialog)
User Prompt:
„Stelle mir mein kommendes Semester zusammen. Ich möchte max. 24 ECTS absolvieren.“

LLM Nachfrage:
„Welche LVAs wurden bereits absolviert? Bitte ergänze wenn nötig in deinen Nutzerdaten.  
„Welches ist das kommende Semester? Ist SS2026 korrekt?“

Retrieval / Datenbankzugriffe:  

JKU Curriculum (Voraussetzungen & ECTS)
Idealtypischer Studienplan
Abgeschlossene LVAs des Nutzers   

LLM Antwort:

Liste der empfohlenen LVAs, deren Voraussetzungen erfüllt sind
Gesamtumfang ≤ 24 ECTS
Optional: Priorisierung nach Studienfortschritt oder Semesterempfehlung
Optional: Liste mit Not-To-Do´s

## HOW - Systemarchitektur / Technologystack    
- Backend:  
  - Python
  - FastAPI  
  - Langchain
- Frontend:
  - Angular
  - HTTP Client 
- ETL-Pipeline:
  - Loader: PyPDFLoader (für PDFs), UnstructuredURLLoader (für Webseiten)
  - Chunker: RecursiveCharacterTextSplitter von Langchain
  - Preprocessor: Multi-Representation Indexing (ref: https://www.youtube.com/watch?v=sVcwVQRHIc8&t=4472s)
      Dokument → Split → mithilfe eines LLM die Splits überarbeiten und eine Proposition/Extraktion der Splits erzeugen → anschließend eine Zusammenfassung destillieren (eine Darstellung mit Schlüsselwörtern usw. des Dokuments), die für das Retrieval optimiert ist.
      Schritte: Zusammenfassung aus dem VektorDB abrufen, das vollständige Dokument aus dem Dokumentenspeicher anhand der Zusammenfassung heraussuchen, damit das LLM die Antwort generieren kann – das LLM kann das gesamte Dokument verarbeiten, sodass kein erneutes Splitting notwendig ist.
  - Embedder: Google Generative AI Embeddings 
- LLM
  - Gemini 
- Datenbank: 
     Neon DB, Tests bei allen Teammitgliedern erfolgreich.
  Entscheidung für eine einzige DB, auch für Nutzerdaten aufgrund der Größe des Projektes.
      
### Architektur
- Frontend (Angular) sendet die Planungsanfrage (ECTS-Ziel, neue Kurse) via HTTP an den Backend-Server. Format json, REST API
- Das Backend (Python) ruft die gespeicherten Kurse des Benutzers ab. 
- Der RAG-Orchestrator (LangChain) erstellt eine semantische Suchanfrage und sucht in der Neon Vektordatenbank nach den relevanten Modulbeschreibungen/Voraussetzungsketten (Retrieval).
- Der Orchestrator erstellt den finalen Prompt (Benutzerkontext + abgerufene Dokumente) und sendet ihn an das Gemini LLM.
- Gemini generiert den optimalen, begründeten Plan (Generation).
- Das Backend formatiert die LLM-Antwort und sendet sie als JSON via HTTP zurück an das Frontend.
- Das Frontend visualisiert den Plan als Chatantwort.

## Evaluierungsmethodik
- Login
Login mit vorhandenen Userdaten.  
Login erfolgreich und richtige Daten sichtbar.
- erste Planung
"Stelle mir mein kommendes Semester zusammen. Ich möchte max. 24 ECTS absolvieren."  
Liste von LVAs (ECTS $\le 24$): Alle vorgeschlagenen LVAs müssen freie Plätze haben (Voraussetzungen erfüllt).  
- Planung mit Constraints
Es wurde ALGO als absolviert eingetragen. "Chat: Max 18 ECTS für das SS2026."   
Muss SOFT1 enthalten (Voraussetzung ALGO erfüllt) und SOFT2 ausschließen (Voraussetzung SOFT1 noch nicht erfüllt).
- Erklärung
(Nach der Planung) "Warum wurde SOFT2 nicht vorgeschlagen?"   
"SOFT2 wurde nicht vorgeschlagen, da die Voraussetzung SOFT1 noch nicht absolviert wurde."

### 1. Retrieval-Komponente (Vektordatenbank & Embeddings)
Ziel ist es, die Trefferquote und Relevanz der abgerufenen curricularen Daten zu messen.
Methode: Manuelle Relevanzprüfung (Hit Rate/Precision)
- Vorgehen: Eine Reihe von mind. 15 testrelevanten Abfragen (z.B. "Voraussetzungen für den Kurs SOFT2", "ECTS von ALGO") an den RAG-Orchestrator stellen.
- Bewertung: Manuelle Prüfung der Top-3 abgerufenen Dokumenten-Chunks. Wurde die korrekte Modulbeschreibung oder Voraussetzungskette gefunden
- Metrik: Hit Rate: Wurde das relevante Dokument gefunden? und Precision: Wie viele der Top-3 Dokumente sind wirklich relevant?).
- Minimalanforderung: Eine Hit Rate @ 3 von mindestens 90 % für die kritischen Abfragen (Voraussetzungsketten, ECTS-Werte).
   
### 2. Generation-Komponente (LLM-Antwort)  
Ziel ist es, die Korrektheit und Nützlichkeit des generierten Semesterplans zu messen.
Methode: Manuelle/Experten-EvaluierungVorgehen: mind. 15 typische bis komplexe Planungsaufgaben mit verschiedenen absolvierten Kursen und ECTS-Zielen durchführen.
- Bewertung: Ein Experte (jemand mit Curriculum-Kenntnis) bewertet jede LLM-Antwort anhand folgender Kriterien:  
Faktische Korrektheit (Must-Have): Wurden alle Voraussetzungsketten beachtet? Wurde die Max-ECTS-Vorgabe eingehalten?
Vollständigkeit/Relevanz (Nice-to-Have): Wurde der Plan optimal nach dem idealtypischen Studienplan gefüllt?  
Begründungsqualität: Ist die Erklärung für die Kurswahl (oder Nicht-Wahl) klar und korrekt?  
- Minimalanforderung: 100 % faktische Korrektheit (Kriterium 1).  
Methode: LLM-basierte Ähnlichkeit (GPT-Similarity)  
Vorgehen: Die generierte Antwort des STUDYverse-LLM mit einer idealen, manuell erstellten Referenz-Antwort vergleichen.
Metrik: Nutzung eines externen, leistungsstarken LLM (z.B. GPT-4) zur Berechnung der semantischen Ähnlichkeit (Similarity-Score) zwischen der generierten und der idealen Antwort. Dies hilft bei der schnellen Überprüfung der Konsistenz in der Erklärung und der Priorisierung.
- Minimalanforderung: Ein durchschnittlicher Similarity-Score > 0,8 für die Begründungstexte.

### 3. Speicherung des Studienfortschritts (Memory-Funktion)  
Die Memory-Funktion zur Speicherung der absolvierten LVAs wird durch einfache Integrationstests geprüft.
Testfall: User gibt erstmals 5 absolvierte Kurse ein. User fragt im nächsten Chat nach der Planung.
Erwartung: Das System fragt nutzt die gespeicherten Daten und plant absolvierte Kurse nicht, Voraussetzungsketten stimmen.
