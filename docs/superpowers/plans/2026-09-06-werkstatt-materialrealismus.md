# Werkstatt ohne Comic-Look: Material-, Licht- und Detailrealismus — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Werkstatthalle liest in allen neun Posen als fotografierte Instandhaltungshalle statt als Spielzeug-Diorama: strukturierte Oberflächen, Gebrauchsspuren, Kontaktschatten, glaubwürdiges Tageslicht, entsättigte und variierte Lackfarben, Requisiten mit Detail.

**Architecture:** Zwei Baustellen, die zusammen wirken. (1) Im Viewer (`app/src`) kommen eine Postprocessing-Kette mit Ambient Occlusion (GTAO), ein neu abgestimmtes Licht und ein Himmelsverlauf dazu. (2) Im Szenengenerator (`blender/blockout.py`) werden prozedural erzeugte PBR-Texturen (Albedo, Rauheit, Normal) für Boden, Gleiszone, Wand und Lack angelegt, die Palette wird entsättigt und variiert, der Zuglack bekommt Klarlack, Schienen werden zweiteilig (blanker Kopf, rostiger Fuß), Decals für Öl, Fahrspuren und Abrieb kommen dazu, und die auffälligsten Primitiv-Requisiten (Fässer, Paletten, Schläuche) erhalten Detail. Alle Texturen entstehen im Bauskript mit dem vorhandenen reinen Python-PNG-Schreiber — keine Downloads, keine Lizenzfragen.

**Tech Stack:** three.js 0.180 (EffectComposer, RenderPass, GTAOPass, OutputPass aus `three/addons`), Vite 7, Vitest; Blender 5.2 headless, glTF-Exporter (KHR_materials_clearcoat, KHR_materials_emissive_strength, metallicRoughnessTexture, normalTexture); Node 20 für `tools/`.

**Spec:** Es gibt keine eigene Spec; bindend bleiben `docs/superpowers/specs/2026-08-25-werkstattrundgang-praesentation-design.md` (Gestaltungsregeln, feste Posen, Greek-Regel) und der Befund in Abschnitt "Ausgangsbefund" unten, der aus den Renders `blender/renders/p_*.png` (Stand fcf3c39) und dem Code abgeleitet ist.

## Global Constraints

- Sprache Deutsch, Ton sachlich; Schrift im Overlay Arial; alles graustufentauglich; Kopfzeile "DB Intern / DB internal" (Spec §1, Briefing Abschnitt 7). Overlay und Panels werden von diesem Plan nicht angefasst.
- Keine erfundenen Zahlen. Keine lesbaren Ziffern, Buchstaben oder Logos in der Szene; alle Anschriften bleiben "gegreekt". Einzige Ausnahme: das DB-Logo am Zugkopf. Texturen dürfen keine Schrift enthalten.
- Die sieben Kameraposen in `app/src/stationen.json` sind per Juryentscheid fest. Sichtprobleme werden über Geometrie, Material und Licht gelöst, nie über Kamerabewegung. Kamera-FOV bleibt 50.
- Nichts schwebt: `pruefe_geometrie.py` meldet jedes Objekt ohne Nachbarn näher als 0.08 m. Die bekannte Durchdringungsliste hat seit Commit 60637bb genau **11** Einträge und darf nicht wachsen. Decals (Öl, Fahrspuren) liegen 2 mm über dem Boden und dürfen deshalb nie mehr als 2 mm hoch sein.
- Alle 20 Kamerarouten aus `berechne_fahrtwege.py` müssen lösbar bleiben (`0 ungeloest`), `pruefe_flugpfade.py` muss `0 Kollisionen` melden. Der Prüfer liest ohne Postprocessing; er bleibt unverändert.
- Nur CC0-Assets. Neue Texturen werden ausschließlich prozedural im Bauskript erzeugt (`schreibe_*_png`), keine Bilddateien aus dem Netz.
- Der Zugkopf (`fuehrerstand()`) bleibt geometrisch unangetastet; Materialänderungen (Klarlack, Entsättigung) sind erlaubt, weil sie alle Zugflächen gleich betreffen.
- `app/public/szene.glb` bleibt unter 8 MB (heute 6.36 MB). Texturbudget dieses Plans: höchstens 1.4 MB zusätzlich; Texturen als PNG 8 Bit RGB, Kantenlänge 1024 nur für Albedo des Bodens, sonst 512.
- Nach jeder Aufgabe: Prüfer grün, `npm test` grün (heute 40 Tests; neue Tests kommen dazu, die Zahl steigt), Commit und Push auf `main`.
- Der Viewer muss mit Postprocessing auf dem Präsentationsrechner flüssig bleiben: Zielwert mittlere Bildzeit ≤ 16.7 ms bei 1920×1080 und Pixel-Ratio ≤ 2; fällt sie über 25 ms, schaltet die AO automatisch ab (Task 1). `?ao=0` in der URL erzwingt das Abschalten.
- Koordinaten in `blockout.py`: three.js-Konvention, x längs (Ost positiv), y hoch, z quer. `kasten(name, dx, dz, dy, x, y, z, mat, drehung=None, fase=0.02)` nimmt Länge x, Tiefe z, Höhe y. `zylinder(name, radius, laenge, x, y, z, mat, achse="y", ecken=16, fase=0.0)`. Blender-intern ist (x, y, z)_three = (x, −z, y)_blender. Bauen: `"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/blockout.py`; Weltboxen: `blender/frage_szene.py -- <Namen|--alle>` (Ausgabe `Name|minx,miny,minz|maxx,maxy,maxz` zwischen `AABB-ANFANG`/`AABB-ENDE`); Prüfer: `blender/pruefe_alles.py`; Renders: Dev-Server `rundgang-dev` (Port 5199), `node tools/schuss-server.mjs` (Port 5198), Snippet `tools/render-posen.js` in der Browserkonsole.
- Der Prüfer und `frage_szene.py` führen `blockout.py` per `exec` aus. Neue Hilfsmodule unter `blender/` müssen deshalb über `sys.path` importiert werden (Task 2 zeigt wie), und der Export bleibt der einzige `bpy.ops.export_scene.gltf(`-Aufruf.

## Ausgangsbefund (warum es nach Comic aussieht)

Aus `p_totale.png`, `p_pruefstand.png`, `p_meisterbuero.png`, `p_hero_kranbahn.png` (Stand fcf3c39) und dem Code:

1. **Flache Einheitsfarben auf großen Flächen.** Wand fast weiß mit kaum sichtbarer Struktur (`gen_wand.png`, 256 px, Spannweite 7), Boden eine wolkige Value-Noise-Kachel (256 px auf 4 m = 1.6 cm/px, ohne Plattenstruktur), Zug reinweiß mit 25 % Metalness (liest als Kunststoff). Kein Material erzählt Gebrauch.
2. **Keine Kontaktschatten.** Alles steht "aufgeklebt" auf dem Boden (Prüfstand, Fässer, Stapler): der Viewer hat keine Ambient Occlusion, das Hemisphärenlicht (0.55) und das Ambientlicht (0.3) füllen jede Fuge auf.
3. **Gesättigte, makellose Akzentfarben in identischem Ton.** 53 Objekte in `m_blau`, 45 in `m_orange`, 37 in `m_markierung`, alle exakt gleich — Spielzeugpalette. Echte Hallen haben Chargenunterschiede, Ausbleichen, Kratzer, Staub.
4. **Konstante Rauheit pro Material.** Ohne Rauheitsvariation spiegelt die RoomEnvironment jede Fläche gleichmäßig; Lack, Beton und Stahl unterscheiden sich nur in einem Zahlenwert.
5. **Kontrastarmes Licht.** Sonne 1.5 aus (12, 20, 8), Fülllicht 0.4, Belichtung 0.92: weiche Schatten, keine hellen Lichtinseln, die Fenster zeigen die Hintergrundfarbe als flache Fläche, die Oberlichter leuchten nicht.
6. **Primitive Requisiten.** Fass = Zylinder, Palette = Platte, Kiste = Quader, keine Schläuche, Kabel, Lappen; nur drei Ölflecken, keine Fahrspuren, keine Abnutzung an Markierungen und Schienen.
7. **Schienen aus einem Material.** Der ganze Schienenquerschnitt ist "blank" — real ist nur der Kopf blank, Steg und Fuß sind rostbraun.

Die Reihenfolge der Aufgaben folgt der Wirkung pro Aufwand: erst Licht und AO im Viewer (wirkt auf alles), dann Oberflächenstruktur, dann Gebrauchsspuren, dann Farben, dann Requisitendetail.

## File Structure

- Create: `tools/glb-info.mjs` — liest eine .glb ohne Abhängigkeiten, gibt Materialien (PBR-Felder, Texturzuweisungen, Erweiterungen), Bildanzahl und -größen, Gesamtgröße aus; Verifikationswerkzeug für alle Blender-Aufgaben.
- Create: `app/tests/glb-info.test.js` — testet den Parser gegen `app/public/szene.glb`.
- Create: `app/src/komposition.js` — baut die Render-Kette (EffectComposer mit RenderPass, GTAOPass, OutputPass), liest den AO-Schalter aus der URL, misst Bildzeiten und schaltet AO bei Überlast ab. Exportiert `leseAoSchalter(search)`, `erzeugeKomposition(renderer, szene, kamera, optionen)`.
- Create: `app/tests/komposition.test.js` — testet Schalterlogik, Rückfallpfad ohne AO und die Überlast-Abschaltung mit Stub-Renderer.
- Modify: `app/src/szene.js` — Lichtabstimmung, Himmelsverlauf als Hintergrund (`erzeugeHimmelTextur()`), Env-Intensität.
- Modify: `app/src/main.js` — Render-Schleife über `komposition.render()`, Resize weiterreichen, Dev-Global `window.__komposition`.
- Modify: `tools/render-posen.js` — rendert über `window.__komposition.render()` statt `rn.render`.
- Create: `blender/texturen.py` — prozedurale Texturgeneratoren: `fbm(u, v, oktaven, seed)`, `schreibe_pbr_set(basispfad, ...)` (Albedo, Rauheit, Normal), `schreibe_lackrauheit_png`, `schreibe_markierung_png`.
- Modify: `blender/blockout.py` — `material_pbr(...)`, Materialdefinitionen, Palette, Klarlack, Schienen zweiteilig, Decals, Requisiten-Helfer `fass()`, `palette()`, `schlauch()`, Tageslichtmaterial.
- Modify: `README.md` — Abschnitt "Sichtprüfung": AO-Schalter, glb-info.

---

### Task 0: Verifikationswerkzeug `glb-info` und Vorher-Renders

**Files:**
- Create: `tools/glb-info.mjs`
- Create: `app/tests/glb-info.test.js`
- Modify: `README.md` (Abschnitt "Sichtprüfung der Szene", eine Zeile)

**Interfaces:**
- Produces: `node tools/glb-info.mjs <pfad.glb> [--json]` druckt pro Material eine Zeile `NAME | base=R,G,B | metal=M rough=R | tex=baseColor,metallicRoughness,normal,emissive | ext=KHR_...` sowie `images: N (bytes gesamt)`, `extensionsUsed: [...]`, `size: N bytes`; mit `--json` das Objekt `{materials:[{name, baseColorFactor, metallicFactor, roughnessFactor, textures:{baseColor,metallicRoughness,normal,emissive}, extensions:[...], alphaMode}], images:[{name, mimeType, bytes}], extensionsUsed, size}`. Exportiert `liesGlbInfo(buffer)` für den Test.
- Später konsumiert von Task 2, 3, 4, 6 (Erwartungen an Texturen, Erweiterungen, Größe).

- [ ] **Step 1: Test schreiben (muss FEHLSCHLAGEN)**

`app/tests/glb-info.test.js`:
```js
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { liesGlbInfo } from '../../tools/glb-info.mjs';

const hier = dirname(fileURLToPath(import.meta.url));
const glb = readFileSync(join(hier, '..', 'public', 'szene.glb'));

describe('glb-info', () => {
  it('liest Materialien, Bilder und Erweiterungen aus der Szene', () => {
    const info = liesGlbInfo(glb);
    expect(info.size).toBe(glb.length);
    expect(info.materials.length).toBeGreaterThan(30);
    const leuchte = info.materials.find((m) => m.name === 'Leuchte');
    expect(leuchte).toBeDefined();
    expect(leuchte.extensions).toContain('KHR_materials_emissive_strength');
    expect(info.images.length).toBeGreaterThanOrEqual(4);
    expect(info.images.every((b) => b.bytes > 0)).toBe(true);
  });
  it('weist einem texturierten Material seine Bildreferenz zu', () => {
    const info = liesGlbInfo(glb);
    const boden = info.materials.find((m) => m.name === 'Boden');
    expect(boden.textures.baseColor).toBeTypeOf('number');
  });
});
```

- [ ] **Step 2: Test laufen lassen**

Run: `cd app && npx vitest run tests/glb-info.test.js`
Expected: FAIL — `Cannot find module '../../tools/glb-info.mjs'`.

- [ ] **Step 3: Werkzeug schreiben**

`tools/glb-info.mjs`:
```js
// tools/glb-info.mjs — Materialien, Texturen und Erweiterungen einer .glb ohne Abhaengigkeiten.
// Aufruf: node tools/glb-info.mjs app/public/szene.glb [--json]
import { readFileSync } from 'node:fs';

const TEXTURFELDER = {
  baseColor: (m) => m.pbrMetallicRoughness?.baseColorTexture?.index,
  metallicRoughness: (m) => m.pbrMetallicRoughness?.metallicRoughnessTexture?.index,
  normal: (m) => m.normalTexture?.index,
  emissive: (m) => m.emissiveTexture?.index,
};

export function liesGlbInfo(buffer) {
  const b = Buffer.isBuffer(buffer) ? buffer : Buffer.from(buffer);
  if (b.readUInt32LE(0) !== 0x46546c67) throw new Error('keine glb-Datei (Magic fehlt)');
  const jsonLaenge = b.readUInt32LE(12);
  const json = JSON.parse(b.subarray(20, 20 + jsonLaenge).toString('utf8'));
  const bin = b.subarray(20 + jsonLaenge + 8);
  const views = json.bufferViews || [];
  const images = (json.images || []).map((img, i) => {
    const v = views[img.bufferView];
    return { name: img.name || `image_${i}`, mimeType: img.mimeType, bytes: v ? v.byteLength : 0 };
  });
  const textures = json.textures || [];
  const materials = (json.materials || []).map((m) => {
    const pbr = m.pbrMetallicRoughness || {};
    const tex = {};
    for (const [feld, lies] of Object.entries(TEXTURFELDER)) {
      const idx = lies(m);
      tex[feld] = idx === undefined ? null : textures[idx]?.source ?? null;
    }
    return {
      name: m.name,
      baseColorFactor: pbr.baseColorFactor || [1, 1, 1, 1],
      metallicFactor: pbr.metallicFactor ?? 1,
      roughnessFactor: pbr.roughnessFactor ?? 1,
      textures: tex,
      extensions: Object.keys(m.extensions || {}),
      alphaMode: m.alphaMode || 'OPAQUE',
    };
  });
  void bin;
  return { materials, images, extensionsUsed: json.extensionsUsed || [], size: b.length };
}

function formatiere(info) {
  const zeilen = info.materials.map((m) => {
    const base = m.baseColorFactor.slice(0, 3).map((c) => c.toFixed(2)).join(',');
    const tex = Object.entries(m.textures).filter(([, v]) => v !== null).map(([k]) => k).join(',') || '-';
    return `${m.name} | base=${base} | metal=${m.metallicFactor.toFixed(2)} rough=${m.roughnessFactor.toFixed(2)} | tex=${tex} | alpha=${m.alphaMode} | ext=${m.extensions.join(',') || '-'}`;
  });
  const bildBytes = info.images.reduce((s, i) => s + i.bytes, 0);
  zeilen.push(`images: ${info.images.length} (${bildBytes} bytes)`);
  zeilen.push(`extensionsUsed: ${info.extensionsUsed.join(', ') || '-'}`);
  zeilen.push(`size: ${info.size} bytes`);
  return zeilen.join('\n');
}

if (process.argv[1] && import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const [pfad, flag] = process.argv.slice(2);
  if (!pfad) { console.error('Aufruf: node tools/glb-info.mjs <datei.glb> [--json]'); process.exit(2); }
  const info = liesGlbInfo(readFileSync(pfad));
  console.log(flag === '--json' ? JSON.stringify(info, null, 2) : formatiere(info));
}
```
Hinweis für Windows: Der `import.meta.url`-Vergleich muss mit `C:/...`-Pfaden funktionieren; prüfen mit `node tools/glb-info.mjs app/public/szene.glb | tail -3`. Druckt er nichts, den Vergleich durch `process.argv[1].endsWith('glb-info.mjs')` ersetzen.

- [ ] **Step 4: Test laufen lassen**

Run: `cd app && npx vitest run tests/glb-info.test.js`
Expected: PASS (2 Tests). Danach `npm test --silent` → `42 passed`.

- [ ] **Step 5: Vorher-Renders sichern und README**

Run (Bash): `for f in blender/renders/p_*.png; do case "$f" in *_vorher*|*_v2vorher*) ;; *) cp "$f" "${f%.png}_v2vorher.png";; esac; done; ls blender/renders/*_v2vorher.png | wc -l`
Expected: 9 (die sieben Jury-Posen plus zwei Hero-Bilder; existieren weniger, zuerst mit `tools/render-posen.js` rendern).

README, Abschnitt "Sichtprüfung der Szene", neue Zeile: `5. Materialien und Texturen der glb: \`node tools/glb-info.mjs app/public/szene.glb\` (mit \`--json\` maschinenlesbar).`

- [ ] **Step 6: Commit**

```bash
git add tools/glb-info.mjs app/tests/glb-info.test.js README.md
git commit -m "chore(werkzeuge): glb-info liest Materialien, Texturen und Erweiterungen der Szene"
git push origin main
```

---

### Task 1: Viewer — Ambient Occlusion, Lichtabstimmung, Himmelsverlauf

**Files:**
- Create: `app/src/komposition.js`
- Create: `app/tests/komposition.test.js`
- Modify: `app/src/szene.js` (`erzeugeRenderer`, `erzeugeSzene`, neu `erzeugeHimmelTextur`)
- Modify: `app/src/main.js` (Schleife, Resize, Dev-Global)
- Modify: `tools/render-posen.js`

**Interfaces:**
- Produces: `leseAoSchalter(search: string): boolean` (`'?ao=0'` → false, sonst true); `erzeugeKomposition(renderer, szene, kamera, { ao = true, jetzt = () => performance.now(), aoAbschaltenAb = 25, messfenster = 120 } = {})` → `{ render(): void, setSize(w, h): void, get aoAktiv(): boolean, mittlereBildzeit(): number }`. Ohne AO ruft `render()` direkt `renderer.render(szene, kamera)`; mit AO baut es einmalig `EffectComposer(renderer)` mit `RenderPass`, `GTAOPass(szene, kamera, w, h)` und `OutputPass`. Nach jeweils `messfenster` Bildern wird die mittlere Bildzeit gebildet; liegt sie über `aoAbschaltenAb` ms, wird AO dauerhaft abgeschaltet (`console.info('AO abgeschaltet: mittlere Bildzeit X ms')`).
- `erzeugeHimmelTextur(): THREE.DataTexture` — 1×64 Pixel vertikaler Verlauf von Zenit `#b9c6d4` zu Horizont `#e8ecef`, `colorSpace = SRGBColorSpace`, `magFilter = LinearFilter`; wird `szene.background`.
- Dev-Global: `window.__komposition` (nur wenn `import.meta.env.DEV`, neben den bestehenden `__szene/__kamera/__renderer`).

- [ ] **Step 1: Tests schreiben (müssen FEHLSCHLAGEN)**

`app/tests/komposition.test.js`:
```js
import { describe, it, expect, vi } from 'vitest';
import { leseAoSchalter, erzeugeKomposition } from '../src/komposition.js';

function stubRenderer() {
  return { render: vi.fn(), getSize: (v) => v.set(1600, 900), domElement: {}, capabilities: {} };
}

describe('leseAoSchalter', () => {
  it('ist standardmäßig an', () => { expect(leseAoSchalter('')).toBe(true); });
  it('lässt sich per ao=0 abschalten', () => { expect(leseAoSchalter('?ao=0')).toBe(false); });
  it('akzeptiert ao=1 ausdrücklich', () => { expect(leseAoSchalter('?x=1&ao=1')).toBe(true); });
});

describe('erzeugeKomposition ohne AO', () => {
  it('rendert direkt über den Renderer', () => {
    const r = stubRenderer();
    const k = erzeugeKomposition(r, {}, {}, { ao: false });
    k.render();
    expect(r.render).toHaveBeenCalledTimes(1);
    expect(k.aoAktiv).toBe(false);
  });
});

describe('Überlast-Abschaltung', () => {
  it('schaltet AO ab, wenn die mittlere Bildzeit über der Schwelle liegt', () => {
    let t = 0;
    const jetzt = () => { t += 40; return t; }; // 40 ms pro Bild
    const r = stubRenderer();
    const composer = { render: vi.fn(), setSize: vi.fn() };
    const k = erzeugeKomposition(r, {}, {}, { ao: true, jetzt, messfenster: 5, aoAbschaltenAb: 25, _composerFabrik: () => composer });
    for (let i = 0; i < 6; i += 1) k.render();
    expect(k.aoAktiv).toBe(false);
    expect(r.render).toHaveBeenCalled();
    expect(k.mittlereBildzeit()).toBeGreaterThan(25);
  });
  it('behält AO bei schnellen Bildern', () => {
    let t = 0;
    const jetzt = () => { t += 8; return t; };
    const composer = { render: vi.fn(), setSize: vi.fn() };
    const k = erzeugeKomposition(stubRenderer(), {}, {}, { ao: true, jetzt, messfenster: 5, _composerFabrik: () => composer });
    for (let i = 0; i < 12; i += 1) k.render();
    expect(k.aoAktiv).toBe(true);
    expect(composer.render).toHaveBeenCalledTimes(12);
  });
});
```

- [ ] **Step 2: Tests laufen lassen**

Run: `cd app && npx vitest run tests/komposition.test.js`
Expected: FAIL — Modul `../src/komposition.js` fehlt.

- [ ] **Step 3: `app/src/komposition.js` schreiben**

```js
// app/src/komposition.js — Render-Kette mit Ambient Occlusion (GTAO) und Ueberlastschutz.
// Ohne AO (URL ?ao=0 oder Ueberlast) rendert die Kette direkt ueber den Renderer.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

export function leseAoSchalter(search) {
  const wert = new URLSearchParams(search || '').get('ao');
  return wert !== '0';
}

function baueComposer(renderer, szene, kamera) {
  const groesse = renderer.getSize(new THREE.Vector2());
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(szene, kamera));
  const gtao = new GTAOPass(szene, kamera, groesse.x, groesse.y);
  gtao.output = GTAOPass.OUTPUT.Default;
  // Werkstattmassstab: Fugen und Fussleisten sollen dunkel werden, nicht ganze Waende.
  gtao.updateGtaoMaterial({ radius: 0.35, distanceExponent: 1.0, thickness: 1.0, scale: 1.2, samples: 12, distanceFallOff: 1.0, screenSpaceRadius: false });
  gtao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 4, radiusExponent: 1, rings: 2, samples: 16 });
  gtao.blendIntensity = 0.85;
  composer.addPass(gtao);
  composer.addPass(new OutputPass());
  return composer;
}

export function erzeugeKomposition(renderer, szene, kamera, optionen = {}) {
  const {
    ao = true,
    jetzt = () => performance.now(),
    aoAbschaltenAb = 25,
    messfenster = 120,
    _composerFabrik = () => baueComposer(renderer, szene, kamera),
  } = optionen;
  let aoAktiv = ao;
  let composer = aoAktiv ? _composerFabrik() : null;
  let zuletzt = null;
  const zeiten = [];
  let mittel = 0;

  function messe() {
    const t = jetzt();
    if (zuletzt !== null) {
      zeiten.push(t - zuletzt);
      if (zeiten.length >= messfenster) {
        mittel = zeiten.reduce((s, z) => s + z, 0) / zeiten.length;
        zeiten.length = 0;
        if (aoAktiv && mittel > aoAbschaltenAb) {
          aoAktiv = false;
          composer = null;
          console.info(`AO abgeschaltet: mittlere Bildzeit ${mittel.toFixed(1)} ms`);
        }
      }
    }
    zuletzt = t;
  }

  return {
    render() {
      messe();
      if (aoAktiv && composer) composer.render();
      else renderer.render(szene, kamera);
    },
    setSize(breite, hoehe) {
      if (composer) composer.setSize(breite, hoehe);
    },
    get aoAktiv() { return aoAktiv; },
    mittlereBildzeit() { return mittel; },
  };
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `cd app && npx vitest run tests/komposition.test.js`
Expected: PASS (6 Tests). Hinweis: Der Import von `three/addons/...` läuft unter Vitest im Node-Kontext; falls `GTAOPass` beim Import WebGL-Globals verlangt, die vier `three/addons`-Importe in `baueComposer` per dynamischem `await import()` verschieben und `erzeugeKomposition` so belassen (die Fabrik wird dann asynchron: `render()` rendert bis zur Fertigstellung direkt).

- [ ] **Step 5: Licht und Himmel in `szene.js`**

In `erzeugeRenderer`: `renderer.toneMappingExposure = 1.0;` (statt 0.92).

In `erzeugeSzene` die Licht- und Hintergrundzeilen ersetzen durch:
```js
  szene.background = erzeugeHimmelTextur();
  if (renderer) {
    const pmrem = new THREE.PMREMGenerator(renderer);
    szene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    szene.environmentIntensity = 0.45; // Reflexe auf Lack und Stahl, aber unter dem Sonnenlicht
  }
  // Weniger Fuellung, mehr Richtung: die AO (komposition.js) uebernimmt die Fugen,
  // das Hemisphaerenlicht bringt kuehlen Himmel von oben und warmen Bodenrueckschein.
  szene.add(new THREE.AmbientLight(0xffffff, 0.12));
  szene.add(new THREE.HemisphereLight(0xdfe6ee, 0x6a6560, 0.7));
  const sonne = new THREE.DirectionalLight(0xfff1e0, 2.3); // Tageslicht durch Oberlichter, leicht warm
  sonne.position.set(10, 24, 6);
  sonne.castShadow = true;
  sonne.shadow.mapSize.set(4096, 4096);
  sonne.shadow.camera.left = -24;
  sonne.shadow.camera.right = 24;
  sonne.shadow.camera.top = 24;
  sonne.shadow.camera.bottom = -24;
  sonne.shadow.camera.near = 1;
  sonne.shadow.camera.far = 70;
  sonne.shadow.bias = -0.0002;
  sonne.shadow.normalBias = 0.02;
  sonne.shadow.radius = 3;
  szene.add(sonne);
  const fuelllicht = new THREE.DirectionalLight(0xd6e2f5, 0.25); // kuehle Gegenseite, ohne Schatten
  fuelllicht.position.set(-14, 10, -10);
  szene.add(fuelllicht);
```
und die Funktion ergänzen:
```js
// Vertikaler Himmelsverlauf als Hintergrund: Fenster und Tore zeigen Himmel statt Einheitsgrau.
export function erzeugeHimmelTextur() {
  const hoehe = 64;
  const daten = new Uint8Array(hoehe * 4);
  const zenit = [0xb9, 0xc6, 0xd4];
  const horizont = [0xe8, 0xec, 0xef];
  for (let i = 0; i < hoehe; i += 1) {
    const t = i / (hoehe - 1); // 0 = unten (Horizont), 1 = oben (Zenit)
    for (let c = 0; c < 3; c += 1) daten[i * 4 + c] = Math.round(horizont[c] + (zenit[c] - horizont[c]) * t);
    daten[i * 4 + 3] = 255;
  }
  const tex = new THREE.DataTexture(daten, 1, hoehe);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.magFilter = THREE.LinearFilter;
  tex.minFilter = THREE.LinearFilter;
  tex.needsUpdate = true;
  return tex;
}
```
Bestehender Test `app/tests/kamera.test.js`/`rauchtest` bleibt grün; ergänze in `komposition.test.js` keinen WebGL-Test (jsdom hat kein WebGL).

- [ ] **Step 6: `main.js` verdrahten**

Nach `const kamera = ...`:
```js
import { erzeugeKomposition, leseAoSchalter } from './komposition.js';
const komposition = erzeugeKomposition(renderer, szene, kamera, { ao: leseAoSchalter(window.location.search) });
```
Im Resize-Handler nach `renderer.setSize(...)`: `komposition.setSize(window.innerWidth, window.innerHeight);`
In `schleife()`: `renderer.render(szene, kamera);` → `komposition.render();`
Die bestehende Dev-Zeile `if (import.meta.env.DEV) Object.assign(window, { __szene: szene, __renderer: renderer, __kamera: kamera });` (heute `main.js:185`) um `__komposition: komposition` erweitern.

`tools/render-posen.js`: `rn.render(s, k);` → `(window.__komposition ? window.__komposition.render() : rn.render(s, k));` und nach `rn.setSize(1600, 900, false);` die Zeile `if (window.__komposition) window.__komposition.setSize(1600, 900);` einfügen. Kopfkommentar um `__komposition` ergänzen.

- [ ] **Step 7: Im Browser prüfen**

Dev-Server `rundgang-dev` starten, Konsole: keine Fehler; `window.__komposition.aoAktiv` → `true`; nach 10 s `window.__komposition.mittlereBildzeit()` notieren (Erwartung auf dem Entwicklungsrechner < 16.7 ms bei 1080p; Wert in den Report). Mit `?ao=0` laden: `aoAktiv` → `false`.
Renders über `tools/render-posen.js` (alle neun) und Vergleich mit `*_v2vorher.png`: Fugen zwischen Boden und Prüfstand/Fässern/Stapler dunkel, Fenster und Tore zeigen einen Verlauf, Schatten schärfer mit weicher Kante, keine schwarzen Flecken auf Wänden (sonst `gtao.blendIntensity` auf 0.7).

- [ ] **Step 8: Tests und Commit**

Run: `cd app && npm test --silent` Expected: `48 passed`.
```bash
git add app/src/komposition.js app/tests/komposition.test.js app/src/szene.js app/src/main.js tools/render-posen.js
git commit -m "feat(viewer): Ambient Occlusion (GTAO) mit Ueberlastschutz, Lichtabstimmung, Himmelsverlauf"
git push origin main
```

---

### Task 2: Prozedurale PBR-Texturen für Boden, Gleiszone, Wand und Sockel

**Files:**
- Create: `blender/texturen.py`
- Modify: `blender/blockout.py` (Import, `material_pbr`, Materialdefinitionen `m_boden`, `m_gleiszone`, `m_wand`, `m_sockel`, `m_decke`)
- Modify: `.gitignore` (nichts; `blender/gen_*.png` bleiben versioniert, damit `frage_szene.py` ohne Erzeugung läuft — die Erzeugung ist deterministisch)

**Interfaces:**
- Produces in `texturen.py`: `fbm(u, v, gitter, oktaven, seed)` → float 0..1; `schreibe_pbr_set(basispfad, groesse, basis_rgb, spann, seed, platten=None, koernung=0, normal_staerke=1.0, rauheit_basis=0.85, rauheit_spann=0.12)` schreibt `<basispfad>_albedo.png`, `<basispfad>_rauheit.png` (Graustufe als RGB, Größe `groesse // 2`), `<basispfad>_normal.png` (Tangent-Space, Größe `groesse // 2`); `platten=(n, tint)` teilt die Kachel in n×n Platten mit je eigener Helligkeit ±tint.
- Produces in `blockout.py`: `material_pbr(name, farbe, albedo=None, rauheit_png=None, normal_png=None, rauheit=0.85, metall=0.0, kachel=2.0, normal_staerke=1.0)` — Principled BSDF mit optional Albedo (sRGB), Rauheit über `Separate Color`→G (Non-Color) und Normal Map (Non-Color); registriert `KACHEL[name] = kachel` wie `material_mit_textur`. Materialien: `m_boden` (Beton, kachel 10 mit 2×2 Platten = 5-m-Raster), `m_gleiszone` (dunkler, öliger Beton, kachel 4), `m_wand` (Putz, kachel 3, schwache Normal), `m_sockel` (Anstrich, Rauheit-Textur, kachel 2), `m_decke` (Trapezblech-Rillen in der Normal, kachel 1).
- Konsumiert von Task 3 (Rauheitstextur `gen_lack_rauheit.png` für Lacke) und Task 4.

- [ ] **Step 1: Erwartung vor der Änderung (muss FEHLSCHLAGEN)**

Run: `node tools/glb-info.mjs app/public/szene.glb | grep -E '^(Boden|Gleiszone|Wand|Sockel|Decke) '`
Expected heute: `Boden ... tex=baseColor`, `Wand ... tex=baseColor`, `Sockel ... tex=-`, kein `normal` in der Liste; `images: 5`. Danach: `Boden | ... | tex=baseColor,metallicRoughness,normal`, `Wand ... tex=baseColor,metallicRoughness,normal`, `Sockel ... tex=metallicRoughness`, `Decke ... tex=normal`; `images` ≥ 14.

- [ ] **Step 2: `blender/texturen.py` anlegen**

```python
"""Prozedurale PBR-Texturen (Albedo, Rauheit, Normal) als 8-Bit-RGB-PNG ohne Abhaengigkeiten.

Alles ist deterministisch (Seed), damit ein Bau die versionierten gen_*.png byteweise
reproduziert. Keine Schrift, keine Logos (Greek-Regel der Spec)."""
import random
import struct
import zlib


def png_speichern(pfad, breite, hoehe, zeilen):
    def chunk(typ, daten):
        return struct.pack(">I", len(daten)) + typ + daten + struct.pack(">I", zlib.crc32(typ + daten) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(zeilen, 6))
    png += chunk(b"IEND", b"")
    with open(pfad, "wb") as f:
        f.write(png)


def _gitter(g, rnd):
    return [[rnd.random() for _ in range(g + 1)] for _ in range(g + 1)]


def _wert(knoten, g, u, v):
    """Bilinear interpoliertes Value-Noise, periodisch in u und v (Kachel ohne Naht)."""
    x = (u % 1.0) * g
    y = (v % 1.0) * g
    x0, y0 = int(x) % g, int(y) % g
    fx, fy = x - int(x), y - int(y)
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    x1, y1 = (x0 + 1) % g, (y0 + 1) % g
    a = knoten[y0][x0] * (1 - fx) + knoten[y0][x1] * fx
    b = knoten[y1][x0] * (1 - fx) + knoten[y1][x1] * fx
    return a * (1 - fy) + b * fy


def fbm_feld(groesse, gitter=6, oktaven=4, seed=1):
    """Liefert eine groesse x groesse Liste von Werten 0..1 (fraktales Value-Noise)."""
    rnd = random.Random(seed)
    schichten = []
    g, amp, summe = gitter, 1.0, 0.0
    for _ in range(oktaven):
        schichten.append((_gitter(g, rnd), g, amp))
        summe += amp
        g *= 2
        amp *= 0.5
    feld = []
    for j in range(groesse):
        zeile = []
        v = j / groesse
        for i in range(groesse):
            u = i / groesse
            n = sum(_wert(k, gg, u, v) * a for k, gg, a in schichten) / summe
            zeile.append(n)
        feld.append(zeile)
    return feld


def schreibe_pbr_set(basispfad, groesse=512, basis_rgb=(120, 122, 125), spann=18, seed=1,
                     platten=None, koernung=0, normal_staerke=1.0,
                     rauheit_basis=0.85, rauheit_spann=0.12):
    """Schreibt <basispfad>_albedo.png (groesse), _rauheit.png und _normal.png (groesse//2)."""
    rnd = random.Random(seed + 101)
    feld = fbm_feld(groesse, gitter=6, oktaven=4, seed=seed)
    fein = fbm_feld(groesse, gitter=48, oktaven=2, seed=seed + 7)
    n_platten, tint = platten if platten else (1, 0)
    platten_tint = [[rnd.uniform(-tint, tint) for _ in range(n_platten)] for _ in range(n_platten)]
    fuge = max(2, groesse // 256)

    def plattenwert(i, j):
        pi, pj = i * n_platten // groesse, j * n_platten // groesse
        am_rand = n_platten > 1 and (i % (groesse // n_platten) < fuge or j % (groesse // n_platten) < fuge)
        return platten_tint[pj][pi], am_rand

    albedo = b""
    for j in range(groesse):
        zeile = b"\x00"
        for i in range(groesse):
            n = 0.7 * feld[j][i] + 0.3 * fein[j][i]
            t, rand = plattenwert(i, j)
            f = (n - 0.5) * 2 * spann + t * 255
            if rand:
                f -= 22  # Dehnfuge dunkler
            if koernung:
                f += rnd.randint(-koernung, koernung)
            zeile += bytes(max(0, min(255, int(c + f))) for c in basis_rgb)
        albedo += zeile
    png_speichern(f"{basispfad}_albedo.png", groesse, groesse, albedo)

    h = groesse // 2
    rauheit = b""
    normal = b""
    for j in range(h):
        zr = b"\x00"
        zn = b"\x00"
        for i in range(h):
            n = feld[j * 2][i * 2]
            r = rauheit_basis + (n - 0.5) * 2 * rauheit_spann + (fein[j * 2][i * 2] - 0.5) * 0.06
            g = max(0, min(255, int(r * 255)))
            zr += bytes((g, g, g))
            # Normal aus dem Hoehenfeld (zentrale Differenz), periodisch
            hx = feld[j * 2][(i * 2 + 2) % groesse] - feld[j * 2][(i * 2 - 2) % groesse]
            hy = feld[(j * 2 + 2) % groesse][i * 2] - feld[(j * 2 - 2) % groesse][i * 2]
            nx = max(-1.0, min(1.0, -hx * 4.0 * normal_staerke))
            ny = max(-1.0, min(1.0, -hy * 4.0 * normal_staerke))
            zn += bytes((int((nx * 0.5 + 0.5) * 255), int((ny * 0.5 + 0.5) * 255), 255))
        rauheit += zr
        normal += zn
    png_speichern(f"{basispfad}_rauheit.png", h, h, rauheit)
    png_speichern(f"{basispfad}_normal.png", h, h, normal)


def schreibe_rillen_normal_png(pfad, groesse=256, periode=32, tiefe=0.6):
    """Trapezblech: Rillen entlang u als Normal-Map (fuer die Hallendecke)."""
    zeilen = b""
    for j in range(groesse):
        zeile = b"\x00"
        for i in range(groesse):
            phase = (i % periode) / periode
            steig = tiefe if 0.1 < phase < 0.25 else (-tiefe if 0.6 < phase < 0.75 else 0.0)
            zeile += bytes((int((steig * 0.5 + 0.5) * 255), 128, 255))
        zeilen += zeile
    png_speichern(pfad, groesse, groesse, zeilen)


def schreibe_rauheit_png(pfad, groesse=256, basis=0.5, spann=0.25, seed=3, kratzer=0):
    """Reine Rauheitskarte (Lack mit Wolken und optional feinen Kratzern)."""
    rnd = random.Random(seed)
    feld = fbm_feld(groesse, gitter=5, oktaven=3, seed=seed)
    zeilen = b""
    for j in range(groesse):
        zeile = b"\x00"
        for i in range(groesse):
            r = basis + (feld[j][i] - 0.5) * 2 * spann
            if kratzer and rnd.random() < kratzer:
                r += 0.35
            g = max(0, min(255, int(r * 255)))
            zeile += bytes((g, g, g))
        zeilen += zeile
    png_speichern(pfad, groesse, groesse, zeilen)
```

- [ ] **Step 3: Import und `material_pbr` in `blockout.py`**

Direkt nach der Definition von `WURZEL` (oben in `blockout.py`):
```python
import sys
if os.path.join(WURZEL, "blender") not in sys.path:
    sys.path.insert(0, os.path.join(WURZEL, "blender"))
from texturen import png_speichern, schreibe_pbr_set, schreibe_rillen_normal_png, schreibe_rauheit_png  # noqa: E402
```
Den Rumpf von `_png_speichern(pfad, groesse, pixelzeilen)` in `blockout.py` durch den Einzeiler `png_speichern(pfad, groesse, groesse, pixelzeilen)` ersetzen (ein PNG-Schreiber statt zwei; `schreibe_noise_png` und `schreibe_riffelblech_png` rufen weiter `_png_speichern` auf).
Nach `material_mit_textur` einfügen:
```python
def material_pbr(name, farbe, albedo=None, rauheit_png=None, normal_png=None,
                 rauheit=0.85, metall=0.0, kachel=2.0, normal_staerke=1.0):
    """Principled BSDF mit optionalen Texturen in der Verdrahtung, die der glTF-Exporter
    als baseColorTexture / metallicRoughnessTexture (G-Kanal) / normalTexture erkennt."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*farbe, 1.0)
    bsdf.inputs["Roughness"].default_value = rauheit
    bsdf.inputs["Metallic"].default_value = metall
    if albedo:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(albedo, check_existing=True)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if rauheit_png:
        rt = nt.nodes.new("ShaderNodeTexImage")
        rt.image = bpy.data.images.load(rauheit_png, check_existing=True)
        rt.image.colorspace_settings.name = "Non-Color"
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(rt.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        bsdf.inputs["Roughness"].default_value = 1.0  # Faktor 1, die Textur traegt den Wert
    if normal_png:
        nm = nt.nodes.new("ShaderNodeTexImage")
        nm.image = bpy.data.images.load(normal_png, check_existing=True)
        nm.image.colorspace_settings.name = "Non-Color"
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = normal_staerke
        nt.links.new(nm.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    KACHEL[name] = kachel
    return mat
```

- [ ] **Step 4: Texturen erzeugen und Materialien umstellen**

Die vier `schreibe_noise_png(...)`-Aufrufe für `BODEN_PNG`, `GLEIS_PNG`, `WAND_PNG` (nicht Riffelblech) ersetzen durch:
```python
BETON = os.path.join(WURZEL, "blender", "gen_beton")
GLEISBETON = os.path.join(WURZEL, "blender", "gen_gleisbeton")
PUTZ = os.path.join(WURZEL, "blender", "gen_putz")
LACK_RAUHEIT_PNG = os.path.join(WURZEL, "blender", "gen_lack_rauheit.png")
SOCKEL_RAUHEIT_PNG = os.path.join(WURZEL, "blender", "gen_sockel_rauheit.png")
DECKE_NORMAL_PNG = os.path.join(WURZEL, "blender", "gen_decke_normal.png")
# Boden: 10-m-Kachel mit 2 x 2 Platten = 5-m-Plattenraster wie die Dehnfugen (Task 4 des Vorplans)
schreibe_pbr_set(BETON, groesse=1024, basis_rgb=(112, 113, 116), spann=16, seed=7, platten=(2, 0.035), koernung=5, normal_staerke=0.6, rauheit_basis=0.88, rauheit_spann=0.08)
schreibe_pbr_set(GLEISBETON, groesse=512, basis_rgb=(70, 71, 74), spann=20, seed=11, koernung=7, normal_staerke=0.5, rauheit_basis=0.72, rauheit_spann=0.18)
schreibe_pbr_set(PUTZ, groesse=512, basis_rgb=(204, 200, 192), spann=9, seed=5, koernung=3, normal_staerke=0.35, rauheit_basis=0.9, rauheit_spann=0.05)
schreibe_rauheit_png(LACK_RAUHEIT_PNG, groesse=256, basis=0.42, spann=0.18, seed=3, kratzer=0.004)
schreibe_rauheit_png(SOCKEL_RAUHEIT_PNG, groesse=256, basis=0.6, spann=0.2, seed=9, kratzer=0.01)
schreibe_rillen_normal_png(DECKE_NORMAL_PNG, groesse=256, periode=32, tiefe=0.6)
```
und die Materialzeilen:
```python
m_boden = material_pbr("Boden", (1, 1, 1), albedo=BETON + "_albedo.png", rauheit_png=BETON + "_rauheit.png", normal_png=BETON + "_normal.png", kachel=10.0, normal_staerke=0.6)
m_gleiszone = material_pbr("Gleiszone", (1, 1, 1), albedo=GLEISBETON + "_albedo.png", rauheit_png=GLEISBETON + "_rauheit.png", normal_png=GLEISBETON + "_normal.png", kachel=4.0, normal_staerke=0.5)
m_wand = material_pbr("Wand", (1, 1, 1), albedo=PUTZ + "_albedo.png", rauheit_png=PUTZ + "_rauheit.png", normal_png=PUTZ + "_normal.png", kachel=3.0, normal_staerke=0.35)
m_sockel = material_pbr("Sockel", SOCKEL, rauheit_png=SOCKEL_RAUHEIT_PNG, kachel=2.0)
m_decke = material_pbr("Decke", DECKE, normal_png=DECKE_NORMAL_PNG, rauheit=0.6, metall=0.2, kachel=1.0, normal_staerke=0.8)
```
Die alten `gen_boden.png`, `gen_gleiszone.png`, `gen_wand.png` löschen (`git rm`), `GLEIS_PNG`/`BODEN_PNG`/`WAND_PNG`-Konstanten entfernen (`grep -n "BODEN_PNG\|GLEIS_PNG\|WAND_PNG" blender/blockout.py` → keine Treffer außer ggf. Kommentaren). `schreibe_noise_png` bleibt, falls andere Aufrufer existieren; sonst entfernen.

- [ ] **Step 5: Bauen, Erwartung, Größe, Reproduzierbarkeit**

Run: Bauen (dauert durch 1024²-Noise in reinem Python ~60 s länger; steigt die Bauzeit über 4 Minuten, `groesse` des Bodens auf 768 senken und im Report begründen).
Run: `node tools/glb-info.mjs app/public/szene.glb | grep -E '^(Boden|Gleiszone|Wand|Sockel|Decke) |^images|^size'`
Expected: die vier Texturfelder wie in Step 1 beschrieben; `images: 14` (5 alte − 3 ersetzte + 12 neue); `size` < 7 800 000.
Run: Bauen ein zweites Mal, dann `git status --short blender/` → keine Änderung an `gen_*.png` (deterministisch).
Run: Prüfer → unverändert (kein `SCHWEBT`, `11 Durchdringungen gesamt`, `20 Routen, 0 ungeloest`, `0 Kollisionen`).

- [ ] **Step 6: Sichtprüfung**

Renders aller neun Posen. Erwartung: Boden zeigt ein 5-m-Plattenraster mit leicht unterschiedlich hellen Platten und feiner Körnung (kein Wolkenmuster mehr), im Streiflicht der Sonne eine leichte Struktur; Wand mit feinem Putzkorn statt Fläche; Sockel wolkig-satiniert; Decke mit Rillen. Keine sichtbare Kachelwiederholung in `p_totale.png` (sonst `seed`/`gitter` variieren oder `platten=(3, ...)` mit `kachel=15`).

- [ ] **Step 7: Tests und Commit**

Run: `cd app && npm test --silent` Expected: alle grün (48).
```bash
git add blender/texturen.py blender/blockout.py blender/gen_*.png app/public/szene.glb
git commit -m "feat(szene): prozedurale PBR-Texturen (Albedo, Rauheit, Normal) fuer Boden, Gleiszone, Wand, Sockel und Decke"
git push origin main
```

---

### Task 3: Gebrauchsspuren — zweiteilige Schienen, abgenutzte Markierungen, Öl und Fahrspuren

**Files:**
- Modify: `blender/blockout.py` (Gleisblock `Gleis_Schiene_*`, Materialien `m_markierung`, neue `m_schienenkopf`/`m_schienenfuss`/`m_decal_dunkel`, Decal-Helfer `decal_ellipse`, `fahrspur`)

**Interfaces:**
- Consumes: `material_pbr`, `LACK_RAUHEIT_PNG` (Task 2), `zylinder`, `kasten`
- Produces: `Gleis_Schiene_Nord_kopf`/`_fuss`, `Gleis_Schiene_Sued_kopf`/`_fuss` (ersetzen `Gleis_Schiene_Nord/Sued`), `Oelfleck_4..6`, `Fahrspur_{k}_{i}`, `Abrieb_Tor_{i}`; Material `Markierung` mit Rauheitstextur; `decal_ellipse(name, x, z, rx, rz, alpha, y_boden=0.0)` und `fahrspur(name, x0, z0, x1, z1, breite=0.24, alpha=0.32)`.

- [ ] **Step 1: Erwartung vor der Änderung (muss FEHLSCHLAGEN)**

Run: `"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/frage_szene.py -- Gleis_Schiene_Nord Oelfleck_ Fahrspur_ 2>/dev/null | sed -n '/AABB-ANFANG/,/AABB-ENDE/p'`
Expected heute: `Gleis_Schiene_Nord|-41.000,-0.138,-0.775|21.000,0.012,-0.625`, drei `Oelfleck_`-Zeilen, keine `Fahrspur_`. Danach: `Gleis_Schiene_Nord_fuss|-41.000,-0.138,-0.775|21.000,-0.028,-0.625`, `Gleis_Schiene_Nord_kopf|-41.000,-0.028,-0.735|21.000,0.012,-0.665`, sechs `Oelfleck_`, Fahrspuren vorhanden.

- [ ] **Step 2: Schienen zweiteilig**

Materialien neben `m_schiene`:
```python
m_schienenkopf = material("Schienenkopf", (0.66, 0.64, 0.60), rauheit=0.22, metall=0.9)   # blank gefahren
m_schienenfuss = material("Schienenfuss", (0.30, 0.21, 0.16), rauheit=0.95, metall=0.1)  # Flugrost an Steg und Fuss
```
Die beiden Zeilen `kasten("Gleis_Schiene_Nord", 62, 0.15, 0.15, -10, SCHIENE_OK - 0.075, -0.7, m_schiene, fase=0)` / `..._Sued ... 0.7 ...` ersetzen durch
```python
# Schiene zweiteilig: nur der Kopf (7 x 4 cm) ist blank, Steg und Fuss sind rostbraun matt
for seite, sz in (("Nord", -0.7), ("Sued", 0.7)):
    kasten(f"Gleis_Schiene_{seite}_fuss", 62, 0.15, 0.11, -10, SCHIENE_OK - 0.095, sz, m_schienenfuss, fase=0)
    kasten(f"Gleis_Schiene_{seite}_kopf", 62, 0.07, 0.04, -10, SCHIENE_OK - 0.020, sz, m_schienenkopf, fase=0.004)
```
Rechnung: Fuß y 0.012−0.095±0.055 = −0.138..−0.028; Kopf 0.012−0.020±0.02 = −0.028..0.012. `grep -rn "Gleis_Schiene_Nord\b\|Gleis_Schiene_Sued\b" blender app/src tools` → nur noch Kommentare/Prüfer-Familienlogik (Familie "Gleis" bleibt gleich). `m_schiene` entfernen, falls ohne weiteren Verwender (`grep -c m_schiene`).

- [ ] **Step 3: Markierungen mit Abrieb**

`m_markierung = material("Markierung", MARKIERUNG, rauheit=0.55, metall=0.15)` → `m_markierung = material_pbr("Markierung", (0.86, 0.66, 0.08), rauheit_png=LACK_RAUHEIT_PNG, metall=0.05, kachel=1.0)` (leicht gedecktes Verkehrsgelb; die Kratzer aus der Rauheitstextur lesen als Abrieb). `KACHEL`-UVs greifen automatisch über `_kachel_uv`.

- [ ] **Step 4: Decal-Helfer und Gebrauchsspuren**

Nach `def auffangwanne(...)`:
```python
m_decal_dunkel = material("DecalDunkel", (0.10, 0.10, 0.10), rauheit=0.5)
if hasattr(m_decal_dunkel, "blend_method"):          # Blender < 4.2
    m_decal_dunkel.blend_method = "BLEND"
if hasattr(m_decal_dunkel, "surface_render_method"):  # Blender >= 4.2 (EEVEE Next)
    m_decal_dunkel.surface_render_method = "BLENDED"


def _decal_material(alpha):
    """Eigene Materialkopie je Deckkraft, damit der Exporter alphaMode BLEND mit baseColor-Alpha schreibt."""
    name = f"DecalDunkel_{int(alpha * 100)}"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = m_decal_dunkel.copy()
        mat.name = name
        mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = alpha
    return mat


def decal_ellipse(name, x, z, rx, rz, alpha=0.6, y_boden=0.0):
    """Flacher Fleck 2 mm ueber der Unterlage (Oel, Wasser, Abrieb)."""
    zylinder(name, 1.0, 0.002, x, y_boden + 0.002, z, _decal_material(alpha), ecken=28)
    o = bpy.data.objects[name]
    o.scale = (rx, rz, o.scale.z)


def fahrspur(name, x0, z0, x1, z1, breite=0.24, alpha=0.32, y_boden=0.0):
    """Zwei dunkle Reifenspuren (Spurweite 0.9 m) entlang der Strecke (x0,z0)->(x1,z1)."""
    dx, dz = x1 - x0, z1 - z0
    laenge = (dx * dx + dz * dz) ** 0.5
    winkel = math.atan2(dz, dx)
    for i, off in enumerate((-0.45, 0.45)):
        ox, oz = -math.sin(winkel) * off, math.cos(winkel) * off
        kasten(f"{name}_{i}", laenge, breite, 0.002, (x0 + x1) / 2 + ox, y_boden + 0.001, (z0 + z1) / 2 + oz,
               _decal_material(alpha), fase=0, drehung=(0, 0, -winkel))
```
`blockout.py` importiert heute nur `random`, `struct`, `zlib`: neben `import random` die Zeile `import math` ergänzen. Drehachsen: `drehung` ist ein Blender-Euler (x, y, z)_blender; die Hochachse three-y ist Blender-z, also steht eine Drehung um die Hochachse an dritter Stelle. Weil Blender +y = three −z ist, zeigt die lange Seite eines Kastens mit `drehung=(0, 0, -winkel)` in three-Richtung `(cos winkel, sin winkel)` in der (x, z)-Ebene. Kontrolle: `Fahrspur_Stapler_0` muss laut AABB von etwa x −12.4..−6.4 und z −8.9..−4.7 reichen (Diagonale); läuft die Box stattdessen gespiegelt (z −5.7..−1.5), Vorzeichen auf `+winkel` drehen und im Report festhalten.

Gebrauchsspuren anlegen (nach den drei bestehenden `Oelfleck_*`):
```python
# Weitere Gebrauchsspuren: Oel unter Pruefstand und Fasslager, Reifenspuren des Staplers
# vom Stellplatz zur Palette und zum Osttor, Abrieb auf dem Fussweg vor der Buerotuer.
decal_ellipse("Oelfleck_4", 1.4, 5.6, 0.45, 0.30, alpha=0.55)
decal_ellipse("Oelfleck_5", -9.4, 3.1, 0.32, 0.22, alpha=0.5)
decal_ellipse("Oelfleck_6", 13.6, 8.2, 0.38, 0.26, alpha=0.5)
fahrspur("Fahrspur_Stapler", -12.0, -5.2, -6.8, -8.4)
fahrspur("Fahrspur_Tor", 8.5, 4.6, 16.4, 4.6, alpha=0.26)
decal_ellipse("Abrieb_Tuer_Buero", -8.05, -6.6, 0.55, 0.40, alpha=0.22, y_boden=0.035)  # auf Halle_Weg_Nord_W
```
Die Koordinaten liegen auf freiem Boden bzw. auf dem Fußweg; vor dem Bau mit `frage_szene.py -- --alle` prüfen, dass in den Ellipsen/Streifen kein stehendes Objekt liegt (Fahrspur_Stapler folgt der Achse Stapler_1 (−12.8, −5.2) → Requisite_Palette (−6.5, −8.6)). Trifft eine Spur ein Objekt, die Endpunkte um bis zu 0.5 m verschieben und im Report festhalten.

- [ ] **Step 5: Bauen, Erwartung, Prüfer**

Run: Bauen; Abfrage aus Step 1 plus `Abrieb_ Fahrspur_Stapler_0`. Expected: Schienenwerte wie in Step 1; `Oelfleck_4|0.950,0.002,5.300|1.850,0.004,5.900`; `Fahrspur_Stapler_0` mit Länge ≈ 6.1 m (Diagonale) und Höhe 0.000..0.002.
Run: `node tools/glb-info.mjs app/public/szene.glb | grep -E '^DecalDunkel|^Markierung|^Schienen'` Expected: `DecalDunkel_55 ... alpha=BLEND`, `Markierung ... tex=metallicRoughness`, `Schienenkopf ... metal=0.90`. Zeigt ein Decal `alpha=OPAQUE`, fehlt dem Exporter die Blend-Information: dann im Material `mat.blend_method`/`surface_render_method` prüfen und ersatzweise `mat["gltf_alpha_mode"]` nicht verwenden, sondern die Deckkraft in die Farbe backen (Farbe (0.10,0.10,0.10) → (0.28,0.28,0.29), alpha 1) — im Report als Abweichung vermerken.
Run: Prüfer. Expected: kein `SCHWEBT` (Decals liegen 2 mm auf ihrer Unterlage, min y ≤ 0.06 gilt als stehend), `11 Durchdringungen gesamt`, `20 Routen, 0 ungeloest`, `0 Kollisionen`.

- [ ] **Step 6: Sichtprüfung, Tests, Commit**

Renders: `p_pruefstand.png` — Ölfleck unter dem Prüfstand, Markierungen mit stumpfen Stellen; `p_totale.png` — Schienen mit hellem Kopf auf dunklem Fuß; `p_meisterbuero.png` — dunkler Abrieb vor der Bürotür; Fahrspuren als zwei parallele dunkle Bänder, nicht als schwarze Balken (sonst alpha −0.08).
Run: `cd app && npm test --silent` Expected: alle grün.
```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json
git commit -m "feat(szene): Gebrauchsspuren — zweiteilige Schienen, abgenutzte Markierungen, Oelflecken und Reifenspuren"
git push origin main
```

---

### Task 4: Palette entsättigen und variieren, Klarlack am Zug

**Files:**
- Modify: `blender/blockout.py` (Palettenkonstanten, Materialblock, `m_zugweiss`/`m_zug`, Variantenzuweisung)

**Interfaces:**
- Consumes: `material_pbr`, `LACK_RAUHEIT_PNG`
- Produces: `m_blau`, `m_orange`, `m_gruen` mit Rauheitstextur und gedeckteren Farben; Varianten `m_blau_alt`, `m_orange_alt` (ausgeblichen, matter); Funktion `lackvariante(name_obj, mat)` → wählt deterministisch per `zlib.crc32(name)` für `Requisite_*`, `UnterEmpore_*`, `Kiste_*`, `Sued_*`, `Werkbank2_*`, `Werkstattwagen_*` die Alt-Variante (jedes dritte Objekt); Zuglacke mit Klarlack (`Coat Weight` 0.6, `Coat Roughness` 0.12) → glTF `KHR_materials_clearcoat`.

- [ ] **Step 1: Erwartung vor der Änderung (muss FEHLSCHLAGEN)**

Run: `node tools/glb-info.mjs app/public/szene.glb | grep -E '^(Blau|Orange|Gruen|ZugWeiss|Zug|BlauAlt) |^extensionsUsed'`
Expected heute: `Blau | base=0.10,0.33,0.56 ... tex=-`, kein `BlauAlt`, `extensionsUsed` ohne `KHR_materials_clearcoat`. Danach: `Blau | base=0.12,0.31,0.50 | ... tex=metallicRoughness`, `BlauAlt` vorhanden, `ZugWeiss ... ext=KHR_materials_clearcoat`.

- [ ] **Step 2: Farben und Lackmaterialien**

Konstanten anpassen (gedeckter, wie 10 Jahre Hallenluft):
```python
BLAU = (0.12, 0.31, 0.50)
BLAU_ALT = (0.22, 0.36, 0.48)
ORANGE = (0.82, 0.36, 0.16)
ORANGE_ALT = (0.80, 0.47, 0.30)
GRUEN = (0.14, 0.32, 0.27)
WEISS_ZUG = (0.86, 0.86, 0.87)
ROT_ZUG = (0.66, 0.11, 0.15)
```
Materialien:
```python
m_blau = material_pbr("Blau", BLAU, rauheit_png=LACK_RAUHEIT_PNG, metall=0.15, kachel=1.5)
m_blau_alt = material_pbr("BlauAlt", BLAU_ALT, rauheit_png=SOCKEL_RAUHEIT_PNG, metall=0.05, kachel=1.5)
m_orange = material_pbr("Orange", ORANGE, rauheit_png=LACK_RAUHEIT_PNG, metall=0.15, kachel=1.5)
m_orange_alt = material_pbr("OrangeAlt", ORANGE_ALT, rauheit_png=SOCKEL_RAUHEIT_PNG, metall=0.05, kachel=1.5)
m_gruen = material_pbr("Gruen", GRUEN, rauheit_png=LACK_RAUHEIT_PNG, metall=0.1, kachel=1.5)
m_objekt = material_pbr("Objekt", GRAU_OBJEKT, rauheit_png=LACK_RAUHEIT_PNG, metall=0.1, kachel=1.5)
```
Zuglack mit Klarlack (nach den Zeilen `m_zug = ...`, `m_zugweiss = ...`):
```python
def klarlack(mat, gewicht=0.6, rauheit=0.12):
    """Zweischichtlack: der glTF-Exporter schreibt KHR_materials_clearcoat, three.js rendert ihn."""
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Coat Weight"].default_value = gewicht
    bsdf.inputs["Coat Roughness"].default_value = rauheit
    return mat


klarlack(m_zug)
klarlack(m_zugweiss)
```
und `m_zugweiss`/`m_zug` auf `rauheit=0.42, metall=0.05` (Lack ist dielektrisch; die Reflexe kommen aus dem Klarlack).

- [ ] **Step 3: Varianten deterministisch zuweisen**

Nach den Materialdefinitionen:
```python
VARIANTEN = {"Blau": m_blau_alt, "Orange": m_orange_alt}
VARIANTEN_FAMILIEN = ("Requisite_", "UnterEmpore_", "Kiste_", "Sued_", "Werkbank2_", "Werkstattwagen_", "Empore_Kiste")


def lackvariante(name, mat):
    """Jedes dritte Requisit in Blau/Orange bekommt die ausgeblichene Variante — gleiche
    Farbe an allen Kisten liest als Spielzeug. Maschinen (Station_*) behalten den RAL-Ton."""
    if mat.name in VARIANTEN and name.startswith(VARIANTEN_FAMILIEN) and zlib.crc32(name.encode()) % 3 == 0:
        return VARIANTEN[mat.name]
    return mat
```
In `kasten()` und `zylinder()` (an der Stelle, wo das Material an das Mesh gehängt wird — suche `data.materials.append(mat)` in den Primitiv-Helfern) `mat = lackvariante(name, mat)` davor einsetzen; ebenso in `fass()` und `lade_asset(..., einfaerbung=...)`.
Expected: `frage_szene.py` unverändert (Geometrie gleich); `glb-info` zeigt `BlauAlt`/`OrangeAlt`; ein Zählskript über die glb-Knoten ist nicht nötig — die Sichtprüfung (Step 5) genügt, im Report aber `grep -c` der betroffenen Familien nennen.

- [ ] **Step 4: Bauen, Erwartung, Prüfer**

Run: Bauen; `node tools/glb-info.mjs app/public/szene.glb | grep -E '^(Blau|BlauAlt|Orange|OrangeAlt|Gruen|Objekt|ZugWeiss|Zug) |^extensionsUsed|^size'`. Expected: wie Step 1 beschrieben, `extensionsUsed` enthält `KHR_materials_clearcoat`, `size` < 7 800 000.
Run: Prüfer → unverändert. `frage_szene.py -- Triebzug_Korpus Requisite_Palette` → unverändert.

- [ ] **Step 5: Sichtprüfung, Tests, Commit**

Renders: `p_totale.png` — der Zug liest als lackiertes Metall mit schmalen Glanzlichtern statt als weißer Kunststoff; Kisten und Fässer in zwei Blau-/Orangetönen; Gelb gedeckt. `p_pruefstand.png` — Prüfstand behält sein Maschinenblau, das Fass daneben ist matter.
Run: `cd app && npm test --silent` Expected: alle grün.
```bash
git add blender/blockout.py app/public/szene.glb
git commit -m "feat(szene): gedeckte Lackpalette mit Rauheitstextur, ausgeblichene Varianten, Klarlack am Zug"
git push origin main
```

---

### Task 5: Requisiten mit Detail — Fässer, Paletten, Schläuche, Bodenkabel

**Files:**
- Modify: `blender/blockout.py` (`fass()`, neu `palette()`, `schlauch()`, Aufrufe der drei Platten-Paletten, vier neue Schläuche/Kabel)

**Interfaces:**
- Consumes: `zylinder`, `kasten`, `rohr_mit_bogen`, `lackvariante`, `m_stahl`, `m_dunkel`, `m_objekt`
- Produces: `fass(name, x, z, y_boden, farbe)` erzeugt zusätzlich `{name}_ring_mitte`, `{name}_deckel`, `{name}_spund`; `palette(name, x, z, y_boden, dreh_y=0.0)` (Argumentreihenfolge wie `fass`) erzeugt `{name}_brett_{i}` (3), `{name}_klotz_{i}` (3), `{name}_traeger_{i}` (2) in der Hüllbox 1.2 × 1.0 × 0.144; `schlauch(name, x, z, y_boden, radius=0.02, windungen=3, spule=0.35, mat=None)` erzeugt eine liegende Schlauchrolle `{name}_seg_{i}` (Kreisbogen aus 24 Segmenten je Umlauf) plus ein loses Ende `{name}_ende_seg_{i}`.

- [ ] **Step 1: Erwartung vor der Änderung (muss FEHLSCHLAGEN)**

Run: `frage_szene.py -- Requisite_Palette Sued_Palette Empore_Palette UnterEmpore_Fass_1 Schlauchrolle_`
Expected heute: drei Paletten als eine Zeile je Name (Platte 0.12 hoch), `UnterEmpore_Fass_1` ohne `_ring_mitte`, keine `Schlauchrolle_`. Danach: `Requisite_Palette_brett_0..2`, `_klotz_0..2`, `_traeger_0..1` (Gesamthülle wie zuvor: x −7.1..−5.9, z −9.1..−8.1, y 0..0.144), `UnterEmpore_Fass_1_ring_mitte`, drei Schlauchrollen.

- [ ] **Step 2: `fass()` erweitern**

Die bestehende `fass()` (Zeile ~409) hat heute Korpus (r 0.23, h 0.62), `_ring_oben` (y_boden + 0.46), `_ring_unten` (y_boden + 0.16) und `_deckel` (r 0.2, 0.03 hoch, Mitte y_boden + 0.63, Oberkante 0.645). Ergänzen, ohne Hüllmaße zu ändern:
```python
    # Detail: mittlere Sicke, Spundloch und Spundschraube — ein glatter Zylinder liest als Dose
    zylinder(f"{name}_ring_mitte", 0.237, 0.03, x, y_boden + 0.31, z, m_stahl, ecken=32)
    zylinder(f"{name}_spund", 0.03, 0.02, x + 0.12, y_boden + 0.655, z, m_stahl, ecken=16)
    zylinder(f"{name}_spund_klein", 0.02, 0.016, x - 0.12, y_boden + 0.653, z, m_dunkel, ecken=16)
```
(Spund sitzt auf dem Deckel: Unterkante 0.645 = Deckeloberkante; Familie bleibt der Fassname, der Prüfer meldet nichts Neues.)

- [ ] **Step 3: `palette()` und `schlauch()`**

Nach `fass()`:
```python
def palette(name, x, z, y_boden, dreh_y=0.0):
    """Euro-Palette in Holzoptik: drei Deckbretter, drei Kloetze je Seite, zwei Laengstraeger. Huelle 1.2 x 1.0 x 0.144."""
    mat = m_objekt
    dr = (0, 0, -dreh_y) if dreh_y else None  # Hochachse = Blender z, Vorzeichen wie bei fahrspur()
    for i, bz in enumerate((-0.4, 0.0, 0.4)):
        kasten(f"{name}_brett_{i}", 1.2, 0.14, 0.022, x, y_boden + 0.133, z + bz, mat, fase=0.003, drehung=dr)
    for i, bx in enumerate((-0.5, 0.0, 0.5)):
        kasten(f"{name}_klotz_{i}", 0.145, 1.0, 0.078, x + bx, y_boden + 0.083, z, mat, fase=0.003, drehung=dr)
    for i, bz in enumerate((-0.43, 0.43)):
        kasten(f"{name}_traeger_{i}", 1.2, 0.1, 0.044, x, y_boden + 0.022, z + bz, mat, fase=0.003, drehung=dr)


def schlauch(name, x, z, y_boden, radius=0.02, windungen=3, spule=0.35, mat=None):
    """Liegende Schlauchrolle (Druckluft) plus loses Ende — Kleinkram, den jede Werkstatt hat."""
    mat = mat or m_dunkel
    punkte = []
    n = 24 * windungen
    for i in range(n + 1):
        w = 2 * math.pi * i / 24
        punkte.append((x + spule * math.cos(w), y_boden + radius + (i / n) * radius * 2.2 * windungen, z + spule * math.sin(w)))
    rohr_mit_bogen(name, punkte, radius, mat)
    rohr_mit_bogen(f"{name}_ende", [punkte[-1], (x + spule + 0.5, y_boden + radius, z + 0.2), (x + spule + 0.9, y_boden + radius, z + 0.6)], radius, mat)
```
Hinweis: `rohr_mit_bogen` setzt an jedem Knick eine Kugel (`{name}_bogen_{i}`); bei 72 Segmenten sind das 71 Kugeln — akzeptabel (kleine Meshes, geteilte Vorlage). Wird die glb dadurch um mehr als 300 KB größer, `windungen=2` und 16 Segmente je Umlauf verwenden.

- [ ] **Step 4: Aufrufe ersetzen und Requisiten setzen**

Die drei `kasten(... "_Palette", 1.2, 1.0, 0.12, X, Y, Z, m_objekt, fase=0)`-Zeilen (`Empore_Palette`, `Sued_Palette`, `Requisite_Palette`) durch `palette("Empore_Palette", -16.3, -9.3, 3.13)`, `palette("Sued_Palette", 14.2, 8.9, 0.0)`, `palette("Requisite_Palette", -6.5, -8.6, 0.0)` ersetzen (Reihenfolge name, x, z, y_boden). Was auf den Paletten steht (`Empore_Palette_Kiste` bei y 3.48, `Kiste_Palette` bei y 0.12), bleibt: Palettenoberkante ist weiterhin y_boden + 0.144 → `Kiste_Palette` auf `y=0.144`, `Empore_Palette_Kiste` Mitte auf 3.13 + 0.144 + 0.225 = 3.499 setzen (Kiste 0.45 hoch), damit nichts schwebt und nichts einsinkt.
Neue Requisiten (freie Bodenflächen, mit `--alle` gegen Nachbarn prüfen):
```python
schlauch("Schlauchrolle_1", 3.9, 6.9, 0.0)         # neben dem Pruefstand
schlauch("Schlauchrolle_2", -10.6, 4.1, 0.0)       # Besprechungsecke, an der Suedwand
schlauch("Schlauchrolle_3", 12.6, -8.2, 0.0, mat=m_orange)  # Druckluft, Nordost
rohr_mit_bogen("Bodenkabel_Pruefstand", [(1.9, 0.02, 4.3), (3.2, 0.02, 4.9), (4.4, 0.02, 4.6)], 0.014, m_dunkel)
```

- [ ] **Step 5: Bauen, Erwartung, Prüfer**

Run: Bauen; Abfrage aus Step 1 plus `Kiste_Palette Empore_Palette_Kiste Bodenkabel_`. Expected: Palettenhüllen wie zuvor (min y = y_boden, max y = y_boden + 0.144), `Kiste_Palette` min y 0.144, Schlauchrollen max y ≈ 0.16, `Bodenkabel_Pruefstand_seg_0` y 0.006..0.034.
Run: Prüfer. Expected: kein `SCHWEBT` (Bretter liegen auf Klötzen, Klötze auf Trägern, Träger auf dem Boden; Schlauchsegmente berühren sich), `11 Durchdringungen gesamt` (die Kugeln der Schlauchrolle sind Familie „Schlauchrolle" wie ihre Segmente), `20 Routen, 0 ungeloest`, `0 Kollisionen`. Meldet der Prüfer ein Schlauchrollen-Paar gegen ein Fremdobjekt: die Rolle um 0.5 m verschieben, nicht die Liste ändern.

- [ ] **Step 6: Sichtprüfung, Tests, Commit**

Renders: `p_pruefstand.png` — Schlauchrolle und Bodenkabel im Vordergrund, Fass mit Sicke und Spund; `p_meisterbuero.png`/`p_datenraum.png` — Palette mit Brettern statt Platte.
Run: `cd app && npm test --silent` Expected: alle grün.
```bash
git add blender/blockout.py app/public/szene.glb app/src/fahrtwege.json
git commit -m "feat(szene): Requisiten mit Detail — Faesser mit Sicken, Bretterpaletten, Schlauchrollen, Bodenkabel"
git push origin main
```

---

### Task 6: Tageslicht aus Fenstern und Oberlichtern, Stahl und Glas abgestimmt

**Files:**
- Modify: `blender/blockout.py` (neues `m_tageslicht`, Zuweisung an `Wand_*_Fenster` und `Dach_Oberlicht_*`, `m_stahlhell`/`m_stahl`/`m_hallenglas`/`m_fenster`)

**Interfaces:**
- Consumes: `material(... emission=...)`
- Produces: `m_tageslicht = material("Tageslicht", (0.90, 0.94, 1.0), rauheit=0.15, emission=1.3)`; Fensterbänder und Oberlichter leuchten wie Tageslicht; `m_stahlhell` mit `rauheit=0.42, metall=0.6`, `m_stahl` mit `rauheit=0.5, metall=0.8`; `m_fenster` bleibt für Schilder/Kästen (nicht emissiv).

- [ ] **Step 1: Erwartung vor der Änderung (muss FEHLSCHLAGEN)**

Run: `node tools/glb-info.mjs app/public/szene.glb | grep -E '^(Tageslicht|Hallenglas|StahlHell) '`
Expected heute: kein `Tageslicht`, `StahlHell | ... metal=0.70 rough=0.35`. Danach: `Tageslicht ... ext=KHR_materials_emissive_strength`, `StahlHell ... metal=0.60 rough=0.42`.

- [ ] **Step 2: Materialien**

Neben `m_hallenglas`: `m_tageslicht = material("Tageslicht", (0.90, 0.94, 1.0), rauheit=0.15, emission=1.3)`.
In `wand_mit_fenster` beide `Wand_{seite}_Fenster`-Aufrufe (durchgehend und geteilt) von `m_hallenglas` auf `m_tageslicht`; die `Dach_Oberlicht_{i}`-Zeile von `m_fenster` auf `m_tageslicht`. `m_stahlhell = material("StahlHell", STAHL_HELL, rauheit=0.42, metall=0.6)`, `m_stahl = material("Stahl", STAHL, rauheit=0.5, metall=0.8)`. `m_hallenglas` entfernen, falls ohne Verwender (`grep -c m_hallenglas`).

- [ ] **Step 3: Bauen, Erwartung, Prüfer, Sichtprüfung**

Run: Bauen; `glb-info` wie Step 1. Prüfer unverändert.
Renders: `p_totale.png` — Fensterbänder und Oberlichter lesen als helle Lichtquellen, die Halle wirkt von oben belichtet; keine ausgefressenen Flächen (sonst `emission` auf 1.0). Stahlträger weniger spiegelnd, dafür strukturierter im Streiflicht.

- [ ] **Step 4: Tests, Commit**

Run: `cd app && npm test --silent` Expected: alle grün.
```bash
git add blender/blockout.py app/public/szene.glb
git commit -m "feat(szene): Tageslicht aus Fensterbaendern und Oberlichtern, Stahl matter abgestimmt"
git push origin main
```

---

### Task 7: Gesamtabnahme und Sichtprotokoll

**Files:**
- Modify: `README.md` (Abschnitt "Sichtprüfung": Hinweis auf `_v2vorher`-Vergleich und AO-Schalter)
- Create: `docs/superpowers/plans/2026-09-06-werkstatt-materialrealismus-abnahme.md` (Sichtprotokoll)

**Interfaces:**
- Consumes: alle vorigen Tasks; `tools/render-posen.js`, `tools/glb-info.mjs`, Prüfer, Vitest

- [ ] **Step 1: Messwerte**

Run: Prüfer → kein `SCHWEBT`, `11 Durchdringungen gesamt`, `20 Routen, 0 ungeloest`, `0 Kollisionen`. `node tools/glb-info.mjs app/public/szene.glb | tail -3` → `size` < 8 000 000, `extensionsUsed` enthält `KHR_materials_emissive_strength` und `KHR_materials_clearcoat`. `cd app && npm test --silent` → alle grün. Im Browser (Dev-Server, 1920×1080, Pixel-Ratio 1): nach 20 s `window.__komposition.mittlereBildzeit()` < 16.7 und `aoAktiv === true`; mit Pixel-Ratio 2 (`renderer.setPixelRatio(2)` in der Konsole) Wert notieren.

- [ ] **Step 2: Renders und Vergleich**

Alle neun Posen rendern; für jede Pose `p_<name>.png` neben `p_<name>_v2vorher.png` betrachten und im Sichtprotokoll je Pose eine Zeile schreiben: besser / gleich / schlechter, welche der sieben Befundpunkte (Ausgangsbefund 1–7) dort sichtbar behoben sind, und was noch nach Comic aussieht (z. B. verbleibende Primitiv-Requisiten, harte Farbflächen). Kriterium für "fertig": in keiner Jury-Pose ein Objekt ohne Kontaktschatten, keine unstrukturierte Großfläche, keine gesättigte Einheitsfarbe an mehr als zwei benachbarten Requisiten.

- [ ] **Step 3: Protokoll und Commit**

`docs/superpowers/plans/2026-09-06-werkstatt-materialrealismus-abnahme.md` mit Messwerten (Step 1), der Posen-Tabelle (Step 2) und einer Liste offener Punkte für einen Folgeplan (nur Beobachtungen, keine Zahlen erfinden).
```bash
git add README.md docs/superpowers/plans/2026-09-06-werkstatt-materialrealismus-abnahme.md
git commit -m "docs(szene): Sichtprotokoll Materialrealismus — Messwerte und Posenvergleich"
git push origin main
```

---

## Self-Review

- **Befund-Abdeckung:** Befund 1 (Einheitsflächen) → Task 2; Befund 2 (Kontaktschatten) → Task 1; Befund 3 (Palette) → Task 4; Befund 4 (Rauheit) → Task 2/4; Befund 5 (Licht) → Task 1 und 6; Befund 6 (Requisiten, Spuren) → Task 3 und 5; Befund 7 (Schienen) → Task 3. Abnahme → Task 7.
- **Platzhalter:** keine; alle Code-Schritte enthalten den Code. Zwei Stellen verlangen eine Prüfung vor Ort (Vorzeichen der Hochachsendrehung in `fahrspur`, Alpha-Export der Decals) und nennen jeweils den Rückfall.
- **Namenskonsistenz:** `material_pbr`, `LACK_RAUHEIT_PNG`, `SOCKEL_RAUHEIT_PNG`, `lackvariante`, `erzeugeKomposition`, `leseAoSchalter`, `erzeugeHimmelTextur`, `liesGlbInfo`, `fass`/`palette`/`schlauch` werden in allen Tasks gleich verwendet. Testzahlen: 40 → 42 (Task 0) → 48 (Task 1); spätere Tasks: "alle grün".
- **Risiken benannt:** Bauzeit durch reines Python-Noise (Task 2 Step 5 mit Rückfall auf 768 px), GTAO-Import unter Vitest (Task 1 Step 4 mit Rückfall auf dynamischen Import), Decal-Alpha im Exporter (Task 3 Step 5), Leistung auf dem Präsentationsrechner (Überlastschutz, `?ao=0`).
