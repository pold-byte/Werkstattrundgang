# Foliensatz als Werkstattobjekte: Designsprache und Konstruktion

Stand 2026-09-04, zweite Fassung. Ergebnis des Brainstormings zur
Prüfungspräsentation (8 bis 10 Minuten, zwei technisch versierte Prüfer,
DHBW Mannheim). Ersetzt `docs/foliensatz/DESIGN.md` in allen Punkten, in denen
sich beide widersprechen.

Inhaltsquelle ist `T2000_Vortrag_7Folien_Dunkel.pptx` im Repo-Wurzelverzeichnis
(elf Folien, Stand 2026-09-04). Alle Texte, Zahlen und Quellenangaben kommen
von dort. Wo diese Datei dem älteren `BRIEFING_praesentation.md` widerspricht,
gilt die Datei. Die vier Widersprüche sind in Abschnitt 2 benannt.

## 1. Leitidee

Jede Folie ist ein Anzeigeobjekt aus der Werkstatt, gezeichnet als frontale
Umrisszeichnung in einer schwarzen Tinte, wie in einem Handbuch. Auf der
Anzeigefläche des Objekts steht der Plan des Systems. Der Plan wird nicht auf
einmal gezeigt, sondern wächst von Station zu Station: Station 1 zeigt den
heutigen Handweg vom SAP-Export bis zum Planungsdialog als gestrichelte Kette,
Station 5 zeigt den vollständigen Plan mit dem Messaufbau der Bewertung.

Objekt = wo wir stehen. Plan = was das System an dieser Stelle ist. Dieselbe
Kennzahl läuft als Nutzlast auf den Kanten mit: Excel-Zelle, Datenbankzeile,
SQL, Ergebnistabelle, Diagramm.

Zielformat: PowerPoint 16:9 (13,333 x 7,5 Zoll) über pptxgenjs. Statisch,
hell, druckfähig, graustufentauglich. Keine Animation, keine Verläufe, kein
Dark Mode. Schriften ausschließlich Arial und Consolas.

## 2. Rahmenbedingungen und Korrekturen gegenüber dem Briefing

Unverändert gültig: Sprache Deutsch, sachlich. Kopfzeile "DB Intern / DB
internal" auf jeder Folie. Je Station eine Kernaussage, maximal drei
Belegpunkte, ein Anschauungsobjekt. Keine Zahl ohne Quelle. Begriffe Importpfad
und Auswertungspfad. Diagrammtypwahl regelbasiert. Kein Streamlit.

Aus der Inhaltsquelle folgen vier Korrekturen, die den Plan verändern:

1. **Drei Modellaufrufe, nicht zwei.** SQL-Erzeugung (Aufruf 1),
   Einordnungstext (Aufruf 2), Mapping-Spezifikation (Aufruf 3). Alle über
   `frage_llm()`. Jeder Modellaufruf hat einen deterministischen Nachfolger.
2. **Zwei Datenbankdateien, kein Zusammenfluss.** Der Importpfad schreibt in
   `ih_arbeit.db` (Arbeitsstand). Der Auswertungspfad liest ausschließlich
   `ih.db` (Referenzstand). Der Import kann den Referenzstand nicht erreichen.
3. **Ist-Zustand:** SAP-Export, manuelle Weiterverarbeitung in Excel durch eine
   Person, rund drei Stunden je Zyklus, Plausibilisierung von Hand, rund zwei
   unbeantwortbare Rückfragen je Planungsdialog. Der Prototyp setzt hinter dem
   Systemexport an.
4. **Importpfad hat drei Glieder** hinter der Quelle: Mapping-Spezifikation
   (Modell), Wächter (festes Vokabular), Anwendung (deterministisch).

## 3. Designsprache

### 3.1 Farbe

Eine Tinte. Kein Akzent.

| Rolle        | Hex       | Verwendung                                             |
|--------------|-----------|--------------------------------------------------------|
| Papier       | `#FFFFFF` | Folienhintergrund und Anzeigeflächen.                  |
| Tinte        | `#111111` | Objektumrisse, Plan, Text.                             |
| Tinte 60 %   | `#5C5C5C` | Kopfzeile, Kantenbeschriftung, Sekundäres.             |
| Tinte 25 %   | `#C8C8C8` | Gestrichelte Handkette, Quellenzeile.                  |
| Feld         | `#F0F0F0` | Hintergrund der Consolas-Nutzlast auf Kanten, Datenbankknoten. |

Unterscheidung ausschließlich über Form und Linienstärke.

### 3.2 Typografie (pt)

| Stufe               | Schrift        | Größe | Verwendung                                  |
|---------------------|----------------|-------|---------------------------------------------|
| Folientitel         | Arial Bold     | 28    | Stationstitel, ein je Folie.                |
| Kernaussage         | Arial          | 16    | Ein Satz, maximal zwei Zeilen.              |
| Belegpunkt          | Arial          | 13    | Nur auf Hochformat-Folien (5, 6), max. drei. |
| Knotentitel         | Arial Bold     | 11    | Im Plan.                                    |
| Knotenzeile         | Arial          | 8,5   | Zweite Zeile im Knoten ("drei Quellformate"). |
| Kantenlabel (Mensch)| Arial          | 9     | "natürliche Sprache".                       |
| Kopfzeile           | Arial          | 9     | Versalien, Zeichenabstand 0,08 em.          |
| Quellenzeile        | Arial          | 8     | Unter dem Objekt, Tinte 60 %.               |
| Nutzlast            | Consolas       | 8,5   | Auf Kanten, in Feld-Hintergrund.            |
| Knoten-Artefakt     | Consolas       | 8,5   | `ih.db`, `frage_llm()`, `nur lesend`.       |

Regeln: nur Regular und Bold. Consolas ausschließlich für Dinge, die im System
wörtlich vorkommen. Kein Gedankenstrich in sichtbarem Text. Versalien nur in
der Kopfzeile. Zahlen aus der Quelle wörtlich, Rundung wie dort.

### 3.3 Linien

| Stärke  | Verwendung                                                       |
|---------|------------------------------------------------------------------|
| 1,5 pt  | Objektumrisse, Knotenrahmen, Doppelrahmen außen.                 |
| 1,0 pt  | Plankanten mit Pfeilspitze, Doppelrahmen innen, Objektdetails.   |
| 0,75 pt | Stiftablage, Magnete, Tasten, sonstige Kleinteile.               |

Strichart: durchgezogen für Bestehendes, gestrichelt (6 pt Strich, 5 pt Lücke)
für Manuelles. Pfeilspitze geschlossen, 8 pt lang. Eckenradius 0, einzige
Ausnahme Tablet-Gehäuse 0,25 Zoll. Keine Füllungen außer Feld. Keine Schatten.

### 3.4 Folienraster (Zoll)

Kopfzeile y 0,30, x 0,60 bis 12,73: links "DB INTERN / DB INTERNAL", rechts
"STATION n VON 6". Keine Fußzeile, keine Seitenzahl. Quellenzeile direkt unter
dem Objekt.

Querformat-Folien (Stationen 1 bis 4):

| Zone        | x     | y     | w      | h     |
|-------------|-------|-------|--------|-------|
| Titel       | 0,60  | 0,80  | 12,13  | 0,50  |
| Kernaussage | 0,60  | 1,40  | 11,00  | 0,65  |
| Objekt      | 0,60  | 2,15  | 12,13  | 4,85  |
| Quellenzeile| 0,60  | 7,05  | 12,13  | 0,20  |

Hochformat-Folien (Stationen 5 und 6):

| Zone        | x     | y     | w      | h     |
|-------------|-------|-------|--------|-------|
| Titel       | 0,60  | 0,80  | 6,00   | 0,50  |
| Kernaussage | 0,60  | 1,40  | 6,00   | 1,00  |
| Belegpunkte | 0,60  | 2,80  | 6,00   | 3,80  |
| Objekt      | 7,00  | 0,55  | 5,73   | 6,50  |
| Quellenzeile| 7,00  | 7,10  | 5,73   | 0,20  |

Belegpunkte auf Querformat-Folien stehen in den Sprechernotizen.

## 4. Die Objekte

Alle frontal, ohne Perspektive, Umriss 1,5 pt. Maße in Zoll relativ zur
Objektzone. Die Anzeigefläche nimmt den Plan zentriert auf.

| Station | Objekt                       | Format | Kennzeichen |
|---------|------------------------------|--------|-------------|
| 1 | Tablet am Scanner-Arbeitsplatz     | quer | Gehäuse 12,13 x 4,85, Radius 0,25; Rand 0,35; Kameraloch oben mittig (r 0,05); zwei Tastenstriche rechts außen. Fläche 11,43 x 4,15. |
| 2 | Magnettafel mit Datenkatalog       | quer | Rahmen 12,13 x 4,60 als Doppellinie (Abstand 0,08); Stiftablage unten mittig 3,00 x 0,12; vier Magnete (r 0,12) an den Ecken der Planfläche. Fläche 11,60 x 4,00. |
| 3 | Terminal-Monitor                   | quer | Bildschirm 12,13 x 4,25, Rand 0,15; Kinn 0,30 mit Betriebspunkt (r 0,04); Standhals 0,80 x 0,25; Fuß als Linie 3,00. Fläche 11,83 x 3,95. |
| 4 | Fernseher an der Hallenwand        | quer | Bildschirm 12,13 x 4,60, Rand 0,08; kein Stand; Wandhalter 1,00 x 0,35 hinter der Unterkante, 0,25 sichtbar. Fläche 11,97 x 4,44. |
| 5 | Klemmbrett                         | hoch | Brett 5,40 x 6,40; Klemme oben mittig 1,60 x 0,35 mit Halbkreis (r 0,30); Blatt eingerückt 0,25. Fläche 4,90 x 5,70. |
| 6 | Flipchart im Besprechungsraum      | hoch | Kopfschiene 5,50 x 0,25 mit zwei Klemmen (0,30 x 0,15); Bogen 5,30 x 5,70; drei Ständerbeine als Linien ab Unterkante, am Folienrand angeschnitten. Fläche 4,90 x 5,40. |

Kein Objekt trägt Beschriftung, Logo oder Marke. Die Silhouette erklärt sich
selbst.

## 5. Der Plan

Eine Knoten-Kanten-Liste, zwei Layouts. Koordinaten in Zoll relativ zur
linken oberen Ecke der Planfläche, Plan auf der Fläche zentriert, nie skaliert.

### 5.1 Knoten

| Code | Titel                 | Zweite Zeile                       | Art        | Stufe |
|------|-----------------------|------------------------------------|------------|-------|
| N1   | Excel-Quellen         | drei Quellformate                  | Schritt    | 1 |
| N2   | Mapping-Spezifikation | `frage_llm()`  Aufruf 3            | Modell     | 2 |
| N2b  | Wächter               | festes Vokabular                   | Schritt    | 2 |
| N2c  | Anwendung             | deterministisch                    | Schritt    | 2 |
| N3b  | `ih_arbeit.db`        | Arbeitsstand                       | Datenbank  | 2 |
| N4   | Frage                 | natürliche Sprache                 | Schritt    | 3 |
| N5   | SQL-Erzeugung         | `frage_llm()`  Aufruf 1            | Modell     | 3 |
| N6   | Guardrails L1 und L2  | `nur lesend`                       | Schritt    | 3 |
| N3   | `ih.db`               | Referenzstand                      | Datenbank  | 3 |
| N7   | Diagrammwahl          | regelbasiert                       | Schritt    | 4 |
| N7b  | Einordnungstext       | `frage_llm()`  Aufruf 2            | Modell     | 4 |
| N8   | Planungsdialog        | Diagramm und Text                  | Schritt    | 1 |
| N9   | Referenzabfrage       | manuell geprüft                    | Schritt    | 5 |
| N10  | Ergebnisvergleich     | Execution Accuracy                 | Schritt    | 5 |

Darstellung: Schritt = Rahmen 1,5 pt. Modell = Doppelrahmen (1,5 pt außen,
1,0 pt innen, Abstand 0,05). Datenbank = Rahmen 1,5 pt mit Feld-Füllung
`#F0F0F0`. Das ist dieselbe Dreiteilung wie in der Legende der Quelle
(Folie 4), nur in einer Tinte.

Handkette (nur Stufe 1, gestrichelt, Tinte 25 %): H1 SAP-System, H2 manueller
Export, N1 Excel-Quellen, H3 Plausibilisierung von Hand, N8 Planungsdialog.
Ab Stufe 2 bleibt von ihr ein gestrichelter Stummel links in N1 mit dem Label
"aus SAP-Export" (der Prototyp setzt hinter dem Systemexport an) und die
gestrichelte Kante N1 nach N8 mit dem Label "heute von Hand, rund drei Stunden
je Zyklus". Auf Stufe 4 verschwindet die Kante N1 nach N8, der Stummel bleibt.

### 5.2 Kanten

| Von  | Nach | Nutzlast                              | Art   | Stufe |
|------|------|---------------------------------------|-------|-------|
| N1   | N2   | `Stichprobenzeilen`                   | mono  | 2 |
| N2   | N2b  | `Zuordnungsvorschrift`                | mono  | 2 |
| N2b  | N2c  | `geprüft`                             | mono  | 2 |
| N2c  | N3b  | `INSERT`                              | mono  | 2 |
| N4   | N5   | Frage und Schemabeschreibung          | arial | 3 |
| N5   | N6   | `SELECT ...`                          | mono  | 3 |
| N6   | N3   | `nur lesend`                          | mono  | 3 |
| N3   | N7   | `Ergebnistabelle`                     | mono  | 4 |
| N7   | N7b  | Diagrammtyp                           | arial | 4 |
| N7b  | N8   | Diagramm und Text                     | arial | 4 |
| N9   | N3   | `Referenz-SQL`                        | mono  | 5 |
| N3   | N10  | `zwei Ergebnistabellen`               | mono  | 5 |

Keine Kante zwischen Importpfad und Auswertungspfad. Das Fehlen ist die
Aussage (Korrektur 2).

### 5.3 Layout quer (Planfläche 11,20 x 3,25)

Sechs Spalten, Spaltenabstand 1,95, Knotenbreite 1,45, Knotenhöhe 0,85.
Spalten x: c0 0,00, c1 1,95, c2 3,90, c3 5,85, c4 7,80, c5 9,75.
Zeilen y: oben 0,00 (Importpfad), Mitte 1,20 (Datenbanken, Messaufbau),
unten 2,40 (Auswertungspfad).

| Zeile | c0  | c1  | c2  | c3  | c4  | c5  |
|-------|-----|-----|-----|-----|-----|-----|
| oben  | N1  | N2  | N2b | N2c | N3b |     |
| Mitte |     | N9  | N3  |     | N10 |     |
| unten | N4  | N5  | N6  | N7  | N7b | N8  |

Kantenführung: Zeilen waagerecht von links nach rechts. N6 nach N3 senkrecht
nach oben (x 4,625). Aus N3 rechts (y 1,625) ein Stamm nach rechts: Abzweig
bei x 6,575 nach unten in N7 (Stufe 4), Weiterlauf bis N10 (Stufe 5). N9 nach
N3 waagerecht. Spalte c3 Mitte bleibt frei, damit der Abzweig Platz hat.
Handkette Stufe 1: H1 bei c0 Mitte, H2 bei c1 Mitte, N1 bei c2 Mitte, H3 bei c3
Mitte, N8 bei c5 Mitte, gestrichelt verbunden. Ab Stufe 2 rückt N1 an seinen
Platz oben links und N8 nach unten rechts.

Nutzlast oberhalb waagerechter Segmente, rechts neben senkrechten, 0,05 Abstand.

### 5.4 Layout hoch (Planfläche 4,90 x 5,60)

Zwei Spalten, Knotenbreite 2,10, Knotenhöhe 0,50, Zeilenabstand 0,80.
Spalte links x 0,00 (Importpfad, Messaufbau), rechts x 2,80 (Auswertungspfad).
Zeilen y 0,00 / 0,80 / 1,60 / 2,40 / 3,20 / 4,00 / 4,80.

| Zeile | links | rechts |
|-------|-------|--------|
| 0     | N1    | N4     |
| 1     | N2    | N5     |
| 2     | N2b   | N6     |
| 3     | N2c   | N3     |
| 4     | N3b   | N7     |
| 5     | N9    | N7b    |
| 6     | N10   | N8     |

Beide Spalten als senkrechte Ketten. N9 nach N3: rechts aus N9 (y 4,15) in die
Rinne x 2,35, hoch bis y 2,55, nach rechts in N3. N3 nach N10: links aus N3
(y 2,75) in die Rinne x 2,55, hinunter bis y 4,95, nach links in N10. Die
beiden Rinnenläufe liegen 0,20 auseinander und kreuzen sich nicht. Handkette
kommt im Hochformat nicht vor (beide Hochformat-Folien zeigen Stufe 5).

### 5.5 Stationen, Ausbaustufen und Inhalte aus der Quelle

| St. | Titel (Rundgang)            | Objekt      | Stufe | Kernaussage (Quelle)                                                                                     | Quelle |
|-----|-----------------------------|-------------|-------|-----------------------------------------------------------------------------------------------------------|--------|
| 1 | Wo die Zahl entsteht          | Tablet      | 1 | Die Kennzahlen werden aus SAP exportiert und in dezentralen Excel-Dateien weiterverarbeitet. Der Aufwand ist überschaubar. Das Problem ist seine Bindung. | Folie 2 |
| 2 | Aus Chaos wird Struktur       | Magnettafel | 2 | Das Modell erzeugt aus einer Excel-Quelle eine Zuordnungsvorschrift. Geprüft und angewendet wird sie regelbasiert. Drei Quellen wurden vollständig überführt, je Quelle eine manuelle Korrektur. | Folien 4, 11 |
| 3 | Fragen statt Formeln          | Monitor     | 3 | Das Modell erzeugt die Vorschrift, nicht das Ergebnis. Schreibende Anweisungen sind technisch ausgeschlossen, nicht per Prompt untersagt. | Folie 5 |
| 4 | Ergebnis lesen                | Fernseher   | 4 | Alle Zahlenwerte entstehen in der Datenbank. Der Diagrammtyp folgt Regeln, der Einordnungstext ist der zweite Modellaufruf. | Folien 4, 5 |
| 5 | Stimmt das auch?              | Klemmbrett  | 5 | Mit welcher Zuverlässigkeit lassen sich Auswertungsfragen in korrekte Datenbankabfragen übersetzen, und welche Fehlerquellen bestimmen das Ergebnis? | Folien 3, 6, 7 |
| 6 | Was es bringt, was nicht      | Flipchart   | 5 | Entscheidend ist nicht der Preis je Frage, sondern ob eine Antwort ungeprüft übernommen werden darf.       | Folien 8, 9 |

Belegpunkte (Station 5, auf der Folie): 36 Einträge, drei Durchgänge je
Frage, fünf Läufe, 540 Messsätze. Die vier vergleichbaren Läufe ergeben ein
Band von 82,8 bis 86,2 Prozent. 27 der 29 Fragen sind über alle zwölf
Durchgänge geschlossen richtig oder geschlossen falsch. Auf dem Klemmbrett
zusätzlich zum Plan: der Messrahmen (gestricheltes Rechteck 1,0 pt um N5, N6,
N3, N9, N10, Abstand 0,15, Beschriftung "Messaufbau, 540 Messsätze").

Belegpunkte (Station 6, auf der Folie): Kosten je Frage 2,35 Cent, je Messlauf
rund 2,45 $, Messreihe 12,27 $. Kostentreiber ist die Architektur (96,3 Prozent
der Token in der Eingabe). A-3 nur der Form nach erfüllt, A-7 nicht erprobt.

Sprechernotizen der Querformat-Folien übernehmen die Belegpunkte der
jeweiligen Quellfolie wörtlich. Die Ergänzungsfolien 8 bis 11 der Quelle
bleiben als Fragerunden-Reserve in der Quelldatei; sie werden nicht in
Werkstattobjekte übersetzt.

Titelfolie: Objekt "Hallentor" entfällt. Stattdessen Folie 1 der Quelle in
Textform: Titel, Untertitel, Name, Kurs, Betreuung, hell und in einer Tinte,
ohne Bild. Die Einordnung "Zielsetzung" (Folie 3) verteilt sich: Leitfrage
auf Station 5, Anforderungskatalog A-1 bis A-7 auf Station 6.

## 6. Technische Umsetzung

### 6.1 Ein Quellmodell, zwei Ausgaben

`docs/foliensatz/plan.json` hält Knoten, Kanten, beide Layouts, Objekte,
Stationen und Texte genau so, wie in Abschnitt 4 und 5 tabelliert. Daraus:

1. `docs/foliensatz/referenz.html`: alle sieben Folien (Titel plus sechs
   Stationen) 1:1 in Zoll. Generator `tools/foliensatz/baue-referenz.mjs`.
2. `app/foliensatz/foliensatz.pptx`: Generator `tools/foliensatz/baue-pptx.mjs`
   mit pptxgenjs, `LAYOUT_WIDE`. Objekte aus `addShape` (rect, roundRect,
   ellipse, line), Plan aus `addShape` und `addText`, Kanten als `line` mit
   Pfeilspitze. Zoll 1:1. Sprechernotizen über `addNotes`.

Beide Generatoren nutzen dasselbe Layout-Modul `tools/foliensatz/layout.mjs`,
das aus Stufe, Layout und Objekt die absoluten Koordinaten aller Elemente
berechnet. HTML und PPTX unterscheiden sich nur im Zeichenbefehl.

### 6.2 Verifikation

- Vitest auf `layout.mjs`: kein Element verlässt die Anzeigefläche, keine zwei
  Knoten überlappen, Stufe n ist Obermenge von Stufe n-1 (bis auf Handkette),
  keine Kante verbindet Importpfad und Auswertungspfad, die Handkette N1 nach
  N8 fehlt ab Stufe 4.
- Textprüfung: kein Gedankenstrich in sichtbarem Text; jede Zahl auf einer
  Folie kommt in `T2000_Vortrag_7Folien_Dunkel.pptx` wörtlich vor (Test liest
  die Quelle per zipfile und vergleicht).
- PPTX-Validierung mit dem Prüfskript des pptx-Skills; Sichtprüfung über den
  PowerPoint-Export nach PNG (COM), da kein LibreOffice vorhanden ist.

### 6.3 Außerhalb des Umfangs

- Änderungen an der 3D-App und ihrem Panel.
- Übersetzung der Ergänzungsfolien 8 bis 11.
- Demo-Video, Handout, Druckversion mit Beschnitt.

## 7. Abnahme des Entwurfs

- Jede Folie: ein Titel, eine Kernaussage, ein Objekt, der Plan in der
  richtigen Stufe, eine Quellenzeile. Nichts sonst.
- Objekt ohne Beschriftung erkennbar.
- Plan auf keiner Folie skaliert, auf jeder zentriert.
- Nur Arial und Consolas, nur die fünf Grauwerte aus 3.1.
- Kein Element außerhalb der Zonen aus 3.4.
- Kein Zusammenfluss der beiden Pfade, drei Modellstellen sichtbar.
- Graustufendruck verliert keine Unterscheidung.
