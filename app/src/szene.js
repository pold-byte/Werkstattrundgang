import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export function erzeugeRenderer(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Spec §5: Deckel 2
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap; // weiche Schatten fuer den Iso-Look
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

export function erzeugeSzene() {
  const szene = new THREE.Scene();
  szene.background = new THREE.Color(0xdfe3e6);
  szene.add(new THREE.AmbientLight(0xffffff, 0.45));
  // Himmel/Boden-Verlauf ersetzt einen Teil des Ambient — wirkt wie weiche AO.
  szene.add(new THREE.HemisphereLight(0xf4f6f8, 0x878c90, 0.55));
  const sonne = new THREE.DirectionalLight(0xffffff, 1.5);
  sonne.position.set(12, 20, 8);
  sonne.castShadow = true;
  sonne.shadow.mapSize.set(2048, 2048);
  sonne.shadow.camera.left = -24;
  sonne.shadow.camera.right = 24;
  sonne.shadow.camera.top = 24;
  sonne.shadow.camera.bottom = -24;
  sonne.shadow.camera.near = 1;
  sonne.shadow.camera.far = 70;
  sonne.shadow.bias = -0.0004;
  szene.add(sonne);
  // Fuelllicht von der Gegenseite: zeichnet die sonnenabgewandten Flaechen.
  const fuelllicht = new THREE.DirectionalLight(0xdfe8ff, 0.4);
  fuelllicht.position.set(-14, 10, -10);
  szene.add(fuelllicht);
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
