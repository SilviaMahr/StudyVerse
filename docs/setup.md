# PROJECT SETUP GUIDE 

## 🐍 Python Setup 

Dieser kurze Leitfaden dient der Vereinheitlichung unserer Python-Umgebung für das Projekt.  
Zudem sollen zeitfressende Konfigurationsprobleme umgangen werden.

**Version:**  
Die letzte stabile Version ist Python 3.12.0.  
Version 3.13 wäre grundsätzlich auch möglich, aber für unser kleines Projekt würde ich von Experimenten eher absehen und daher die *last stable version* verwenden.

**Download-Link:**  
- **Windows:**  
  https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe  
- **macOS:**  
  https://www.python.org/ftp/python/3.12.0/python-3.12.0-macos11.pkg


## ➡️ Weitere Schritte: 
- **Setzen der PATH-Variable:**  
  Python macht das „automatisch“ – **Wichtig:**  
  Bevor die Installation gestartet wird, gibt es unten die Möglichkeit *„Add Python 3.12.0 to PATH“* anzuklicken.  
  → Anklicken, dann erfolgt die Einbindung automatisch.

  Ob es geklappt hat, kann nach Abschluss des Installationsprozesses getestet werden:  
  Öffne die Eingabeaufforderung (`cmd.exe`) und gib folgenden Befehl ein:
  ```bash
  python --version

- 🧩 **IntelliJ Integration**:  
  IntelliJ Ultimate (gratis über die Uni erhältlich) beinhaltet ein Python-Plugin.  

  Navigiere zu:  
  `File` → `Settings` → `Plugins`  
  Gib in der Suchleiste **Python** ein → **Python** auswählen (NICHT *Python Community Edition*) → installieren.

- 📦 **Virtual Environment erstellen (VENV)** Da ich hier leider Probleme hatte, führe ich euch noch einen Workaround an, der für mich gut geklappt hat:
  - ```bash
    C:\Users\marle\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv
❗An euren individuellen Speicherort anpassen.
  - ```bash
    .venv\Scripts\Activate.ps1
  Falls die Script-Datei nicht startet, kann das an den Execution-Policies liegen
  Befehl unten erlaubt eigene Skripte und signierte Skripte aus dem Internet, blockiert aber nicht signierte Skripte von Drittanbietern.
  - ```bash
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  Nach erfolgreicher Aktivierung sollte (.venv) vor deinem Cursor im Terminal erscheinen.
  - ```bash
    python --version
    pip list
❗An dieser Stelle habe ich das empfohlene Update von pip 23.2.1 auf 25.2 vorgenommen -> Wenn das bei euch nötigt ist wird der cmd Befehl im IDE Terminal angezeigt
  - ```bash
    pip install -r requirements.txt
  Du musst dich aber im richtigen Ordner befinden, wo die .txt-Datei liegt.  
- ```bash
    cd backend
 ℹ️ Python Pakete für unsere Applikation -> wsl. wachsendes Doc. 

## 🔎 Google Gemini API
  - 🗝️ **API KEY**
    - Jeder muss einen Individuellen API Key generiern - folgend der Link zu Google AI Studios 
    - https://aistudio.google.com/
    - Mit eigenem Google-Konto anmelden
    - Zuerst neues Projekt erstellen: Linke Seitenleiste -> Projekte -> Create a new Project (oben)
    - Linke Seitenleiste: API Keys -> API-Schlüssel erstellen (rechts oben) -> Schlüssel benennen -> Projekt auswählen

❗Je Projekt ein neues Gemini Projekt erstellen -> also für die DKE Dummy Projekte eines und für unser Projekt dann auch ein eigenes erstellen - kann sonst ggf. zu Problemen führen! 

Nun gibt es zwei unterschiedliche Verfahren: 
1. Im DKE Dummy Projekt kann der API Key temporär per Terminaleingabe verknüpft werden: $Env:GEMINI_API_KEY="KEY_GOES_IN_HERE"
2. Im StudyVerse Projekt ist es sinnvoll den Key als IntelliJ Umgebungsvariable zu speichern, muss sonst jedes Mal aufs Neue eingegeben werden.
   Step by Step Erklärung in IntelliJ: 
   - Run -> Edit Configurations
   - Name z.B. beliebig auswählen z.B. rag 
   - Environment variables: API KEY -> Es müsste initial Pythonbufferd=1 im Feld stehen -> Edit Button anklicken -> + -> Name z.B.: GEMINI_API_KEY, Value: Persönlicher Key
   - ❗Evtl. ist es auch sinnvoll am lokalen PC eine Umgebungsvariable mit GEMINI_API_KEY (muss exakt so heißen) + Value = persönlicher Schlüssel zu setzen (ich hatte heute beim Neustart nämlich Probleme, seit Setzen des Path am lokalen PC funktioniert es aber. 

## Neon DB
https://neon.com/ login studyVerse@gmx.at !studyVerse0   
Examples: https://github.com/neondatabase/examples  


# 🌐 Angular/Frontend SET UP GUIDE
Following steps must be performed in order to run the angular frontend:

- install node.js ( v20.19.0 or newer) https://angular.dev/reference/versions
- open terminal in your IDE and run following commands:

Navigate from the root (StudyVerse) of the project to "frontend" $\to$ ...\StudyVerse\frontend:
with command:
```
cd frontend
```
Install required packages:
```
npm install
```

Run the build command:
```
ng build
```

In case the command fails, run:
```
npm install -g @angular/cli
```
Then build the frontend again.

After a successful build, start server:
```
ng serve
```
Open the application on localhost (you find the link in the terminal).

# 🔧 Fast API Backend Setup

Requirements Text updaten 
```
pip install -r requirements.txt
```
Backend starten
```
uvicorn backend.app.main:app --reload
```
Swagger UI öffnen: http://localhost:8000/docs 
