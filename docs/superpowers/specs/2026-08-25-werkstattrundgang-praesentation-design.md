# Design-Spec: Interaktiver Werkstattrundgang (Präsentation Projektarbeit DB Regio)

Stand: 2026-08-25 · Status: Entwurf zur Nutzer-Review

## 1. Ziel und Kontext

Live navigierbare 3D-Präsentation für die ~15-minütige Verteidigung der Projektarbeit
„Konzeption, prototypische Umsetzung und Bewertung einer KI-gestützten Datenplattform zur
Instandhaltungssteuerung in der Region Mitte der DB Regio AG" (DHBW Mannheim, Prüfer-Publikum).

Eine in Blender modellierte Instandhaltungswerkstatt dient als räumliche Gliederung: Tastendruck
→ deterministische Kamerafahrt zur nächsten Station → Themen-Slide blendet als HTML-Overlay ein.
Roter Faden laut Briefing: **eine Kennzahl von der Werkstatthalle bis in die Planungsrunde.**

Grundlage: [BRIEFING_praesentation.md](../../../BRIEFING_praesentation.md) — insbesondere
Abschnitt 6 (Stationen) und Abschnitt 7 (Gestaltungsregeln). Alle dortigen Regeln gelten
unverändert (Deutsch, sachlich, Arial, graustufentauglich, Kopfzeile „DB Intern / DB internal",
pro Station eine Kernaussage + max. drei Belegpunkte + ein Anschauungsobjekt, keine erfundenen
Zahlen).

## 2. Getroffene Entscheidungen

| Entscheidung | Wahl |
|---|---|
| Ablaufmodus | Live navigierbar (kein Video-Durchlauf) |
| Konzept | **A: Three.js-Web-App**, mit **Ausbaustufe D** („Route /vortrag" im Prototyp) optional |
| Visueller Stil | **C: Low-Poly, entsättigte Farben**; Verkehrsrot nur dezent am Triebzug, Rest grau-blau |
| Prototyp-Demo | Aufgezeichnetes Screen-Recording (stumm); in Stufe D ersetzt durch echtes Frontend im Replay-Modus |
| Zeitbudget Bau | > 3 Wochen, realistisch 10–14 Arbeitstage (Basis A) |
| Zielzeit Vortrag | 13:00 min (Puffer zu 15:00) |
| Slide-Inhalte | **Werden später entschieden/befüllt** — die App wird mit Platzhalter-Inhalten in korrekter Struktur gebaut; echte Zahlen erst nach Bereitstellung der Quelldateien (TextV14.docx, Fragenkatalog_v4.docx, Messprotokolle) |

## 3. Nicht-Ziele

- Kein Live-API-Zugriff, kein Internet zur Laufzeit; Präsentation läuft vollständig offline.
- Keine PowerPoint-/Prezi-/Spline-Nutzung.
- Keine erfundenen Zahlen, Prozentwerte oder Beispielfragen — Platzhalter sind als solche
  gekennzeichnet (`[PLATZHALTER: …]`) und dürfen nie präsentiert werden.
- Kein Predictive Maintenance, keine Sensorik/SAP/ECM-Inhalte (nur ggf. als Abgrenzung auf Slides).
- Keine Soundeffekte, keine Effekte ohne Funktion.

## 4. Dramaturgie und Stationen

Startbild: Totale der Halle von schräg oben, sechs nummerierte Stationsschilder sichtbar,
Titel-Overlay. Die Agenda wird am Raum erklärt (≈ 1 min).

Pro Presenter-Druck passiert genau eines: nächste Kamerafahrt **oder** nächster Belegpunkt.
Fahrten laufen 5–8 s (eher 5), sind deterministisch (zeitbasiertes Easing, framerate-unabhängig)
und enden immer exakt auf der Zielpose; eine laufende Fahrt spricht nie mit neuem Text.

| # | Station / Ort in der Halle | Thema (Briefing) | Besonderheit |
|---|---|---|---|
| 1 | Meisterbüro mit Pinnwand + Excel-Ausdrucken | Wo die Zahl entsteht (Ist-Zustand) | Text auf Requisiten „gegreekt" (unleserlich), damit keine erfundenen Zahlen im Bild stehen |
| 2 | Datenraum/Regal: ungeordnete Ablage davor, geordnete Struktur darin | Aus Chaos wird Struktur (Importpfad) | Kein Animations-Höhepunkt (Importpfad ist bewusst nicht evaluiert); die Kamerafahrt vom Chaos zur Ordnung trägt die Aussage |
| 3 | Bedienterminal am Arbeitsplatz | Fragen statt Formeln (Auswertungspfad) | Demo-Video läuft als Bildschirmtextur; Taste V holt es scharf nach vorn (Stufe D: Wechsel ins echte Frontend) |
| 4 | Anzeigetafel | Ergebnis lesen (Diagrammwahl R-D1–R-D9, AK-1–AK-18) | Bewusst wieder in der Halle mit regulärem Overlay — auch in Stufe D kehrt der Ablauf hierfür aus dem Frontend zurück |
| 5 | Prüfstand | Stimmt das auch? (Evaluation) | **Längste Station** (3–3,5 min); zusätzlich zur Kernaussage ein Graustufen-SVG mit Execution-Accuracy-Ergebnissen (Panel-Wechsel per Tastendruck erlaubt) |
| 6 | Besprechungsraum | Was es bringt, was nicht | Wird im Vortrag nicht angefahren; Reserve für Fragerunde (Taste 6) |

Nach Station 5: Rückflug zur Totale = Schlussbild und Oberfläche für die Fragerunde.
Gesamtzeit aller Fahrten < 1 min. Für jede Fahrt existiert ein Übergangssatz im Sprechtext.

Vorbereitete Zwei-Satz-Antwort auf die absehbare Prüferfrage „Warum 3D statt Folien?":
Der Rundgang ist die räumliche Form der im Briefing festgelegten Gliederung (eine Kennzahl von
der Halle bis in die Planungsrunde) und entstand außerhalb des Bewertungszeitraums der Arbeit;
die Importpfad-Abgrenzung war eine methodische Scoping-Entscheidung, keine Zeitfrage.

## 5. Architektur (Basis A)

Vier Bausteine, ein Datenmodell:

1. **Blender-Szene** → Export als eine `szene.glb` (glTF 2.0).
   - Low-Poly, Budget ≈ 200k Dreiecke, Timebox 2–3 Tage, danach Einbau des vorhandenen Stands.
   - Nur Base-Color/Roughness-PBR (keine prozeduralen Shader — exportieren nicht); Beleuchtung
     komplett in Three.js (Ambient + 1–2 Directional), keine Blender-Lichter exportieren.
   - Graustufen-Gegenprobe: Screenshot entsättigen; alle Unterscheidungen müssen über Form/
     Helligkeit lesbar bleiben.
   - Claude modelliert über die vorhandene Blender-MCP-Anbindung mit.
2. **Three.js-Viewer** (Vanilla JS, Vite; Three.js lokal gevendort/gepinnt, kein CDN).
   - Kamerafahrten: Waypoints (Position, Blickziel, Dauer) + kubisches Ease-in-out, zeitbasiert;
     Abbruch (Skip) setzt hart auf die Zielpose. Pixel-Ratio-Deckel 2.
   - Dev-Werkzeug (nur im Dev-Build): OrbitControls + Taste „Waypoint speichern" → schreibt
     Pose als JSON in die Konsole/Datei.
3. **Zustandsmaschine + HTML-Overlays** (DOM über dem Canvas).
   - Lineare Schrittliste (Totale → Fahrt S1 → Belegpunkt 1..n → Fahrt S2 → …) + Direktsprünge.
   - Slides: Panel über dem rechten Bilddrittel, ≥ 90 % Deckkraft, Arial, nur Schwarz/Weiß/Grau,
     relative Einheiten (clamp/vw/rem — keine pt), Kopfzeile „DB Intern / DB internal" als fixe
     Leiste immer sichtbar. Diagramme als Inline-SVG (Unterscheidung über Linienstärke/
     Strichelung/Form). Mindestlesbarkeit: 24-pt-Äquivalent bei 1080p.
   - Beim Ankommen: Szene dimmt leicht, Panel blendet in ~300 ms ein; Belegpunkte einzeln.
4. **Demo-Video** (stumm, MP4/H.264, Start erst nach Tastendruck — Nutzergeste).
   - Zwei Dateifassungen, zwei `<video>`-Elemente: 720p-Fassung als `VideoTexture` (sRGB,
     geloopt) auf dem Terminal-Monitor; 1080p-Fassung als DOM-Großansicht (Taste V),
     Pause per Leertaste bei offener Großansicht.
   - Aufnahme mit OBS: 2–3 Fragen aus dem Fragenkatalog inkl. eines Zurückweisungsfalls,
     Schnitt auf ≤ 90 s, Hinweis „Aufzeichnung, [Datum]" eingeblendet.

**Datenmodell `stationen.json`** — einzige Quelle der Wahrheit für App und PDF-Export:

```json
{
  "stationen": [
    {
      "nr": 1,
      "id": "meisterbuero",
      "titel": "Wo die Zahl entsteht",
      "kapitel": "Kap. 1.1, 3.1",
      "kamera": { "position": [x, y, z], "blickziel": [x, y, z], "dauer_s": 6 },
      "kernaussage": "[PLATZHALTER: wird nach Bereitstellung der Quelldateien befüllt]",
      "belegpunkte": ["[PLATZHALTER]", "[PLATZHALTER]", "[PLATZHALTER]"],
      "anschauungsobjekt": "Pinnwand mit Excel-Ausdrucken",
      "quelle_kommentar": "[Quelldatei + Abschnitt, nicht gerendert]"
    }
  ]
}
```

Slide-Inhalte befüllen ist damit reine Datenpflege (keine Codeänderung) und ein **separater,
späterer Arbeitsschritt**, der erst nach Bereitstellung der Quelldateien erfolgt.

## 6. Steuerung

| Taste(n) | Wirkung |
|---|---|
| Pfeil rechts / Leertaste / Bild-ab | Nächster Schritt (Belegpunkt bzw. nächste Fahrt) |
| Pfeil links / Bild-auf | Ein Schritt zurück |
| 1–6 | Direktflug zur Station (Fragerunde); 6 = Reservestation |
| 0 | Zurück zur Totale (nicht Esc — Esc gehört dem Browser-Vollbild) |
| S | Laufende Fahrt abbrechen → hart auf Zielpose |
| V | Demo-Video groß / zurück in die Szene; Leertaste pausiert bei offenem Video |
| B | Schwarzbild an/aus |

Härtung: Start im Kiosk-Modus (`--kiosk`, Chrome/Edge); F5, Leertasten-Scroll etc. per
`preventDefault` abgefangen; aktueller Schritt wird bei jeder Änderung in `sessionStorage`
persistiert (Reload landet an derselben Stelle). Eingaben während einer Fahrt: gesperrt,
genau ein Folgedruck wird gepuffert. Presenter-Remote-Tastencodes werden in Woche 1 mit einem
Key-Logger-Snippet am konkreten Gerät verifiziert; Pfeiltasten bleiben immer funktionsfähig.

## 7. Start und Fallback-Leiter

Regelstart: Doppelklick-Batchdatei → lokaler Webserver (localhost) + Browser-Kiosk-Vollbild.
Direktes `file://`-Öffnen scheitert an CORS beim `.glb`-Laden und ist deshalb kein dokumentierter Weg.

1. **Single-File-Notversion:** eine HTML-Datei mit eingebetteter `.glb` als Base64 — läuft per
   Doppelklick ohne Server auf jedem Rechner (Video via `<video src>` funktioniert unter file://).
2. **PDF als vollwertiges, abgabefähiges Dokument** (nicht Notnagel): pro Station eine
   A4-Querformat-Seite — weiße Seite, identischer Slide-Inhalt, Kopfzeile, kleines
   Szenen-Thumbnail als Anker. Generiert aus `stationen.json` + gerenderten Standbildern.
   Wird früh gebaut (deckt mögliche Abgabepflicht des Foliensatzes ab).
3. **MP4-Komplettmitschnitt** eines Probedurchlaufs als Notreserve (USB-Stick + Laptop).

Vorab-Klärung bei der DHBW (Woche 1, per E-Mail): eigener Laptop erlaubt? Beamer-Auflösung/
Anschluss (HDMI/VGA)? Abgabepflicht des Foliensatzes? Rüstzeit vor dem Slot?

## 8. Ausbaustufe D: „Route /vortrag" (optional)

Nur nach positivem **Tag-0-Check** am bestehenden Prototyp (eigener Branch, bewerteter Code
bleibt unverändert):

- (a) Welche Endpunkte ruft das Frontend auf (Anzahl, Pfade, Strukturen)?
- (b) Antwort als einzelnes JSON oder Stream?
- (c) Diagramme clientseitig gerendert (gut) oder serverseitig (dann Bilddateien als Fixtures)?
- (d) Prüft das Backend beim Start API-Schlüssel/Erreichbarkeit — per Flag abschaltbar?
- (e) CSS-Designsystem kollisionsfrei wiederverwendbar (Namensräume)?
- (f) Einbettung: iframe vs. integrierte Ansicht — wer bekommt die Tastatur-Events der Remote?
- (g) Trägt das Prototyp-Frontend selbst die Kopfzeile „DB Intern / DB internal"?

Umsetzung: FastAPI-Route `GET /vortrag` liefert die Präsentation aus; Flag `REPLAY=1` lässt das
Backend für die 1–2 Demo-Fragen JSON-Fixtures aus realen Messläufen mit gedeckelter Latenz
(1–2 s) zurückgeben — Frontend unverändert. Übergang an Station 3: **harter, sauberer Schnitt**
(kurze Blende) als Standard; „nahtlos/pixelgleich" ist explizit kein Anspruch. Der Replay-Modus
wird im Sprechtext offen deklariert (Offline-Pflicht, benannter Nichtdeterminismus,
Reproduzierbarkeit) — inklusive vorbereiteter 30-s-Antwort auf die Frage „Was ist daran noch
echt?" (Angebot: Live-Vorführung mit Netz im Anschluss). Im Vortrag genau **eine** Replay-Frage;
die zweite ist Reserve für die Fragerunde. Station 4 kehrt in die Halle zurück (siehe Tabelle).
Scheitert der Check oder die Timebox: Basis A trägt denselben Ablauf mit dem Video — Szene,
Overlays und Dramaturgie ändern sich nicht.

## 9. Arbeitsreihenfolge und Gates

1. **Phase 1 — App-Gerüst:** Vite-Projekt, Platzhalterszene (Boxen), Zustandsmaschine,
   Tastensteuerung, Overlay-System mit `stationen.json` (Platzhalter-Inhalte).
2. **Phase 2 — Kamerafahrten:** Waypoints, Easing, Skip, Dev-Waypoint-Werkzeug.
3. **Phase 3 — Blender-Modell** (Timebox 2–3 Tage) + Integration, Posen-Feinjustage, Performance.
4. **Phase 4 — Video-Integration**; parallel möglich: Tag-0-Check und ggf. Ausbaustufe D (Timebox 1 Tag für den Übergang).
5. **Phase 5 — Fallbacks:** Single-File-Version, PDF-Generator, Mitschnitt.
6. **Phase 6 — Generalprobe** auf Zielhardware (spätestens Ende Woche 2): 1024×768/4:3,
   1280×800, 1920×1080, Skalierung 125/150 %, Presenter-Remote. Danach **Feature-Stopp** —
   nur noch Bugfixes, Inhalte, Sprechtext.
7. **Später, entkoppelt — Inhalte:** Quelldateien bereitstellen → Slide-Texte destillieren →
   `stationen.json` befüllen (jede Zahl mit Quellvermerk) → PDF neu generieren → Demo-Video
   aufnehmen. Blockiert keine der Phasen 1–6 außer der finalen Generalprobe mit echten Inhalten.

## 10. Abnahmekriterien

- Kompletter Durchlauf offline (Flugmodus) vom eigenen Laptop, Start per Batchdatei.
- Jede Fahrt endet in identischer Pose, unabhängig von Framerate und Skip.
- Panels lesbar bei 1024×768 aus 5 m (Testprojektion); kein Text unter 24-pt-Äquivalent@1080p.
- Reload während des Vortrags landet am selben Schritt.
- PDF aus `stationen.json` generierbar und eigenständig vortragsfähig.
- Kein präsentierbarer `[PLATZHALTER]` mehr im finalen Stand.
- Stoppuhr-Durchlauf ≤ 13:00.

## 11. Offene Punkte

- Pfade zu Quelldateien und Prototyp-Repo (nötig erst für Phase „Inhalte" und Tag-0-Check).
- Konkretes Presenter-Remote-Modell (Tastencodes verifizieren).
- Antwort der DHBW zur Raumtechnik/Abgabepflicht.
