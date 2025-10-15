# 🐍 PYTHON SETUP GUIDE

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


## Weitere Schritte: 
- **Setzen der PATH-Variable:**  
  Python macht das „automatisch“ – **Wichtig:**  
  Bevor die Installation gestartet wird, gibt es unten die Möglichkeit *„Add Python 3.12.0 to PATH“* anzuklicken.  
  → Anklicken, dann erfolgt die Einbindung automatisch.

  Ob es geklappt hat, kann nach Abschluss des Installationsprozesses getestet werden:  
  Öffne die Eingabeaufforderung (`cmd.exe`) und gib folgenden Befehl ein:
  ```bash
  python --version

- **IntelliJ Integration**:  
  IntelliJ Ultimate (gratis über die Uni erhältlich) beinhaltet ein Python-Plugin.  

  Navigiere zu:  
  `File` → `Settings` → `Plugins`  
  Gib in der Suchleiste **Python** ein → **Python** auswählen (NICHT *Python Community Edition*) → installieren.

  **Virtual Environment erstellen (VENV)** Da ich hier leider Probleme hatte, führe ich euch noch einen Workaround an, der für mich gut geklappt hat:
  - ```bash
    C:\Users\marle\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv
❗An euren individuellen Speicherort anpassen.

  - ```bash
    .venv\Scripts\Activate.ps1
  - ```bash
    python --version
    pip list
❗An dieser Stelle habe ich das empfohlene Update von pip 23.2.1 auf 25.2 vorgenommen -> Wenn das bei euch nötigt ist wird der cmd Befehl im IDE Terminal angezeigt
  - ```bash
    pip install -r requirements.txt
 ℹ️ Python Pakete für rag.py und llm-agent.py

- **Google Gemini API**




 
  
