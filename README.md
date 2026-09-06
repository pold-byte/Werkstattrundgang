## Sichtprüfung der Szene

1. Dev-Server starten (`cd app && npm run dev -- --port 5199`) und http://localhost:5199 öffnen.
2. `node tools/schuss-server.mjs` im Repo-Wurzelverzeichnis starten.
3. Inhalt von `tools/render-posen.js` in die Browser-Konsole einfügen. Die neun Bilder
   liegen danach in `blender/renders/p_*.png` (nicht versioniert).
4. Weltboxen einzelner Objekte: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python blender/frage_szene.py -- <Name>`.
5. Materialien und Texturen der glb: `node tools/glb-info.mjs app/public/szene.glb` (mit `--json` maschinenlesbar).
