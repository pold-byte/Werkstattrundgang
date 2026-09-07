## Sichtprüfung der Szene

1. Dev-Server starten (`cd app && npm run dev -- --port 5199`) und http://localhost:5199 öffnen.
2. `node tools/schuss-server.mjs` im Repo-Wurzelverzeichnis starten.
3. Inhalt von `tools/render-posen.js` in die Browser-Konsole einfügen. Die neun Bilder
   liegen danach in `blender/renders/p_*.png` (nicht versioniert).
4. Weltboxen einzelner Objekte: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python blender/frage_szene.py -- <Name>`.
5. Materialien und Texturen der glb: `node tools/glb-info.mjs app/public/szene.glb` (mit `--json` maschinenlesbar).
6. Jedes `p_<pose>.png` neben `p_<pose>_v2vorher.png` (Stand vor Plan `2026-09-06-werkstatt-materialrealismus`) legen, um Material-, Licht- und Detailänderungen zu vergleichen; Ergebnis siehe `docs/superpowers/plans/2026-09-06-werkstatt-materialrealismus-abnahme.md`. Der Viewer schaltet Ambient Occlusion bei Überlast automatisch ab; `?ao=0` an die URL anhängen, um sie manuell zu erzwingen.
