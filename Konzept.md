# Konzept  

## WHY - Problemstellung    
Studierende haben oft Schwierigkeiten, ihr Semester oder das Studium optimal zu planen: Sie wissen nicht genau, welche Lehrveranstaltungen im kommenden Semester sinnvoll sind.  

Voraussetzungsketten (z. B. ALGO → SOFT1 → SOFT2 → PR SE) sind im Studienhandbuch zwar dokumentiert, aber schwer überschaubar.
Der Studienfortschritt (bereits absolvierte Kurse) wird selten automatisch berücksichtigt.  

Der Study Planner soll Studierende bei der individuellen Semesterplanung unterstützen, indem er basierend auf bisherigen Leistungen, ECTS-Zielvorgaben und Curriculumsdaten ein ideales Semester vorschlägt.  

## WHAT - Ziel des Systems  
Der Study Planner soll automatisch ein Semester mit passenden LVAs zusammenstellen.
Er berücksichtigt dabei:
- Die gewünschte Anzahl an ECTS (z. B. max. 24 ECTS)
- Bereits absolvierte LVAs (Ideal wäre mit Memory Funktion: Eine einmalige Eingabe je absolvierter LVA sollte ausreichend sein - für die nächste Semesterplanung sollen nicht ALLE absolvierten Kurse wieder ausgewählt werden müssen, sondern nur jene die noch nie abgegeben wurde - Redundanzvermeidung).
- Voraussetzungsketten laut Curriculum (Oft im Studienhandbuch zu finden)
- Berücksichtigung Idealtypischer Studienplan

Optional: Empfehlungen für alternative LVAs, wenn kein ideales Semester möglich ist
Optional: Vermeidung - LVAs die basierend auf dem Kursverlauf noch nicht ratsam sind
Optional: Erklärung warum bestimmte LVAs nicht gewählt wurden z.B. "Da du Soft1 noch nicht absolviert hast, ist Soft2, obwohl im Idealtypischen Studienplan sinnvoll, in deinem Plan noch nicht inkludiert."

Scope: Fokus auf Bachelor Wirtschaftsinformatik 

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
  - Loader: PyPDFLoader (für PDFs), UnstructuredURLLoader (für Webseiten)
  - Chunker: RecursiveCharacterTextSplitter von Langchain
  - Preprocessor: Multi-Representation Indexing (ref: https://www.youtube.com/watch?v=sVcwVQRHIc8&t=4472s)
      Dokument → Split → mithilfe eines LLM die Splits überarbeiten und eine Proposition/Extraktion der Splits erzeugen → anschließend eine Zusammenfassung destillieren (eine Darstellung mit Schlüsselwörtern usw. des Dokuments), die für das Retrieval optimiert ist.
      Schritte: Zusammenfassung aus dem VektorDB abrufen, das vollständige Dokument aus dem Dokumentenspeicher anhand der Zusammenfassung heraussuchen, damit das LLM die Antwort generieren kann – das LLM kann das gesamte Dokument verarbeiten, sodass kein erneutes Splitting notwendig ist.
  - Embedder: Google Generative AI Embeddings 
- LLM
  - Gemini 
- Datenbank: 
    1. Relationale DB: SQLite
        - Nutzerdaten inkl. Authentication 
        - Absolvierte LVAs je Nutzer
        - Concurrency Probleme: kein echtes Multi-user System 
        - (multi-user: PostgreSQL eher geeignet)
    2. Vektordatenbank: zB ChromaDB
        - gut für Kleinprojekt, prototypisch (nicht Produktivumgebung)
        - Python kompatibel mit Flask/FastAPI
        - integrierbar mit LangChain
        - open source, lokal
        - einfach einzurichten (kein API-key notwendig)
        - speichert Embeddings, unterstützt Retrieval
        - MRI mit Chroma: mehrere Collections oder Embeddings nutzen (MultiVectorRetriever)
        - ansonsten Qdrant

## Evaluierungsmethodik
//TODO: Silvia⚠️
