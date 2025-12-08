# Retrieval → LLM: Informationsfluss in StudyVerse

Dieses Dokument beschreibt, welche Informationen das Retrieval-System beschafft und an das LLM (Gemini) weiterleitet, sowie was das LLM damit tun kann.

---

## 1. Was das Retrieval-System beschafft

### 1.1 User-Query Parsing

**Datei:** `backend/app/retrieval/query_parser.py:31-86`

Das System extrahiert aus der natürlichsprachlichen User-Anfrage:

| Parameter | Beispiel | Beschreibung |
|-----------|----------|--------------|
| `ects_target` | `15` | Gewünschte ECTS-Anzahl |
| `semester` | `"SS"` oder `"WS"` | Zielsemester |
| `preferred_days` | `["Mo.", "Mi."]` | Bevorzugte Wochentage |
| `desired_lvas` | `["Einführung in die Softwareentwicklung"]` | Explizit gewünschte LVAs (via Aliase wie "SOFT1") |
| `free_text` | Original-Query | Text für semantische Suche |

**Manche Aliase werden automatisch aufgelöst** (`query_parser.py:10-20`):
- `"soft1"` → `"Einführung in die Softwareentwicklung"`
- `"algo"` → `"Algorithmen und Datenstrukturen"`
- `"dm"` → `"Datenmodellierung"`
- etc. **Sollte das Alias nicht bekannt sein z.B. User gibt ein: SE1 muss das LLM nachfragen**

---

### 1.2 Datenbank-Retrieval (Hybrid Search)

**Datei:** `backend/app/retrieval/hybrid_retriever.py:164-284`

Das System führt eine **Hybrid-Suche** durch, die kombiniert:
1. **Vector Similarity Search** (semantische Suche via Embeddings) (für Freitextsuche und Userfragen) 
2. **Metadata Filtering** (harte Constraints wie Semester, Tage, ECTS)

#### Für jede LVA werden folgende Informationen abgerufen:

```python
{
    "id": int,                    # Dokument-ID
    "content": str,               # Vollständiger Textinhalt aus Studienhandbuch
    "metadata": {
        "lva_nr": str,            # z.B. "256.100"
        "lva_name": str,          # z.B. "Einführung in die Softwareentwicklung"
        "lva_type": str,          # VL/UE/PR/SE/KS/KV/PS/PE/PJ/KT
        "ects": float,            # ECTS-Punkte
        "semester": str,          # SS/WS/SS+ (SS+ = ganzjährig)
        "tag": str,               # Mo./Di./Mi./Do./Fr.
        "uhrzeit": str,           # z.B. "08:30 - 10:00"
        "lva_leiter": str,        # Dozent/LVA-Leiter
        "anmeldevoraussetzungen": str  # Voraussetzungen (oder "Keine")
    },
    "url": str,                   # Link zum Studienhandbuch
    "similarity": float           # Cosinus-Ähnlichkeit (0.0 - 1.0)
}
```

**Der `content`-String enthält:**
- Lehrziele
- Lehrinhalte
- Prüfungsmodalitäten
- Erwartete Vorkenntnisse
- Detaillierte Beschreibungen aus dem Studienhandbuch

---

### 1.3 User-Profil: Absolvierte LVAs

**Datei:** `backend/app/retrieval/hybrid_retriever.py:631-660`

Das System holt alle abgeschlossenen LVAs des Users aus der Datenbank:

```sql
SELECT l.name, l.ects, l.hierarchielevel2
FROM completed_lvas cl
JOIN lvas l ON cl.lva_id = l.id
WHERE cl.user_id = %s
```

**Rückgabe:** Liste von LVA-Namen
```python
["Einführung in die Softwareentwicklung", "BWL", "Mathematik"]
```

---

### 1.4 Automatisches Filtering

**Datei:** `backend/app/retrieval/hybrid_retriever.py:452-629`

**Vor** der Weiterleitung an das LLM werden LVAs automatisch herausgefiltert, die:

#### ❌ Filter-Kriterien (in dieser Reihenfolge):

1. **Falsches Semester** (`hybrid_retriever.py:534-556`)
   - LVA hat kein Semester-Feld (Curriculum-Eintrag, nicht konkrete LVA)
   - LVA findet im falschen Semester statt (z.B. WS-LVA bei SS-Anfrage)

2. **Wahlfach** (`hybrid_retriever.py:558-566`)
   - LVA ist in der `wahlfach`-Tabelle
   - AUSNAHME: User erwähnt Wahlfach explizit in Query

3. **Bereits absolviert** (`hybrid_retriever.py:568-587`)
   - Fuzzy-Match gegen `completed_lvas` (Threshold: 0.75)
   - Substring-Match für LVA-Nummern

4. **Voraussetzungen nicht erfüllt** (`hybrid_retriever.py:589-624`)
   - Extrahiert Voraussetzungen aus `anmeldevoraussetzungen`-Feld
   - Fallback: Bekannte Voraussetzungsketten (`KNOWN_PREREQUISITES`)
   - LIKE-Abgleich gegen absolvierte LVAs

**Rückgabe:**
```python
{
    "eligible": [...]      # LVAs die alle Kriterien erfüllen
    "filtered": [          # LVAs die gefiltert wurden (mit Grund)
        {
            "lva": {...},
            "missing_prerequisites": ["SOFT1", "ALGO"],
            "reason": "Fehlende Voraussetzungen: SOFT1, ALGO"
        }
    ]
}
```

---

### 1.5 Deduplication

**Datei:** `backend/app/retrieval/hybrid_retriever.py:232-273`

Das System entfernt Duplikate basierend auf `(lva_name, lva_type)`:
- **Problem:** Gleiche LVA mit verschiedenen Zeitslots (z.B. "VL Datenmodellierung" mit lva_nr 258.100, 258.101, 258.102)
- **Lösung:** Nur die **erste (beste)** Instanz wird behalten (höchster Similarity Score)

---

## 2. Was an das LLM weitergeleitet wird

### 2.1 Prompt-Struktur für Semesterplanung (JSON-Modus)

**Datei:** `backend/app/llm_connection/semester_planner.py:360-447`

Das LLM erhält einen strukturierten Prompt mit folgenden Sektionen:

#### A) **Kontext & Zielvorgaben:**

```
**USER-ANFRAGE:**
[Original User-Query]

**ZIEL-PARAMETER:**
- ECTS-Ziel: 15 ECTS
- Bevorzugte Tage: Mo., Mi.
- Bereits absolvierte LVAs: SOFT1, BWL, Mathematik
- Gewünschte LVAs: Datenmodellierung

**IDEALTYPISCHER STUDIENVERLAUF:**
[Laden aus ideal_plan_loader.py - zeigt empfohlene LVA-Reihenfolge]
```

#### B) **Verfügbare LVAs** (nur eligible):

**Datei:** `backend/app/llm_connection/semester_planner.py:247-282`

Für jede LVA wird formatiert:

```
LVA 256.100: Einführung in die Softwareentwicklung (VL)
  - ECTS: 3.0
  - Semester: SS
  - Wochentag: Mo. um 08:30 - 10:00
  - LVA-Leiter: Wieland Schwinger
  - Voraussetzungen: Keine

  DETAILLIERTE INFORMATIONEN AUS STUDIENHANDBUCH:
  [Vollständiger Content-String aus der Datenbank]
  - Lehrziele
  - Lehrinhalte
  - Prüfungsmodalitäten
  - Erwartete Vorkenntnisse
  - etc.
```

#### C) **Ausgeschlossene LVAs** (optional):

**Datei:** `backend/app/llm_connection/semester_planner.py:372-381`

```
**AUSGESCHLOSSENE LVAs (Voraussetzungen nicht erfüllt):**
Diese LVAs wurden bereits herausgefiltert und sollten NICHT im Plan erscheinen:
- Software Engineering (256.200): Fehlende Voraussetzungen: SOFT1, SOFT2
- Data Mining (258.300): Fehlende Voraussetzungen: DKE
```

---

### 2.2 Prompt-Struktur für Chat-Antworten

**Datei:** `backend/app/llm_connection/semester_planner.py:285-357`

Wenn ein **existierender Plan** vorhanden ist:

```
**USER-ANFRAGE:**
[Neue Frage des Users]

**BEREITS ERSTELLTER SEMESTERPLAN:**
Der User hat bereits folgenden Semesterplan erstellt:

```json
{
  "semester": "SS26",
  "total_ects": 15,
  "lvas": [...]
}
```

**ZIEL-PARAMETER:**
[Wie oben]

**VERFÜGBARE LVAs (Voraussetzungen erfüllt):**
[Wie oben]

**AUSGESCHLOSSENE LVAs:**
[Wie oben]
```

---

## 3. Was das LLM damit tun kann

### 3.1 Semesterplanung (JSON-Output)

**Datei:** `backend/app/llm_connection/semester_planner.py:107-186`

#### **Aufgaben des LLM:**

1. **Optimale LVA-Auswahl** (`semester_planner.py:401-408`)
   - ✅ ECTS-Ziel erreichen (Unterschreitung max. 3 ECTS, keine Überschreitung)
   - ✅ Gewünschte LVAs priorisieren
   - ✅ Idealtypischen Studienverlauf berücksichtigen/priorisieren 

3. **Zeitkonfliktprüfung** (`semester_planner.py:415-416`)
   - ✅ Keine zwei LVAs zur selben Zeit

4. **JSON-Output generieren** (`semester_planner.py:419-438`)
   ```json
   {
     "semester": "SS26",
     "total_ects": 15,
     "uni_days": ["Mo.", "Mi."],
     "lvas": [
       {
         "name": "Einführung in die Softwareentwicklung",
         "type": "VL",
         "ects": 3,
         "day": "Mo.",
         "time": "08:30 - 10:00",
         "instructor": "Wieland Schwinger",
         "reason": "Pflichtfach im 1. Semester, keine Voraussetzungen"
       }
     ],
     "summary": "Der Plan erfüllt dein ECTS-Ziel von 15 ECTS...",
     "warnings": "SOFT2 UE überschneidet sich mit BWL VL..."
   }
   ```

---

### 3.2 Chat-Antworten (Text-Output)

**Datei:** `backend/app/llm_connection/semester_planner.py:50-105`

#### **Aufgaben des LLM:**

1. **Fragen beantworten** basierend auf:
   - ✅ Existierendem Semesterplan (falls vorhanden)
   - ✅ Retrieved LVA-Daten (Content + Metadata)
   - ✅ Filtered LVAs (mit Erklärungen)

2. **Erklärungen geben:**
   - ✅ Warum bestimmte LVAs vorgeschlagen/nicht vorgeschlagen wurden
   - ✅ Welche Voraussetzungen fehlen
   - ✅ Welche Alternativen existieren

3. **Auf Studienhandbuch verweisen:**
   - ✅ Falls Informationen nicht im Kontext vorhanden sind
   - ✅ Link: https://studienhandbuch.jku.at/?lang=de

**Beispiel-Output:**
```
Dein Plan für SS26 sieht gut aus! Ich habe dir SOFT1 (VL + UE)
für Montag eingeplant, da du das explizit gewünscht hast.

⚠️ Hinweis: Software Engineering (SOFT2) konnte ich nicht
einplanen, da die Voraussetzungen (SOFT1) noch nicht erfüllt
sind. Du kannst SOFT2 im nächsten Semester machen.

Für weitere Details siehe: https://studienhandbuch.jku.at/...
```

---

### 3.3 Allgemeine Studienfragen

**Datei:** `backend/app/llm_connection/semester_planner.py:449-487`

#### **Aufgaben des LLM:**

- ✅ Fragen zu LVAs beantworten (z.B. "Muss ich in BWL eine Klausur schreiben?")
- ✅ Basierend auf retrieved Content (ohne Planungsfunktion)
- ✅ Präzise Antworten, keine Halluzinationen

**Beispiel-Query:**
```
"Muss ich in Softwareentwicklung eine Klausur schreiben?"
```

**LLM erhält:**
```
**KONTEXT (Relevante LVA-Daten):**
LVA 256.100: Einführung in die Softwareentwicklung (VL)
  ...
  DETAILLIERTE INFORMATIONEN:
  Prüfungsmodalitäten: Schriftliche Klausur (60 Min.),
  Anwesenheitspflicht in UE...
```

**LLM antwortet:**
```
Ja, in der VL Einführung in die Softwareentwicklung gibt es
eine schriftliche Klausur (60 Minuten). Zusätzlich besteht
Anwesenheitspflicht in der begleitenden Übung (UE).
```

---

## 4. Technische Details

### 4.1 Embeddings

- **Modell:** `text-embedding-004` (Google Generative AI)
- **Datei:** `backend/app/retrieval/hybrid_retriever.py:50-53`
- **Verwendung:** Vektorisierung der User-Query für semantische Suche

### 4.2 LLM-Modell

- **Modell:** `gemini-2.5-flash-lite` (aktuell im Code)
- **Datei:** `backend/app/llm_connection/semester_planner.py:44`
- **Temperature:** 0.3 (für Planung), 0.1 (für Fragen)

### 4.3 Datenbankabfrage

**Similarity-Berechnung:**
```sql
1 - (embedding <=> %s::vector) AS similarity
```
- `<=>` = Cosinus-Distanz-Operator (pgvector)
- `1 - distance` = Similarity Score (höher = ähnlicher)

**Top-K Retrieval:**
- Default: 100 LVAs (vor Deduplication)
- Fetch-Limit: `max(top_k * 50, 5000)` für comprehensive Semester-Planung
- Nach Deduplication: Deutlich weniger (nur unique LVAs)

---

## 5. Zusammenfassung: Informationsfluss

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                               │
│    "15 ECTS im SS26, Mo+Mi, ich will SOFT1 machen"        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. QUERY PARSING (query_parser.py)                         │
│    ✓ ECTS: 15                                              │
│    ✓ Semester: SS                                          │
│    ✓ Tage: [Mo., Mi.]                                      │
│    ✓ LVAs: [Einführung in die Softwareentwicklung]        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. HYBRID RETRIEVAL (hybrid_retriever.py)                  │
│    ✓ Vector Search (Embeddings)                           │
│    ✓ Metadata Filter (Semester, Tage, ECTS)               │
│    ✓ Fetch: ~5000 Documents                               │
│    ✓ Deduplication: ~200 unique LVAs                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. FILTERING (hybrid_retriever.py)                         │
│    ❌ Falsches Semester                                     │
│    ❌ Wahlfächer (außer explizit gewünscht)                 │
│    ❌ Bereits absolviert                                    │
│    ❌ Voraussetzungen nicht erfüllt                         │
│    ✓ Eligible: ~50 LVAs                                    │
│    ✓ Filtered: ~150 LVAs (mit Grund)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. LLM PROMPT BUILDING (semester_planner.py)               │
│    ✓ User-Query + Ziele                                    │
│    ✓ Eligible LVAs (Content + Metadata)                   │
│    ✓ Filtered LVAs (mit Erklärungen)                      │
│    ✓ Absolvierte LVAs                                      │
│    ✓ Idealtypischer Studienverlauf                        │
│    → Prompt: ~50,000 chars (~12,500 tokens)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. LLM PROCESSING (Gemini 2.5 Flash Lite)                  │
│    ✓ Analysiert alle LVAs                                  │
│    ✓ Prüft Voraussetzungen (Metadata + Content)           │
│    ✓ Prüft Zeitkonflikte                                   │
│    ✓ Optimiert nach ECTS-Ziel                             │
│    ✓ Berücksichtigt User-Wünsche                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. OUTPUT                                                   │
│    JSON: Semesterplan mit Begründungen                     │
│    TEXT: Chat-Antwort mit Erklärungen                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Key Insights

### ✅ Was das System GUT macht:
- **Hybrid Search:** Kombiniert semantische Suche + Metadata-Filter
- **Automatisches Filtering:** LLM erhält nur relevante LVAs
- **Vollständiger Content:** LLM kann Voraussetzungen aus Studienhandbuch prüfen
- **Deduplication:** Keine redundanten LVAs (verschiedene Zeitslots)
- **Erklärbarkeit:** Filtered LVAs mit Begründungen

### ⚠️ Potenzielle Herausforderungen:
- **Prompt-Size:** ~12,500 tokens (kann bei vielen LVAs Limit erreichen)
- **LLM-Reliability:** Voraussetzungsprüfung hängt von LLM ab (keine harte Logik)
- **Fuzzy Matching:** Threshold 0.75 kann False Positives/Negatives erzeugen
- **Wahlfach-Filter:** Substring-Match könnte zu aggressiv sein

---

**Erstellt:** 2025-12-08
**Autor:** Dokumentation des StudyVerse RAG-Systems
**Codebase:** `backend/app/retrieval/`, `backend/app/llm_connection/`
