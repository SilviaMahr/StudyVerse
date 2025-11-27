# StudyVerse (RAG)
Beantwortet Fragen zur JKU, Studienrichtungen oder Kursen.   
Kontext: JKU-Webseite, Studienhandbuch, Curricula, …  

1. User Interface (z.B. Für Webinterface mit Chateingabe) --> Johanna  
2. ETL Komponente (z.B. Studienhandbuch parsen und für Retrieval aufbereiten) --> Sabiha
3. Retrieval Komponente (z.B. Relevante Nachrichten anhand der Benutzerfrage finden) --> Marlene
4. LLM Komponente (z.B. Aktuellen Chat merken; Fragen + relevante Nachrichten als Prompt an das LLM senden und Chatverlauf erweitern) --> Silvia
  
[Figma Prototyp](https://www.figma.com/design/uTokxSX0O6d765v8ZwYtTI/STUDYverse-aktuell?node-id=66-916&p=f&t=iqx1N1wW5LkpCcbu-0)  
[weekly - Dienstags 14:00](https://jku.zoom.us/j/92197402897?pwd=41cmjlSR6S64oAqpvEmRWyhW36d75D.1)  

Start backend
```
uvicorn backend.app.main:app --reload
```
