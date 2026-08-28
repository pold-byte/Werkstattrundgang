# Werkstattrundgang-App (Basis A) — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Live navigierbare 3D-Präsentations-App (Three.js) mit Werkstatt-Szene, deterministischen Kamerafahrten, HTML-Slide-Overlays aus `stationen.json` (Platzhalter-Inhalte), Video-Einbindung, Druck-/PDF-Ansicht, Notfall-Single-File-Build und Kiosk-Start — vollständig offline lauffähig.

**Architecture:** Vanilla-JS-Web-App (Vite). Reine Logik (Schrittliste, Zustandsmaschine, Kamerafahrt-Mathematik, Tastatur-Reducer, Speicher) als getrennte, testbare Module ohne DOM/Three-Abhängigkeit (TDD mit Vitest); darüber eine dünne Integrationsschicht (`main.js`) mit Three.js-Szene und DOM-Overlays. Eine zentrale `stationen.json` ist die einzige Quelle der Wahrheit für App und Druckansicht. Die 3D-Szene kommt zuerst als Platzhalter (Boxen), später als `.glb` aus Blender (Blockout-Skript beiliegend).

**Tech Stack:** Node ≥ 20, Vite 7, Three.js 0.180.0 (gepinnt), Vitest 3 + happy-dom, Blender 4.x LTS (MCP-gesteuert), vite-plugin-singlefile.

**Spec:** `docs/superpowers/specs/2026-08-25-werkstattrundgang-praesentation-design.md` — bei Widerspruch gilt die Spec.

**Nicht Teil dieses Plans** (separate spätere Pläne laut Spec §9): Befüllen der Slide-Inhalte aus den Quelldateien, die Station-5-Ergebnisgrafik mit Panel-Wechsel (Spec §4 — braucht die echten Execution-Accuracy-Zahlen, kommt mit der Inhalte-Phase), Demo-Video-Aufnahme (OBS), Ausbaustufe D (Route /vortrag + Replay), Blender-Feinschliff über das Blockout hinaus, Generalprobe auf Zielhardware.

**Arbeitsverzeichnis:** Projektwurzel `C:\Users\leopo\claude\Test_präsentation_T2000`. Alle Pfade unten relativ dazu. Die App lebt in `app/`. Shell-Befehle sind für PowerShell/cmd unter Windows notiert; `npm`-Befehle laufen in `app/`.

---

## Dateistruktur (Zielbild)

```
app/
  package.json               — Abhängigkeiten (exakt gepinnt), Skripte
  vite.config.js             — Vite + Vitest-Konfiguration, zwei HTML-Eingänge
  vite.notfall.config.js     — Single-File-Build (Task 13)
  index.html                 — Präsentations-Einstieg (Canvas, Overlays, Kopfzeile)
  druck.html                 — Druck-/PDF-Ansicht (Task 12)
  start.bat                  — Kiosk-Start für den Prüfungstag (Task 14)
  public/
    szene.glb                — Blender-Export (ab Task 11)
    video/demo_720.mp4       — später (Aufnahme separat); App verkraftet Fehlen
    video/demo_1080.mp4      — später
  src/
    stationen.json           — EINZIGE Quelle: Stationen, Kameraposen, Slide-Inhalte
    schritte.js              — baut lineare Schrittliste aus stationen.json
    zustand.js               — Zustandsmaschine + Ansichtsableitung
    kamera.js                — Easing, Interpolation, Kamerafahrt (reine Mathematik)
    steuerung.js             — Taste→Aktion-Reducer + Eingabesperre mit Puffer
    speicher.js              — sessionStorage-Persistenz (Storage injizierbar)
    overlays.js              — Panel, Titel, Schwarzbild, Video-Großansicht (DOM)
    szene.js                 — Three.js-Szene, Platzhalter, glb-Laden, Base64-Pfad
    videotextur.js           — VideoTexture auf Mesh "Monitor_Bildschirm"
    waypoint-werkzeug.js     — Dev-Werkzeug: OrbitControls + Pose als JSON ausgeben
    main.js                  — Integration: Rendering-Loop, Events, Ansicht anwenden
    druck.js                 — rendert druck.html-Seiten aus stationen.json
    stil.css                 — Präsentations-Styles (Arial, Graustufen, clamp())
    druck.css                — @page-/Print-Styles
    generiert/szene-glb.js   — Stub; wird nur vom Notfall-Build überschrieben
  tests/
    schritte.test.js, zustand.test.js, kamera.test.js,
    steuerung.test.js, speicher.test.js, overlays.test.js
tools/
  baue-notfall.mjs           — erzeugt dist-notfall/notfall.html (Task 13)
blender/
  blockout.py                — bpy-Skript: Blockout-Szene + glb-Export (Task 11)
PRUEFUNGSTAG.md              — Checkliste (Task 14)
```

**Namenskonventionen (verbindlich, mehrfach verwendet):**
- Stations-IDs: `meisterbuero`, `datenraum`, `terminal`, `anzeigetafel`, `pruefstand`, `besprechung`.
- Blender/Szenen-Objekte: `Station_<nr>_<id>` (z. B. `Station_3_terminal`), Video-Fläche exakt `Monitor_Bildschirm`, Platzhaltergruppe `Platzhalter`, geladenes Modell `Werkstatt`.
- Schritt-Typen: `totale`, `fahrt`, `belegpunkt`, `rueckflug`, `sprung`.

---

### Task 1: Projektgerüst & Werkzeugkette

**Files:**
- Create: `app/package.json`
- Create: `app/vite.config.js`
- Create: `app/index.html`
- Create: `app/src/main.js` (Stub, wird in Task 8 ersetzt)
- Create: `app/src/stil.css`
- Create: `app/src/generiert/szene-glb.js`
- Create: `app/tests/rauchtest.test.js`

- [ ] **Step 1: package.json anlegen**

```json
{
  "name": "werkstattrundgang",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "engines": { "node": ">=20.19" },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview --port 4173 --strictPort",
    "test": "vitest run"
  },
  "dependencies": {
    "three": "0.180.0"
  },
  "devDependencies": {
    "happy-dom": "18.0.1",
    "vite": "7.1.0",
    "vite-plugin-singlefile": "2.3.0",
    "vitest": "3.2.4"
  }
}
```

- [ ] **Step 2: Abhängigkeiten installieren**

Run (in `app/`): `npm install`
Expected: `node_modules/` entsteht, Exit-Code 0. Sollte eine der exakt gepinnten Versionen nicht existieren (Registry-Fehler „No matching version"), die nächstliegende existierende Patch-Version derselben Major-Version eintragen und im Commit-Text vermerken.

- [ ] **Step 3: vite.config.js anlegen**

```js
import { defineConfig } from 'vitest/config';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  base: './',
  build: {
    rollupOptions: {
      input: {
        index: fileURLToPath(new URL('./index.html', import.meta.url)),
        druck: fileURLToPath(new URL('./druck.html', import.meta.url)),
      },
    },
  },
  test: {
    environment: 'happy-dom',
  },
});
```

Hinweis: `druck.html` existiert erst ab Task 12. Damit `npm run build` bis dahin nicht scheitert, den `druck`-Eintrag zunächst auskommentieren und in Task 12 aktivieren:

```js
      input: {
        index: fileURLToPath(new URL('./index.html', import.meta.url)),
        // druck: aktiviert in Task 12
      },
```

- [ ] **Step 4: index.html anlegen**

```html
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Werkstattrundgang</title>
  <link rel="stylesheet" href="./src/stil.css">
</head>
<body>
  <header id="kopfzeile">DB Intern / DB internal</header>
  <canvas id="buehne"></canvas>
  <div id="titel" class="titel">
    <h1>Eine Kennzahl — von der Werkstatthalle bis in die Planungsrunde</h1>
    <p>[PLATZHALTER: Untertitel/Name/Datum]</p>
  </div>
  <div id="dimmer"></div>
  <aside id="panel"></aside>
  <div id="video-overlay" hidden>
    <video id="video-gross" src="./video/demo_1080.mp4" muted playsinline preload="auto"></video>
  </div>
  <video id="video-textur" src="./video/demo_720.mp4" muted playsinline loop preload="auto" hidden></video>
  <div id="schwarzbild" hidden></div>
  <script type="module" src="./src/main.js"></script>
</body>
</html>
```

- [ ] **Step 5: main.js-Stub anlegen** — `app/src/main.js`

index.html referenziert `./src/main.js`; ohne die Datei bricht `vite build` ab. Bis zur echten Integrationsschicht (Task 8) genügt ein Stub:

```js
// Integrationsschicht — wird in Task 8 implementiert.
```

- [ ] **Step 6: src/stil.css anlegen**

```css
:root {
  --grau-05: #f4f4f4;
  --grau-20: #d0d0d0;
  --grau-60: #5a5a5a;
  --grau-90: #1a1a1a;
  --panel-deckkraft: 0.94;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body {
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-family: Arial, Helvetica, sans-serif;
  background: #000;
  color: var(--grau-90);
}

#buehne { position: fixed; inset: 0; width: 100%; height: 100%; display: block; }

#kopfzeile {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 40;
  padding: 0.4rem 1rem;
  background: var(--grau-05);
  border-bottom: 1px solid var(--grau-20);
  font-size: clamp(0.7rem, 1.2vw, 1rem);
  color: var(--grau-60);
}

.titel {
  position: fixed;
  left: 5vw; bottom: 8vh;
  z-index: 20;
  max-width: 60vw;
  background: rgba(244, 244, 244, var(--panel-deckkraft));
  border: 1px solid var(--grau-20);
  padding: 1.2rem 1.6rem;
}
.titel h1 { font-size: clamp(1.2rem, 2.6vw, 2.9rem); }
.titel p { margin-top: 0.5rem; font-size: clamp(1.1rem, 1.8vw, 2.2rem); color: var(--grau-60); }

/* Spec §10: kein Panel-Text unter 24-pt-Äquivalent bei 1080p (24 pt = 32 px CSS). */
#panel {
  position: fixed;
  top: 12vh; right: 3vw; bottom: 10vh;
  z-index: 20;
  width: min(34vw, 660px);
  overflow: hidden;
  background: rgba(244, 244, 244, var(--panel-deckkraft));
  border: 1px solid var(--grau-20);
  padding: 1.2rem 1.4rem;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s; /* Spec §5: Panel blendet in ~300 ms ein */
}
#panel.sichtbar { opacity: 1; pointer-events: auto; }
#panel .stationsnummer {
  font-size: clamp(1rem, 1.7vw, 2.1rem);
  color: var(--grau-60);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
#panel h2 { font-size: clamp(1.4rem, 2.4vw, 3rem); margin: 0.3rem 0 0.8rem; }
#panel .kernaussage { font-size: clamp(1.2rem, 2vw, 2.5rem); font-weight: bold; margin-bottom: 1rem; }
#panel ul { list-style: none; }
#panel li {
  font-size: clamp(1.1rem, 1.8vw, 2.25rem);
  padding: 0.45rem 0 0.45rem 1.2rem;
  position: relative;
}
#panel li::before { content: "—"; position: absolute; left: 0; color: var(--grau-60); }
#panel .kapitel {
  position: absolute;
  bottom: 0.8rem; right: 1.4rem;
  font-size: clamp(1rem, 1.7vw, 2.1rem);
  color: var(--grau-60);
}

#dimmer {
  position: fixed; inset: 0;
  z-index: 10;
  background: rgba(0, 0, 0, 0.25); /* Spec §5: Szene dimmt beim Ankommen leicht ab */
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s;
}
#dimmer.aktiv { opacity: 1; }

#video-overlay {
  position: fixed; inset: 0;
  z-index: 30;
  background: rgba(0, 0, 0, 0.92);
  display: flex; align-items: center; justify-content: center;
}
#video-overlay video { max-width: 96vw; max-height: 90vh; }

#schwarzbild { position: fixed; inset: 0; z-index: 50; background: #000; }

[hidden] { display: none !important; }
```

- [ ] **Step 7: Stub für den Notfall-Build anlegen** — `app/src/generiert/szene-glb.js`

```js
// Wird nur vom Notfall-Build (tools/baue-notfall.mjs) mit echten Daten überschrieben.
export const szeneGlbBase64 = '';
```

- [ ] **Step 8: Rauchtest schreiben** — `app/tests/rauchtest.test.js`

```js
import { describe, it, expect } from 'vitest';

describe('Werkzeugkette', () => {
  it('führt Tests aus', () => {
    expect(1 + 1).toBe(2);
  });

  it('stellt die happy-dom-Umgebung bereit', () => {
    expect(typeof document).toBe('object');
  });
});
```

- [ ] **Step 9: Testlauf**

Run (in `app/`): `npm test`
Expected: `2 passed`.

- [ ] **Step 10: Dev-Server-Probe**

Run (in `app/`): `npm run dev` — im Browser `http://localhost:5173` öffnen.
Expected: schwarze Seite mit grauer Kopfzeile „DB Intern / DB internal" und Titel-Panel. Server danach beenden (Strg+C).

- [ ] **Step 11: Commit**

```bash
git add app/package.json app/package-lock.json app/vite.config.js app/index.html app/src/main.js app/src/stil.css app/src/generiert/szene-glb.js app/tests/rauchtest.test.js
git commit -m "feat(app): Projektgeruest mit Vite, Vitest und Grundlayout"
```

---

### Task 2: Stationsdaten & Schrittliste

**Files:**
- Create: `app/src/stationen.json`
- Create: `app/src/schritte.js`
- Test: `app/tests/schritte.test.js`

- [ ] **Step 1: stationen.json anlegen** (Platzhalter-Politik laut Spec §5; Kameraposen sind provisorisch für die Platzhalterszene und werden in Task 11 mit dem Waypoint-Werkzeug ersetzt)

```json
{
  "totale": {
    "kamera": { "position": [20, 16, 20], "blickziel": [0, 0, 0], "dauer_s": 6 }
  },
  "sprung_dauer_s": 2.5,
  "stationen": [
    {
      "nr": 1,
      "id": "meisterbuero",
      "titel": "Wo die Zahl entsteht",
      "kapitel": "Kap. 1.1, 3.1",
      "kamera": { "position": [-6.5, 2.5, -1.5], "blickziel": [-10, 1, -5], "dauer_s": 6 },
      "kernaussage": "[PLATZHALTER: Kernaussage Station 1 — wird nach Bereitstellung der Quelldateien befüllt]",
      "belegpunkte": ["[PLATZHALTER 1.1]", "[PLATZHALTER 1.2]", "[PLATZHALTER 1.3]"],
      "anschauungsobjekt": "Pinnwand mit Excel-Ausdrucken",
      "quelle_kommentar": "[Quelldatei + Abschnitt eintragen]"
    },
    {
      "nr": 2,
      "id": "datenraum",
      "titel": "Aus Chaos wird Struktur",
      "kapitel": "Kap. 3.3, 3.5, 4.4",
      "kamera": { "position": [0.5, 2.2, -2.5], "blickziel": [-3, 1, -6], "dauer_s": 5 },
      "kernaussage": "[PLATZHALTER: Kernaussage Station 2]",
      "belegpunkte": ["[PLATZHALTER 2.1]", "[PLATZHALTER 2.2]", "[PLATZHALTER 2.3]"],
      "anschauungsobjekt": "Regal: ungeordnete Ablage davor, geordnete Struktur darin",
      "quelle_kommentar": "[Quelldatei + Abschnitt eintragen]"
    },
    {
      "nr": 3,
      "id": "terminal",
      "titel": "Fragen statt Formeln",
      "kapitel": "Kap. 3.4, 4.3",
      "kamera": { "position": [9.5, 1.8, -2], "blickziel": [7, 1.2, -5], "dauer_s": 5 },
      "kernaussage": "[PLATZHALTER: Kernaussage Station 3]",
      "belegpunkte": ["[PLATZHALTER 3.1]", "[PLATZHALTER 3.2]", "[PLATZHALTER 3.3]"],
      "anschauungsobjekt": "Bedienterminal mit Monitor (Demo-Video)",
      "quelle_kommentar": "[Quelldatei + Abschnitt eintragen]"
    },
    {
      "nr": 4,
      "id": "anzeigetafel",
      "titel": "Ergebnis lesen",
      "kapitel": "Kap. 4.2, 4.5",
      "kamera": { "position": [5.5, 2.2, 2], "blickziel": [9, 2, 5], "dauer_s": 5 },
      "kernaussage": "[PLATZHALTER: Kernaussage Station 4]",
      "belegpunkte": ["[PLATZHALTER 4.1]", "[PLATZHALTER 4.2]", "[PLATZHALTER 4.3]"],
      "anschauungsobjekt": "Anzeigetafel",
      "quelle_kommentar": "[Quelldatei + Abschnitt eintragen]"
    },
    {
      "nr": 5,
      "id": "pruefstand",
      "titel": "Stimmt das auch?",
      "kapitel": "Kap. 5",
      "kamera": { "position": [-1.5, 2.5, 2.5], "blickziel": [2, 1, 6], "dauer_s": 5 },
      "kernaussage": "[PLATZHALTER: Kernaussage Station 5]",
      "belegpunkte": ["[PLATZHALTER 5.1]", "[PLATZHALTER 5.2]", "[PLATZHALTER 5.3]"],
      "anschauungsobjekt": "Prüfstand mit Ergebnis-Grafik",
      "quelle_kommentar": "[Quelldatei + Abschnitt eintragen]"
    },
    {
      "nr": 6,
      "id": "besprechung",
      "titel": "Was es bringt, was nicht",
      "kapitel": "Kap. 6, 7",
      "im_rundgang": false,
      "kamera": { "position": [-5.5, 2.2, 2.5], "blickziel": [-9, 1, 6], "dauer_s": 6 },
      "kernaussage": "[PLATZHALTER: Kernaussage Station 6 (Reserve)]",
      "belegpunkte": ["[PLATZHALTER 6.1]", "[PLATZHALTER 6.2]", "[PLATZHALTER 6.3]"],
      "anschauungsobjekt": "Besprechungstisch (Planungsrunde)",
      "quelle_kommentar": "[Quelldatei + Abschnitt eintragen]"
    }
  ]
}
```

- [ ] **Step 2: Fehlschlagenden Test schreiben** — `app/tests/schritte.test.js`

```js
import { describe, it, expect } from 'vitest';
import { baueSchritte } from '../src/schritte.js';
import daten from '../src/stationen.json';

describe('baueSchritte', () => {
  const schritte = baueSchritte(daten.stationen);

  it('beginnt mit der Totale und endet mit dem Rückflug', () => {
    expect(schritte[0]).toEqual({ typ: 'totale' });
    expect(schritte[schritte.length - 1]).toEqual({ typ: 'rueckflug' });
  });

  it('nimmt Station 6 (im_rundgang: false) nicht in den linearen Ablauf auf', () => {
    expect(schritte.some((s) => s.stationId === 'besprechung')).toBe(false);
  });

  it('erzeugt pro Rundgang-Station eine Fahrt plus einen Schritt je Belegpunkt', () => {
    // 1 Totale + 5 Stationen * (1 Fahrt + 3 Belegpunkte) + 1 Rückflug = 22
    expect(schritte).toHaveLength(22);
    expect(schritte[1]).toEqual({ typ: 'fahrt', stationId: 'meisterbuero' });
    expect(schritte[2]).toEqual({ typ: 'belegpunkt', stationId: 'meisterbuero', index: 0 });
    expect(schritte[4]).toEqual({ typ: 'belegpunkt', stationId: 'meisterbuero', index: 2 });
    expect(schritte[5]).toEqual({ typ: 'fahrt', stationId: 'datenraum' });
  });
});
```

- [ ] **Step 3: Test laufen lassen — muss fehlschlagen**

Run (in `app/`): `npm test -- tests/schritte.test.js`
Expected: FAIL — „Failed to resolve import ../src/schritte.js".

- [ ] **Step 4: Implementierung** — `app/src/schritte.js`

```js
// Baut aus den Stationsdaten die lineare Schrittliste des Vortrags.
// Station mit im_rundgang === false (Reserve) ist nur per Direktsprung erreichbar.
export function baueSchritte(stationen) {
  const schritte = [{ typ: 'totale' }];
  for (const st of stationen) {
    if (st.im_rundgang === false) continue;
    schritte.push({ typ: 'fahrt', stationId: st.id });
    for (let i = 0; i < st.belegpunkte.length; i++) {
      schritte.push({ typ: 'belegpunkt', stationId: st.id, index: i });
    }
  }
  schritte.push({ typ: 'rueckflug' });
  return schritte;
}
```

- [ ] **Step 5: Test laufen lassen — muss bestehen**

Run (in `app/`): `npm test -- tests/schritte.test.js`
Expected: PASS (3 Tests).

- [ ] **Step 6: Commit**

```bash
git add app/src/stationen.json app/src/schritte.js app/tests/schritte.test.js
git commit -m "feat(app): Stationsdaten (Platzhalter) und Schrittlisten-Generator"
```

---

### Task 3: Zustandsmaschine & Ansichtsableitung

**Files:**
- Create: `app/src/zustand.js`
- Test: `app/tests/zustand.test.js`

- [ ] **Step 1: Fehlschlagenden Test schreiben** — `app/tests/zustand.test.js`

```js
import { describe, it, expect } from 'vitest';
import { Zustandsmaschine, leiteAnsichtAb } from '../src/zustand.js';
import { baueSchritte } from '../src/schritte.js';
import daten from '../src/stationen.json';

const schritte = baueSchritte(daten.stationen);

describe('Zustandsmaschine', () => {
  it('startet auf der Totale und geht mit weiter()/zurueck() durch die Liste', () => {
    const z = new Zustandsmaschine(schritte);
    expect(z.aktuell).toEqual({ typ: 'totale' });
    expect(z.weiter()).toEqual({ typ: 'fahrt', stationId: 'meisterbuero' });
    expect(z.weiter()).toEqual({ typ: 'belegpunkt', stationId: 'meisterbuero', index: 0 });
    expect(z.zurueck()).toEqual({ typ: 'fahrt', stationId: 'meisterbuero' });
  });

  it('läuft an den Enden nicht aus der Liste', () => {
    const z = new Zustandsmaschine(schritte);
    expect(z.zurueck()).toEqual({ typ: 'totale' });
    for (let i = 0; i < 100; i++) z.weiter();
    expect(z.aktuell).toEqual({ typ: 'rueckflug' });
  });

  it('Direktsprung überlagert den linearen Stand, weiter() kehrt dorthin zurück', () => {
    const z = new Zustandsmaschine(schritte);
    z.weiter(); // fahrt meisterbuero (index 1)
    expect(z.springeZuStation('besprechung')).toEqual({ typ: 'sprung', stationId: 'besprechung' });
    expect(z.index).toBe(1); // linearer Stand unverändert
    // weiter() räumt nur den Sprung ab und kehrt zum linearen Stand (schritte[1]) zurück
    expect(z.weiter()).toEqual({ typ: 'fahrt', stationId: 'meisterbuero' });
  });

  it('springeZurTotale() zeigt die Totale, ohne den Stand zu verlieren', () => {
    const z = new Zustandsmaschine(schritte);
    z.weiter(); z.weiter();
    expect(z.springeZurTotale()).toEqual({ typ: 'sprung-totale' });
    expect(z.index).toBe(2);
  });

  it('setzeStand() stellt Index und Sprung wieder her (für sessionStorage)', () => {
    const z = new Zustandsmaschine(schritte);
    z.setzeStand({ index: 5, sprung: { typ: 'sprung', stationId: 'terminal' } });
    expect(z.index).toBe(5);
    expect(z.aktuell).toEqual({ typ: 'sprung', stationId: 'terminal' });
    z.setzeStand({ index: 999, sprung: null }); // ungültig → ignoriert
    expect(z.index).toBe(5);
  });
});

describe('leiteAnsichtAb', () => {
  it('Totale und Rückflug zeigen die Totale ohne Panel', () => {
    expect(leiteAnsichtAb({ typ: 'totale' }, daten.stationen)).toEqual({ ort: 'totale', belegpunkte: 0 });
    expect(leiteAnsichtAb({ typ: 'rueckflug' }, daten.stationen)).toEqual({ ort: 'totale', belegpunkte: 0 });
  });

  it('Fahrt zeigt die Station mit 0 Belegpunkten, Belegpunkt i zeigt i+1', () => {
    expect(leiteAnsichtAb({ typ: 'fahrt', stationId: 'terminal' }, daten.stationen))
      .toEqual({ ort: 'terminal', belegpunkte: 0 });
    expect(leiteAnsichtAb({ typ: 'belegpunkt', stationId: 'terminal', index: 1 }, daten.stationen))
      .toEqual({ ort: 'terminal', belegpunkte: 2 });
  });

  it('Sprung zeigt alle Belegpunkte der Station', () => {
    expect(leiteAnsichtAb({ typ: 'sprung', stationId: 'besprechung' }, daten.stationen))
      .toEqual({ ort: 'besprechung', belegpunkte: 3 });
    expect(leiteAnsichtAb({ typ: 'sprung-totale' }, daten.stationen))
      .toEqual({ ort: 'totale', belegpunkte: 0 });
  });
});
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run (in `app/`): `npm test -- tests/zustand.test.js`
Expected: FAIL — „Failed to resolve import ../src/zustand.js".

- [ ] **Step 3: Implementierung** — `app/src/zustand.js`

```js
// Linearer Vortragsstand plus überlagernder Direktsprung (Fragerunde).
// weiter()/zurueck() räumen einen aktiven Sprung ab und arbeiten auf der Liste.
export class Zustandsmaschine {
  constructor(schritte) {
    this.schritte = schritte;
    this.index = 0;
    this.sprung = null;
  }

  get aktuell() {
    return this.sprung ?? this.schritte[this.index];
  }

  weiter() {
    if (this.sprung) {
      this.sprung = null;
      return this.aktuell;
    }
    if (this.index < this.schritte.length - 1) this.index++;
    return this.aktuell;
  }

  zurueck() {
    if (this.sprung) {
      this.sprung = null;
      return this.aktuell;
    }
    if (this.index > 0) this.index--;
    return this.aktuell;
  }

  springeZuStation(stationId) {
    this.sprung = { typ: 'sprung', stationId };
    return this.aktuell;
  }

  springeZurTotale() {
    this.sprung = { typ: 'sprung-totale' };
    return this.aktuell;
  }

  setzeStand(stand) {
    if (!stand || typeof stand.index !== 'number') return;
    if (stand.index < 0 || stand.index >= this.schritte.length) return;
    this.index = stand.index;
    this.sprung = stand.sprung ?? null;
  }
}

// Übersetzt den aktuellen Schritt in das, was Kamera und Panel zeigen sollen.
export function leiteAnsichtAb(schritt, stationen) {
  switch (schritt.typ) {
    case 'totale':
    case 'rueckflug':
    case 'sprung-totale':
      return { ort: 'totale', belegpunkte: 0 };
    case 'fahrt':
      return { ort: schritt.stationId, belegpunkte: 0 };
    case 'belegpunkt':
      return { ort: schritt.stationId, belegpunkte: schritt.index + 1 };
    case 'sprung': {
      const st = stationen.find((s) => s.id === schritt.stationId);
      return { ort: schritt.stationId, belegpunkte: st ? st.belegpunkte.length : 0 };
    }
    default:
      return { ort: 'totale', belegpunkte: 0 };
  }
}
```

Hinweis: Der Test erwartet, dass `weiter()`/`zurueck()` bei aktivem Sprung NUR den Sprung abräumen (Rückkehr zum linearen Stand), ohne zusätzlich zu schalten — genau so ist es oben implementiert.

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run (in `app/`): `npm test -- tests/zustand.test.js`
Expected: PASS (8 Tests).

- [ ] **Step 5: Commit**

```bash
git add app/src/zustand.js app/tests/zustand.test.js
git commit -m "feat(app): Zustandsmaschine mit Direktsprung und Ansichtsableitung"
```

---

### Task 4: Kamerafahrt-Mathematik

**Files:**
- Create: `app/src/kamera.js`
- Test: `app/tests/kamera.test.js`

- [ ] **Step 1: Fehlschlagenden Test schreiben** — `app/tests/kamera.test.js`

```js
import { describe, it, expect } from 'vitest';
import { glaetten, lerp3, Kamerafahrt } from '../src/kamera.js';

describe('glaetten (kubisches Ease-in-out)', () => {
  it('liefert die Fixpunkte 0, 0.5 und 1', () => {
    expect(glaetten(0)).toBe(0);
    expect(glaetten(0.5)).toBeCloseTo(0.5, 10);
    expect(glaetten(1)).toBe(1);
  });

  it('ist monoton steigend', () => {
    let vorher = -1;
    for (let t = 0; t <= 1.0001; t += 0.01) {
      const e = glaetten(Math.min(t, 1));
      expect(e).toBeGreaterThanOrEqual(vorher);
      vorher = e;
    }
  });
});

describe('lerp3', () => {
  it('interpoliert komponentenweise', () => {
    expect(lerp3([0, 0, 0], [10, -4, 2], 0.5)).toEqual([5, -2, 1]);
    expect(lerp3([1, 2, 3], [1, 2, 3], 0.7)).toEqual([1, 2, 3]);
  });
});

describe('Kamerafahrt', () => {
  const von = { position: [0, 0, 0], blickziel: [0, 0, -1] };
  const nach = { position: [10, 4, -6], blickziel: [12, 1, -9] };

  it('endet exakt auf der Zielpose, unabhängig von der Schrittweite', () => {
    const fahrt = new Kamerafahrt(von, nach, 6);
    let pose;
    // unregelmäßige Frame-Zeiten, Summe > Dauer
    for (const dt of [0.016, 0.4, 1.3, 0.016, 2.0, 3.0]) pose = fahrt.fortschritt(dt);
    expect(fahrt.fertig).toBe(true);
    expect(pose.position).toEqual(nach.position);
    expect(pose.blickziel).toEqual(nach.blickziel);
  });

  it('abbrechen() (Skip) springt hart auf die Zielpose', () => {
    const fahrt = new Kamerafahrt(von, nach, 6);
    fahrt.fortschritt(0.5);
    const pose = fahrt.abbrechen();
    expect(fahrt.fertig).toBe(true);
    expect(pose.position).toEqual(nach.position);
  });

  it('ist bei halber Zeit genau in der Mitte (deterministisch)', () => {
    const fahrt = new Kamerafahrt(von, nach, 4);
    const pose = fahrt.fortschritt(2);
    expect(pose.position[0]).toBeCloseTo(5, 10);
    expect(pose.blickziel[1]).toBeCloseTo(0.5, 10);
  });
});
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run (in `app/`): `npm test -- tests/kamera.test.js`
Expected: FAIL — „Failed to resolve import ../src/kamera.js".

- [ ] **Step 3: Implementierung** — `app/src/kamera.js`

```js
// Zeitbasierte, framerate-unabhängige Kamerafahrt (Spec §5: deterministisch, Skip → Zielpose).
export function glaetten(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export function lerp3(a, b, t) {
  return [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t,
  ];
}

export class Kamerafahrt {
  constructor(von, nach, dauerS) {
    this.von = von;
    this.nach = nach;
    this.dauerS = dauerS;
    this.zeit = 0;
    this.fertig = false;
  }

  fortschritt(deltaS) {
    this.zeit += deltaS;
    const t = this.dauerS <= 0 ? 1 : Math.min(this.zeit / this.dauerS, 1);
    if (t >= 1) {
      this.fertig = true;
      return { position: [...this.nach.position], blickziel: [...this.nach.blickziel] };
    }
    const e = glaetten(t);
    return {
      position: lerp3(this.von.position, this.nach.position, e),
      blickziel: lerp3(this.von.blickziel, this.nach.blickziel, e),
    };
  }

  abbrechen() {
    this.zeit = this.dauerS;
    this.fertig = true;
    return { position: [...this.nach.position], blickziel: [...this.nach.blickziel] };
  }
}
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run (in `app/`): `npm test -- tests/kamera.test.js`
Expected: PASS (6 Tests).

- [ ] **Step 5: Commit**

```bash
git add app/src/kamera.js app/tests/kamera.test.js
git commit -m "feat(app): deterministische Kamerafahrt mit Easing und Skip"
```

---

### Task 5: Tastatur-Reducer & Eingabesperre

**Files:**
- Create: `app/src/steuerung.js`
- Test: `app/tests/steuerung.test.js`

- [ ] **Step 1: Fehlschlagenden Test schreiben** — `app/tests/steuerung.test.js`

```js
import { describe, it, expect } from 'vitest';
import { tasteZuAktion, Eingabesperre } from '../src/steuerung.js';
import daten from '../src/stationen.json';

describe('tasteZuAktion (Spec §6)', () => {
  it('belegt weiter/zurueck auf Pfeile, Leertaste und Bild-Tasten', () => {
    expect(tasteZuAktion('ArrowRight', daten.stationen)).toEqual({ typ: 'weiter' });
    expect(tasteZuAktion(' ', daten.stationen)).toEqual({ typ: 'weiter' });
    expect(tasteZuAktion('PageDown', daten.stationen)).toEqual({ typ: 'weiter' });
    expect(tasteZuAktion('ArrowLeft', daten.stationen)).toEqual({ typ: 'zurueck' });
    expect(tasteZuAktion('PageUp', daten.stationen)).toEqual({ typ: 'zurueck' });
  });

  it('übersetzt Ziffern in Stations-Sprünge und 0 in die Totale', () => {
    expect(tasteZuAktion('3', daten.stationen)).toEqual({ typ: 'sprung', stationId: 'terminal' });
    expect(tasteZuAktion('6', daten.stationen)).toEqual({ typ: 'sprung', stationId: 'besprechung' });
    expect(tasteZuAktion('0', daten.stationen)).toEqual({ typ: 'totale' });
    expect(tasteZuAktion('7', daten.stationen)).toBeNull();
  });

  it('belegt S, V und B; Escape ist bewusst NICHT belegt', () => {
    expect(tasteZuAktion('s', daten.stationen)).toEqual({ typ: 'skip' });
    expect(tasteZuAktion('V', daten.stationen)).toEqual({ typ: 'video' });
    expect(tasteZuAktion('b', daten.stationen)).toEqual({ typ: 'schwarz' });
    expect(tasteZuAktion('Escape', daten.stationen)).toBeNull();
  });
});

describe('Eingabesperre (während Kamerafahrt)', () => {
  it('lässt Aktionen ohne Sperre durch', () => {
    const sperre = new Eingabesperre();
    expect(sperre.verarbeite({ typ: 'weiter' })).toEqual({ typ: 'weiter' });
  });

  it('puffert bei aktiver Sperre genau einen weiter-Druck', () => {
    const sperre = new Eingabesperre();
    sperre.sperren();
    expect(sperre.verarbeite({ typ: 'weiter' })).toBeNull();
    expect(sperre.verarbeite({ typ: 'weiter' })).toBeNull(); // zweiter Druck verworfen
    expect(sperre.verarbeite({ typ: 'sprung', stationId: 'terminal' })).toBeNull();
    expect(sperre.entsperren()).toEqual({ typ: 'weiter' }); // genau einer kommt nach
    expect(sperre.entsperren()).toBeNull();
  });

  it('lässt skip und schwarz auch bei Sperre durch', () => {
    const sperre = new Eingabesperre();
    sperre.sperren();
    expect(sperre.verarbeite({ typ: 'skip' })).toEqual({ typ: 'skip' });
    expect(sperre.verarbeite({ typ: 'schwarz' })).toEqual({ typ: 'schwarz' });
  });
});
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run (in `app/`): `npm test -- tests/steuerung.test.js`
Expected: FAIL — „Failed to resolve import ../src/steuerung.js".

- [ ] **Step 3: Implementierung** — `app/src/steuerung.js`

```js
// Tastenbelegung laut Spec §6. Escape gehört dem Browser (Vollbild) und wird nie belegt.
export function tasteZuAktion(key, stationen) {
  switch (key) {
    case 'ArrowRight':
    case ' ':
    case 'PageDown':
      return { typ: 'weiter' };
    case 'ArrowLeft':
    case 'PageUp':
      return { typ: 'zurueck' };
    case '0':
      return { typ: 'totale' };
    case 's': case 'S':
      return { typ: 'skip' };
    case 'v': case 'V':
      return { typ: 'video' };
    case 'b': case 'B':
      return { typ: 'schwarz' };
    default: {
      if (/^[1-9]$/.test(key)) {
        const st = stationen.find((s) => s.nr === Number(key));
        return st ? { typ: 'sprung', stationId: st.id } : null;
      }
      return null;
    }
  }
}

// Während einer Fahrt: alles sperren, genau EINEN weiter-Druck puffern (Spec §6).
// skip und schwarz müssen immer sofort wirken.
export class Eingabesperre {
  constructor() {
    this.gesperrt = false;
    this.puffer = null;
  }

  sperren() {
    this.gesperrt = true;
    this.puffer = null;
  }

  entsperren() {
    const gepuffert = this.puffer;
    this.puffer = null;
    this.gesperrt = false;
    return gepuffert;
  }

  verarbeite(aktion) {
    if (!aktion) return null;
    if (!this.gesperrt) return aktion;
    if (aktion.typ === 'skip' || aktion.typ === 'schwarz') return aktion;
    if (aktion.typ === 'weiter' && !this.puffer) this.puffer = aktion;
    return null;
  }
}
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run (in `app/`): `npm test -- tests/steuerung.test.js`
Expected: PASS (6 Tests).

- [ ] **Step 5: Commit**

```bash
git add app/src/steuerung.js app/tests/steuerung.test.js
git commit -m "feat(app): Tastatur-Reducer und Eingabesperre mit Ein-Druck-Puffer"
```

---

### Task 6: Sitzungsspeicher (Reload-Sicherheit)

**Files:**
- Create: `app/src/speicher.js`
- Test: `app/tests/speicher.test.js`

- [ ] **Step 1: Fehlschlagenden Test schreiben** — `app/tests/speicher.test.js`

```js
import { describe, it, expect } from 'vitest';
import { speichereStand, ladeStand } from '../src/speicher.js';

function attrappenStorage() {
  const daten = new Map();
  return {
    getItem: (k) => (daten.has(k) ? daten.get(k) : null),
    setItem: (k, v) => daten.set(k, String(v)),
  };
}

describe('speichereStand / ladeStand', () => {
  it('speichert und lädt Index und Sprung', () => {
    const storage = attrappenStorage();
    speichereStand(storage, { index: 7, sprung: { typ: 'sprung', stationId: 'pruefstand' } });
    expect(ladeStand(storage)).toEqual({ index: 7, sprung: { typ: 'sprung', stationId: 'pruefstand' } });
  });

  it('liefert null, wenn nichts gespeichert ist', () => {
    expect(ladeStand(attrappenStorage())).toBeNull();
  });

  it('liefert null bei kaputtem JSON statt zu werfen', () => {
    const storage = attrappenStorage();
    storage.setItem('rundgang-stand', '{kaputt');
    expect(ladeStand(storage)).toBeNull();
  });
});
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run (in `app/`): `npm test -- tests/speicher.test.js`
Expected: FAIL — „Failed to resolve import ../src/speicher.js".

- [ ] **Step 3: Implementierung** — `app/src/speicher.js`

```js
// Reload-Sicherheit (Spec §6): Stand überlebt ein versehentliches F5.
// storage ist injizierbar (sessionStorage in der App, Attrappe im Test).
const SCHLUESSEL = 'rundgang-stand';

export function speichereStand(storage, stand) {
  storage.setItem(SCHLUESSEL, JSON.stringify({ index: stand.index, sprung: stand.sprung ?? null }));
}

export function ladeStand(storage) {
  const roh = storage.getItem(SCHLUESSEL);
  if (!roh) return null;
  try {
    const stand = JSON.parse(roh);
    if (typeof stand.index !== 'number') return null;
    return { index: stand.index, sprung: stand.sprung ?? null };
  } catch {
    return null;
  }
}
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run (in `app/`): `npm test -- tests/speicher.test.js`
Expected: PASS (3 Tests).

- [ ] **Step 5: Commit**

```bash
git add app/src/speicher.js app/tests/speicher.test.js
git commit -m "feat(app): sessionStorage-Persistenz des Vortragsstands"
```

---

### Task 7: Overlays (Panel, Titel, Schwarzbild, Video-Großansicht)

**Files:**
- Create: `app/src/overlays.js`
- Test: `app/tests/overlays.test.js`

- [ ] **Step 1: Fehlschlagenden Test schreiben** — `app/tests/overlays.test.js`

```js
import { describe, it, expect, beforeEach } from 'vitest';
import { zeigePanel, versteckePanel, schalteSchwarzbild, zeigeTitel, schalteDimmer } from '../src/overlays.js';
import daten from '../src/stationen.json';

let panel, schwarz, titel, dimmer;

beforeEach(() => {
  document.body.innerHTML =
    '<div id="titel" hidden></div><div id="dimmer"></div><aside id="panel"></aside><div id="schwarzbild" hidden></div>';
  panel = document.getElementById('panel');
  schwarz = document.getElementById('schwarzbild');
  titel = document.getElementById('titel');
  dimmer = document.getElementById('dimmer');
});

describe('zeigePanel', () => {
  const station = daten.stationen.find((s) => s.id === 'terminal');

  it('rendert Nummer, Titel, Kernaussage und nur die sichtbaren Belegpunkte', () => {
    zeigePanel(panel, station, 2);
    expect(panel.classList.contains('sichtbar')).toBe(true);
    expect(panel.querySelector('.stationsnummer').textContent).toBe('Station 3');
    expect(panel.querySelector('h2').textContent).toBe('Fragen statt Formeln');
    expect(panel.querySelector('.kernaussage').textContent).toContain('PLATZHALTER');
    expect(panel.querySelectorAll('li')).toHaveLength(2);
    expect(panel.querySelector('.kapitel').textContent).toBe('Kap. 3.4, 4.3');
  });

  it('rendert bei 0 sichtbaren Belegpunkten eine leere Liste', () => {
    zeigePanel(panel, station, 0);
    expect(panel.querySelectorAll('li')).toHaveLength(0);
  });

  it('verwendet textContent (kein HTML-Injection über JSON-Inhalte)', () => {
    zeigePanel(panel, { ...station, kernaussage: '<img src=x>' }, 0);
    expect(panel.querySelector('.kernaussage img')).toBeNull();
  });
});

describe('versteckePanel / zeigeTitel / schalteSchwarzbild / schalteDimmer', () => {
  it('versteckt das Panel über die Sichtbarkeitsklasse', () => {
    panel.classList.add('sichtbar');
    versteckePanel(panel);
    expect(panel.classList.contains('sichtbar')).toBe(false);
  });

  it('zeigt und versteckt den Titel', () => {
    zeigeTitel(titel, true);
    expect(titel.hidden).toBe(false);
    zeigeTitel(titel, false);
    expect(titel.hidden).toBe(true);
  });

  it('schaltet das Schwarzbild um und meldet den neuen Zustand', () => {
    expect(schalteSchwarzbild(schwarz)).toBe(true);
    expect(schwarz.hidden).toBe(false);
    expect(schalteSchwarzbild(schwarz)).toBe(false);
    expect(schwarz.hidden).toBe(true);
  });

  it('schaltet den Dimmer über die aktiv-Klasse', () => {
    schalteDimmer(dimmer, true);
    expect(dimmer.classList.contains('aktiv')).toBe(true);
    schalteDimmer(dimmer, false);
    expect(dimmer.classList.contains('aktiv')).toBe(false);
  });
});
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run (in `app/`): `npm test -- tests/overlays.test.js`
Expected: FAIL — „Failed to resolve import ../src/overlays.js".

- [ ] **Step 3: Implementierung** — `app/src/overlays.js`

```js
// DOM-Overlays über dem Canvas (Spec §5): scharfer Browser-Text, keine 3D-Texturen.
// Inhalte kommen aus stationen.json und werden ausschließlich als textContent gesetzt.
export function zeigePanel(panelEl, station, anzahlBelegpunkte) {
  panelEl.replaceChildren();

  const nummer = document.createElement('div');
  nummer.className = 'stationsnummer';
  nummer.textContent = `Station ${station.nr}`;
  panelEl.append(nummer);

  const ueberschrift = document.createElement('h2');
  ueberschrift.textContent = station.titel;
  panelEl.append(ueberschrift);

  const kernaussage = document.createElement('p');
  kernaussage.className = 'kernaussage';
  kernaussage.textContent = station.kernaussage;
  panelEl.append(kernaussage);

  const liste = document.createElement('ul');
  for (const punkt of station.belegpunkte.slice(0, anzahlBelegpunkte)) {
    const li = document.createElement('li');
    li.textContent = punkt;
    liste.append(li);
  }
  panelEl.append(liste);

  const kapitel = document.createElement('div');
  kapitel.className = 'kapitel';
  kapitel.textContent = station.kapitel;
  panelEl.append(kapitel);

  panelEl.classList.add('sichtbar'); // CSS blendet über opacity in ~300 ms ein (Spec §5)
}

export function versteckePanel(panelEl) {
  panelEl.classList.remove('sichtbar');
}

// Dimmt die Szene an Stationen leicht ab (Spec §5); Element: #dimmer.
export function schalteDimmer(dimmerEl, aktiv) {
  dimmerEl.classList.toggle('aktiv', aktiv);
}

export function zeigeTitel(titelEl, sichtbar) {
  titelEl.hidden = !sichtbar;
}

export function schalteSchwarzbild(schwarzEl) {
  schwarzEl.hidden = !schwarzEl.hidden;
  return !schwarzEl.hidden;
}

// Video-Großansicht (Taste V): zeigt/versteckt das Overlay und startet/pausiert das Video.
export function schalteVideoGross(overlayEl, videoEl) {
  if (overlayEl.hidden) {
    overlayEl.hidden = false;
    videoEl.play().catch(() => {}); // fehlende Datei o. Ä. darf den Vortrag nie stoppen
    return true;
  }
  videoEl.pause();
  overlayEl.hidden = true;
  return false;
}
```

- [ ] **Step 4: Test laufen lassen — muss bestehen**

Run (in `app/`): `npm test -- tests/overlays.test.js`
Expected: PASS (7 Tests).

- [ ] **Step 5: Commit**

```bash
git add app/src/overlays.js app/tests/overlays.test.js
git commit -m "feat(app): DOM-Overlays fuer Panel, Titel, Schwarzbild und Video"
```

---

### Task 8: Three.js-Bühne mit Platzhalterszene & Integration

**Files:**
- Create: `app/src/szene.js`
- Modify: `app/src/main.js` (Stub aus Task 1 wird vollständig ersetzt)

- [ ] **Step 1: szene.js anlegen**

```js
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export function erzeugeRenderer(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Spec §5: Deckel 2
  renderer.setSize(window.innerWidth, window.innerHeight);
  return renderer;
}

export function erzeugeSzene() {
  const szene = new THREE.Scene();
  szene.background = new THREE.Color(0xdfe3e6);
  szene.add(new THREE.AmbientLight(0xffffff, 0.9));
  const sonne = new THREE.DirectionalLight(0xffffff, 1.6);
  sonne.position.set(12, 20, 8);
  szene.add(sonne);
  return szene;
}

// Graue Boxen an den Blickzielen aus stationen.json, bis das Blender-Modell da ist.
export function bauePlatzhalter(szene, daten) {
  const gruppe = new THREE.Group();
  gruppe.name = 'Platzhalter';

  const boden = new THREE.Mesh(
    new THREE.BoxGeometry(34, 0.2, 20),
    new THREE.MeshStandardMaterial({ color: 0x9aa0a4 }),
  );
  boden.position.y = -0.1;
  gruppe.add(boden);

  for (const st of daten.stationen) {
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(2, 2, 2),
      new THREE.MeshStandardMaterial({ color: 0xc2c8cc }),
    );
    box.position.set(st.kamera.blickziel[0], 1, st.kamera.blickziel[2]);
    box.name = `Station_${st.nr}_${st.id}`;
    gruppe.add(box);
  }

  // Monitorfläche für die Videotextur — Name ist Vertrag mit videotextur.js und Blender.
  const terminal = daten.stationen.find((s) => s.id === 'terminal');
  const monitor = new THREE.Mesh(
    new THREE.PlaneGeometry(1.6, 0.9),
    new THREE.MeshBasicMaterial({ color: 0x222222 }),
  );
  monitor.position.set(terminal.kamera.blickziel[0], 1.5, terminal.kamera.blickziel[2] + 1.05);
  // UVs auf glTF-Konvention spiegeln, damit die Videotextur (flipY=false, Task 10)
  // auf Platzhalter und Blender-Export identisch orientiert ist.
  const uv = monitor.geometry.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getY(i));
  uv.needsUpdate = true;
  monitor.name = 'Monitor_Bildschirm';
  gruppe.add(monitor);

  szene.add(gruppe);
  return gruppe;
}

// Lädt szene.glb (URL) oder parst einen ArrayBuffer (Notfall-Build) und ersetzt den Platzhalter.
export async function ladeModell(szene, quelle) {
  const lader = new GLTFLoader();
  const gltf =
    typeof quelle === 'string'
      ? await lader.loadAsync(quelle)
      : await new Promise((ok, fehler) => lader.parse(quelle, '', ok, fehler));
  const platzhalter = szene.getObjectByName('Platzhalter');
  if (platzhalter) szene.remove(platzhalter);
  gltf.scene.name = 'Werkstatt';
  szene.add(gltf.scene);
  return gltf.scene;
}

export function base64ZuArrayBuffer(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}
```

- [ ] **Step 2: main.js anlegen** (Integration aller Module; die Video-/Waypoint-Teile kommen in Task 9/10 dazu)

```js
import * as THREE from 'three';
import daten from './stationen.json';
import { baueSchritte } from './schritte.js';
import { Zustandsmaschine, leiteAnsichtAb } from './zustand.js';
import { Kamerafahrt } from './kamera.js';
import { tasteZuAktion, Eingabesperre } from './steuerung.js';
import { speichereStand, ladeStand } from './speicher.js';
import { zeigePanel, versteckePanel, zeigeTitel, schalteSchwarzbild, schalteVideoGross, schalteDimmer } from './overlays.js';
import { erzeugeRenderer, erzeugeSzene, bauePlatzhalter, ladeModell, base64ZuArrayBuffer } from './szene.js';

const canvas = document.getElementById('buehne');
const panelEl = document.getElementById('panel');
const titelEl = document.getElementById('titel');
const schwarzEl = document.getElementById('schwarzbild');
const dimmerEl = document.getElementById('dimmer');
const videoOverlayEl = document.getElementById('video-overlay');
const videoGrossEl = document.getElementById('video-gross');

const renderer = erzeugeRenderer(canvas);
const szene = erzeugeSzene();
const kamera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 200);

const schritte = baueSchritte(daten.stationen);
const zustand = new Zustandsmaschine(schritte);
const sperre = new Eingabesperre();

let aktuelleFahrt = null;
let aktuellerOrt = 'totale';

function poseFuerOrt(ort) {
  if (ort === 'totale') return daten.totale.kamera;
  return daten.stationen.find((s) => s.id === ort).kamera;
}

function setzeKamera(pose) {
  kamera.position.set(...pose.position);
  kamera.lookAt(...pose.blickziel);
}

// Wendet den aktuellen Schritt auf Kamera und Overlays an.
// sofort=true (Reload-Wiederherstellung): keine Fahrt, direkt Zielpose.
function wendeAnsichtAn(sofort = false) {
  const ansicht = leiteAnsichtAb(zustand.aktuell, daten.stationen);

  if (ansicht.ort !== aktuellerOrt) {
    const von = {
      position: kamera.position.toArray(),
      blickziel: aktuelleFahrt ? aktuelleFahrt.nach.blickziel : poseFuerOrt(aktuellerOrt).blickziel,
    };
    const nach = poseFuerOrt(ansicht.ort);
    aktuellerOrt = ansicht.ort;
    versteckePanel(panelEl);
    zeigeTitel(titelEl, false); // Spec §4: während der Fahrt kein neuer Text
    schalteDimmer(dimmerEl, false);
    if (sofort) {
      aktuelleFahrt = null;
      setzeKamera(nach);
      zeigeAnkunft(ansicht);
    } else {
      const dauer = zustand.aktuell.typ?.startsWith('sprung') ? daten.sprung_dauer_s : nach.dauer_s;
      aktuelleFahrt = new Kamerafahrt(von, { position: nach.position, blickziel: nach.blickziel }, dauer);
      sperre.sperren();
    }
  } else {
    zeigeAnkunft(ansicht);
  }
  speichereStand(sessionStorage, zustand);
}

function zeigeAnkunft(ansicht) {
  zeigeTitel(titelEl, ansicht.ort === 'totale'); // Titel erst bei Ankunft (Spec §4)
  schalteDimmer(dimmerEl, ansicht.ort !== 'totale');
  if (ansicht.ort === 'totale') {
    versteckePanel(panelEl);
    return;
  }
  const station = daten.stationen.find((s) => s.id === ansicht.ort);
  zeigePanel(panelEl, station, ansicht.belegpunkte);
}

function fuehreAktionAus(aktion) {
  switch (aktion.typ) {
    case 'weiter': zustand.weiter(); wendeAnsichtAn(); break;
    case 'zurueck': zustand.zurueck(); wendeAnsichtAn(); break;
    case 'totale': zustand.springeZurTotale(); wendeAnsichtAn(); break;
    case 'sprung': zustand.springeZuStation(aktion.stationId); wendeAnsichtAn(); break;
    case 'skip':
      if (aktuelleFahrt) {
        setzeKamera(aktuelleFahrt.abbrechen());
        beendeFahrt();
      }
      break;
    case 'video': schalteVideoGross(videoOverlayEl, videoGrossEl); break; // V wirkt global (Spec §6)
    case 'schwarz': schalteSchwarzbild(schwarzEl); break;
  }
}

function beendeFahrt() {
  aktuelleFahrt = null;
  zeigeAnkunft(leiteAnsichtAb(zustand.aktuell, daten.stationen));
  const gepuffert = sperre.entsperren();
  if (gepuffert) fuehreAktionAus(gepuffert);
}

window.addEventListener('keydown', (ereignis) => {
  // Prüfungsraum-Härtung (Spec §6): F5/Scroll-Tasten neutralisieren.
  if (ereignis.key === 'F5') { ereignis.preventDefault(); return; }
  // Leertaste bei offener Großansicht = Pause/Weiter des Videos.
  if (ereignis.key === ' ' && !videoOverlayEl.hidden) {
    ereignis.preventDefault();
    if (videoGrossEl.paused) videoGrossEl.play().catch(() => {});
    else videoGrossEl.pause();
    return;
  }
  const aktion = tasteZuAktion(ereignis.key, daten.stationen);
  if (!aktion) return;
  ereignis.preventDefault();
  const freigegeben = sperre.verarbeite(aktion);
  if (freigegeben) fuehreAktionAus(freigegeben);
});

window.addEventListener('resize', () => {
  kamera.aspect = window.innerWidth / window.innerHeight;
  kamera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
});

const uhr = new THREE.Clock();
function schleife() {
  const delta = uhr.getDelta();
  if (aktuelleFahrt) {
    setzeKamera(aktuelleFahrt.fortschritt(delta));
    if (aktuelleFahrt.fertig) beendeFahrt();
  }
  renderer.render(szene, kamera);
  requestAnimationFrame(schleife);
}

async function start() {
  bauePlatzhalter(szene, daten);
  if (import.meta.env.VITE_NOTFALL === '1') {
    const { szeneGlbBase64 } = await import('./generiert/szene-glb.js');
    if (szeneGlbBase64) await ladeModell(szene, base64ZuArrayBuffer(szeneGlbBase64));
  } else {
    try {
      await ladeModell(szene, './szene.glb');
    } catch {
      // Kein Modell vorhanden (vor Task 11): Platzhalter bleibt stehen.
    }
  }

  const gespeichert = ladeStand(sessionStorage);
  if (gespeichert) zustand.setzeStand(gespeichert);
  setzeKamera(poseFuerOrt(leiteAnsichtAb(zustand.aktuell, daten.stationen).ort));
  aktuellerOrt = leiteAnsichtAb(zustand.aktuell, daten.stationen).ort;
  wendeAnsichtAn(true);
  schleife();
}

start();
```

- [ ] **Step 3: Alle Tests laufen lassen (Regressionscheck)**

Run (in `app/`): `npm test`
Expected: PASS — alle Tests aus Task 1–7 weiterhin grün.

- [ ] **Step 4: Visuelle Prüfung im Browser**

Run (in `app/`): `npm run dev` — `http://localhost:5173` öffnen und prüfen:
1. Totale sichtbar (grauer Boden, 6 Boxen), Titel-Panel unten links, Kopfzeile oben.
2. Pfeil rechts → Titel verschwindet, Kamera fliegt ~6 s weich zur ersten Box; bei Ankunft dunkelt die Szene leicht ab und das Panel „Station 1 / Wo die Zahl entsteht" blendet weich ein (0 Belegpunkte).
3. Dreimal Pfeil rechts → Belegpunkte erscheinen einzeln (PLATZHALTER-Texte).
4. Taste 6 → Fahrt zur Besprechungs-Box, Panel mit allen 3 Belegpunkten; Pfeil rechts → zurück im linearen Ablauf.
5. Taste 0 → Totale; B → Schwarzbild an/aus; S während einer Fahrt → harter Sprung ans Ziel.
6. Seite mitten im Ablauf über die Reload-Schaltfläche des Browsers neu laden (F5 ist absichtlich gesperrt) → die App steht wieder am selben Schritt (sessionStorage).
7. Doppeldruck während einer Fahrt → genau ein Schritt wird nachgeholt, nicht zwei.

- [ ] **Step 5: Commit**

```bash
git add app/src/szene.js app/src/main.js
git commit -m "feat(app): Three.js-Buehne, Platzhalterszene und Integrations-Loop"
```

---

### Task 9: Waypoint-Werkzeug (Dev)

**Files:**
- Create: `app/src/waypoint-werkzeug.js`
- Create: `app/public/standbilder/HINWEIS.md`
- Modify: `app/src/main.js` (Import + Aktivierung am Ende von `start()`)

- [ ] **Step 1: waypoint-werkzeug.js anlegen**

```js
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Nur im Dev-Modus mit ?werkzeug=1: freie Kamera. Taste W gibt die Pose als JSON aus
// (zum direkten Einfügen in stationen.json, Spec §5); Taste P lädt das aktuelle Bild
// als PNG herunter — Standbilder für die Druckansicht (Spec §7, Szenen-Thumbnail).
export function aktiviereWaypointWerkzeug(kamera, renderer, szene) {
  if (!import.meta.env.DEV) return null;
  if (new URLSearchParams(window.location.search).get('werkzeug') !== '1') return null;

  const orbit = new OrbitControls(kamera, renderer.domElement);
  orbit.target.set(0, 1, 0);

  window.addEventListener('keydown', (ereignis) => {
    if (ereignis.key === 'w' || ereignis.key === 'W') {
      const p = kamera.position;
      const z = orbit.target;
      const runden = (n) => Number(n.toFixed(2));
      console.log(JSON.stringify({
        position: [runden(p.x), runden(p.y), runden(p.z)],
        blickziel: [runden(z.x), runden(z.y), runden(z.z)],
        dauer_s: 5,
      }));
    }
    if (ereignis.key === 'p' || ereignis.key === 'P') {
      renderer.render(szene, kamera); // direkt vor toDataURL rendern (kein preserveDrawingBuffer)
      const link = document.createElement('a');
      link.href = renderer.domElement.toDataURL('image/png');
      link.download = 'standbild.png';
      link.click();
    }
  });

  console.info('[Waypoint-Werkzeug] aktiv: Maus = Kamera, W = Pose ausgeben, P = Standbild speichern');
  return orbit;
}
```

- [ ] **Step 2: In main.js einbinden** — genau vier Änderungen, in dieser Reihenfolge:

1. Import bei den übrigen Imports ergänzen:

```js
import { aktiviereWaypointWerkzeug } from './waypoint-werkzeug.js';
```

2. Oberhalb von `async function start()` die Modul-Variable deklarieren:

```js
let orbitAktiv = null;
```

3. In `start()` direkt vor `schleife();` einfügen:

```js
  orbitAktiv = aktiviereWaypointWerkzeug(kamera, renderer, szene);
```

4. In `schleife()` unmittelbar vor `renderer.render(szene, kamera);` einfügen:

```js
  if (orbitAktiv) orbitAktiv.update();
```

(Im Werkzeugmodus stören die automatischen Fahrten nicht, weil dort keine Vortrags-Tasten gedrückt werden.)

- [ ] **Step 3: Standbilder-Ablage anlegen** — `app/public/standbilder/HINWEIS.md`:

```markdown
# Standbilder für die Druckansicht

Pro Station ein PNG, Dateiname exakt `<stations-id>.png` (z. B. `terminal.png`).
Erzeugung: Dev-Server mit `?werkzeug=1` öffnen, Kamera passend zur Stationspose
einrichten, Taste P → Download, Datei hierher verschieben und umbenennen.
Fehlende Bilder blendet die Druckansicht automatisch aus (onerror).
```

- [ ] **Step 4: Prüfen**

Run (in `app/`): `npm run dev` — `http://localhost:5173/?werkzeug=1` öffnen.
Expected: Kamera per Maus frei drehbar/zoombar; Taste W schreibt eine JSON-Zeile mit `position`, `blickziel`, `dauer_s` in die Browser-Konsole; Taste P lädt ein PNG des aktuellen Bilds herunter. Ohne `?werkzeug=1` verhält sich die App wie in Task 8.

- [ ] **Step 5: Alle Tests laufen lassen**

Run (in `app/`): `npm test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/src/waypoint-werkzeug.js app/src/main.js app/public/standbilder/HINWEIS.md
git commit -m "feat(app): Dev-Waypoint-Werkzeug fuer Kameraposen und Standbilder"
```

---

### Task 10: Videotextur & Video-Handling

**Files:**
- Create: `app/src/videotextur.js`
- Create: `app/public/video/HINWEIS.md`
- Modify: `app/src/main.js` (Videotextur verbinden, Erststart nach Nutzergeste)

- [ ] **Step 1: videotextur.js anlegen**

```js
import * as THREE from 'three';

// Legt das 720p-Video als Textur auf das Mesh "Monitor_Bildschirm" (Namens-Vertrag
// mit Platzhalterszene und Blender-Export). Liefert false, wenn das Mesh fehlt.
export function verbindeVideoTextur(szene, videoEl) {
  const ziel = szene.getObjectByName('Monitor_Bildschirm');
  if (!ziel) return false;
  const textur = new THREE.VideoTexture(videoEl);
  textur.colorSpace = THREE.SRGBColorSpace; // Spec §5: sonst ausgewaschen
  textur.flipY = false; // glTF-UV-Konvention (V-Ursprung oben) — sonst steht das Video ab Task 11 kopf
  ziel.material = new THREE.MeshBasicMaterial({ map: textur });
  return true;
}
```

- [ ] **Step 2: Hinweisdatei anlegen** — `app/public/video/HINWEIS.md`

```markdown
# Demo-Videos

Hier gehören zwei Dateien hin (Aufnahme laut Spec §5 — separater Arbeitsschritt
„Inhalte", OBS-Screen-Recording des Prototyps, stumm, H.264):

- `demo_720.mp4`  — 1280x720, läuft geloopt als Textur auf dem Terminal-Monitor
- `demo_1080.mp4` — 1920x1080, Großansicht über Taste V

Bis die Aufnahmen existieren, zeigt der Monitor Schwarz und die Großansicht ein
leeres Videofenster; die App funktioniert vollständig ohne die Dateien.
```

- [ ] **Step 3: In main.js einbinden**

Import ergänzen:

```js
import { verbindeVideoTextur } from './videotextur.js';
```

Referenz auf das Textur-Video oben bei den anderen `getElementById`-Zeilen ergänzen:

```js
const videoTexturEl = document.getElementById('video-textur');
```

In `start()` nach dem Modell-Laden (nach dem `try/catch`-Block bzw. Notfall-Zweig) einfügen:

```js
  verbindeVideoTextur(szene, videoTexturEl);
```

Autoplay-Regel (Spec §5: Start erst nach Nutzergeste): im bestehenden `keydown`-Listener als erste Zeile nach der F5-Prüfung einfügen:

```js
  if (videoTexturEl.paused) videoTexturEl.play().catch(() => {});
```

- [ ] **Step 4: Prüfen (ohne echte Videos)**

Run (in `app/`): `npm run dev` — Ablauf bis Station 3 durchklicken.
Expected: Monitorfläche bleibt schwarz (Videodatei fehlt — kein Fehlerabbruch, Konsole darf 404 für die MP4s zeigen); Taste V an Station 3 öffnet die dunkle Großansicht, zweites V schließt sie. Danach eine beliebige MP4-Testdatei als `app/public/video/demo_720.mp4` einlegen und neu laden: die Fläche zeigt das laufende Video nach dem ersten Tastendruck.

- [ ] **Step 5: Alle Tests laufen lassen**

Run (in `app/`): `npm test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/src/videotextur.js app/public/video/HINWEIS.md app/src/main.js
git commit -m "feat(app): Videotextur am Terminal-Monitor und Video-Grossansicht"
```

---

### Task 11: Blender-Blockout, glTF-Export & Einbindung

**Voraussetzung:** Blender läuft mit aktiviertem MCP-Add-on (Verbindung besteht in dieser Umgebung). Das Skript wird über das MCP-Tool `execute_blender_code` ausgeführt; alternativ headless: `blender --background --python blender/blockout.py`.

**Files:**
- Create: `blender/blockout.py`
- Create: `app/public/szene.glb` (durch das Skript erzeugt)
- Modify: `app/src/stationen.json` (Kameraposen nachjustieren, per Waypoint-Werkzeug)

- [ ] **Step 1: blockout.py anlegen**

```python
"""Blockout der Instandhaltungswerkstatt (Stil C: Low-Poly, entsaettigte Farben).

Koordinaten-Vertrag: Three.js ist Y-up, Blender Z-up; der glTF-Exporter konvertiert
automatisch (+Y up). Die Hilfsfunktion pos() nimmt daher Three.js-Koordinaten
(x, y, z wie in stationen.json) und uebersetzt sie nach Blender (x, -z, y).
Objektnamen folgen dem Vertrag Station_<nr>_<id> bzw. Monitor_Bildschirm.
"""
import bpy
import os

ZIEL = os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd(),
                    "app", "public", "szene.glb")


def pos(x, y, z):
    return (x, -z, y)


def material(name, farbe):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*farbe, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def quader(name, groesse, position, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (groesse[0], groesse[1], groesse[2])
    obj.data.materials.append(mat)
    return obj


# ---- Szene leeren -----------------------------------------------------------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

GRAU_BODEN = (0.55, 0.58, 0.60)
GRAU_WAND = (0.76, 0.79, 0.81)
GRAU_OBJEKT = (0.62, 0.66, 0.69)
GRAU_DUNKEL = (0.30, 0.32, 0.34)
ROT_ZUG = (0.55, 0.16, 0.20)  # entsaettigtes Verkehrsrot, nur am Triebzug (Spec §2)

m_boden = material("Boden", GRAU_BODEN)
m_wand = material("Wand", GRAU_WAND)
m_objekt = material("Objekt", GRAU_OBJEKT)
m_dunkel = material("Dunkel", GRAU_DUNKEL)
m_zug = material("Zug", ROT_ZUG)

# ---- Halle ------------------------------------------------------------------
quader("Halle_Boden", (34, 20, 0.2), pos(0, -0.1, 0), m_boden)
quader("Halle_Wand_Nord", (34, 0.3, 6), pos(0, 3, -10), m_wand)
quader("Halle_Wand_Sued", (34, 0.3, 6), pos(0, 3, 10), m_wand)
quader("Halle_Wand_West", (0.3, 20, 6), pos(-17, 3, 0), m_wand)
quader("Halle_Wand_Ost", (0.3, 20, 6), pos(17, 3, 0), m_wand)

# ---- Gleis + Triebzug (quer durch die Halle bei z=0) ------------------------
quader("Gleis_Schiene_1", (30, 0.15, 0.15), pos(0, 0.08, -0.7), m_dunkel)
quader("Gleis_Schiene_2", (30, 0.15, 0.15), pos(0, 0.08, 0.7), m_dunkel)
quader("Triebzug_Korpus", (14, 1.6, 2.4), pos(1, 1.4, 0), m_zug)
quader("Triebzug_Dach", (13.4, 1.5, 0.4), pos(1, 2.4, 0), m_dunkel)

# ---- Stationen (Positionen = blickziel aus stationen.json) ------------------
quader("Station_1_meisterbuero", (3, 2.4, 2.6), pos(-10, 1.3, -5), m_objekt)
quader("Station_1_pinnwand", (2.2, 0.1, 1.2), pos(-10, 1.8, -6.2), m_wand)

quader("Station_2_datenraum", (2.6, 1.2, 2.4), pos(-3, 1.2, -6), m_objekt)
for i, dx in enumerate((-0.8, 0.0, 0.8)):
    quader(f"Station_2_regalbrett_{i}", (2.2, 1.0, 0.08), pos(-3, 0.6 + i * 0.7, -6), m_dunkel)

quader("Station_3_terminal_saeule", (0.6, 0.6, 1.4), pos(7, 0.7, -5), m_dunkel)
bpy.ops.mesh.primitive_plane_add(size=1, location=pos(7, 1.5, -3.95))
monitor = bpy.context.active_object
monitor.name = "Monitor_Bildschirm"
monitor.scale = (1.6, 0.9, 1)
monitor.rotation_euler = (1.5708, 0, 0)  # senkrecht stellen, Front Richtung Sued
monitor.data.materials.append(m_dunkel)

quader("Station_4_anzeigetafel", (3.2, 0.15, 1.8), pos(9, 2, 5.8), m_dunkel)
quader("Station_5_pruefstand", (2.8, 1.4, 1.0), pos(2, 0.5, 6), m_objekt)
quader("Station_6_besprechung_tisch", (2.4, 1.2, 0.75), pos(-9, 0.4, 6), m_objekt)

# ---- Stationsschilder: dunkler Wuerfel + helle Ziffer (Spec §4 Startbild) ---
for nr, (x, z) in {1: (-10, -5), 2: (-3, -6), 3: (7, -5), 4: (9, 5), 5: (2, 6), 6: (-9, 6)}.items():
    quader(f"Schild_{nr}", (0.5, 0.5, 0.5), pos(x, 3.4, z), m_dunkel)
    bpy.ops.object.text_add(location=pos(x, 3.4, z + 0.28))
    ziffer = bpy.context.active_object
    ziffer.name = f"Schild_{nr}_ziffer"
    ziffer.data.body = str(nr)
    ziffer.data.size = 0.35
    ziffer.data.extrude = 0.02
    ziffer.data.align_x = "CENTER"
    ziffer.data.align_y = "CENTER"
    ziffer.rotation_euler = (1.5708, 0, 0)  # aufrecht, Front nach Sueden (Three +z)
    ziffer.data.materials.append(m_wand)
    bpy.ops.object.convert(target="MESH")  # glTF exportiert Text-Objekte nicht zuverlaessig

# ---- Export -----------------------------------------------------------------
os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=ZIEL,
    export_format="GLB",
    export_lights=False,
    export_cameras=False,
    export_apply=True,
)
print(f"Export fertig: {ZIEL}")
```

- [ ] **Step 2: Skript ausführen**

Über die Blender-MCP-Anbindung (`execute_blender_code` mit dem Dateiinhalt; vorher in Blender eine leere Datei im Projektwurzel-Kontext öffnen oder `ZIEL` auf den absoluten Pfad `C:\Users\leopo\claude\Test_präsentation_T2000\app\public\szene.glb` setzen). Alternativ:

Run (Projektwurzel): `blender --background --python blender/blockout.py`
Expected: Ausgabe „Export fertig: …szene.glb"; Datei `app/public/szene.glb` existiert (Größe grob 50–500 KB).

- [ ] **Step 3: Im Browser prüfen**

Run (in `app/`): `npm run dev` — neu laden.
Expected: Statt der Platzhalter-Boxen die Blockout-Halle (Boden, Wände, roter Triebzug, Stationsobjekte, Nummern-Würfel). Videotextur läuft weiterhin auf der Monitorfläche (Objektname `Monitor_Bildschirm` bleibt erhalten — bei Namenskollision durch den Export in der Browser-Konsole `szene.getObjectByName('Monitor_Bildschirm')` prüfen).

- [ ] **Step 4: Kameraposen nachjustieren**

`http://localhost:5173/?werkzeug=1` öffnen; für die Totale und jede der 6 Stationen die Kamera per Maus einrichten, W drücken, die JSON-Ausgabe in `app/src/stationen.json` in das jeweilige `kamera`-Feld übernehmen (Dauer laut Spec: Fahrten 5–8 s, eher 5). Danach normalen Modus testen: jede Fahrt endet mit gut kadriertem Anschauungsobjekt und lesbarem Panel daneben.

- [ ] **Step 5: Graustufen-Gegenprobe (Spec §5)**

Screenshot der Totale und von Station 3 anfertigen, entsättigen (z. B. Windows-Fotos → Sättigung 0). Expected: Triebzug, Stationen und Schilder bleiben über Helligkeit/Form unterscheidbar. Falls nicht: Grauwerte in `blockout.py` spreizen und Export wiederholen.

- [ ] **Step 6: Alle Tests laufen lassen**

Run (in `app/`): `npm test`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add blender/blockout.py app/public/szene.glb app/src/stationen.json
git commit -m "feat(szene): Blender-Blockout der Werkstatt mit glTF-Export"
```

**Zeitbox-Hinweis (Spec §5/§9):** Alles über dieses Blockout hinaus (Detaillierung, schönere Materialien) ist Feinschliff mit hartem Budget von 2–3 Tagen und läuft interaktiv über die Blender-MCP-Anbindung — nicht Teil dieses Plans.

---

### Task 12: Druckansicht (abgabefähiges PDF)

**Files:**
- Create: `app/druck.html`
- Create: `app/src/druck.js`
- Create: `app/src/druck.css`
- Modify: `app/vite.config.js` (den `druck`-Eintrag aus Task 1 Step 3 aktivieren)

- [ ] **Step 1: druck.html anlegen**

```html
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Werkstattrundgang — Druckfassung</title>
  <link rel="stylesheet" href="./src/druck.css">
</head>
<body>
  <p class="druckhinweis">Diese Seite über Strg+P als PDF drucken (Querformat ist voreingestellt).</p>
  <main id="seiten"></main>
  <script type="module" src="./src/druck.js"></script>
</body>
</html>
```

- [ ] **Step 2: druck.js anlegen**

```js
// Erzeugt aus stationen.json die druckbare Fassung (Spec §7: PDF ist vollwertiges,
// abgabefähiges Dokument — weiße Seiten, identischer Slide-Inhalt, Kopfzeile).
import daten from './stationen.json';

const wurzel = document.getElementById('seiten');

function seite(inhaltBauen) {
  const abschnitt = document.createElement('section');
  abschnitt.className = 'seite';
  const kopf = document.createElement('header');
  kopf.textContent = 'DB Intern / DB internal';
  abschnitt.append(kopf);
  inhaltBauen(abschnitt);
  wurzel.append(abschnitt);
}

// Deckblatt
seite((s) => {
  const h1 = document.createElement('h1');
  h1.textContent = 'Eine Kennzahl — von der Werkstatthalle bis in die Planungsrunde';
  const p = document.createElement('p');
  p.className = 'untertitel';
  p.textContent = '[PLATZHALTER: Untertitel/Name/Datum]';
  s.append(h1, p);
});

// Eine Seite pro Station (inklusive Reservestation 6)
for (const st of daten.stationen) {
  seite((s) => {
    const nummer = document.createElement('div');
    nummer.className = 'stationsnummer';
    nummer.textContent = `Station ${st.nr}${st.im_rundgang === false ? ' (Reserve)' : ''}`;
    const h2 = document.createElement('h2');
    h2.textContent = st.titel;
    const kern = document.createElement('p');
    kern.className = 'kernaussage';
    kern.textContent = st.kernaussage;
    const liste = document.createElement('ul');
    for (const punkt of st.belegpunkte) {
      const li = document.createElement('li');
      li.textContent = punkt;
      liste.append(li);
    }
    const bild = document.createElement('img');
    bild.className = 'thumbnail';
    bild.src = `./standbilder/${st.id}.png`; // Spec §7: Szenen-Thumbnail (Taste P, Task 9)
    bild.alt = '';
    bild.onerror = () => bild.remove(); // solange das Standbild fehlt: ausblenden
    const fuss = document.createElement('div');
    fuss.className = 'kapitel';
    fuss.textContent = `${st.kapitel} · Anschauungsobjekt: ${st.anschauungsobjekt}`;
    s.append(nummer, h2, kern, liste, bild, fuss);
  });
}
```

- [ ] **Step 3: druck.css anlegen**

```css
@page { size: A4 landscape; margin: 0; }

* { margin: 0; padding: 0; box-sizing: border-box; }

body { font-family: Arial, Helvetica, sans-serif; color: #1a1a1a; background: #fff; }

.druckhinweis { padding: 0.5rem 1rem; background: #f4f4f4; font-size: 0.9rem; }
@media print { .druckhinweis { display: none; } }

.seite {
  width: 297mm;
  height: 209mm;
  padding: 14mm 18mm;
  page-break-after: always;
  position: relative;
  border-bottom: 1px dashed #d0d0d0; /* nur Bildschirm; Druck bricht ohnehin um */
}
@media print { .seite { border-bottom: none; } }

.seite header {
  position: absolute;
  top: 6mm; left: 18mm; right: 18mm;
  font-size: 10pt;
  color: #5a5a5a;
  border-bottom: 0.3mm solid #d0d0d0;
  padding-bottom: 2mm;
}

.seite h1 { font-size: 28pt; margin-top: 40mm; max-width: 220mm; }
.untertitel { font-size: 16pt; color: #5a5a5a; margin-top: 8mm; }

.stationsnummer { margin-top: 14mm; font-size: 12pt; color: #5a5a5a; text-transform: uppercase; letter-spacing: 0.06em; }
.seite h2 { font-size: 26pt; margin: 4mm 0 8mm; }
.kernaussage { font-size: 18pt; font-weight: bold; margin-bottom: 8mm; max-width: 230mm; }
.seite ul { list-style: none; }
.seite li { font-size: 15pt; padding: 2.5mm 0 2.5mm 8mm; position: relative; }
.seite li::before { content: "—"; position: absolute; left: 0; color: #5a5a5a; }
.thumbnail { position: absolute; bottom: 10mm; left: 18mm; width: 60mm; border: 0.3mm solid #d0d0d0; }
.kapitel { position: absolute; bottom: 10mm; right: 18mm; font-size: 10pt; color: #5a5a5a; }
```

- [ ] **Step 4: vite.config.js — druck-Eingang aktivieren**

Den auskommentierten Eintrag aus Task 1 Step 3 ersetzen durch:

```js
        druck: fileURLToPath(new URL('./druck.html', import.meta.url)),
```

- [ ] **Step 5: Prüfen**

Run (in `app/`): `npm run dev` — `http://localhost:5173/druck.html` öffnen.
Expected: Deckblatt + 6 Stationsseiten (Station 6 mit Zusatz „(Reserve)"), Kopfzeile auf jeder Seite; solange keine Standbilder in `public/standbilder/` liegen, erscheinen die Thumbnails nicht (onerror blendet sie aus — kein Fehler). Strg+P → Druckvorschau zeigt 7 Querformat-Seiten ohne abgeschnittene Inhalte.
Danach: `npm run build` — Expected: Build läuft fehlerfrei durch und `dist/druck.html` existiert.

- [ ] **Step 6: Commit**

```bash
git add app/druck.html app/src/druck.js app/src/druck.css app/vite.config.js
git commit -m "feat(app): abgabefaehige Druckansicht aus stationen.json"
```

---

### Task 13: Notfall-Single-File-Build

**Files:**
- Create: `app/vite.notfall.config.js`
- Create: `tools/baue-notfall.mjs`

- [ ] **Step 1: vite.notfall.config.js anlegen**

```js
import { defineConfig } from 'vite';
import { viteSingleFile } from 'vite-plugin-singlefile';
import { fileURLToPath, URL } from 'node:url';

// Notfall-Fassung (Spec §7, Stufe 1): eine einzige HTML-Datei, laeuft per Doppelklick
// ohne Webserver. Das glb kommt als Base64 aus src/generiert/szene-glb.js.
export default defineConfig({
  base: './',
  plugins: [viteSingleFile()],
  build: {
    outDir: 'dist-notfall',
    rollupOptions: {
      input: fileURLToPath(new URL('./index.html', import.meta.url)),
    },
  },
});
```

- [ ] **Step 2: tools/baue-notfall.mjs anlegen**

```js
// Baut die Notfall-Single-File-Fassung:
// 1. szene.glb als Base64 in src/generiert/szene-glb.js schreiben
// 2. vite build mit Notfall-Konfiguration (VITE_NOTFALL=1)
// 3. Stub wiederherstellen, Ergebnis nach dist-notfall/notfall.html benennen
// Aufruf aus der Projektwurzel: node tools/baue-notfall.mjs
import { readFileSync, writeFileSync, renameSync, existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { fileURLToPath, URL } from 'node:url';

const wurzel = fileURLToPath(new URL('..', import.meta.url));
const appDir = `${wurzel}app`;
const glbPfad = `${appDir}/public/szene.glb`;
const stubPfad = `${appDir}/src/generiert/szene-glb.js`;
const stubInhalt = readFileSync(stubPfad, 'utf8');

if (!existsSync(glbPfad)) {
  console.error('Abbruch: app/public/szene.glb fehlt (erst Task 11 ausführen).');
  process.exit(1);
}

const b64 = readFileSync(glbPfad).toString('base64');
writeFileSync(
  stubPfad,
  `// GENERIERT von tools/baue-notfall.mjs — nicht committen.\nexport const szeneGlbBase64 = '${b64}';\n`,
);

try {
  execSync('npx vite build --config vite.notfall.config.js', {
    cwd: appDir,
    stdio: 'inherit',
    env: { ...process.env, VITE_NOTFALL: '1' },
  });
  renameSync(`${appDir}/dist-notfall/index.html`, `${appDir}/dist-notfall/notfall.html`);
  console.log('Fertig: app/dist-notfall/notfall.html');
} finally {
  writeFileSync(stubPfad, stubInhalt); // Stub immer wiederherstellen
}
```

- [ ] **Step 3: Prüfen**

Run (Projektwurzel): `node tools/baue-notfall.mjs`
Expected: Build läuft durch, `app/dist-notfall/notfall.html` existiert (mehrere MB). `git status` zeigt `app/src/generiert/szene-glb.js` als unverändert (Stub wiederhergestellt).
Dann `notfall.html` per Doppelklick im Explorer öffnen (file://): Werkstatt-Szene lädt, Navigation funktioniert. (Die Videos liegen nicht in der Datei — Monitorfläche bleibt im Notfallmodus schwarz, das ist laut Spec akzeptiert; die MP4s liegen auf dem Stick daneben.)

- [ ] **Step 4: dist-Ordner ignorieren** — `.gitignore` (Projektwurzel) um folgende Zeilen ergänzen:

```
app/dist/
app/dist-notfall/
```

- [ ] **Step 5: Commit**

```bash
git add app/vite.notfall.config.js tools/baue-notfall.mjs .gitignore
git commit -m "feat(app): Notfall-Single-File-Build mit eingebetteter Szene"
```

---

### Task 14: Kiosk-Start & Prüfungstag-Checkliste

**Files:**
- Create: `app/start.bat`
- Create: `PRUEFUNGSTAG.md`

- [ ] **Step 1: start.bat anlegen** (Zeilenenden CRLF; Spec §7: Batchdatei ist der dokumentierte Startweg)

```bat
@echo off
rem Werkstattrundgang - Kiosk-Start (erst "npm run build" ausgefuehrt haben)
cd /d "%~dp0"
if not exist dist\index.html (
  echo Fehler: dist\index.html fehlt. Erst "npm run build" ausfuehren.
  pause
  exit /b 1
)
start "rundgang-server" cmd /c "npm run preview"
timeout /t 3 /nobreak >nul
rem Edge ist auf Windows 11 immer vorhanden und per App-Pfad startbar.
rem Fuer Chrome stattdessen die auskommentierte Zeile verwenden.
start "" msedge --kiosk http://localhost:4173 --edge-kiosk-type=fullscreen --no-first-run
rem start "" chrome --kiosk http://localhost:4173
```

- [ ] **Step 2: Prüfen**

Run (in `app/`): `npm run build`, dann `start.bat` doppelklicken.
Expected: Browser öffnet im Kiosk-Vollbild (keine Tabs/Adressleiste), Präsentation läuft; Esc verlässt den Kioskmodus NICHT (Chrome/Edge-Kiosk-Verhalten — genau deshalb liegt „Totale" auf Taste 0). Serverfenster danach schließen.

- [ ] **Step 3: PRUEFUNGSTAG.md anlegen** (Projektwurzel)

```markdown
# Checkliste Prüfungstag

## Eine Woche vorher
- [ ] DHBW schriftlich geklärt: eigener Laptop erlaubt? Beamer-Auflösung? HDMI oder VGA
      (Adapter!)? Abgabepflicht Foliensatz (→ PDF aus druck.html)? Rüstzeit vor dem Slot?
- [ ] Presenter-Remote-Tastencodes am eigenen Laptop verifiziert (erwartet: PageUp/PageDown).
- [ ] Generalprobe bei 1024x768 (4:3), 1280x800, 1920x1080 und Windows-Skalierung 125/150 %.
- [ ] Automatische Updates (Windows, Browser) pausiert; Umgebung eingefroren.
- [ ] `npm run build` + Probelauf über `app/start.bat`; `node tools/baue-notfall.mjs` frisch gebaut.
- [ ] USB-Stick 1 und 2: kompletter `app/`-Ordner ohne node_modules ist NICHT nötig — es reichen:
      `app/dist/`, `app/dist-notfall/notfall.html`, PDF-Export aus `druck.html`,
      MP4-Komplettmitschnitt, beide Demo-Videos.
- [ ] Kein `[PLATZHALTER]` mehr sichtbar (Abnahmekriterium Spec §10) — vorher Inhalte-Phase abschließen.

## Am Tag
- [ ] Laptop: Netzteil, HDMI-Adapter, Energiesparmodus aus, Benachrichtigungen aus, Flugmodus an.
- [ ] Bildschirm DUPLIZIEREN (nicht erweitern), dann `app/start.bat`.
- [ ] Startprobe: eine Fahrt hin und zurück, Taste B testen, dann auf Totale (Taste 0) parken.

## Wenn etwas hakt (Fallback-Leiter, Spec §7)
1. App startet nicht über start.bat → `app/dist-notfall/notfall.html` per Doppelklick.
2. WebGL/3D versagt → PDF-Foliensatz (identische Inhalte) in beliebigem PDF-Reader.
3. Laptop versagt → USB-Stick an Fremdrechner: PDF oder MP4-Mitschnitt.

## Tastenkarte (ausdrucken)
Pfeile/Leertaste/Bild-Tasten = weiter/zurück · 1–6 = Direktflug (6 = Reserve) · 0 = Totale
S = Fahrt überspringen · V = Demo-Video groß/klein · B = Schwarzbild · Esc = NICHT belegt
```

- [ ] **Step 4: Alle Tests + Build final**

Run (in `app/`): `npm test`, dann `npm run build`.
Expected: alle Tests PASS, Build fehlerfrei.

- [ ] **Step 5: Commit**

```bash
git add app/start.bat PRUEFUNGSTAG.md
git commit -m "feat: Kiosk-Start und Pruefungstag-Checkliste"
```

---

## Abschluss-Selbstcheck gegen die Spec (§10 Abnahmekriterien)

| Kriterium (Spec §10) | Abgedeckt durch |
|---|---|
| Komplett offline lauffähig, Start per Batchdatei | Task 14 (start.bat), Task 13 (Notfall) |
| Fahrten enden deterministisch in identischer Pose | Task 4 (Tests), Task 8 |
| Panels lesbar, relative Einheiten | Task 1 (clamp()-CSS); Projektionstest bleibt Teil der Generalprobe (separater Schritt) |
| Reload landet am selben Schritt | Task 6 + Task 8 (Step 4.6) |
| PDF aus stationen.json, eigenständig vortragsfähig | Task 12 (Szenen-Thumbnails via Taste P aus Task 9) |
| Kein präsentierbarer [PLATZHALTER] | spätere Inhalte-Phase; Checkliste Task 14 erinnert daran |
| Stoppuhr ≤ 13:00 | Generalprobe (nicht Teil dieses Plans, Spec §9 Phase 6) |
