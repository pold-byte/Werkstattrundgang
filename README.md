## Sichtprüfung der Szene

1. Dev-Server starten (`cd app && npm run dev -- --port 5199`) und http://localhost:5199 öffnen.
2. `node tools/schuss-server.mjs` im Repo-Wurzelverzeichnis starten.
3. Inhalt von `tools/render-posen.js` in die Browser-Konsole einfügen. Die neun Bilder
   liegen danach in `blender/renders/p_*.png` (nicht versioniert).
4. Weltboxen einzelner Objekte: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python blender/frage_szene.py -- <Name>`.
5. Materialien und Texturen der glb: `node tools/glb-info.mjs app/public/szene.glb` (mit `--json` maschinenlesbar).
6. Jedes `p_<pose>.png` neben `p_<pose>_v2vorher.png` (Stand vor Plan `2026-09-06-werkstatt-materialrealismus`) legen, um Material-, Licht- und Detailänderungen zu vergleichen; Ergebnis siehe `docs/superpowers/plans/2026-09-06-werkstatt-materialrealismus-abnahme.md`. Der Viewer schaltet Ambient Occlusion bei Überlast automatisch ab; `?ao=0` an die URL anhängen, um die Abschaltung manuell zu erzwingen.

## Folienschau

Der Foliensatz ist die Standardansicht. Inhalt aus `app/src/folien-inhalt.js`,
Gestaltung nach `docs/foliensatz/DESIGN.md`. Die Folie füllt den Bildschirm bis
auf einen Rahmen, in dem die Halle gedämpft sichtbar bleibt.

Die sieben Hauptfolien laufen mit Leertaste und Pfeiltasten; die Kamera fährt
dabei an die Station, die im Feld `station` steht:

| Folie | Station |
|-------|---------|
| 1 Titel | Totale |
| 2 Ausgangslage | 1 Meisterbüro |
| 3 Zielsetzung | 1 Meisterbüro |
| 4 Gesamtarchitektur | 2 Datenraum |
| 5 Auswertungspfad | 3 Terminal |
| 6 Messaufbau | 4 Anzeigetafel |
| 7 Ergebnis | 5 Prüfstand |

Folie 2 und 3 teilen sich das Meisterbüro, bis zwei weitere Stationen gebaut
sind. Taste `f` schaltet nach der letzten Hauptfolie auf die vier
Ergänzungsfolien, ein weiteres `f` zeigt die Halle ohne Folie, das dritte kehrt
zum Hauptsatz zurück.

