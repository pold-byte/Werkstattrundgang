# Briefing: Präsentation zur Projektarbeit

Diese Datei ist der Kontext für die Erstellung einer Präsentation. Sie beschreibt die
zugrundeliegende Projektarbeit. Keine Inhalte erfinden — alle Zahlen, Beispielfragen und
Ergebnisse ausschließlich aus den Projektdateien übernehmen (siehe "Quellen im Repo").

## 1. Worum es geht

Titel der Arbeit: "Konzeption, prototypische Umsetzung und Bewertung einer KI-gestützten
Datenplattform zur Instandhaltungssteuerung in der Region Mitte der DB Regio AG"

Projektarbeit, DHBW Mannheim, Wirtschaftsingenieurwesen, dualer Student, Praxispartner
DB Regio AG (Region Mitte). Umfang 25–30 Seiten.

**Ausgangslage:** Die Instandhaltung der Schienenfahrzeuge wird kennzahlenbasiert gesteuert.
Die Kennzahlen werden heute dezentral von mehreren Personen in einzelnen Excel-Dateien auf
SharePoint gepflegt. Es gibt keine einheitliche, abfragbare Datenbasis. Folge: wiederkehrender
manueller Aufbereitungsaufwand vor Planungsrunden und uneinheitliche Ergebnisse. Die
Bewertungslogik der Kennzahlen existiert bislang nur als personengebundenes Erfahrungswissen;
ihre Prüfung ist nicht nachvollziehbar dokumentiert.

**Ziel:** Prototyp einer zentralen Datenplattform, die (a) uneinheitliche Excel-Quellen in ein
einheitliches Datenmodell überführt und (b) natürlichsprachliche Auswertungsfragen entgegennimmt,
in SQL übersetzt, ausführt und als Diagramm mit kurzer textlicher Einordnung darstellt.

## 2. Architektur — verbindliche Fakten

Vier Schichten:

1. Excel-Quellen (synthetisch erzeugt, bilden das SharePoint-Chaos nach)
2. Relationale Datenbank: SQLite (`ih.db` Referenz, `ih_arbeit.db` Arbeitsstand)
3. Text-to-SQL-Pipeline mit Guardrails (nur SELECT, Tabellen-Whitelist, Timeout)
4. FastAPI-Backend mit eigenem HTML/CSS/JS-Frontend

Zwei Pfade:

- **Auswertungspfad** (wissenschaftlicher Kern): Frage → SQL → Ausführung → Diagramm +
  Einordnungstext. Systematisch evaluiert.
- **Importpfad**: KI-gestütztes Schema-Mapping uneinheitlicher Excel-Quellen nach SQLite.
  Umgesetzt und demonstriert, aber bewusst **nicht** systematisch evaluiert.

**Genau zwei LLM-Aufrufstellen:** SQL-Generierung und Import-Schema-Mapping.
Die LLM-Aufrufe sind hinter der austauschbaren Funktion `frage_llm()` gekapselt, damit die
Anthropic-API ohne strukturelle Codeänderung gegen einen konzerninternen Endpunkt getauscht
werden kann. Das ist die technische Antwort auf die Vorgabe "muss mit Bahnmitteln umsetzbar sein".

**Häufige Fehler, die vermieden werden müssen:**

- Die Diagrammtypwahl ist **regelbasiert** (Regeln R-D1 bis R-D9), **kein** LLM-Einsatz.
  Sie ist als "geprüfter Nicht-Einsatz von KI" darzustellen, nicht als dritte KI-Stelle.
- Kein Streamlit (frühere Planung, wurde ersetzt).
- Nicht "Variante A / Variante B" — die Bezeichnungen sind **Importpfad** und **Auswertungspfad**.

## 3. Evaluation

- Eigener Fragenkatalog (v4): 23 Kernfragen, 6 Ergänzungsfragen, 5 Zurückweisungsfälle,
  2 unscharfe Fragen (36 gesamt), in drei Komplexitätsstufen.
- Ground Truth: handgeschriebenes Referenz-SQL, manuell in einem vierstufigen Protokoll geprüft.
- Metrik: Execution Accuracy (Ergebnisvergleich, nicht Textvergleich). Zeilenreihenfolge
  standardmäßig irrelevant, Spaltennamen irrelevant, Spaltenposition relevant,
  Float-Vergleich mit Toleranz, Multiset-Vergleich bei Duplikaten.
- Auswertungskonventionen AK-1 bis AK-18 legen fest, wie eine Frage fachlich korrekt zu
  beantworten ist. Damit wird die bisher personengebundene Bewertungslogik erstmals verschriftlicht.
- Mehrere Messläufe; Ergebnisse in den Protokolldateien. Auch bei fixierter Temperatur ist die
  Ausgabe nicht deterministisch — das ist offen zu benennen.
- Zentrales Risiko, das benannt werden muss: plausibel aussehende, aber falsche Antworten.

## 4. Abgrenzung

Nur strukturierte Daten. Nur synthetische Daten, keine Echtdaten. Vortrainiertes Modell, kein
Fine-Tuning. Außerhalb der Konzern-IT entwickelt, Anschlussfähigkeit nur konzeptionell
beschrieben. Kein Predictive Maintenance, keine Freitextauswertung/RAG, keine Sensorik-,
SAP- oder ECM-Prozesse — diese Themen kommen nur als Abgrenzung bzw. Ausblick vor.

## 5. Kapitelstruktur der Arbeit

1 Einleitung (1.1 Problemstellung, 1.2 Zielsetzung, 1.3 Methodisches Vorgehen)
2 Fachliche und technische Grundlagen (2.1 Instandhaltung, 2.2 Kennzahlenbasierte Steuerung,
  2.3 Relationale Datenbanken und SQL, 2.4 Große Sprachmodelle und Text-to-SQL,
  2.5 Bewertung von Text-to-SQL-Systemen)
3 Konzeption (3.1 Anforderungen, 3.2 Gesamtarchitektur, 3.3 Datenmodell, 3.4 Auswertungspfad,
  3.5 Importpfad)
4 Prototypische Umsetzung (4.1 Laufzeitumgebung und Technologiewahl, 4.2 Aufbau der Anwendung,
  4.3 Auswertungspfad, 4.4 Importpfad, 4.5 Bedienoberfläche)
5 Bewertung des Auswertungspfads (5.1 Zielsetzung und Abgrenzung, 5.2 Aufbau der Untersuchung,
  5.3 Ergebnisse, 5.4 Bewertung und Grenzen)
6 Einordnung (6.1 Wirtschaftliche Einordnung, 6.2 Betriebliche Bedeutung)
7 Fazit und Ausblick

## 6. Anlass und Aufbau der Präsentation

Die Präsentation wird als Stationenrundgang in der Werkstatt gehalten. Roter Faden:
**eine Kennzahl von der Werkstatthalle bis in die Planungsrunde.** Fünf Stationen, eine optional:

1. **Wo die Zahl entsteht** — Ist-Zustand: dezentrale Excel-Dateien, manuelle
   Zusammenführung, personengebundene Bewertungslogik. (Kap. 1.1, 3.1)
2. **Aus Chaos wird Struktur** — Importpfad: uneinheitliche Quellen, KI-Schema-Mapping,
   einheitliches Datenmodell. (Kap. 3.3, 3.5, 4.4)
3. **Fragen statt Formeln** — Auswertungspfad: Frage → SQL → Ergebnis, Guardrails,
   austauschbarer LLM-Adapter. (Kap. 3.4, 4.3)
4. **Ergebnis lesen** — regelbasierte Diagrammwahl, Einordnungstext, Auswertungskonventionen
   AK-1 bis AK-18. (Kap. 4.2, 4.5)
5. **Stimmt das auch?** — Fragenkatalog, Referenz-SQL, Execution Accuracy, Grenzen,
   Fehlerfälle. (Kap. 5)
6. *(optional)* **Was es bringt, was nicht** — Aufwand, betriebliche Bedeutung,
   Abgrenzung und Ausblick. (Kap. 6, 7)

## 7. Auftrag

<!-- AUSFÜLLEN vor dem Start: -->
- Format: (z. B. Foliensatz / Stationskarten A4 / Handout)
- Technik: (z. B. HTML → PDF, python-pptx, Markdown)
- Dauer und Zielgruppe:
- Anzahl Folien bzw. Karten pro Station:

Anforderungen an das Ergebnis:

- Sprache Deutsch, sachlich und präzise. Keine Marketingsprache, keine Superlative.
- Jede Station: eine Kernaussage, maximal drei Belegpunkte, ein konkretes Anschauungsobjekt.
- Schriftart Arial, Darstellungen graustufentauglich (Unterscheidung über Form und Linienstärke,
  nicht über Farbe).
- Kopfzeile "DB Intern / DB internal" beibehalten.
- Keine Zahlen, Prozentwerte oder Beispielfragen erfinden — ausschließlich aus den Quelldateien
  übernehmen und die Quelle im Kommentar vermerken.

## 8. Quellen im Repo

- `TextV14.docx` — aktuelle Textfassung der Arbeit
- `Fragenkatalog_v4.docx` — Fragenkatalog inkl. AK-1 bis AK-18
- `MESSPROTOKOLL_alle_laeufe.md`, `BEWERTUNG_alle_laeufe.md` — Messdaten, maßgeblich für alle Zahlen
- `IMPORTPFAD_lauf_02.md` — Importpfad-Durchlauf
- `IMPORT_chaos_manifest.md` — Beschreibung der uneinheitlichen Quelldateien
- `schema.sql`, `seed.py`, `DATENMODELL_koernung.md` — Datenmodell und Datengenerierung
- `KOSTEN_tokenverbrauch.md` — Token- und Kostendaten
