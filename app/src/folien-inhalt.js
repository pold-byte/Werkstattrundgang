// Inhalt des Foliensatzes, übernommen aus T2000_Vortrag_7Folien_Dunkel_kompakt.pptx
// (elf Folien: sieben Hauptfolien, vier Ergänzungsfolien). Aufbau und Reihenfolge
// bleiben erhalten; die Gestaltung uebernimmt Farben, Schriftgrade und Zonen
// des Originals (siehe folien.css).
//
// Das Feld 'station' benennt den Ort im Rundgang, an den die Kamera zu dieser
// Folie faehrt ('totale' fuer die Halleneinstellung, null fuer "bleib stehen").
// Folie 1 ist die Begruessungsfolie und liegt auf der Totale: sie steht gleich
// beim Ueberblick ueber die Werkstatt. Die sechs Inhaltsfolien verteilen sich auf
// die fuenf Stationen; das Meisterbuero traegt zwei, bis zwei weitere Stationen
// gebaut sind. Der Rundgang fuehrt: erst die Fahrt, dann auf Tastendruck die Folie.
//
// Blocktypen: 'punkte' (Absätze), 'gruppe' (Überschrift + Absätze), 'tabelle'
// (Kopfzeile + Zeilen), 'fluss' (waagerechte Kette), 'schritte' (nummerierte
// Verarbeitungsschritte), 'kasten' (hervorgehobene Feststellung), 'notiz'
// (Bildunterschrift oder Quellenangabe).

export const fusszeile =
  'Leopold Heinrich  ·  KI-gestützte Datenplattform zur kennzahlenbasierten Instandhaltungssteuerung  ·  DHBW Mannheim, T3_2000';

export const folien = [
  {
    nr: 1,
    station: 'totale',
    art: 'titel',
    klein: true, // Begruessung als Karte ueber der Halle, damit der Ueberblick steht
    kopf: 'Projektarbeit T3_2000 · DHBW Mannheim',
    titel: 'KI-gestützte Datenplattform zur kennzahlenbasierten Instandhaltungssteuerung',
    unterzeile: 'Konzeption, prototypische Umsetzung und Bewertung · DB Regio AG, Region Mitte',
    name: 'Leopold Heinrich',
    meta: ['Kurs TWIW24C · Matrikelnummer 6752182', 'Betreuung: Erik-Wilhelm Scholz · 21.06. bis 24.08.2026'],
  },
  {
    nr: 2,
    station: 'meisterbuero',
    sektion: '01 Ausgangslage',
    titel: 'Warum das Thema entstanden ist',
    kern: 'SAP-Export, Weiterverarbeitung in dezentralen Excel-Dateien. Nicht der Aufwand ist das Problem, sondern seine Bindung.',
    spalten: [
      [
        {
          typ: 'fluss',
          glieder: ['SAP-System', 'Manueller Export', 'Auswertungsdateien (Excel)', 'Plausibilisierung von Hand', 'Planungsdialog'],
        },
        {
          typ: 'notiz',
          text: 'Abb. 1: Heutiger Ablauf der Kennzahlenaufbereitung (eigene Darstellung). Der Prototyp setzt hinter dem Systemexport an.',
        },
      ],
      [
        {
          typ: 'tabelle',
          kopf: ['Gebunden an', 'Beobachtung', 'Folge'],
          zeilen: [
            ['eine Person', 'Rund drei Stunden je Zyklus. Logik gewachsen, nicht hinterlegt.', 'Übergreifende Fragen: manuell und nur mit dieser Person.'],
            ['einen abgeschlossenen Durchlauf', 'Kennzahlen nur vorbereitet. Rund zwei Rückfragen je Dialog bleiben offen.', 'Beantwortbar ist, was vorgesehen war. Alles andere: nächster Zyklus.'],
            ['eine nicht überprüfbare Logik', 'Prüfung von Hand, Ergebnis nicht festgehalten.', 'Zahl von Dritten nicht nachrechenbar.'],
          ],
        },
        { typ: 'notiz', text: 'Schätzungen des betrieblichen Betreuers, Gespräch vom 17.08.2026 (Anhang A).' },
      ],
    ],
  },
  {
    nr: 3,
    station: 'meisterbuero',
    sektion: '02 Zielsetzung',
    titel: 'Was untersucht wurde',
    kern: 'Sprachmodelle übersetzen Sprache in SQL. Offen war, ob das auf einem fachlich geprägten Kennzahlenschema eine Steuerungsentscheidung trägt.',
    breit: [
      {
        typ: 'kasten',
        marke: 'Leitfrage',
        text: 'Mit welcher Zuverlässigkeit lassen sich Auswertungsfragen durch ein Sprachmodell in korrekte Datenbankabfragen übersetzen, und welche Fehlerquellen bestimmen das Ergebnis?',
      },
    ],
    spalten: [
      [
        {
          typ: 'tabelle',
          titel: 'Anforderungen aus der Ausgangslage',
          kopf: ['Block', 'Anforderungen'],
          zeilen: [
            ['Zugänglichkeit', 'A-1 gemeinsam auswertbar · A-2 ohne Abfragesprache · A-3 ohne Nachbereitung verwendbar'],
            ['Nachprüfbarkeit', 'A-4 Definitionen explizit hinterlegt · A-5 Ergebnisse überprüfbar · A-6 Datenbestand unverändert'],
            ['Betrieb', 'A-7 mit konzerneigenen Mitteln betreibbar'],
          ],
        },
        { typ: 'notiz', text: 'Abgeleitet aus der Ausgangslage, nicht aus dem Funktionsumfang.' },
      ],
      [
        {
          typ: 'tabelle',
          titel: 'Abgrenzung des Untersuchungsgegenstands',
          kopf: ['Funktionsstrang', 'Aufgabe', 'Prüfung'],
          zeilen: [
            ['Importpfad', 'uneinheitliche Excel-Quellen zu einem einheitlichen Schema', 'erprobt'],
            ['Auswertungspfad', 'Fragen in natürlicher Sprache', 'systematisch gemessen'],
          ],
        },
        { typ: 'notiz', text: 'Gemessen wird nur der Auswertungspfad. Dort geht ein Fehler unbemerkt in eine Zahl ein.' },
      ],
    ],
  },
  {
    nr: 4,
    station: 'datenraum',
    sektion: '03 Prototyp',
    titel: 'Gesamtarchitektur des Prototyps',
    kern: 'Zwei Funktionsstränge, ein Schema.',
    spalten: [
      [
        {
          typ: 'gruppe',
          titel: 'Zwei Funktionsstränge, ein Schema',
          punkte: [
            'Drei Excel-Quellen führen in den Arbeitsstand. Die Auswertung liest nur den Referenzstand.',
            'Getrennte Dateien: der Import erreicht den Referenzstand nicht.',
          ],
        },
        {
          typ: 'gruppe',
          titel: 'Drei Modellaufrufe, eine Funktion',
          punkte: [
            'SQL, Einordnungstext und Mapping laufen alle über frage_llm().',
            'Ein Endpunktwechsel betrifft nur diese Funktion (A-7).',
          ],
        },
      ],
      [
        {
          typ: 'gruppe',
          titel: 'Jeder Modellaufruf hat einen deterministischen Nachfolger',
          punkte: [
            'Guardrails nach der SQL-Erzeugung, Wächter nach dem Mapping.',
            'Das Modell liefert die Vorschrift, die Ausführung ist regelbasiert.',
          ],
        },
        { typ: 'notiz', text: 'Abb. 1: Gesamtarchitektur des Prototyps (eigene Darstellung, Abschnitt 3.2 der Arbeit).' },
      ],
    ],
  },
  {
    nr: 5,
    station: 'terminal',
    sektion: '03 Prototyp',
    titel: 'Das Modell erzeugt die Vorschrift, nicht das Ergebnis',
    kern: 'Fragen über eine Weboberfläche. Das Modell wirkt an zwei Stellen, über eine einzige Funktion.',
    breit: [
      {
        typ: 'schritte',
        glieder: [
          { nr: '1', name: 'Frage', text: 'natürliche Sprache, ohne SQL-Kenntnis' },
          { nr: '2', name: 'Kontext', text: 'Schema aus der Datenbank, dazu fachliche Konventionen' },
          { nr: '3', name: 'SQL-Erzeugung', text: 'Modell; Schema und Frage, kein Datensatz', modell: true },
          { nr: '4', name: 'Strukturprüfung', text: 'regelbasiert; verwirft schreibende Anweisungen' },
          { nr: '5', name: 'Ausführung', text: 'nur lesend, gegen den Referenzstand' },
          { nr: '6', name: 'Ausgabe', text: 'Diagrammtyp regelbasiert, Text vom Modell', modell: true },
        ],
      },
      {
        typ: 'notiz',
        text: 'Abb. 2: Verarbeitungsschritte des Auswertungspfads (eigene Darstellung). Hervorgehoben: Sprachmodell. 16 Module, rund 3.000 Zeilen, 25 Tabellen.',
      },
    ],
    spalten: [
      [
        {
          typ: 'gruppe',
          titel: 'Folgen für die Belastbarkeit',
          punkte: [
            'Wiederholbar ohne erneuten Modellaufruf.',
            'Die Abfrage geht als lesbares Zwischenprodukt mit (A-5).',
            'Zahlen entstehen in der Datenbank. Halluzination bleibt auf Deutung und Text beschränkt.',
          ],
        },
      ],
      [
        {
          typ: 'gruppe',
          titel: 'Zwei bewusste Entscheidungen',
          punkte: [
            'Diagrammtyp per Regel. Beim Modell instabil, weil an dessen eigenen Spaltennamen hängend.',
            'Schreibzugriff technisch ausgeschlossen, nicht per Prompt: eine Anweisung ist keine Zusicherung (A-6).',
          ],
        },
      ],
    ],
  },
  {
    nr: 6,
    station: 'anzeigetafel',
    sektion: '04 Bewertung',
    titel: 'Wie die Zuverlässigkeit gemessen wurde',
    kern: 'Aufbau wie in veröffentlichten Referenzdatensätzen: je Frage eine manuell geprüfte Referenzabfrage.',
    spalten: [
      [
        {
          typ: 'tabelle',
          titel: 'Aufbau der Messung',
          kopf: ['Element', 'Umfang'],
          zeilen: [
            ['Fragenkatalog', '36: 29 positiv, 5 zurückzuweisend, 2 unscharf'],
            ['Durchgänge je Frage', 'drei, gleiche Frage, nicht zwingend gleiche Abfrage'],
            ['Messläufe', 'fünf, 540 Messsätze'],
            ['Primärmetrik', 'Execution Accuracy, verglichen werden Ergebnistabellen'],
          ],
        },
      ],
      [
        {
          typ: 'gruppe',
          titel: 'Drei Entscheidungen, die das Ergebnis tragen',
          punkte: [
            'Warum nicht Exact Match: der Vergleich des SQL-Textes zählt jede zulässige Umformulierung als Fehler. Gemessen werden soll die Antwort.',
            'Warum die Referenz unabhängig ist: auch sie ist KI-gestützt entstanden. Deshalb erst die erwartete Antwort in Prosa, dann der Abfrageentwurf. Die Erwartung ist älter als beide Abfragen.',
            'Warum wiederholt gemessen wird: Temperatur null sichert keinen Determinismus zu. Der Antwortspeicher war beim Messen abgeschaltet.',
          ],
        },
      ],
    ],
    schluss: {
      typ: 'kasten',
      text: 'Erst die Wiederholung zeigt, ob eine Frage stabil richtig, stabil falsch oder instabil ist. Ein einzelner Messwert sagt darüber nichts. Das ist der wesentliche Befund.',
    },
  },
  {
    nr: 7,
    station: 'pruefstand',
    sektion: '05 Ergebnis',
    titel: 'Streuung und Zurechnung der Fehler',
    kern: 'Vier vergleichbare Läufe: 82,8 bis 86,2 Prozent. Die Spannweite von 3,4 Prozentpunkten entspricht genau einer Frage, ohne jede Änderung am System.',
    spalten: [
      [
        {
          typ: 'punkte',
          punkte: [
            '27 von 29 Fragen sind über zwölf Durchgänge geschlossen richtig oder geschlossen falsch.',
            'In keinem Fall ist die erzeugte Abfrage strukturell fehlerhaft.',
            'Kein dauerhafter Fehlschlag ging auf die Fähigkeit des Modells zurück. Der begrenzende Faktor ist die Schärfe der eigenen Kennzahlendefinition.',
          ],
        },
        { typ: 'notiz', text: 'Abb. 3: Anteil korrekter Durchgänge je Messlauf. Grau: Lauf 01, frühere Katalogfassung.' },
      ],
      [
        {
          typ: 'tabelle',
          titel: 'Die vier dauerhaft falschen Fragen',
          kopf: ['Zurechnung', 'Befund'],
          zeilen: [
            ['eigene Spezifikation', 'Quote liefert null, die Ganzzahldivision schneidet ab. Formel wörtlich umgesetzt.'],
            ['eigene Spezifikation', 'Beide Bedingungsgrößen ausgegeben. Auswahl richtig, Formatregel verletzt.'],
            ['Schemabeschreibung', 'Begriff in falscher Spalte gesucht, Schemabeschreibung ohne Wertebereiche.'],
            ['Vergleichsverfahren', 'Abfrage einwandfrei. Scheitert an Spaltenreihenfolge und Rundung.'],
          ],
        },
      ],
    ],
    schluss: {
      typ: 'kasten',
      marke: 'Einschränkung',
      text: 'Jede siebte Antwort ist falsch, ohne dass man es ihr ansieht. Die freie Frage liefert einen Vorschlag, keine Auskunft. Kennzahlenübersicht ausgenommen.',
    },
  },
  {
    nr: 8,
    station: null, // Ergänzungsfolie: die Kamera bleibt stehen
    sektion: 'Ergänzende Folie',
    titel: 'Bilanz gegen den Anforderungskatalog',
    breit: [
      {
        typ: 'tabelle',
        kopf: ['ID', 'Anforderung', 'Erfüllung', 'Begründung'],
        breiten: ['0.9in', '3.1in', '1.9in', 'auto'],
        zeilen: [
          ['A-1', 'gemeinsam auswertbar', 'erfüllt', 'Alle Kennzahlen liegen in einem dimensionalen Schema mit 25 Tabellen.'],
          ['A-2', 'ohne Abfragesprache zugänglich', 'erfüllt', 'Fragen in natürlicher Sprache über beide Oberflächen.'],
          ['A-3', 'ohne Nachbereitung verwendbar', 'nur der Form nach', 'Das Ergebnis liegt als Diagramm mit Einordnung vor, doch an die Stelle der Aufbereitung tritt die Prüfung der mitgelieferten Abfrage. Der Aufwand ist verlagert, nicht beseitigt.'],
          ['A-4', 'Definitionen explizit hinterlegt', 'erfüllt', 'Auswertungskonventionen schriftlich festgelegt und in den Systemprompt überführt.'],
          ['A-5', 'Ergebnisse überprüfbar', 'erfüllt', 'Jede Antwort führt die ausgeführte Abfrage mit.'],
          ['A-6', 'Datenbestand unverändert', 'erfüllt', 'Über alle 540 Messsätze unverändert, nachgewiesen über einen je Messsatz mitgeschriebenen Prüfwert.'],
          ['A-7', 'mit konzerneigenen Mitteln betreibbar', 'nicht erprobt', 'Konzeptionell umgesetzt, der Wechsel betrifft eine einzige Funktion. Ein konzerninterner Endpunkt stand nicht zur Verfügung.'],
        ],
      },
    ],
    schluss: {
      typ: 'kasten',
      marke: 'Offen vor einem produktiven Einsatz',
      text: 'Messung gegen reale statt synthetische Daten · fachliche Abnahme der Kennzahlendefinitionen · Zugang zu einem konzerninternen Modellendpunkt · Bezifferung des heutigen Ist-Aufwands',
    },
  },
  {
    nr: 9,
    station: null, // Ergänzungsfolie: die Kamera bleibt stehen
    sektion: 'Ergänzende Folie',
    titel: 'Wirtschaftliche und betriebliche Einordnung',
    spalten: [
      [
        {
          typ: 'tabelle',
          titel: 'Betriebskosten des Auswertungspfads',
          kopf: ['Größe', 'Wert'],
          zahlen: true,
          zeilen: [
            ['Modellaufrufe je beantworteter Frage', 'zwei'],
            ['Token je Frage im Mittel', '6.545 Eingabe / 256 Ausgabe'],
            ['Kosten je Frage', '2,35 Cent'],
            ['Kosten je Messlauf', 'rund 2,45 $'],
            ['Kosten der gesamten Messreihe', '12,27 $'],
          ],
        },
        {
          typ: 'punkte',
          punkte: [
            '96,3 Prozent der Token entfallen auf die Eingabe, davon 95,2 Prozent auf die Systemprompts, die bei jedem Aufruf unverändert erneut übertragen werden. Kostentreiber ist damit die Architektur, nicht die Nutzung.',
            'Zwischenspeichern gleichbleibender Eingabeteile senkt die Kosten je Lauf rechnerisch von 2,45 $ auf 0,71 $. Nicht umgesetzt, weil das betreffende Modul Teil des Messgegenstands ist.',
          ],
        },
      ],
      [
        {
          typ: 'gruppe',
          titel: 'Betriebliche Einordnung',
          punkte: [
            'Der Nutzen liegt dort, wo heute die Bindung wirkt: bei Rückfragen im Planungsdialog, die bislang einen erneuten Aufbereitungsdurchlauf erfordern.',
            'Die Kennzahlenübersicht entsteht ohne Sprachmodell und unterliegt weder Fehlerquote noch Streuung. Sie ist von der Bewertung der freien Frage zu trennen.',
            'Entscheidend ist nicht der Preis je Frage, sondern ob eine Antwort ungeprüft übernommen werden darf.',
            'Eine Entscheidung über die Weiterverfolgung setzt voraus, dass der Aufwand des bestehenden Verfahrens beziffert ist. Das ist er heute nicht.',
          ],
        },
      ],
    ],
  },
  {
    nr: 10,
    station: null, // Ergänzungsfolie: die Kamera bleibt stehen
    sektion: 'Ergänzende Folie',
    titel: 'Datenmodell, Konventionen und Absicherung',
    spalten: [
      [
        {
          typ: 'gruppe',
          titel: 'Datenmodell',
          punkte: [
            'Dimensionales Schema mit 25 Tabellen. Hierarchie: Region, Fahrzeugzentrum, Standort, Teilnetz.',
            'Umlaufdeckung auf Teilnetz-Ebene, alle übrigen Fakten auf Standort-Ebene.',
            'Verbindet eine Frage zwei Fakten unterschiedlicher Körnung, vervielfacht ein naiver Verbund die Werte der gröberen Tabelle. Beide Seiten müssen zuvor getrennt verdichtet werden.',
          ],
        },
        {
          typ: 'gruppe',
          titel: 'Auswertungskonventionen',
          punkte: [
            'Wertarten: Plan, Ist und Forecast liegen teils als Zeilen, teils als Spalten vor. Ohne Filter werden sie addiert.',
            'Begriffe: Werkstatt ist kein Standort, sondern eine Ausprägung des Standorttyps.',
            'Berechnungsregeln: Quoten als Verhältnis der Summen, nicht als Mittelwert der Einzelquoten.',
          ],
        },
        { typ: 'notiz', text: 'Neun fachliche Konventionen als Teil von insgesamt achtzehn, schriftlich festgehalten (A-4).' },
      ],
      [
        {
          typ: 'gruppe',
          titel: 'Absicherung',
          punkte: [
            'Erste Schranke: zugelassen sind nur lesende Anweisungen und nur die Tabellen des Auswertungsschemas.',
            'Zweite Schranke: die Verbindung selbst besitzt ausschließlich lesenden Zugriff. Eine Prüfung erkennt nur, was sie kennt.',
            'Ein bloßes Verbot im Prompt wurde verworfen: eine Anweisung an das Modell ist eine Erwartung, keine Zusicherung.',
            'Von fünf zurückzuweisenden Fällen wurden in allen Läufen vier zutreffend abgelehnt.',
          ],
        },
      ],
    ],
  },
  {
    nr: 11,
    station: null, // Ergänzungsfolie: die Kamera bleibt stehen
    sektion: 'Ergänzende Folie',
    titel: 'Importpfad und Grenzen der Untersuchung',
    spalten: [
      [
        {
          typ: 'gruppe',
          titel: 'Importpfad',
          punkte: [
            'Das Modell erzeugt aus einer Excel-Quelle eine Zuordnungsvorschrift zwischen Quell- und Zielspalten. Wenige Stichprobenzeilen dienen als Grundlage des Vorschlags, nicht als Absicherung.',
            'Drei strukturell verschiedene Quellen wurden vollständig und feldgleich überführt, je Quelle mit einer manuellen Korrektur.',
            'Keiner der drei Fehler betraf die inhaltliche Zuordnung. Alle wurden von Schemabedingung oder Prüfschicht gefangen, ein fehlerhafter Datenbestand entstand nicht.',
            'Je Quelle nur ein Aufruf. Daraus folgt keine Aussage über Stabilität, und das Ergebnis darf nicht neben die Prozentwerte des Auswertungspfads gestellt werden.',
          ],
        },
      ],
      [
        {
          typ: 'tabelle',
          titel: 'Drei Grenzen der Untersuchung',
          kopf: ['Grenze', 'Konsequenz'],
          zeilen: [
            ['Messgenauigkeit', 'Wiederholte Läufe des unveränderten Systems liegen um 3,4 Prozentpunkte auseinander. Ein Unterschied unterhalb dieser Größe ist nicht von der Streuung zu trennen.'],
            ['Übertragbarkeit', 'Ein Modell, eine Einstellung, ein synthetischer Datenbestand, dessen Fallkonstellationen bei der Erzeugung bekannt waren.'],
            ['Unabhängigkeit des Maßstabs', 'Die Referenzabfragen sind KI-gestützt entstanden. Dass die Läufe drei von ihnen korrigiert haben, zeigt, dass der Maßstab nicht nur bestätigt. Die gemeinsame Herkunft bleibt.'],
          ],
        },
      ],
    ],
    schluss: {
      typ: 'kasten',
      text: 'Innerhalb dieser Grenzen trägt die Untersuchung eine Aussage über die Zurechenbarkeit der Fehler, nicht über eine allgemeingültige Trefferquote.',
    },
  },
];

// Die sieben Hauptfolien laufen im Vortrag; die vier Ergänzungsfolien liegen
// dahinter und werden mit der Taste f aufgerufen.
export const hauptfolien = folien.filter((f) => f.nr <= 7);
export const zusatzfolien = folien.filter((f) => f.nr > 7);

// Folien je Station, in Folienreihenfolge. Der Rundgang baut daraus seine Schritte.
export function folienJeStation() {
  const karte = new Map();
  for (const f of hauptfolien) {
    if (!f.station) continue;
    if (!karte.has(f.station)) karte.set(f.station, []);
    karte.get(f.station).push(f);
  }
  return karte;
}
