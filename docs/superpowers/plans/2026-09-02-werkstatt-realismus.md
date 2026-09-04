# Werkstatt-Realismus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die 3D-Werkstatthalle des Werkstattrundgangs so überarbeiten, dass sie in allen sieben Jury-Posen als echtes DB-Instandhaltungswerk liest: Gleis bündig im Boden, Lichtbänder statt Pendelkegel, Industriefarben statt Pastell, Drehgestelle mit Achsdeckeln, Kabelwege mit Anschlusskästen, Fasen an den Kenney-Möbeln und ein Zugkasten im ICE-Verhältnis.

**Architecture:** Die gesamte Szene wird von `blender/blockout.py` (Blender 5.2, headless) erzeugt und als `app/public/szene.glb` exportiert; jede Aufgabe ist eine Änderung an diesem Skript plus Neuexport. Drei automatische Prüfer (`blender/pruefe_alles.py`) messen nach jeder Änderung Schweber, Durchdringungen und Kamerarouten. Ein neues Abfragewerkzeug (`blender/frage_szene.py`) liefert Weltboxen einzelner Objekte, damit jede Aufgabe eine messbare Erwartung hat, die VOR der Änderung fehlschlägt und DANACH erfüllt ist. Sichtprüfungen laufen über den Dev-Server und einen kleinen Bildempfänger (`tools/schuss-server.mjs`).

**Tech Stack:** Blender 5.2 Python (bpy, mathutils), glTF-Export, Node 24 (Vite 7, Three.js 0.180, Vitest 3), Git.

**Spec:** `docs/superpowers/specs/2026-08-25-werkstattrundgang-praesentation-design.md` (Dramaturgie, Gestaltungsregeln, Abnahmekriterien). Die Realismus-Anforderungen dieses Plans stammen aus dem Werkstatt-Audit vom 2026-09-02 (zwei Kritik-Linsen: Glaubwürdigkeit und Stil) und sind im Abschnitt "Ausgangsbefunde" unten festgehalten; der Plan argumentiert aus beiden.

## Global Constraints

- Sprache Deutsch, Ton sachlich; Schrift im Overlay Arial; alles graustufentauglich; Kopfzeile "DB Intern / DB internal" (Spec §1, Briefing Abschnitt 7).
- Keine erfundenen Zahlen. Keine lesbaren Ziffern, Buchstaben oder Logos in der Szene; alle Anschriften bleiben "gegreekt" (abstrakte Balken). Einzige Ausnahme: das DB-Logo an den Zugköpfen.
- Die sieben Kameraposen in `app/src/stationen.json` sind per Juryentscheid fest. Sichtprobleme werden über Geometrie gelöst, nie über Kamerabewegung.
- Nichts schwebt: `pruefe_geometrie.py` meldet jedes Objekt ohne Nachbarn näher als 0.08 m. Durchdringungen über 35 Prozent des kleineren Objekts werden gemeldet; die bekannte Liste hat genau 13 Einträge (Kenney-Cloneteile, Rohr_Blau/Ventilrad, Gasflaschen, Kabelbruecke/Schlauch, Stuhl/Tisch) und darf nicht wachsen.
- Alle 20 Kamerarouten aus `berechne_fahrtwege.py` müssen lösbar bleiben (`0 ungeloest`), `pruefe_flugpfade.py` muss `0 Kollisionen` melden.
- Nur CC0-Assets (Kenney-Kits unter `blender/assets/kenney/`).
- Der Zugkopf (`fuehrerstand()` in `blender/blockout.py`) ist vom Nutzer abgenommen: Form, Scheibe, Leuchten, Logo bleiben unangetastet.
- `app/public/szene.glb` bleibt unter 8 MB.
- Nach jeder Aufgabe: Prüfer grün, `npm test` grün (40 Tests), Commit und Push auf `main`.
- Koordinaten in `blockout.py`: three.js-Konvention, x längs (Ost positiv), y hoch, z quer. `kasten(name, dx, dz, dy, x, y, z, mat, drehung=None, fase=0.02)` nimmt Maße in dieser Reihenfolge: Länge x, Tiefe z, Höhe y. `zylinder(name, radius, laenge, x, y, z, mat, achse="y", ecken=16, fase=0.0)`. Blender-intern ist (x, y, z)_three = (x, -z, y)_blender.

## Ausgangsbefunde (Audit 2026-09-02, bestätigt am Code)

| Nr | Befund | Pose(n) | Aufgabe |
|---|---|---|---|
| B1 | Hallengleis liegt wie Freistrecke auf sichtbaren Schwellen 15 cm über dem Boden statt bündig im Werkstattboden | Bahnsteig-Hero, Totale, Kranbahn | Task 2 |
| B2 | Kegel-Hängeleuchten als facettierte Spitzkegel; Werkstätten haben Lichtbänder | Totale, Kranbahn, Hintergründe | Task 3 |
| B3 | Pastellfarben (Blau 0.30/0.47/0.75, Grün 0.30/0.55/0.32) lesen als Spielzeug, nicht als RAL-Maschinenlack | alle | Task 1 |
| B4 | Wände ohne Sockelzone; echte Hallen haben einen dunklen, abwaschbaren Sockel | alle Stationsposen | Task 1 |
| B5 | Drehgestelle lesen als Balken, Achslager sind dunkle Klötze ohne Deckel | Bahnsteig-Hero, Totale | Task 5 |
| B6 | Kenney-Möbel ohne Fase, zweite Kantensprache neben den gefasten Kästen | Station 1, 6 | Task 5 |
| B7 | Medienstelen stehen 0.2 m neben dem Wagenkasten im Lichtraum | Bahnsteig-Hero, Kranbahn | Task 5 |
| B8 | Bürobox: Fenster und Tür als aufgesetzte Platten ohne Rahmen und Fensterbank | Station 1 | Task 6 |
| B9 | Bedienterminal steht kabellos frei; Prüfstand-Kabel läuft als starre Schräge, Anschlusskasten liest als Verbandkasten | Station 3, 5 | Task 7 |
| B10 | Höhe-zu-Breite des Wagenkastens 1.26 statt 1.36 (ICE 4) | Totale | Task 8 (optional) |

## Werkzeuge und Kommandos (für alle Aufgaben)

```bash
# Szene bauen und exportieren (rund 25 s)
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/blockout.py 2>&1 | grep -E "Export fertig|Error|Traceback"

# Alle drei Pruefer (rund 20 s). Erwartung: KEINE Zeile "SCHWEBT", "13 Durchdringungen gesamt", "20 Routen, 0 ungeloest", "0 Kollisionen"
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/pruefe_alles.py 2>/dev/null | grep -E "SCHWEBT|Durchdringungen gesamt|Routen|Kollisionen"

# App-Tests
cd app && npm test --silent

# Weltbox eines Objekts (Task 0 legt das Skript an)
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/frage_szene.py -- Gleis_Schiene_Nord 2>/dev/null | sed -n '/AABB-ANFANG/,/AABB-ENDE/p'
```

Sichtprüfung: Dev-Server über `.claude/launch.json` Eintrag `rundgang-dev` (Port 5199) starten, Bildempfänger `node tools/schuss-server.mjs` starten, dann im Browser die Szene laden und den Inhalt von `tools/render-posen.js` in die Konsole einfügen. Die Bilder landen in `blender/renders/p_*.png`. Im Browser-Panel dieser Entwicklungsumgebung frieren Kamerafahrten ein (rAF-Drossel); das Skript setzt die Kamera deshalb direkt.

---

### Task 0: Abfrage- und Renderwerkzeuge

**Files:**
- Create: `blender/frage_szene.py`
- Create: `tools/schuss-server.mjs`
- Create: `tools/render-posen.js`
- Modify: `README.md` (Abschnitt "Sichtprüfung" anhängen)

**Interfaces:**
- Produces: `frage_szene.py` druckt zwischen den Markern `AABB-ANFANG` und `AABB-ENDE` je Objekt eine Zeile `Name|minx,miny,minz|maxx,maxy,maxz` in three.js-Koordinaten (Meter, drei Nachkommastellen). Argumente nach `--` sind Objektnamen oder Namenspräfixe; `--alle` druckt alle Meshes. Alle späteren Aufgaben prüfen ihre Erwartungen damit.
- Produces: `schuss-server.mjs` nimmt `POST http://localhost:5198/` mit JSON `{name, data}` (data = PNG-Data-URL) an und schreibt `blender/renders/<name>.png`.

- [ ] **Step 1: Abfrageskript anlegen**

```python
# blender/frage_szene.py
"""Weltboxen einzelner Objekte in three.js-Koordinaten.

Baut die Szene EINMAL ohne Export (Muster wie pruefe_flugpfade.py) und druckt fuer
jedes Argument hinter '--' (Objektname oder Praefix) eine Zeile
    Name|minx,miny,minz|maxx,maxy,maxz
zwischen den Markern AABB-ANFANG und AABB-ENDE. '--alle' druckt alle Meshes;
das ist der Vorher/Nachher-Dump fuer Regressionsdiffs.

Aufruf:
  blender --background --python blender/frage_szene.py -- Gleis_Schiene_Nord Triebzug_DG_0_
  blender --background --python blender/frage_szene.py -- --alle > /tmp/vorher.txt
"""
import bpy
import os
import sys
from mathutils import Vector

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if "SZENE_BEREIT" not in globals():
    with open(os.path.join(WURZEL, "blender", "blockout.py"), encoding="utf-8") as f:
        code = f.read().replace("bpy.ops.export_scene.gltf(", "(lambda **kw: None)(")
    exec(compile(code, "blockout.py", "exec"))
    SZENE_BEREIT = True

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def weltbox(o):
    ecken = [o.matrix_world @ Vector(e) for e in o.bound_box]
    # Blender (x, y, z) -> three.js (x, z, -y)
    xs = [p.x for p in ecken]
    ys = [p.z for p in ecken]
    zs = [-p.y for p in ecken]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


zeilen = []
for o in sorted(bpy.data.objects, key=lambda ob: ob.name):
    if o.type != "MESH":
        continue
    if args and "--alle" not in args and not any(o.name == a or o.name.startswith(a) for a in args):
        continue
    mn, mx = weltbox(o)
    zeilen.append("%s|%.3f,%.3f,%.3f|%.3f,%.3f,%.3f" % (o.name, mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]))

print("AABB-ANFANG")
print("\n".join(zeilen))
print("AABB-ENDE")
```

- [ ] **Step 2: Abfrage ausführen und gegen bekannte Werte prüfen**

Run:
```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/frage_szene.py -- Gleis_Schiene_Nord Triebzug_Korpus 2>/dev/null | sed -n '/AABB-ANFANG/,/AABB-ENDE/p'
```
Expected (heutiger Stand, Toleranz 0.001):
```
AABB-ANFANG
Gleis_Schiene_Nord|-17.000,0.005,-0.775|21.000,0.155,-0.625
Triebzug_Korpus|-6.500,0.950,-1.200|7.500,2.700,1.200
AABB-ENDE
```
Wenn `Triebzug_Korpus` andere Werte zeigt, stimmt die Koordinatenumrechnung nicht; y muss 0.950..2.700 sein.

- [ ] **Step 3: Bildempfänger anlegen**

```javascript
// tools/schuss-server.mjs
// Nimmt PNG-Data-URLs aus dem Browser entgegen und schreibt sie nach blender/renders/.
// Start: node tools/schuss-server.mjs   (im Repo-Wurzelverzeichnis)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ZIEL = path.join(process.cwd(), 'blender', 'renders');
fs.mkdirSync(ZIEL, { recursive: true });

http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') { res.end(); return; }
  let rumpf = '';
  req.on('data', (teil) => { rumpf += teil; });
  req.on('end', () => {
    try {
      const { name, data } = JSON.parse(rumpf);
      if (!/^[\w-]+$/.test(name)) throw new Error('unerlaubter Name');
      fs.writeFileSync(path.join(ZIEL, name + '.png'), Buffer.from(data.split(',')[1], 'base64'));
      console.log('OK ' + name);
    } catch (fehler) {
      console.log('FEHLER ' + fehler.message);
    }
    res.end('ok');
  });
}).listen(5198, () => console.log('Schuss-Server auf http://localhost:5198'));
```

- [ ] **Step 4: Browser-Renderskript anlegen**

```javascript
// tools/render-posen.js
// In die Browser-Konsole der laufenden App (http://localhost:5199) einfuegen.
// Rendert die sieben Jury-Posen plus zwei freie Blickwinkel in 1600x900 und
// schickt sie an tools/schuss-server.mjs. Braucht die DEV-Globals
// window.__szene/__kamera/__renderer (main.js setzt sie nur im Dev-Modus).
(async () => {
  window.__rafOrig = window.__rafOrig || window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = () => 0; // App-Schleife anhalten, sonst ueberschreibt sie die Kamera
  const s = window.__szene, k = window.__kamera, rn = window.__renderer;
  const c = rn.domElement;
  Array.from(document.body.children).forEach((e) => { if (e !== c) e.style.visibility = 'hidden'; });
  rn.setSize(1600, 900, false); // verborgenes Panel meldet sonst 0x0 und toDataURL liefert 'data:,'
  k.aspect = 16 / 9; k.fov = 50;
  const posen = [
    ['p_totale', [15, 4.6, 4.5], [-8, 0.5, 0.2]],
    ['p_meisterbuero', [-5.2, 2.1, -3.2], [-10.2, 1.2, -6.6]],
    ['p_datenraum', [0.5, 2.2, -2.5], [-3, 1, -6]],
    ['p_terminal', [9.2, 1.6, -1.6], [6.6, 1.2, -4.4]],
    ['p_anzeigetafel', [10.6, 1.9, 2], [8.6, 2, 5.9]],
    ['p_pruefstand', [-1.5, 2.5, 2.5], [2, 1, 6]],
    ['p_besprechung', [-5.5, 2.2, 2.5], [-9, 1, 6]],
    ['p_hero_bahnsteig', [6, 1.7, -5.5], [-2, 1.5, 0]],
    ['p_hero_kranbahn', [-12, 5.5, 6], [4, 1.5, -1]],
  ];
  for (const [name, pos, ziel] of posen) {
    k.position.set(...pos); k.updateProjectionMatrix(); k.lookAt(...ziel); rn.render(s, k);
    const antwort = await fetch('http://localhost:5198/', { method: 'POST', body: JSON.stringify({ name, data: c.toDataURL('image/png') }) });
    console.log(name, antwort.status);
  }
  console.log('fertig; Seite neu laden, um die App wieder normal zu betreiben');
})();
```

- [ ] **Step 5: Bildempfänger einmal testen**

Run (zwei Terminals):
```bash
node tools/schuss-server.mjs
```
```bash
node -e "fetch('http://localhost:5198/',{method:'POST',body:JSON.stringify({name:'probe',data:'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='})}).then(r=>r.text()).then(console.log)"
ls -la blender/renders/probe.png
```
Expected: Server druckt `OK probe`, die Datei hat 70 Bytes. Danach `rm blender/renders/probe.png`.

- [ ] **Step 6: README ergänzen**

An `README.md` anhängen:
```markdown
## Sichtprüfung der Szene

1. Dev-Server starten (`cd app && npm run dev -- --port 5199`) und http://localhost:5199 öffnen.
2. `node tools/schuss-server.mjs` im Repo-Wurzelverzeichnis starten.
3. Inhalt von `tools/render-posen.js` in die Browser-Konsole einfügen. Die neun Bilder
   liegen danach in `blender/renders/p_*.png` (nicht versioniert).
4. Weltboxen einzelner Objekte: `blender --background --python blender/frage_szene.py -- <Name>`.
```

- [ ] **Step 7: Commit**

```bash
git add blender/frage_szene.py tools/schuss-server.mjs tools/render-posen.js README.md
git commit -m "chore(werkzeuge): AABB-Abfrage, Bildempfaenger und Posen-Renderskript"
git push origin main
```

---

### Task 1: Industriefarben und Wandsockel

**Files:**
- Modify: `blender/blockout.py:331-346` (Farbkonstanten), `:351-383` (Materialien), `:451-470` (`wand_mit_fenster`, Relief-Sockel)
- Modify: `app/src/szene.js:12` (nur falls die Belichtung nachgezogen werden muss, siehe Step 5)

**Interfaces:**
- Consumes: `material(name, farbe, rauheit=0.85, metall=0.0)` (`blockout.py:94`)
- Produces: neues Material `m_sockel`; geänderte Konstanten `BLAU`, `ORANGE`, `MARKIERUNG`, `GRUEN`, `GRAU_OBJEKT`, `WAND_RELIEF`. Spätere Aufgaben verwenden `m_sockel` nicht; sie verwenden die bestehenden Materialnamen unverändert.

- [ ] **Step 1: Erwartung festhalten (Sichtvergleich)**

Vor der Änderung Renders ziehen (Task 0, Schritte 3-4) und die Dateien umbenennen:
```bash
for f in blender/renders/p_*.png; do cp "$f" "${f%.png}_vorher.png"; done
```

- [ ] **Step 2: Farbkonstanten auf RAL-nahe Industrietöne setzen**

In `blender/blockout.py` die Zeilen 331-346 so ändern (nur die genannten Zeilen, Reihenfolge beibehalten):

```python
GRAU_GLEISZONE = (0.48, 0.50, 0.52)
GRAU_WAND = (0.80, 0.79, 0.76)
GRAU_OBJEKT = (0.72, 0.73, 0.72)      # RAL 7035 Lichtgrau, leicht gedeckt: Maschinen- und Geraetegrau
GRAU_DUNKEL = (0.29, 0.30, 0.32)
STAHL = (0.55, 0.57, 0.60)
FENSTER = (0.87, 0.91, 0.96)
BLAU = (0.10, 0.33, 0.56)             # RAL 5010 Enziablau, der Maschinenlack der Werkstatt
ORANGE = (0.89, 0.35, 0.13)           # RAL 2004 Reinorange, Faesser und Warnkoerper
MARKIERUNG = (0.95, 0.72, 0.05)       # RAL 1023 Verkehrsgelb, Bodenmarkierung und Rammschutz
STAHL_HELL = (0.85, 0.86, 0.88)
GRUEN = (0.12, 0.33, 0.26)            # RAL 6005 Moosgruen, Schweissschutzwaende
GRUBE = (0.09, 0.10, 0.11)
ROT_ZUG = (0.72, 0.12, 0.16)
WEISS_ZUG = (0.90, 0.90, 0.91)
WAND_RELIEF = (0.62, 0.61, 0.58)
DECKE = (0.84, 0.83, 0.81)
SOCKEL = (0.44, 0.45, 0.45)           # RAL 7037 Staubgrau: abwaschbarer Wandsockel
```

- [ ] **Step 3: Sockelmaterial anlegen und Sockelband auf 1.2 m ziehen**

Nach Zeile 370 (`m_decke = material("Decke", DECKE)`) einfügen:
```python
m_sockel = material("Sockel", SOCKEL, rauheit=0.75)
```

In `wand_mit_fenster` (Zeilen 451-470) die beiden Sockel-Zeilen ersetzen. Aus
```python
        kasten(f"Relief_{seite}_Sockel", laenge, 0.08, 0.4, cx, 0.2, cz + (-0.2 if cz > 0 else 0.2), m_relief)
```
wird
```python
        # Abwaschbarer Sockelanstrich bis 1.2 m: die kraeftigste Horizontale jeder Werkstattwand
        kasten(f"Relief_{seite}_Sockel", laenge, 0.08, 1.2, cx, 0.6, cz + (-0.2 if cz > 0 else 0.2), m_sockel)
```
und im `else`-Zweig aus
```python
        kasten(f"Relief_{seite}_Sockel", 0.08, laenge, 0.4, cx + 0.2, 0.2, cz, m_relief)
```
wird
```python
        kasten(f"Relief_{seite}_Sockel", 0.08, laenge, 1.2, cx + 0.2, 0.6, cz, m_sockel)
```

Die Pilaster (`Relief_{seite}_Pilaster_{i}`, 3.3 m hoch ab y 0.1) bleiben; der Sockel liegt mit z-Versatz 0.2 vor der Wand und schneidet die Pilaster (0.14 tief bei 0.2) genau an, das ist gewollt.

- [ ] **Step 4: Bauen, Prüfer, Weltbox des Sockels**

Run: Bauen und Prüfer (Kommandos oben).
Expected: kein `SCHWEBT`, `13 Durchdringungen gesamt`, `0 Kollisionen`.

Run:
```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/frage_szene.py -- Relief_Nord_Sockel 2>/dev/null | sed -n '/AABB-ANFANG/,/AABB-ENDE/p'
```
Expected: `Relief_Nord_Sockel|-17.000,0.000,-9.840|17.000,1.200,-9.760`.

- [ ] **Step 5: Renders vergleichen und Belichtung nachziehen**

Renders ziehen (Task 0) und `p_totale.png` neben `p_totale_vorher.png` legen. Die dunkleren Blau- und Grüntöne senken die Gesamthelligkeit leicht. Mittlere Helligkeit messen:
```bash
node -e "
const fs=require('fs');const zlib=require('zlib');
function hell(p){const b=fs.readFileSync(p);let pos=8,idat=[],w=0,h=0;while(pos<b.length){const len=b.readUInt32BE(pos),typ=b.toString('ascii',pos+4,pos+8);if(typ==='IHDR'){w=b.readUInt32BE(pos+8);h=b.readUInt32BE(pos+12);}if(typ==='IDAT')idat.push(b.subarray(pos+8,pos+8+len));pos+=12+len;}
const raw=zlib.inflateSync(Buffer.concat(idat));const bpp=4;let s=0,n=0;for(let y=0;y<h;y++){const z=y*(w*bpp+1)+1;for(let x=0;x<w;x+=7){const i=z+x*bpp;s+=(raw[i]+raw[i+1]+raw[i+2])/3;n++;}}return s/n;}
console.log('vorher',hell('blender/renders/p_totale_vorher.png').toFixed(1),'nachher',hell('blender/renders/p_totale.png').toFixed(1));"
```
Expected: `nachher` liegt höchstens 6 Einheiten (von 255) unter `vorher`. Liegt er tiefer, in `app/src/szene.js:12` `renderer.toneMappingExposure = 0.92` auf `0.98` setzen und erneut messen. (Die PNGs sind ungefiltert mit Farbtyp RGBA exportiert; das Messskript setzt Filtertyp 0 voraus, den `canvas.toDataURL` in Chromium liefert. Meldet es Unsinn wie NaN, Vergleich per Auge.)

- [ ] **Step 6: Tests und Commit**

Run: `cd app && npm test --silent` Expected: `40 passed`.

```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json app/src/szene.js
git commit -m "feat(szene): Industriefarben (RAL-nah) und 1.2-m-Wandsockel statt Pastellpalette"
git push origin main
```

---

### Task 2: Gleis bündig im Werkstattboden

**Files:**
- Modify: `blender/blockout.py:413-416` (Gleiszonen), `:601-611` (Schienen, Schwellen), `:612-619` (Grube), `:432-434` (Ölflecken), Fahrleitung-Block (suche `Fahrleitung_Schiene`), Dachbrücken-Block (suche `Dachbruecke_`), Ende des Zugabschnitts (vor der Zeile `# ---- Dacharbeitsbuehnen, Kranbahn, Rollgerueste`)

**Interfaces:**
- Produces: Konstante `GLEIS_SENKUNG = 0.143` und einen Nachlauf, der alle Meshes mit Namenspräfix `Triebzug_` um `-GLEIS_SENKUNG` in y verschiebt. Spätere Aufgaben, die Zugteile mit absoluten y-Werten anlegen (Task 5, Task 8), müssen ihre Objekte VOR diesem Nachlauf erzeugen, damit sie mitwandern; der Nachlauf steht unmittelbar vor `# ---- Dacharbeitsbuehnen`.

Hintergrund: Schienenoberkante (SO) liegt heute bei y 0.155, der Hallenboden bei 0.000, die Gleiszonenplatten bei 0.040. Ziel: SO 0.012 (Schienenkopf 6 mm über einer 6 mm dünnen Gleiszonen-Deckschicht), keine Schwellen, Grubenwände bündig mit 0.000, der Zug um 0.143 abgesenkt. Die Fahrleitung wird nicht verschoben, sondern ihre Hänger werden verlängert (sonst hängen sie 14 cm unter der Dachrippe in der Luft). Die Klappbrücken der Dacharbeitsbühne bleiben am Bühnenscharnier und werden steiler geneigt, damit ihr Ende weiterhin auf der Dachkrone aufsetzt.

- [ ] **Step 1: Erwartung vor der Änderung messen (muss FEHLSCHLAGEN)**

Run:
```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/frage_szene.py -- Gleis_Schiene_Nord Triebzug_Korpus Triebzug_Rad_0_0_nord Grube_Wand_Nord Halle_Gleiszone_Ost 2>/dev/null | sed -n '/AABB-ANFANG/,/AABB-ENDE/p'
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/frage_szene.py -- --alle 2>/dev/null | sed -n '/AABB-ANFANG/,/AABB-ENDE/p' > /tmp/aabb_vorher.txt
```
Expected heute: `Gleis_Schiene_Nord` max y 0.155, `Triebzug_Korpus` min y 0.950, `Grube_Wand_Nord` max y 0.060, `Halle_Gleiszone_Ost` max y 0.040. Zielwerte nach der Aufgabe: 0.012 / 0.807 / 0.000 / 0.006.

- [ ] **Step 2: Schienen absenken, Schwellen entfernen**

Zeilen 601-611 ersetzen durch:
```python
# ---- Gleis + Untersuchungsgrube ---------------------------------------------
# Flachbodengleis: in einer Instandhaltungshalle liegen die Schienen BUENDIG im
# Boden (Schienenkopf 6 mm ueber der Deckschicht), ohne Schotter und ohne
# sichtbare Schwellen. Vorher lag die Schienenoberkante 15.5 cm ueber dem Boden
# auf Schwellen wie auf freier Strecke.
SCHIENE_OK = 0.012
kasten("Gleis_Schiene_Nord", 38, 0.15, 0.15, 2, SCHIENE_OK - 0.075, -0.7, m_schiene, fase=0)
kasten("Gleis_Schiene_Sued", 38, 0.15, 0.15, 2, SCHIENE_OK - 0.075, 0.7, m_schiene, fase=0)
# Vorfeld-Platte hinter dem Tor, damit das Gleis nicht im Nichts endet
kasten("Tor_Vorfeld", 5.0, 5.0, 0.2, 19.5, -0.1, 0, m_gleiszone, fase=0)
```

- [ ] **Step 3: Gleiszonen als 6-mm-Deckschicht, Grube bündig**

Zeilen 413-416 ersetzen:
```python
kasten("Halle_Gleiszone_West", 10, 3.6, 0.006, -12, 0.003, 0, m_gleiszone, fase=0)
kasten("Halle_Gleiszone_Ost", 17, 3.6, 0.006, 8.5, 0.003, 0, m_gleiszone, fase=0)
kasten("Halle_Gleiszone_GrubeNord", 7, 0.8, 0.006, -3.5, 0.003, -1.4, m_gleiszone, fase=0)
kasten("Halle_Gleiszone_GrubeSued", 7, 0.8, 0.006, -3.5, 0.003, 1.4, m_gleiszone, fase=0)
```

Zeilen 613-618 (Grubenwände und Querstege) ersetzen:
```python
kasten("Grube_Wand_Nord", 7, 0.1, 0.70, -3.5, -0.35, -0.95, m_grube, fase=0)   # Oberkante 0.000
kasten("Grube_Wand_Sued", 7, 0.1, 0.70, -3.5, -0.35, 0.95, m_grube, fase=0)
kasten("Grube_Wand_West", 0.1, 1.8, 0.70, -6.95, -0.35, 0, m_grube, fase=0)
kasten("Grube_Wand_Ost", 0.1, 1.8, 0.70, -0.05, -0.35, 0, m_grube, fase=0)
kasten("Grube_Quersteg_1", 0.4, 1.9, 0.04, -5.3, -0.015, 0, m_stahl, fase=0)   # Gitterrost buendig
kasten("Grube_Quersteg_2", 0.4, 1.9, 0.04, -1.8, -0.015, 0, m_stahl, fase=0)
```

Ölflecken auf der Gleiszone (Zeilen 432-433): `0.046` durch `0.012` ersetzen:
```python
zylinder("Oelfleck_1", 0.28, 0.012, -4.5, 0.012, 1.5, m_oelfleck)
zylinder("Oelfleck_2", 0.33, 0.012, 5.5, 0.012, -1.2, m_oelfleck)
```

Gelbe Gleiszonen-Randlinien (Zeilen 426-427, `Halle_Markierung_Nord` und `_Sued`): sie liegen heute bei y 0.045 (Unterkante 0.035, also 3.5 cm über dem Hallenboden). In beiden Zeilen `0.045` durch `0.012` ersetzen (Unterkante 0.002).

- [ ] **Step 4: Zug absenken (Nachlauf)**

Unmittelbar VOR der Zeile `# ---- Dacharbeitsbuehnen, Kranbahn, Rollgerueste` einfügen:
```python
# Der Zug steht auf der Schiene: mit dem Flachbodengleis rueckt ALLES, was
# Triebzug_ heisst, um die Senkung der Schienenoberkante nach unten. Ein Nachlauf
# statt hunderter geaenderter y-Literale; wer Zugteile anlegt, tut das VOR dieser
# Zeile, damit sie mitwandern.
GLEIS_SENKUNG = 0.155 - SCHIENE_OK
for _o in bpy.data.objects:
    if _o.type == "MESH" and _o.name.startswith("Triebzug_"):
        _o.matrix_world = Matrix.Translation((0, 0, -GLEIS_SENKUNG)) @ _o.matrix_world
```
(`Matrix` ist in `blockout.py` bereits importiert; prüfen mit `grep -n "from mathutils import" blender/blockout.py`, sonst `from mathutils import Matrix, Vector, Euler` am Dateianfang ergänzen.)

- [ ] **Step 5: Fahrleitung tiefer hängen, Klappbrücken steiler neigen**

Im Fahrleitungsblock (suche `kasten("Fahrleitung_Schiene"`) die vier Zeilen so ändern:
```python
kasten("Fahrleitung_Schiene", 21, 0.08, 0.12, -1, 4.26 - GLEIS_SENKUNG, 0, m_stahl, fase=0)
for i, s in enumerate((-1, 1)):
    kasten(f"Fahrleitung_Horn_{i}", 0.6, 0.08, 0.06, -1 + s * 10.75, 4.31 - GLEIS_SENKUNG, 0, m_stahl, fase=0,
           drehung=(0, s * 0.25, 0))
for i, hx in enumerate((-10, -4, 2, 8)):   # zwischen den Dachbindern
    zylinder(f"Fahrleitung_Haenger_{i}", 0.025, 1.72 + GLEIS_SENKUNG, hx, 5.18 - GLEIS_SENKUNG / 2, 0, m_stahl)
    zylinder(f"Fahrleitung_Isolator_{i}", 0.06, 0.16, hx, 4.40 - GLEIS_SENKUNG, 0, m_objekt)
```
`GLEIS_SENKUNG` muss vor allen Verwendern definiert sein: die Zeile `GLEIS_SENKUNG = 0.155 - SCHIENE_OK` direkt unter `SCHIENE_OK = 0.012` (Step 2, Zeile ~605) einfügen und im Nachlauf aus Step 4 die Doppeldefinition entfernen. Der Fahrleitungsblock liegt hinter dem Nachlauf (Abschnitt Dacharbeitsbühnen, ab Zeile ~1269); er verwendet die Konstante, wird aber NICHT verschoben, weil sein Name nicht mit `Triebzug_` beginnt.

Vollständigkeit des Nachlaufs prüfen (alle Zugteile müssen mitwandern, auch später angelegte):
```bash
grep -c '^Triebzug_' /tmp/aabb_nachher.txt
diff /tmp/aabb_vorher.txt /tmp/aabb_nachher.txt | grep -c '^> Triebzug_'
```
Expected: beide Zahlen gleich (heute 468). Sind sie ungleich, liegt ein `Triebzug_*`-Objekt hinter dem Nachlauf im Skript; es mit `diff` + `grep -v` finden und den Nachlauf ans Ende des Zugabschnitts verschieben.

Im Dachbrückenblock (suche `kasten(f"Dachbruecke_`) die Brücke ändern. Heute:
```python
        kasten(f"Dachbruecke_{'n' if s < 0 else 's'}_{i}", 1.25, 1.2, 0.05, bx, 3.15, s * 1.69,
               m_riffel, fase=0, drehung=(-s * 0.218, 0, 0))
```
Neu (Scharnierende bleibt auf 3.28 an der Buehne, das Zugende faellt um GLEIS_SENKUNG tiefer):
```python
        kasten(f"Dachbruecke_{'n' if s < 0 else 's'}_{i}", 1.25, 1.2, 0.05, bx, 3.08, s * 1.71,
               m_riffel, fase=0, drehung=(-s * 0.343, 0, 0))
```

- [ ] **Step 6: Bauen, Erwartung prüfen, Regressionsdiff**

Run: Bauen (Kommando oben), dann
```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/frage_szene.py -- Gleis_Schiene_Nord Triebzug_Korpus Triebzug_Rad_0_0_nord Grube_Wand_Nord Halle_Gleiszone_Ost Fahrleitung_Haenger_0 Dachbruecke_n_0 2>/dev/null | sed -n '/AABB-ANFANG/,/AABB-ENDE/p'
```
Expected:
```
Dachbruecke_n_0|...|... (max y 3.305 +-0.01, min y 2.85 +-0.02)
Fahrleitung_Haenger_0|-10.025,4.177,-0.025|-9.975,6.040,0.025
Gleis_Schiene_Nord|-17.000,-0.138,-0.775|21.000,0.012,-0.625
Grube_Wand_Nord|-7.000,-0.700,-1.000|0.000,0.000,-0.900
Halle_Gleiszone_Ost|0.000,0.000,-1.800|17.000,0.006,1.800
Triebzug_Korpus|-6.500,0.807,-1.200|7.500,2.557,1.200
Triebzug_Rad_0_0_nord|...,-0.008,...|...,0.792,...
```

Regressionsdiff: welche Objekte haben sich bewegt?
```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/frage_szene.py -- --alle 2>/dev/null | sed -n '/AABB-ANFANG/,/AABB-ENDE/p' > /tmp/aabb_nachher.txt
diff /tmp/aabb_vorher.txt /tmp/aabb_nachher.txt | grep '^>' | cut -d'|' -f1 | sed 's/^> //' | sed -E 's/_[0-9]+.*$//' | sort | uniq -c | sort -rn
```
Expected: nur Präfixe `Triebzug`, `Gleis`, `Halle_Gleiszone`, `Grube`, `Oelfleck`, `Fahrleitung`, `Dachbruecke`. Taucht ein anderes Präfix auf, ist das ein Fehler in Step 4 (falscher Namensfilter).

- [ ] **Step 7: Prüfer, verbliebene Schweber beheben**

Run: Prüfer. Expected: kein `SCHWEBT`, `13 Durchdringungen gesamt`, `20 Routen, 0 ungeloest`, `0 Kollisionen`.

Meldet der Prüfer `SCHWEBT` für ein Objekt der Gleiszone (Kandidaten: `Kabelbruecke`, `Pylone_*`, `Servicewagen_*`, `Signal_*`), stand es auf der alten Deckschicht (0.040) und hängt jetzt 3.4 cm hoch: dessen y-Literal um `0.034` verringern und Step 6 wiederholen. Meldet er `Dachbruecke_*`, die Neigung aus Step 5 nachrechnen: Scharnierende y = 3.08 + 0.6 * sin(0.343) = 3.282, Zugende y = 3.08 - 0.202 = 2.878; die Dachkrone liegt bei |z| 1.145 nach der Senkung auf 2.705, das Brueckenende darf hoechstens 0.08 darueber liegen. Passt es nicht, `3.08` auf `3.03` und `0.343` auf `0.36` setzen und erneut messen.

- [ ] **Step 8: Sichtprüfung, Tests, Commit**

Renders ziehen; in `p_hero_bahnsteig.png` und `p_totale.png` liegen die Schienen im Boden, keine Schwellen, der Zug sitzt tiefer, die Klappbrücken enden auf dem Dach.

Run: `cd app && npm test --silent` Expected: `40 passed`.

```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json
git commit -m "feat(szene): Flachbodengleis — Schienen buendig im Werkstattboden, Zug und Fahrleitung abgesenkt"
git push origin main
```

---

### Task 3: Lichtbänder statt Kegelleuchten

**Files:**
- Modify: `blender/blockout.py:535-541` (Kegel-Hängelampen)

**Interfaces:**
- Consumes: `kasten`, `zylinder`, `m_stahlhell`, `m_fenster`, `m_dunkel`; Dachrippen `Dach_Rippe_{i}` bei z = -9 + 1.8 i, Unterkante y 6.04 (`blockout.py:493`)
- Produces: Objekte `Lichtband_{zi}_{xi}`, `Lichtband_{zi}_{xi}_wanne`, `Lichtband_{zi}_{xi}_haenger_{k}`; die Objekte `Lampe_*` entfallen.

- [ ] **Step 1: Erwartung vor der Änderung (muss FEHLSCHLAGEN)**

Run:
```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/frage_szene.py -- Lichtband_ Lampe_0_schirm 2>/dev/null | sed -n '/AABB-ANFANG/,/AABB-ENDE/p'
```
Expected heute: eine Zeile `Lampe_0_schirm|...`, keine `Lichtband_`-Zeile. Nach der Aufgabe: zwölf `Lichtband_*`-Zeilen plus Wannen und Hänger, keine `Lampe_`-Zeile.

- [ ] **Step 2: Kegelleuchten durch Lichtbänder ersetzen**

Zeilen 535-541 (Kommentar `# Kegel-Haengelampen` bis `Lampe_{i}_seil`) ersetzen durch:
```python
# Lichtbaender statt Pendel-Kegel: eine Instandhaltungshalle wird mit durchgehenden
# Leuchtenbaendern unter den Dachbindern beleuchtet. Vier Reihen auf den Rippen
# 2/4/6/8 (z +-5.4, +-1.8), je drei Baender a 7 m; die Luecke bei x -12.9 haelt
# die Kranbahnbruecke (y 4.47..5.09) frei, die Reihen +-1.8 halten die
# Fahrleitungshaenger auf z 0 frei.
for zi, lz in enumerate((-5.4, -1.8, 1.8, 5.4)):
    for xi, lx in enumerate((-8.0, 0.0, 8.0)):
        kasten(f"Lichtband_{zi}_{xi}", 7.0, 0.18, 0.10, lx, 4.95, lz, m_stahlhell, fase=0.01)
        kasten(f"Lichtband_{zi}_{xi}_wanne", 6.8, 0.12, 0.02, lx, 4.89, lz, m_fenster, fase=0)
        for k, hx in enumerate((lx - 3.0, lx + 3.0)):
            zylinder(f"Lichtband_{zi}_{xi}_haenger_{k}", 0.012, 1.04, hx, 5.52, lz, m_dunkel)  # 5.00..6.04
```

- [ ] **Step 3: Bauen und Erwartung prüfen**

Run: Bauen, dann die Abfrage aus Step 1.
Expected: `Lichtband_1_1|-3.500,4.900,-1.890|3.500,5.000,-1.710`, `Lichtband_1_1_haenger_0|-3.012,5.000,-1.812|-2.988,6.040,-1.788`, keine `Lampe_`-Zeile.

- [ ] **Step 4: Prüfer und Sichtprüfung**

Run: Prüfer. Expected: kein `SCHWEBT` (die Hänger enden exakt an der Rippenunterkante 6.04), `13 Durchdringungen gesamt`, `0 Kollisionen`.

Renders: in `p_totale.png` und `p_hero_kranbahn.png` laufen helle Bänder parallel zur Halle; kein Band kreuzt die Kranbrücke bei x -12.9. Steht ein Band im Bild vor dem Zugkopf (Totale), ist das die Reihe z 1.8 bei x 8: gewollt, sie liegt 1.9 m über dem Dach.

- [ ] **Step 5: Tests und Commit**

Run: `cd app && npm test --silent` Expected: `40 passed`.

```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json
git commit -m "feat(szene): Lichtbaender unter den Dachbindern statt Kegel-Haengeleuchten"
git push origin main
```

---

### Task 4: Hallenboden mit Dehnfugen-Raster und Bodenmarkierungen

**Files:**
- Modify: `blender/blockout.py` (suche `Halle_Markierung_Nord`; Block der Bodenmarkierungen)

**Interfaces:**
- Consumes: `kasten`, `m_markierung`, `m_dunkel`
- Produces: Objekte `Bodenfuge_x_{i}`, `Bodenfuge_z_{i}`, `Sicherheitsabstand_{seite}` (gelbe 10-cm-Linie 1.0 m neben der Gleiszone)

Hintergrund: Der Boden trägt heute eine Noise-Textur (4-m-Kachel) und zwei gelbe Gleiszonen-Randlinien. Echte Hallenböden haben ein Plattenraster mit Dehnfugen (typisch 5 m) und eine gelbe Sicherheitslinie im Abstand zum Lichtraum. Fugen sind 1 cm breite, 3 mm eingelassene Streifen; sie werden als dunkle Kästen 2 mm ÜBER dem Boden gelegt (eine echte Vertiefung würde die Bodenplatte durchbrechen).

- [ ] **Step 1: Erwartung (muss FEHLSCHLAGEN)**

Run: `frage_szene.py -- Bodenfuge_ Sicherheitsabstand_`
Expected heute: keine Zeile. Danach: 6 `Bodenfuge_x`, 3 `Bodenfuge_z`, 2 `Sicherheitsabstand_`.

- [ ] **Step 2: Fugen und Sicherheitslinien anlegen**

Direkt nach der Zeile mit `kasten("Halle_Markierung_Sued"` einfügen:
```python
# Plattenraster mit Dehnfugen (5-m-Raster) und gelbe Sicherheitslinie 1.0 m neben der
# Gleiszone: der Hallenboden liest sonst als eine einzige Betonflaeche.
for i, fx in enumerate((-15.0, -10.0, -5.0, 5.0, 10.0, 15.0)):
    for seite, z0, z1 in (("n", -9.85, -1.9), ("s", 1.9, 9.85)):
        kasten(f"Bodenfuge_x_{i}_{seite}", 0.012, z1 - z0, 0.002, fx, 0.001, (z0 + z1) / 2, m_dunkel, fase=0)
for i, fz in enumerate((-7.0, -4.0, 4.0, 7.0)):
    kasten(f"Bodenfuge_z_{i}", 34.0, 0.012, 0.002, 0, 0.001, fz, m_dunkel, fase=0)
for seite, sz in (("nord", -2.8), ("sued", 2.8)):
    kasten(f"Sicherheitsabstand_{seite}", 30.0, 0.10, 0.002, 0, 0.001, sz, m_markierung, fase=0)
```
Die Fugen enden bei |z| 1.9, damit sie nicht in die Gleiszone (|z| bis 1.8) laufen; die Fugen in z-Richtung meiden die Gleiszone durch ihre Lage (|z| 4 und 7). Die Fuge bei x -5 kreuzt das Meisterbüro nicht (Büro x -12.5..-8.5) und die Fuge bei x 5 läuft unter Maschine_Nord_1 (x 5.0) durch, das ist unsichtbar und erlaubt.

- [ ] **Step 3: Bauen, Prüfer, Erwartung**

Run: Bauen; Prüfer. Expected: kein `SCHWEBT`, `13 Durchdringungen gesamt` (die Fugen sind 2 mm dünn; Objekte, die darauf stehen, überlappen sie zu weniger als 35 Prozent ihrer Höhe), `0 Kollisionen`.

Run: `frage_szene.py -- Bodenfuge_x_0_n Sicherheitsabstand_nord`
Expected: `Bodenfuge_x_0_n|-15.006,0.000,-9.850|-14.994,0.002,-1.900`, `Sicherheitsabstand_nord|-15.000,0.000,-2.850|15.000,0.002,-2.750`.

- [ ] **Step 4: Sichtprüfung, Tests, Commit**

Renders: in `p_totale.png` ist das Plattenraster als feine dunkle Linien lesbar, die gelbe Linie läuft beidseits parallel zum Gleis. Sind die Fugen aus der Totale unsichtbar, `0.012` auf `0.02` erhöhen (nicht dicker als 2 cm).

Run: `cd app && npm test --silent` Expected: `40 passed`.

```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json
git commit -m "feat(szene): Dehnfugen-Raster und Sicherheitslinien auf dem Hallenboden"
git push origin main
```

---

### Task 5: Drehgestelle, Medienstelen, Kenney-Fasen

**Files:**
- Modify: `blender/blockout.py` Drehgestellblock (suche `Triebzug_DG_{i}_rahmen_`), Medienstelen (`:1323-1325`), `lade_asset` (`:268-306`), glTF-Exportaufruf (suche `bpy.ops.export_scene.gltf(`)

**Interfaces:**
- Consumes: Nachlauf `GLEIS_SENKUNG` aus Task 2 (die Drehgestellobjekte heißen `Triebzug_*` und wandern mit)
- Produces: Objekte `Triebzug_DG_{i}_achsdeckel_{seite}_{j}`; `lade_asset` erhält den Parameter `fase=0.012` (Meter, Weltmaß) und setzt einen Bevel-Modifier; der Export bekommt `export_apply=True`.

- [ ] **Step 1: Erwartung (muss FEHLSCHLAGEN)**

Run: `frage_szene.py -- Triebzug_DG_0_achsdeckel_nord_0 Medienstele_n_0 Triebzug_DG_0_rahmen_nord`
Expected heute: kein Achsdeckel; `Medienstele_n_0` z -1.610..-1.390; `Triebzug_DG_0_rahmen_nord` Höhe 0.15 (max y - min y).
Danach: Achsdeckel vorhanden bei |z| 1.170..1.200; Medienstele z -2.010..-1.790; Rahmenhöhe 0.12.

- [ ] **Step 2: Drehgestellrahmen schlanker, Achsdeckel ergänzen**

Im Drehgestellblock die Rahmenzeile
```python
        kasten(f"Triebzug_DG_{i}_rahmen_{seite}", 2.3, 0.16, 0.15, bx, 0.875, s * 0.98, m_stahl)
```
ersetzen durch
```python
        # Schlanker Langtraeger, die Raeder bleiben darunter sichtbar (vorher las das
        # Drehgestell aus der Seitenansicht als ein Balken)
        kasten(f"Triebzug_DG_{i}_rahmen_{seite}", 2.3, 0.14, 0.12, bx, 0.905, s * 0.98, m_stahl)
```
und in der inneren Schleife (nach der Zeile mit `Triebzug_DG_{i}_achslager_{seite}_{j}`) ergänzen:
```python
            kasten(f"Triebzug_DG_{i}_achslager_{seite}_{j}", 0.3, 0.34, 0.24, bx + rx, 0.55, s * 1.0, m_stahl)
            zylinder(f"Triebzug_DG_{i}_achsdeckel_{seite}_{j}", 0.09, 0.03, bx + rx, 0.55, s * 1.185, m_stahlhell, achse="z", ecken=32)
```
(Die bestehende Achslager-Zeile mit `m_unterflur` wird durch die obige mit `m_stahl` ersetzt.)

- [ ] **Step 3: Medienstelen aus dem Lichtraum**

Zeilen 1323-1325: `s * 1.5` in beiden `kasten`-Zeilen durch `s * 1.9` ersetzen, `s * 1.63` in der `zylinder`-Zeile durch `s * 2.03`. Kommentar darüber ergänzen: `# 0.7 m vom Wagenkasten: 0.2 m waeren im Lichtraum des Fahrzeugs`.

- [ ] **Step 4: Fase für Kenney-Assets**

In `lade_asset` die Signatur um `fase=0.012` erweitern:
```python
def lade_asset(datei, name, x, y, z, dreh_y=0.0, ziel_hoehe=None, ziel_breite=None, einfaerbung=None, fase=0.012):
```
und direkt vor `return anker` einfügen:
```python
    if fase:
        # Gleiche Kantensprache wie die gefasten Kaesten der Szene. Die Breite ist ein
        # Weltmass; die Meshes haengen unter einem skalierten Anker, daher /faktor.
        for o in meshes:
            mod = o.modifiers.new("Fase", "BEVEL")
            mod.width = fase / faktor
            mod.segments = 2
            mod.limit_method = "ANGLE"
            mod.angle_limit = 0.61
```
Beim Exportaufruf `bpy.ops.export_scene.gltf(` das Argument `export_apply=True` ergänzen (sonst exportiert glTF die Modifier nicht). Prüfen, dass das Argument noch nicht gesetzt ist: `grep -n "export_apply" blender/blockout.py`.

- [ ] **Step 5: Bauen, Erwartung, Prüfer**

Run: Bauen; Abfrage aus Step 1. Expected: `Triebzug_DG_0_achsdeckel_nord_0|...,-1.200|...,-1.170` (y um 0.407 nach der Senkung aus Task 2), `Medienstele_n_0|...,-2.010|...,-1.790`, Rahmenhöhe 0.120.

Run: Prüfer. Expected: kein `SCHWEBT` (Medienstelen stehen auf dem Boden, Achsdeckel sitzen am Achslager), `13 Durchdringungen gesamt`, `0 Kollisionen`. Meldet der Prüfer `Medienstele_*` gegen `Absperrpfosten_*` oder `Rollgeruest_*`: die Stele um 0.3 in x verschieben (`gx` in der Aufzählung `(-6.2, -3.5, -0.8)` um 0.3 erhöhen).

- [ ] **Step 6: Sichtprüfung der Fasen**

Renders: in `p_meisterbuero.png` und `p_besprechung.png` haben Tisch, Stühle und Schrank weiche Kanten wie die Kästen daneben. Zeigen Kenney-Meshes Risse oder dunkle Streifen (Bevel auf N-Gons), `mod.segments = 1` setzen; bleibt es, `fase=0` für das betroffene Asset im Aufruf setzen.

- [ ] **Step 7: Tests und Commit**

Run: `cd app && npm test --silent` Expected: `40 passed`.

```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json
git commit -m "feat(szene): Drehgestelle mit Achsdeckeln, Medienstelen aus dem Lichtraum, Fasen an Kenney-Assets"
git push origin main
```

---

### Task 6: Meisterbüro mit Fensterrahmen, Fensterbank und Türschwelle

**Files:**
- Modify: `blender/blockout.py` Meisterbüroblock (suche `Station_1_buerofenster`)

**Interfaces:**
- Consumes: `kasten`, `m_relief`, `m_stahlhell`, `m_dunkel`; Bürokasten `Station_1_meisterbuero` x -12.5..-8.5, z -9.0..-6.0, Ostfläche x -8.5; Fenster bei z -8.1 (1.4 x 0.9, Mitte y 1.9), Tür bei z -6.6 (0.8 x 1.9)
- Produces: Objekte `Station_1_fensterrahmen_{o,u,l,r}`, `Station_1_fensterbank`, `Station_1_tuerschwelle`

- [ ] **Step 1: Erwartung (muss FEHLSCHLAGEN)**

Run: `frage_szene.py -- Station_1_fensterrahmen_ Station_1_fensterbank Station_1_tuerschwelle`
Expected heute: keine Zeile. Danach: vier Rahmenleisten, eine Fensterbank, eine Schwelle.

- [ ] **Step 2: Rahmen, Bank und Schwelle anlegen**

Nach der Zeile `kasten("Station_1_tuerklinke", ...)` einfügen:
```python
# Fenster und Tuer waren aufgesetzte Platten: ein Rahmen aus vier Leisten (5 mm vor
# dem Glas, damit er sichtbar bleibt), eine Fensterbank und eine Tuerschwelle geben
# der Buerowand die Tiefe eines gebauten Raums.
for kennung, dz, dy, y, z in (("o", 1.52, 0.06, 2.38, -8.1), ("u", 1.52, 0.06, 1.42, -8.1),
                              ("l", 0.06, 0.9, 1.9, -8.83), ("r", 0.06, 0.9, 1.9, -7.37)):
    kasten(f"Station_1_fensterrahmen_{kennung}", 0.05, dz, dy, -8.435, y, z, m_relief, fase=0)
kasten("Station_1_fensterbank", 0.12, 1.6, 0.04, -8.44, 1.37, -8.1, m_stahlhell, fase=0)
kasten("Station_1_tuerschwelle", 0.10, 0.9, 0.03, -8.44, 0.015, -6.6, m_dunkel, fase=0)
```
Rechnung: Glas `Station_1_buerofenster` liegt bei x -8.47 mit dx 0.06 (Vorderkante -8.44); die Rahmenleisten bei x -8.435 mit dx 0.05 (Vorderkante -8.41) stehen 3 cm davor. Fensterbank Vorderkante -8.38, Schwelle Vorderkante -8.39; beide berühren die Wand (x -8.5) über ihre Tiefe.

- [ ] **Step 3: Bauen, Erwartung, Prüfer**

Run: Bauen; Abfrage aus Step 1.
Expected: `Station_1_fensterrahmen_o|-8.460,2.350,-8.860|-8.410,2.410,-7.340`, `Station_1_fensterbank|-8.500,1.350,-8.900|-8.380,1.390,-7.300`, `Station_1_tuerschwelle|-8.490,0.000,-7.050|-8.390,0.030,-6.150`.

Run: Prüfer. Expected: kein `SCHWEBT`, `13 Durchdringungen gesamt`, `0 Kollisionen`. Die Schwelle liegt auf dem Fußweg `Halle_Weg_Nord_W` (z -7.6..-6.5, 3 cm dick): Überlappung 3 cm von 3 cm Höhe = 100 Prozent des kleineren Objekts. Meldet der Prüfer `Station_1_tuerschwelle <-> Halle_Weg_Nord_W`, die Schwelle auf y 0.045 heben (Unterkante 0.03 = Oberkante des Wegs).

- [ ] **Step 4: Sichtprüfung, Tests, Commit**

Renders: `p_meisterbuero.png` zeigt Fenster mit Rahmen und Bank, Tür mit Schwelle.

Run: `cd app && npm test --silent` Expected: `40 passed`.

```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json
git commit -m "feat(szene): Meisterbuero mit Fensterrahmen, Fensterbank und Tuerschwelle"
git push origin main
```

---

### Task 7: Kabelwege und Anschlusskästen an Terminal und Prüfstand

**Files:**
- Modify: `blender/blockout.py` Terminalblock (suche `Station_3_bodenplatte`), Prüfstandblock (suche `Station_5_kabel`, `Station_5_anschluss`)

**Interfaces:**
- Consumes: `rohr_mit_bogen(name, punkte, radius, mat)` (`blockout.py:307`), `kasten`, `zylinder`; Nordwand-Kabelkanal `Nordwand_Kabelkanal` bei z -9.8, y 1.43..1.57; Südwand-Innenseite z 9.85; Fußweg `Halle_Weg_Nord_O` z -7.6..-6.5
- Produces: `Station_3_kabel`, `Station_3_kabelbruecke`, `Station_5_kabel` (neuer Verlauf), `Station_5_anschluss_tuer`, `Station_5_notaus`, `Station_5_anschluss_schild`

- [ ] **Step 1: Erwartung (muss FEHLSCHLAGEN)**

Run: `frage_szene.py -- Station_3_kabel Station_5_notaus Station_5_anschluss_tuer`
Expected heute: keine Zeile. Danach drei Objekte (plus `Station_3_kabel_seg_*`, da `rohr_mit_bogen` Segmente erzeugt).

- [ ] **Step 2: Terminalkabel mit Kabelbrücke über den Fußweg**

Nach `kasten("Station_3_bodenplatte", ...)` einfügen:
```python
# Das Terminal haengt am Nordwand-Kabelkanal: Kabel am Boden nach Norden, ueber den
# Fussweg mit gelber Kabelbruecke (Stolperkante), an der Wand hoch in den Kanal.
rohr_mit_bogen("Station_3_kabel", [(7.0, 0.03, -4.55), (7.0, 0.03, -9.7), (7.0, 1.43, -9.76)], 0.02, m_dunkel)
kasten("Station_3_kabelbruecke", 0.5, 1.2, 0.05, 7.0, 0.025, -7.05, m_markierung, fase=0.015)
```

- [ ] **Step 3: Prüfstandkabel mit Bodenlauf und Schaltkasten**

Die Zeile
```python
rohr_mit_bogen("Station_5_kabel", [(1.3, 0.1, 6.9), (1.2, 0.1, 8.6), (1.2, 0.45, 9.6)], 0.04, m_dunkel)
```
ersetzen durch
```python
# Kabel laeuft am Boden zur Wand und dort senkrecht in den Schaltkasten (vorher eine
# starre Schraege frei durch den Raum)
rohr_mit_bogen("Station_5_kabel", [(1.3, 0.06, 6.9), (1.2, 0.06, 9.72), (1.2, 0.55, 9.76)], 0.04, m_dunkel)
```
und nach `kasten("Station_5_anschluss", 0.5, 0.15, 0.7, 1.2, 0.9, 9.78, m_objekt)` ergänzen:
```python
# Schaltkasten mit Tuerblatt, Not-Aus und gegreektem Schild statt Verbandkasten
kasten("Station_5_anschluss_tuer", 0.42, 0.02, 0.6, 1.2, 0.9, 9.695, m_stahlhell, fase=0)
zylinder("Station_5_notaus", 0.04, 0.03, 1.32, 1.15, 9.68, m_zug, achse="z", ecken=32)
kasten("Station_5_anschluss_schild", 0.14, 0.01, 0.05, 1.1, 1.15, 9.68, m_markierung, fase=0)
```
Rechnung: Kasten `Station_5_anschluss` liegt bei z 9.78 mit dz 0.15 (9.705..9.855), berührt die Wand (9.85). Tür bei 9.695 mit dz 0.02 (9.685..9.705) sitzt davor. Not-Aus und Schild bei z 9.68 mit Tiefe 0.03/0.01 stehen vor der Tür.

- [ ] **Step 4: Bauen, Erwartung, Prüfer**

Run: Bauen; Abfrage aus Step 1.
Expected: `Station_5_notaus|1.280,1.110,9.665|1.360,1.190,9.695`, `Station_5_anschluss_tuer|0.990,0.600,9.685|1.410,1.200,9.705`, mindestens eine Zeile `Station_3_kabel`.

Run: Prüfer. Expected: kein `SCHWEBT`, `13 Durchdringungen gesamt`, `0 Kollisionen`. Meldet der Prüfer `Station_3_kabelbruecke <-> Station_3_kabel_seg_*` mit über 35 Prozent: gewollt (das Kabel liegt in der Brücke), dann wächst die Liste auf 14 und dieser Eintrag ist als gewollt in `blender/pruefe_geometrie.py` neben den anderen gewollten Paaren einzutragen (dort existiert keine Ausnahmeliste, die Liste im Commit-Text wird auf 14 aktualisiert).

- [ ] **Step 5: Sichtprüfung, Tests, Commit**

Renders: `p_terminal.png` zeigt das Kabel vom Sockel nach hinten und die gelbe Brücke auf dem Fußweg; `p_pruefstand.png` den Schaltkasten mit rotem Not-Aus.

Run: `cd app && npm test --silent` Expected: `40 passed`.

```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json
git commit -m "feat(szene): Kabelwege mit Kabelbruecke am Terminal, Schaltkasten mit Not-Aus am Pruefstand"
git push origin main
```

---

### Task 8 (optional): Wagenkasten im ICE-Verhältnis (2.23 m breit)

**Files:**
- Modify: `blender/blockout.py` Nachlauf aus Task 2 (vor `# ---- Dacharbeitsbuehnen`), Dachbrückenblock

**Interfaces:**
- Consumes: Nachlauf `GLEIS_SENKUNG`; alle `Triebzug_*`-Objekte
- Produces: Konstante `ZUG_BREITENFAKTOR = 2.23 / 2.40`; alle `Triebzug_*`-Objekte werden um diesen Faktor in z (quer) um die Gleisachse gestaucht.

Stoppregel: Diese Aufgabe nur ausführen, wenn Tasks 1-7 committet sind und der Nutzer sie freigibt; sie verändert die Silhouette des abgenommenen Kopfes um 7 Prozent in der Breite. Die Stauchung ist ein reversibler Nachlauf, keine Änderung von Literalen.

- [ ] **Step 1: Erwartung (muss FEHLSCHLAGEN)**

Run: `frage_szene.py -- Triebzug_Korpus Triebzug_Rad_0_0_nord`
Expected heute: `Triebzug_Korpus` z -1.200..1.200; Rad z -0.840..-0.720. Danach: Korpus z -1.115..1.115; Rad z -0.780..-0.669.

- [ ] **Step 2: Stauchung im Nachlauf**

Den Nachlauf aus Task 2 ersetzen durch:
```python
GLEIS_SENKUNG = 0.155 - SCHIENE_OK
ZUG_BREITENFAKTOR = 2.23 / 2.40   # ICE 4: Hoehe zu Breite 1.36 statt 1.26
for _o in bpy.data.objects:
    if _o.type == "MESH" and _o.name.startswith("Triebzug_"):
        # Blender-y ist three.js-(-z): Stauchung quer zur Gleisachse um z = 0
        _o.matrix_world = (Matrix.Translation((0, 0, -GLEIS_SENKUNG))
                           @ Matrix.Diagonal((1.0, ZUG_BREITENFAKTOR, 1.0, 1.0))
                           @ _o.matrix_world)
```

- [ ] **Step 3: Dachbrücken nachführen**

Das Zugende der Klappbrücken landet jetzt bei |z| 1.145 * 0.929 = 1.064; die Brücke aus Task 2 Step 5 um 0.08 nach innen: `s * 1.71` durch `s * 1.63` ersetzen.

- [ ] **Step 4: Bauen, Erwartung, Prüfer, Sichtprüfung**

Run: Bauen; Abfrage aus Step 1. Expected wie in Step 1 genannt.
Run: Prüfer. Expected: kein `SCHWEBT`, `13 Durchdringungen gesamt`, `0 Kollisionen`. Meldet der Prüfer `Medienstele_*` oder `Dachbruecke_*`, greifen die Abstände aus Task 5 bzw. Step 3 nicht; Werte nachmessen und korrigieren.
Renders: in `p_totale.png` und `p_hero_bahnsteig.png` wirkt der Zug höher und schlanker; das Logo bleibt lesbar.

- [ ] **Step 5: Tests und Commit**

Run: `cd app && npm test --silent` Expected: `40 passed`.

```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json
git commit -m "feat(szene): Wagenkasten auf 2.23 m gestaucht — Hoehe zu Breite 1.36 wie ICE 4"
git push origin main
```

---

## Selbstprüfung des Plans

- Spec-Abdeckung: Jeder Befund B1-B10 hat eine Aufgabe (Tabelle oben). Die Gestaltungsregeln (Greek, feste Posen, keine Schweber, CC0) sind als Global Constraints gefasst; keine Aufgabe fügt Schrift, Zahlen oder Fremdassets hinzu.
- Platzhalter: keine "TBD"-Schritte; jede Änderung steht als Code mit Zahlen, jede Prüfung mit Kommando und erwarteter Ausgabe.
- Typkonsistenz: `SCHIENE_OK`, `GLEIS_SENKUNG`, `ZUG_BREITENFAKTOR`, `m_sockel`, `SOCKEL` werden dort definiert, wo sie zuerst gebraucht werden (Task 2 Step 2/5, Task 8, Task 1); `frage_szene.py` liefert in allen Aufgaben dasselbe Zeilenformat `Name|min|max`.
