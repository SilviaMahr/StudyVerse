# Konzept  

## WHY - Problemstellung    
Studierende haben oft Schwierigkeiten, ihr Semester oder das Studium optimal zu planen: Sie wissen nicht genau, welche Lehrveranstaltungen im kommenden Semester sinnvoll sind.  

Voraussetzungsketten (z. B. ALGO → SOFT1 → SOFT2 → PR SE) sind im Studienhandbuch zwar dokumentiert, aber schwer überschaubar.
Der Studienfortschritt (bereits absolvierte Kurse) wird selten automatisch berücksichtigt. Viele Studierende arbeiten nebenher und/oder haben Betreuungspflichten und haben somit Ressourcen für unter 30 ECTS.  

Der Study Planner soll Studierende bei der individuellen Semesterplanung unterstützen, indem er basierend auf bisherigen Leistungen, ECTS-Zielvorgaben und Curriculumsdaten ein ideales Semester vorschlägt.  

Retrieval-Augmented Generation (RAG)-System ist hier die ideale Lösung, weil hier der Zugriff auf aktuelle und korrekte curriculare Daten essentiell ist, mit Halluzinationen würde das System sinnlos sein. Aktualität, Zuverlässigkeit, Wissenstransparenz und Kontrollierbarkeit sind Vorraussetzung. Durch das Einfügen der Constraints (bisher absolvierte Kurse, Voraussetzungskette, ECTS-Vorgabe) im Abfragekontext wird vom LLM eine gute Antwort generiert.   

RAG verbindet die Verlässlichkeit und Spezifität der Studienordnung (durch den Retrieval-Teil) mit der Flexibilität, Personalisierungsfähigkeit und Kommunikationsstärke des LLMs (durch den Generation-Teil). Es ist die effektivste Methode, um eine individuelle, korrekte und gut begründete Semesterplanung zu erstellen.

## WHAT - Ziel des Systems  
Der Study Planner soll automatisch für Studierende im Bachelorstudium Wirtschaftsinformatik ein Semester mit passenden LVAs zusammenstellen.
Er berücksichtigt dabei:
- Die gewünschte Anzahl an ECTS (z. B. max. 24 ECTS)
- Bereits absolvierte LVAs (Ideal wäre mit Memory Funktion: Eine einmalige Eingabe je absolvierter LVA sollte ausreichend sein - für die nächste Semesterplanung sollen nicht ALLE absolvierten Kurse wieder ausgewählt werden müssen, sondern nur jene die noch nie abgegeben wurde - Redundanzvermeidung).
- Voraussetzungsketten laut Curriculum (Oft im Studienhandbuch zu finden)
- Berücksichtigung Idealtypischer Studienplan

Optional: Empfehlungen für alternative LVAs, wenn kein ideales Semester möglich ist
Optional: Vermeidung - LVAs die basierend auf dem Kursverlauf noch nicht ratsam sind
Optional: Erklärung warum bestimmte LVAs nicht gewählt wurden z.B. "Da du Soft1 noch nicht absolviert hast, ist Soft2, obwohl im Idealtypischen Studienplan sinnvoll, in deinem Plan noch nicht inkludiert."

Scope: Bachelor Wirtschaftsinformatik  

### Benutzerinteraktion (LLM-Dialog)
User Prompt:
„Stelle mir mein kommendes Semester zusammen. Ich möchte max. 24 ECTS absolvieren.“

LLM Nachfrage:
„Welche LVAs wurden bereits absolviert?“

Eingabe über Klick-Option oder Liste
Speicherung im Memory, damit diese Information nur einmal eingegeben werden muss
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
Backend Python, Frontend Angular, Datenbank: ?? 
⚠️ //TODO: muss noch finalisiert werden, jeder recherchiert seinen Part -> Klare Part-Abgrenzung sehr schwierig! 
Habe mal einen kollektiven Generalvorschlag untenstehend -> Jene Punkte mit ? und ⚠️ gehören noch von den jeweiligen
zuständigen Personen selbst recherchiert. Änderungen dürfen vorgenommen werden! 

- Backend: 
  - Python -> ⚠️Flask oder FastAPI um Angular Anbindung zu ermöglichen (Angular + Python nicht rein lokal möglich) daher Entscheidung für Flask oder Fast API treffen! Würde aber Flask vorschlagen, da mit SQLite DB super verbindbar. 
  - Langchain
- Frontend:
  - Angular
  - HTTP Client 
- ETL-Pipeline:
  - Loader ???⚠️
  - Chunker: RecursiveCharacterTextSplitter von Langchain ???? ⚠️
  - Preprocessor ??⚠️
  - Embedder: Google Generative AI Embeddings 
- LLM
  - Gemini 
- Datenbank: 
    1. Relationale DB: SQLite
        - Nutzerdaten inkl. Authentication 
        - Absolvierte LVAs je Nutzer
    2. Vektordatenbank⚠️
        - TBA -> zB Chroma - keine Tiefe Recherche dazu betrieben -> Offenes TODO⚠️

## Evaluierungsmethodik
//TODO: Silvia⚠️
