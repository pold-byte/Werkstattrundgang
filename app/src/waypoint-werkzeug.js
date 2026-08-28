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
