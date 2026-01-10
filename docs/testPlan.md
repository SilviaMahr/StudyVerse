# StudyVerse Testplan
## Testfall 1: Login mit gültigen Zugangsdaten
**Beschreibung:**
Sicherstellung, dass sich ein registrierter User sich mit gültiger E-Mail-Adresse und Passwort einloggen kann. 

**Voraussetzungen:** 
 - Benutzer*in ist bereits registriert.

**Testschritte:**
1. Aufrufen StudyVerse-Website
2. Eingabe einer gültigen E-Mail-Adresse.
3. Eingabe eines gültigen, dazugehörigen Passwort.
4. Bestätigung des Logins durch Klick auf den Button "Anmelden". 

**Erwartetes Ergebnis:** 
 - Benutzer*in wird erfolgreich eingeloggt und die Seite zur Erstellung eines neuen Planes wird angezeigt.

---

## Testfall 2: Neuregistrierung
**Beschreibung:** Sicherstellung, das neue User*innen sich bei der ersten Verwendung von StudyVerse registrieren können.

**Voraussetzungen:** - 

**Testschritte:**
1. Aufrufen der StudyVerse-Website.
2. Klick auf "Jetzt registrieren", unterhalb der Maske zum Login.
3. Eingabe valider Daten. Notwendige Daten: Benutzername, E-Mail-Adresse, Passwort.
4. Klick auf den Button "Weiter zur Fachauswahl"
5. Auswahl von bereits absolvierten Lehrveranstaltungen.
6. Klick auf den Button "Speichern & Fertig".

**Erwartetes Ergebnis:** Benutzer*in wird erfolgreich registriert und wird automatisch auf die "Help"-Seite weitergeleitet. Die Auswahl der Lehrveranstaltungen wurde in den Profildaten gespeichert.

---

## Testfall 3: Ausloggen
**Beschreibung:** Sicherstellung, dass User*innen sich ausloggen können und ohne erneutes Login nicht auf StudyVerse zugreifen können.

**Voraussetzungen:** Benutzer*in ist bereits eingeloggt.

**Testschritte:** 
1. Klick auf den Button "Logout" rechts im Header.
2. Bestätigung des Logouts durch Klick auf den Button "Ausloggen".

**Erwartetes Ergebnis:** Benutzer*in wird ausgeloggt und kann ohne ein erneutes einloggen nicht auf den Account zugreifen. Eine 

---

## Testfall 4: Profil bearbeiten (Benutzername, E-Mail-Adresse)
**Beschreibung:** Sicherstellung, dass User*innen den gespeicherten Benutzernamen und E-Mail-Adresse ändern können.

**Voraussetzungen:** Benutzer*in ist bereits eingeloggt.

**Testschritte:**
1. Klick auf Profil bearbeiten, zu finden in der Sidebar.
2. Bearbeitung der gespeicherten Daten.
3. Klick auf den Button "Änderungen speichern"

**Erwartetes Ergebnis:** Die Änderungen wurden gespeichert und werden, auch bei erneutem Login angezeigt. Bei erfolgreicher Speicherung erscheint ein entsprechender Hinweis.

---

## Testfall 5: Profil bearbeiten (Absolvierte Lehrveranstaltungen)
**Beschreibung:** Sicherstellung, dass User*innen die absolvierten Lehrveranstaltungen bearbeiten können und diese bei der Planung durch UNI berücksichtigt werden.

**Voraussetzungen:** Benutzer*in ist bereits eingeloggt.

**Testschritte:**
1. Klick auf Profil bearbeiten, zu finden in der Sidebar.
2. Klick auf "Absolvierte LVAs bearbeiten".
3. Auswahl aller neu absolvierten Lehrveranstaltungen. 
4. Klick auf den Button "Änderungen speichern".

**Erwartetes Ergebnis:** Die Änderungen wurden gespeichert und werden, auch bei erneutem Login angezeigt 
und bei der nächsten Planung berücksichtigt. Bei erfolgreicher Speicherung erscheint ein entsprechender Hinweis,
danach erfolgt eine Weiterleitung zum Profil.

---

## Testfall 6: Erstellung eines neuen Planes.
**Beschreibung:** Sicherstellung, dass:
 - bereits absolvierte Lehrveranstaltungen nicht mehr eingeplant werden
 - nur Lehrveranstaltungen an den ausgewählten Tagen vorgeschlagen werden
 - nicht mehr ECTS als angegeben eingeplant werden
 - die angegebene ECTS-Anzahl um maximal 3 ECTS unterschritten wird

**Voraussetzungen:** Benutzer*in ist eingeloggt und hat bereits absolvierte Lehrveranstaltungen ausgewählt.

**Testschritte:**
1. Klick auf "neue Planung", zu finden in der Sidebar links
2. Eingabe aller erforderlichen Daten (Semester, max. ECTS, mögliche Tage, explizite LVA-Wünsche)
3. Klick auf den Button "Planung starten"

**Erwartetes Ergebnis:** UNI erstellt einen Plan mit der maximalen Anzahl an ECTS (mit einer Toleranz von -3 ECTS,
falls nicht anders möglich), mit Lehrveranstaltungen, die nur an den Wunschtagen stattfinden und plant keine
Lehrveranstaltungen ein, die als bereits absolviert gekennzeichnet wurden. 

---

## Testfall 8: Bereits erstellte Planung öffnen
**Beschreibung:** Sicherstellen, dass eine bereits erstellte Planung aufgerufen werden kann und der Chat mit UNI gespeichert wurde.

**Voraussetzungen:** Benutzer*in muss bereits mindestens einen Plan erstellt und Fragen dazu an UNI gestellt haben.

**Testschritte:**
1. Klick auf eine bereits erstellte Planung (zu finden in der Sidebar unter dem Reiter "Letzte Planungen").
2. Klick auf den Button "Chat öffnen".

**Erwartetes Ergebnis:** Eine bereits erfolgte Planung mit allen ursprünglichen Informationen
(Semester, max. ECTS, Wunschtage) und erstellte Planung (LVA-Nummer, LVA-Titel, LVA-Termin, ECTS und LVA-Leiter) werden
angezeigt. Ebenso wird die Chat-Historie korrekt dargestellt.

---

## Testfall 7: Chat öffnen
**Beschreibung:** Sicherstellung, dass man Fragen zu dem erstellten Plan stellen kann. Beispielsweise über die groben
Lerninhalte oder ob Prüfungen absolviert werden müssen.

**Voraussetzungen:** Benutzer*in muss einen Plan mit mindestens 1,5 ECTS erstellt haben.

**Testschritte:** 
1. Entweder direkt nach dem Erstellen einer Planung auf den Button "Chat öffnen" klicken ODER
2. Klick auf eine bereits erstellte Planung (zu finden in der Sidebar unter dem Reiter "Letzte Planungen").
3. Klick auf den Button "Chat öffnen".
4. Eingabe der Frage in der Chatmaske.
5. Klick auf den Button "Senden". (es können mehrere Fragen gestellt werden).

**Erwartetes Ergebnis:** UNI gibt eine sinnvolle und korrekte Antwort auf die gestellte Frage. Diese wird leserlich angezeigt.

---

## Testfall 8: Planung löschen
**Beschreibung:** Sicherstellung, dass ein erstellter Plan wieder gelöscht werden kann und dem/der Benutzer*in nicht mehr angezeigt wird.

**Voraussetzungen:** Benutzer*in hat bereits einen Plan erstellt.

**Testschritte:**
1. Klick auf das "Mülleimer-Symbol" neben der gewünschten Planung. (zu finden in der Sidebar unter dem Reiter "Letzte Planungen").
2. Bestätigung durch Klick auf den Button "Löschen" im Dialogfeld.

**Erwartetes Ergebnis:** Anzeige einer Mitteilung, dass die Löschung erfolgreich war. Die gelöschte Planung wird nicht mehr angezeigt.

---

## Testfall 9: Sidebar einklappen
**Beschreibung:** Sicherstellung, dass die Sidebar eingeklappt werden kann und auch beim Aktualisieren oder bei einem
erneuten Logout dieser Zustand gespeichert wird.

**Voraussetzung:** Benutzer*in ist eingeloggt.

**Testschritte:**
1. Klick auf das **"<<"**-Symbol in der Sidebar.
2. Aktualisieren der Seite.

**Erwartetes Ergebnis:** Die Sidebar ist eingeklappt und behält den eingeklappten Zustand bei,
auch nach der Aktualisierung von StudyVerse

---

## Testfall 10: Erscheinungsbild ändern
**Beschreibung:** Sicherstellung, dass das Erscheinungsbild von hell auf dunkel und umgekehrt geändert werden kann und
dieser Zustand für den nächsten Login gespeichert wird.

**Testschritte:**
1. Klick auf das "Mond"-Symbol. (zu finden in der Sidebar)
2. Klick auf Button "Logout" (zu finden im Header) + Bestätigung des Logouts
3. Erneuter Login.

**Erwartetes Ergebnis:** Das Erscheinungsbild ändert sich (dunkler Hintergrund, lila als Hauptfarbe), bei erneutem Login
bleibt das Erscheinungsbild dunkel.

---



