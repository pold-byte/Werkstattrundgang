## Sichtprüfung der Szene

1. Dev-Server starten (`cd app && npm run dev -- --port 5199`) und http://localhost:5199 öffnen.
2. `node tools/schuss-server.mjs` im Repo-Wurzelverzeichnis starten.
3. Inhalt von `tools/render-posen.js` in die Browser-Konsole einfügen. Die neun Bilder
   liegen danach in `blender/renders/p_*.png` (nicht versioniert).
4. Weltboxen einzelner Objekte: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python blender/frage_szene.py -- <Name>`.
5. Materialien und Texturen der glb: `node tools/glb-info.mjs app/public/szene.glb` (mit `--json` maschinenlesbar).
6. Jedes `p_<pose>.png` neben `p_<pose>_v2vorher.png` (Stand vor Plan `2026-09-06-werkstatt-materialrealismus`) legen, um Material-, Licht- und Detailänderungen zu vergleichen; Ergebnis siehe `docs/superpowers/plans/2026-09-06-werkstatt-materialrealismus-abnahme.md`. Der Viewer schaltet Ambient Occlusion bei Überlast automatisch ab; `?ao=0` an die URL anhängen, um die Abschaltung manuell zu erzwingen.

## Folienschau

Der Rundgang führt, die Folien folgen. Ablauf mit Leertaste und Pfeiltasten:

1. Überblick über die Werkstatt, keine Folie.
2. Leertaste: die Kamera fährt zur Station. Während der Fahrt bleibt die Halle frei.
3. Ankunft: die Station ist zu sehen, weiterhin ohne Folie.
4. Leertaste: die erste Folie der Station wird eingeblendet, darunter bleibt die
   Halle als Rahmen sichtbar.
5. Leertaste: zweite Folie der Station, sonst Fahrt zur nächsten Station.

Zuordnung der sieben Hauptfolien:

| Station | Folien |
|---------|--------|
| 1 Meisterbüro | 1 Titel, 2 Ausgangslage |
| 2 Datenraum | 3 Zielsetzung, 4 Gesamtarchitektur |
| 3 Terminal | 5 Auswertungspfad |
| 4 Anzeigetafel | 6 Messaufbau |
| 5 Prüfstand | 7 Ergebnis |

Meisterbüro und Datenraum tragen je zwei Folien, bis zwei weitere Stationen
gebaut sind; die Zuordnung steht im Feld `station` in `app/src/folien-inhalt.js`.
Taste `f` blendet die vier Ergänzungsfolien ein, dort blättern Leertaste und
Pfeiltasten; ein weiteres `f` kehrt in den Rundgang zurück. Gestaltung nach
`docs/foliensatz/DESIGN.md`.
