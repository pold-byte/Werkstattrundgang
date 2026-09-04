# Foliensatz als Werkstattobjekte: Designsprache und Konstruktion

Stand 2026-09-04. Ergebnis des Brainstormings zur Prüfungspräsentation
(8 bis 10 Minuten, zwei technisch versierte Prüfer, DHBW Mannheim). Ersetzt
`docs/foliensatz/DESIGN.md` (Stahlblau-Akzent, Übersetzungspaar) in allen
Punkten, in denen sich beide widersprechen.

## 1. Leitidee

Jede Folie ist ein Anzeigeobjekt aus der Werkstatt, gezeichnet als frontale
Umrisszeichnung in einer schwarzen Tinte, wie in einem Handbuch. Auf der
Anzeigefläche des Objekts steht der Plan des Systems. Der Plan wird nicht auf
einmal gezeigt, sondern wächst von Station zu Station: Station 1 zeigt nur
Excel-Quellen und Planungsrunde mit einer gestrichelten Handkante dazwischen,
Station 5 zeigt den vollständigen Plan mit dem Messaufbau der Evaluation.

Objekt = wo wir stehen. Plan = was das System an dieser Stelle ist. Dieselbe
Kennzahl läuft als Nutzlast auf den Kanten mit: Excel-Zelle, Datenbankzeile,
SQL, Ergebnismenge, Diagramm.

Zielformat: PowerPoint 16:9 (13,333 x 7,5 Zoll) über pptxgenjs. Statisch,
hell, druckfähig, graustufentauglich. Keine Animation, keine Verläufe, kein
Dark Mode. Schriften ausschließlich Arial und Consolas.

## 2. Rahmenbedingungen aus dem Briefing (unverändert gültig)

- Sprache Deutsch, sachlich, kein Marketing.
- Kopfzeile "DB Intern / DB internal" auf jeder Folie.
- Je Station eine Kernaussage, maximal drei Belegpunkte, ein Anschauungsobjekt.
- Keine Zahlen, Prozentwerte oder Beispielfragen erfinden. Bis die Quelldateien
  (`TextV14.docx`, `Fragenkatalog_v4.docx`, `BEWERTUNG_alle_laeufe.md` usw.)
  vorliegen: `[PLATZHALTER]`. Beispieltexte in der HTML-Referenz tragen den
  Marker `MUSTER` und werden vor der Abgabe ersetzt.
- Begriffe: Importpfad und Auswertungspfad (nicht Variante A/B). Diagrammtypwahl
  ist regelbasiert (R-D1 bis R-D9), kein dritter LLM-Aufruf. Kein Streamlit.
- Genau zwei LLM-Aufrufstellen: Schema-Mapping und SQL-Generierung, beide über
  `frage_llm()`.

## 3. Designsprache

### 3.1 Farbe

Eine Tinte. Kein Akzent.

| Rolle        | Hex       | Verwendung                                             |
|--------------|-----------|--------------------------------------------------------|
| Papier       | `#FFFFFF` | Folienhintergrund und Anzeigeflächen.                  |
| Tinte        | `#111111` | Objektumrisse, Plan, Text.                             |
| Tinte 60 %   | `#5C5C5C` | Kopfzeile, Kantenbeschriftung, Sekundäres.             |
| Tinte 25 %   | `#C8C8C8` | Nur für die gestrichelte Handkante und Muster-Marker.  |
| Feld         | `#F0F0F0` | Hintergrund der Consolas-Nutzlast auf Kanten.          |

Unterscheidung ausschließlich über Form und Linienstärke. Kein Rot, kein Blau.
Der Verzicht ist eine Entscheidung, keine Lücke.

### 3.2 Typografie (pt)

| Stufe               | Schrift        | Größe | Verwendung                                  |
|---------------------|----------------|-------|---------------------------------------------|
| Folientitel         | Arial Bold     | 28    | Stationstitel, ein je Folie.                |
| Kernaussage         | Arial          | 16    | Ein Satz, maximal zwei Zeilen.              |
| Belegpunkt          | Arial          | 13    | Nur auf Hochformat-Folien (5, 6), max. drei. |
| Knotentitel         | Arial Bold     | 12    | Im Plan.                                    |
| Knoten-Mensch       | Arial          | 9,5   | Fragetext im Knoten "Frage".                |
| Kantenlabel (Mensch)| Arial          | 9     | "natürliche Sprache", "Diagramm + Einordnung". |
| Kopfzeile           | Arial          | 9     | Versalien, Zeichenabstand 0,08 em.          |
| Nutzlast            | Consolas       | 8,5   | Auf Kanten, in Feld-Hintergrund.            |
| Knoten-Artefakt     | Consolas       | 9     | `ih.db`, `frage_llm()`, `nur SELECT`.       |
| Marker              | Consolas       | 6,5   | `MUSTER`, verschwindet vor Abgabe.          |

Regeln: nur Regular und Bold. Consolas ausschließlich für Dinge, die im System
wörtlich vorkommen. Kein Gedankenstrich in sichtbarem Text. Versalien nur in
der Kopfzeile.

### 3.3 Linien

| Stärke  | Verwendung                                                       |
|---------|------------------------------------------------------------------|
| 1,5 pt  | Objektumrisse, Knotenrahmen, Doppelrahmen außen.                 |
| 1,0 pt  | Plankanten mit Pfeilspitze, Doppelrahmen innen, Objektdetails.   |
| 0,75 pt | Kreideablage, Magnete, Tastenandeutungen, sonstige Kleinteile.   |

Strichart: durchgezogen für Bestehendes, gestrichelt (6 pt Strich, 5 pt Lücke)
für Manuelles oder Fehlendes. Pfeilspitze geschlossen, 8 pt lang.
Eckenradius 0, einzige Ausnahme: Tablet-Gehäuse 0,25 Zoll.
Keine Füllungen außer dem Feld-Hintergrund der Nutzlast. Keine Schatten.

### 3.4 Folienraster (Zoll)

Kopfzeile y 0,30, x 0,60 bis 12,73: links "DB INTERN / DB INTERNAL",
rechts "STATION n VON 5". Keine Fußzeile, keine Seitenzahl.

Querformat-Folien (Stationen 1 bis 4):

| Zone        | x     | y     | w      | h     |
|-------------|-------|-------|--------|-------|
| Titel       | 0,60  | 0,80  | 12,13  | 0,50  |
| Kernaussage | 0,60  | 1,40  | 11,00  | 0,65  |
| Objekt      | 0,60  | 2,15  | 12,13  | 5,10  |

Hochformat-Folien (Stationen 5 und 6):

| Zone        | x     | y     | w      | h     |
|-------------|-------|-------|--------|-------|
| Titel       | 0,60  | 0,80  | 6,00   | 0,50  |
| Kernaussage | 0,60  | 1,40  | 6,00   | 1,00  |
| Belegpunkte | 0,60  | 2,80  | 6,00   | 3,80  |
| Objekt      | 7,00  | 0,55  | 5,73   | 6,75  |

Belegpunkte auf Querformat-Folien stehen in den Sprechernotizen der Folie,
nicht auf der Fläche.

## 4. Die Objekte

Alle frontal, ohne Perspektive, Umriss 1,5 pt. Die Anzeigefläche ist der
Bereich, in den der Plan gesetzt wird. Maße in Zoll relativ zur Objektzone.

| Station | Objekt (aus der 3D-Szene)       | Format | Kennzeichen, die es unterscheidbar machen |
|---------|---------------------------------|--------|-------------------------------------------|
| 1 | Tablet am Scanner-Arbeitsplatz       | quer | Gehäuse 12,13 x 5,10 mit Radius 0,25; Rand 0,35; Kameraloch oben mittig (Kreis r 0,05); zwei Tastenstriche rechts außen. Fläche 11,43 x 4,40. |
| 2 | Magnettafel mit Datenkatalog         | quer | Rahmen 12,13 x 4,80 als Doppellinie (Abstand 0,08); Stiftablage unten mittig 3,00 x 0,12; vier Magnete (Kreis r 0,12) an den Ecken der Planfläche. Fläche 11,60 x 4,20, Plan liegt wie ein angeheftetes Blatt. |
| 3 | Terminal-Monitor                     | quer | Bildschirm 12,13 x 4,60, Rand 0,15; Kinn 0,30 mit Betriebspunkt (Kreis r 0,04); Standhals 0,80 x 0,35; Fuß als Linie 3,00. Fläche 11,83 x 4,30. |
| 4 | Fernseher an der Hallenwand          | quer | Bildschirm 12,13 x 4,90, Rand 0,08; keine Standfläche; Wandhalter als Rechteck 1,00 x 0,35 hinter der Unterkante, davon 0,30 sichtbar. Fläche 11,97 x 4,74. |
| 5 | Klemmbrett                           | hoch | Brett 5,40 x 6,60; Klemme oben mittig 1,60 x 0,35 mit Halbkreis-Griff (r 0,30) darüber; Blatt eingerückt 0,25. Fläche 4,90 x 5,90. |
| 6 | Flipchart im Besprechungsraum        | hoch | Kopfschiene 5,50 x 0,25 mit zwei Klemmen (0,30 x 0,15); Bogen 5,30 x 5,90 darunter; drei Ständerbeine als Linien ab Unterkante, am Folienrand angeschnitten. Fläche 4,90 x 5,60. |

Regel: Kein Objekt trägt Beschriftung, Logo oder Marke. Das Objekt erklärt sich
über seine Silhouette. Wenn ein Prüfer beim Blick auf die Folie nicht sofort
"Klemmbrett" denkt, ist die Zeichnung falsch, nicht der Prüfer.

## 5. Der Plan

Eine Knoten-Kanten-Liste, zwei Layouts. Koordinaten in Zoll relativ zur
linken oberen Ecke der Planfläche. Der Plan wird auf der Anzeigefläche
zentriert, nicht skaliert.

### 5.1 Knoten

| Code | Titel              | Artefakt (Consolas)              | LLM | Stufe |
|------|--------------------|----------------------------------|-----|-------|
| N1   | Excel-Quellen      | `*.xlsx  SharePoint`             |     | 1 |
| N2   | Schema-Mapping     | `frage_llm()`                    | ja  | 2 |
| N3   | Datenbank          | `ih.db  SQLite`                  |     | 2 |
| N4   | Frage              | Fragetext in Arial (Muster bis Quelle) |  | 3 |
| N5   | SQL-Generierung    | `frage_llm()`                    | ja  | 3 |
| N6   | Guardrails         | `nur SELECT` / `Whitelist` / `Timeout` |  | 3 |
| N7   | Diagrammwahl       | `R-D1 bis R-D9` / `regelbasiert` |     | 4 |
| N8   | Planungsrunde      |                                  |     | 1 |
| N9   | Referenz-SQL       | `handgeschrieben` / `4-Stufen-Protokoll` | | 5 |
| N10  | Ergebnisvergleich  | `Execution Accuracy` / `[PLATZHALTER]` | | 5 |

LLM-Knoten: Doppelrahmen (1,5 pt außen, 1,0 pt innen, Abstand 0,05).

### 5.2 Kanten

| Von  | Nach | Nutzlast                              | Art     | Stufe |
|------|------|---------------------------------------|---------|-------|
| N1   | N2   | `Q2 | 91,4` (Muster)                   | mono    | 2 |
| N2   | N3   | `INSERT INTO kennzahl_monat` (Muster)  | mono    | 2 |
| N4   | N5   | natürliche Sprache                    | arial   | 3 |
| N5   | N6   | `SELECT werk, AVG(...)` (Muster)       | mono    | 3 |
| N6   | N3   | `geprüft`                              | mono    | 3 |
| N3   | N7   | `Ergebnismenge`                        | mono    | 4 |
| N7   | N8   | Diagramm + Einordnung                 | arial   | 4 |
| N9   | N3   | `Referenz-SQL`                         | mono    | 5 |
| N3   | N10  | `zwei Ergebnismengen`                  | mono    | 5 |
| N1   | N8   | von Hand, vor jeder Planungsrunde, je Person eine Datei | arial, gestrichelt | 1 bis 3 |

Die gestrichelte Handkante bleibt auf den Stationen 1 bis 3 sichtbar und
verschwindet auf Station 4, wenn der Systempfad die Planungsrunde erreicht.
Das zeigt die Ablösung des Handwegs, ohne sie zu behaupten.

### 5.3 Layout quer (Planfläche 11,20 x 3,25)

Knotenhöhe 0,85. Zeilen: oben y 0,00 (Importpfad, Messaufbau), Mitte y 1,00
(Datenbank), unten y 2,40 (Auswertungspfad).

| Code | x     | y    | w    |
|------|-------|------|------|
| N1   | 0,00  | 0,00 | 1,55 |
| N2   | 2,75  | 0,00 | 1,80 |
| N9   | 7,40  | 0,00 | 1,65 |
| N10  | 9,60  | 0,00 | 1,60 |
| N3   | 5,55  | 1,00 | 1,55 |
| N4   | 0,00  | 2,40 | 1,55 |
| N5   | 2,75  | 2,40 | 1,60 |
| N6   | 5,15  | 2,40 | 1,20 |
| N7   | 7,40  | 2,40 | 1,65 |
| N8   | 9,60  | 2,40 | 1,60 |

Kantenführung orthogonal. N2 und N9 münden von oben in N3 (x 6,33). N6 mündet
von unten in N3. N3 verlässt rechts (y 1,43), Abzweig bei x 8,23 nach unten zu
N7 und weiter bei x 10,40 nach oben zu N10. Nutzlast oberhalb waagerechter
Segmente, rechts neben senkrechten.

### 5.4 Layout hoch (Planfläche 4,90 x 5,60)

Knotenhöhe 0,60, Knotenbreite 2,10. Spalte links x 0,00 (Importpfad,
Messaufbau), Spalte rechts x 2,80 (Auswertungspfad). Zeilen y 0,00 / 1,00 /
2,00 / 3,00 / 4,00 / 5,00.

| Zeile | links | rechts |
|-------|-------|--------|
| 0     | N1    | N4     |
| 1     | N2    | N5     |
| 2     | N9    | N6     |
| 3     | N10   | N3     |
| 4     |       | N7     |
| 5     |       | N8     |

Rechte Spalte als senkrechte Kette N4, N5, N6, N3, N7, N8. N2 und N9 laufen
über die Rinne x 2,45 nach unten und münden links in N3 (y 3,15). N3 verlässt
links (y 3,45) waagerecht nach N10. Die Handkante kommt im Hochformat nicht
vor: Beide Hochformat-Folien (Stationen 5 und 6) zeigen Stufe 5, in der sie
bereits abgelöst ist.

### 5.5 Stationen und Ausbaustufen

| Station | Titel                      | Objekt     | Stufe | Zusätzlich sichtbar |
|---------|----------------------------|------------|-------|---------------------|
| 1 | Wo die Zahl entsteht             | Tablet     | 1 | N1, N8, Handkante. Sonst Leere. |
| 2 | Aus Chaos wird Struktur          | Magnettafel| 2 | + N2, N3, Kanten N1-N2, N2-N3. Handkante bleibt. |
| 3 | Fragen statt Formeln             | Monitor    | 3 | + N4, N5, N6 und Kanten. Handkante bleibt. |
| 4 | Ergebnis lesen                   | Fernseher  | 4 | + N7, Kanten N3-N7, N7-N8. Handkante weg. |
| 5 | Stimmt das auch?                 | Klemmbrett | 5 | + N9, N10, Kanten. Gestrichelter Messrahmen um N5, N6, N3, N9, N10 mit Beschriftung "Messaufbau, 36 Fälle". |
| 6 | Was es bringt, was nicht (Reserve)| Flipchart  | 5 | Vollständiger Plan ohne Messrahmen. Drei Belegpunkte links (Aufwand, Bedeutung, Abgrenzung) als Platzhalter. |

Der Messrahmen auf Station 5 ist die einzige Ergänzung, die nicht Knoten oder
Kante ist: gestricheltes Rechteck 1,0 pt um die beteiligten Knoten mit 0,15
Abstand, Beschriftung Consolas 8,5 pt außen oben links.

## 6. Technische Umsetzung

### 6.1 Ein Quellmodell, zwei Ausgaben

`docs/foliensatz/plan.json` hält Knoten, Kanten, beide Layouts, Objekte und
Stationen genau so, wie in Abschnitt 4 und 5 tabelliert. Daraus entstehen:

1. `docs/foliensatz/referenz.html`: alle sechs Folien 1:1 in Zoll, zum Beurteilen
   und als Abgleich. Generator `tools/foliensatz/baue-referenz.mjs`.
2. `app/foliensatz/foliensatz.pptx`: Generator `tools/foliensatz/baue-pptx.mjs`
   mit pptxgenjs. Objekte aus `addShape` (rect, roundRect, ellipse, line),
   Plan aus `addShape` und `addText`, Kanten als `line` mit `endArrowType`.
   Zoll werden 1:1 übernommen. Sprechernotizen aus `plan.json`.

Beide Generatoren nutzen dasselbe Layout-Modul `tools/foliensatz/layout.mjs`,
das aus Stufe, Layout und Objekt die absoluten Koordinaten aller Elemente
berechnet. HTML und PPTX unterscheiden sich nur im Zeichenbefehl, nicht in der
Geometrie. So bleibt die HTML-Referenz beweiskräftig.

### 6.2 Verifikation

- Vitest: `layout.mjs` liefert für jede Station eine Elementliste; Tests
  prüfen, dass kein Element die Anzeigefläche verlässt, dass keine zwei Knoten
  überlappen, dass Stufe n eine Obermenge von Stufe n-1 ist (bis auf die
  Handkante), und dass die Handkante auf Station 4 fehlt.
- Textprüfung: kein Gedankenstrich, kein `MUSTER` und kein `[PLATZHALTER]` im
  Abgabestand (Test schlägt bis dahin erwartet fehl und ist entsprechend markiert).
- Sichtprüfung: Referenzseite im Browser, Graustufendruck über die
  Druckansicht, PPTX in PowerPoint auf dem Prüfungsrechner.

### 6.3 Außerhalb des Umfangs

- Inhalte aus den Quelldateien (Zahlen, Beispielfragen, Belegpunkte). Sie
  werden in einer eigenen Inhalte-Phase eingetragen, sobald die Dateien im Repo
  liegen.
- Titelfolie und Schlussfolie. Werden in der Inhalte-Phase nach denselben
  Regeln ergänzt (Titelfolie: Plan Stufe 0, also leere Fläche eines Objekts).
- Änderungen an der 3D-App. Die Slides im App-Panel bleiben, wie sie sind.
- Demo-Video, Handout.

## 7. Abnahme des Entwurfs

- Jede Folie: ein Titel, eine Kernaussage, ein Objekt, der Plan in der
  richtigen Stufe. Nichts sonst.
- Objekt ohne Beschriftung erkennbar.
- Plan auf keiner Folie skaliert, auf jeder zentriert.
- Nur Arial und Consolas, nur die fünf Grauwerte aus 3.1.
- Kein Element außerhalb der Zonen aus 3.4.
- Graustufendruck verliert keine Unterscheidung.
