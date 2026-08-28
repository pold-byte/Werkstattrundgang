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
