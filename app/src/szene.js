import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export function erzeugeRenderer(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Spec §5: Deckel 2
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap; // weiche Schatten fuer den Iso-Look
  renderer.toneMapping = THREE.ACESFilmicToneMapping; // filmische Abstufung — Materialien lesen sich besser
  renderer.toneMappingExposure = 0.95; // knapp unter 1: sonst laufen Dach, Pfetten und Maschinenbank weiss zu
  return renderer;
}

// Alle Meshes eines Teilbaums werfen und empfangen Schatten.
// Die Gebaeudehuelle (Dach/Waende) wirft KEINE Schatten, sonst laege die ganze
// geschlossene Halle im Eigenschatten — die Sonne soll wie im Iso-Look einfallen.
const HUELLE = /^(Dach_|Wand_|Halle_|Relief_|Schraffur_|Grube_Kante_|Bodenfuge)/;

export function aktiviereSchatten(objekt) {
  objekt.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = !HUELLE.test(o.name);
      o.receiveShadow = true;
    }
  });
}

export function erzeugeSzene(renderer) {
  const szene = new THREE.Scene();
  szene.background = erzeugeHimmelTextur();
  if (renderer) {
    const pmrem = new THREE.PMREMGenerator(renderer);
    szene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    szene.environmentIntensity = 0.45; // Reflexe auf Lack und Stahl, aber unter dem Sonnenlicht
  }
  // Weniger Fuellung, mehr Richtung: die AO (komposition.js) uebernimmt die Fugen,
  // das Hemisphaerenlicht bringt kuehlen Himmel von oben und warmen Bodenrueckschein.
  // Gegenueber Fassung 2 zurueckgenommen: das hellere Tageslicht hob die mittlere
  // Leuchtdichte in allen neun Posen um 14–20 Punkte und nahm der Szene 20–27 %
  // Saettigung — Dach, Pfetten und Kranträger verschmolzen zu einer weissen Flaeche.
  szene.add(new THREE.AmbientLight(0xffffff, 0.10));
  szene.add(new THREE.HemisphereLight(0xdfe6ee, 0x6a6560, 0.5));
  // 1.6 statt 1.9: auch bei 1.9 lagen alle neun Posen noch ueber dem Zielband der
  // Sichtabnahme, darum bis an die Untergrenze abgesenkt (Bildkontrast bleibt dabei
  // gleich, Standardabweichung der Totale 39.4 → 39.3).
  const sonne = new THREE.DirectionalLight(0xfff1e0, 1.6); // Tageslicht durch Oberlichter, leicht warm
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
  // kein shadow.radius: unter PCFSoftShadowMap wertet three.js ihn nicht aus.
  szene.add(sonne);
  const fuelllicht = new THREE.DirectionalLight(0xd6e2f5, 0.25); // kuehle Gegenseite, ohne Schatten
  fuelllicht.position.set(-14, 10, -10);
  szene.add(fuelllicht);
  return szene;
}

// Vertikaler Himmelsverlauf als Hintergrund: Fenster und Tore zeigen Himmel statt Einheitsgrau.
// Im Composer-Pfad laeuft der Verlauf durch ACES (OutputPass); Horizont ~#dbdfe2,
// Zenit ~#c2ccd6 — gewollt, die Praesentation laeuft mit AO.
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

  aktiviereSchatten(gruppe);
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
  aktiviereSchatten(gltf.scene);
  szene.add(gltf.scene);
  return gltf.scene;
}

export function base64ZuArrayBuffer(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}
