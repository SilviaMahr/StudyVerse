# Retrieval System - StudyVerse

## Überblick

Das Retrieval-System implementiert eine **Hybrid-RAG-Pipeline** für intelligente Studienplanung:

1. **Query Parser** - Extrahiert strukturierte Informationen aus natürlichsprachlichen Anfragen
2. **Hybrid Retrieval** - Kombiniert Metadata-Filtering mit Vector Similarity Search
3. **LLM Planner** - Generiert optimierte Semesterpläne mit Gemini

## Architektur

```
User Query
    ↓
Query Parser (query_parser.py)
    ↓ (parsed parameters + metadata filter)
Hybrid Retriever (retrieval.py)
    ↓ (relevant LVAs)
Semester Planner (semester_planner.py)
    ↓
Semester Plan (formatiert)
```

## Komponenten

### 1. Query Parser (`backend/app/query_parser.py`)

**Funktionen:**
- `parse_user_query(query)` - Extrahiert ECTS, Semester, Tage, gewünschte LVAs
- `build_metadata_filter(parsed_query)` - Erstellt Filter-Dict für pgvector
- `extract_completed_lvas(user_input)` - Findet bereits absolvierte LVAs

**Beispiel:**
```python
from backend.app.query_parser import parse_user_query

query = "15 ECTS im SS26, Montag und Mittwoch, ich möchte SOFT1 machen"
parsed = parse_user_query(query)

# Output:
# {
#   "ects_target": 15,
#   "semester": "SS",
#   "preferred_days": ["Mo.", "Mi."],
#   "desired_lvas": ["Einführung in die Softwareentwicklung", ...],
#   "free_text": "15 ECTS im SS26, ..."
# }
```

### 2. Hybrid Retriever (`backend/app/retrieval.py`)

**Klasse:** `HybridRetriever`

**Hauptmethoden:**
- `retrieve(query, metadata_filter, top_k)` - Hybrid Search (Metadata + Vector)
- `retrieve_by_lva_name(lva_name, top_k)` - Suche nach LVA-Namen/Alias

**Beispiel:**
```python
from backend.app.retrieval import HybridRetriever

retriever = HybridRetriever()

# Hybrid Search mit Filter
filter_dict = {
    "$and": [
        {"semester": {"$eq": "SS"}},
        {"tag": {"$in": ["Mo.", "Mi."]}}
    ]
}

results = retriever.retrieve(
    query="Softwareentwicklung",
    metadata_filter=filter_dict,
    top_k=15
)
```

**Filter-Operatoren:**
- `$eq` - Gleichheit
- `$in` - Enthält (für Listen)
- `$lte` - Kleiner-gleich (für ECTS)
- `$gte` - Größer-gleich
- `$and` - Logisches UND
- `$or` - Logisches ODER

### 3. Semester Planner (`backend/app/semester_planner.py`)

**Klasse:** `SemesterPlanner`

**Hauptmethoden:**
- `create_semester_plan(...)` - Erstellt Semesterplan aus retrieved LVAs
- `answer_study_question(question, context_lvas)` - Beantwortet allgemeine Fragen

**Beispiel:**
```python
from backend.app.semester_planner import SemesterPlanner

planner = SemesterPlanner()

plan = planner.create_semester_plan(
    user_query="15 ECTS im SS26, Mo + Mi",
    retrieved_lvas=lvas,  # Von Retriever
    ects_target=15,
    preferred_days=["Mo.", "Mi."],
    completed_lvas=[],
    desired_lvas=["Einführung in die Softwareentwicklung"]
)
```

### 4. Integriertes RAG-System (`backend/app/integrated_rag.py`)

**Klasse:** `StudyPlanningRAG`

**End-to-End Pipeline** - kombiniert alle Komponenten.

**Hauptmethoden:**
- `create_semester_plan(user_query)` - Komplette Pipeline für Semesterplanung
- `answer_question(question)` - Beantwortet Studienfragen
- `search_lva_by_name(lva_name)` - Sucht spezifische LVAs

**Beispiel:**
```python
from backend.app.integrated_rag import StudyPlanningRAG

rag = StudyPlanningRAG()

# Semesterplanung
result = rag.create_semester_plan(
    "15 ECTS im SS26, Montag und Mittwoch, ich möchte SOFT1 machen"
)
print(result["plan"])

# Frage beantworten
answer = rag.answer_question(
    "Muss ich in Softwareentwicklung eine Klausur schreiben?"
)
print(answer)
```

## Testing

### Test-Skript ausführen:

```bash
cd "C:\Users\marle\PR DKE\StudyVerse"
python test_retrieval.py
```

Das Test-Skript testet:
1. **Semester Planning** - Mit verschiedenen Query-Typen
2. **Question Answering** - Allgemeine Studienfragen
3. **LVA Search** - Suche nach spezifischen LVAs

### Einzelne Komponenten testen:

```bash
# Query Parser testen
python backend/app/query_parser.py

# Retriever testen
python backend/app/retrieval.py

# Planner testen
python backend/app/semester_planner.py

# Komplettes System testen
python backend/app/integrated_rag.py
```

## LVA-Aliase

Häufige Abkürzungen werden automatisch erkannt:

| Alias | Voller Name |
|-------|-------------|
| SOFT1 | Einführung in die Softwareentwicklung |
| SOFT2 | Vertiefung Softwareentwicklung, Algorithmen und Datenstrukturen |
| EWIN | Einführung in die Wirtschaftsinformatik |
| BWL | Betriebswirtschaftslehre |
| DM | Datenmanagement |
| BS | Betriebssysteme |

Neue Aliase können in `backend/app/query_parser.py` hinzugefügt werden.

## Integration ins Backend

Das RAG-System kann einfach in FastAPI-Endpoints integriert werden:

```python
from fastapi import APIRouter
from backend.app.integrated_rag import StudyPlanningRAG

router = APIRouter()
rag = StudyPlanningRAG()

@router.post("/plan")
async def create_plan(user_query: str):
    result = rag.create_semester_plan(user_query)
    return {"plan": result["plan"]}

@router.post("/ask")
async def ask_question(question: str):
    answer = rag.answer_question(question)
    return {"answer": answer}
```

## Troubleshooting

### Fehler: "DATABASE_URL not set"
→ Stelle sicher, dass `.env` die `DATABASE_URL` enthält

### Fehler: "GEMINI_API_KEY not set"
→ Stelle sicher, dass `.env` den `GEMINI_API_KEY` enthält

### Keine Ergebnisse beim Retrieval
→ Prüfe ob die ETL-Pipeline erfolgreich gelaufen ist:
```sql
SELECT COUNT(*) FROM studyverse_data;
```

### Embedding-Dimension-Fehler
→ Stelle sicher, dass die DB-Tabelle 768 Dimensionen hat (siehe `data_ingestion/fix_vector_dimension.py`)

## Nächste Schritte

1. **Frontend-Integration** - Connect Vue.js Frontend mit RAG-Endpoints
2. **User-Profil** - Speichern von absolvierten LVAs pro User
3. **Plan-Persistenz** - Semesterpläne in DB speichern
4. **Feedback-Loop** - User-Feedback für bessere Vorschläge
5. **Erweiterte Filter** - Zusätzliche Constraints (Uhrzeit, Präsenz vs. Remote, etc.)

## Support

Bei Fragen oder Problemen:
- Dokumentation: `docs/End-To-End-Process.md`
- ETL-Pipeline: `data_ingestion/`
- Test-Output analysieren: `python test_retrieval.py`
