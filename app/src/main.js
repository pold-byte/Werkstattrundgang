import * as THREE from 'three';
import daten from './stationen.json';
import { baueSchritte } from './schritte.js';
import { Zustandsmaschine, leiteAnsichtAb } from './zustand.js';
import { Kamerafahrt } from './kamera.js';
import { tasteZuAktion, Eingabesperre } from './steuerung.js';
import { speichereStand, ladeStand } from './speicher.js';
import { zeigePanel, versteckePanel, zeigeTitel, schalteSchwarzbild, schalteVideoGross, schalteDimmer } from './overlays.js';
import { erzeugeRenderer, erzeugeSzene, bauePlatzhalter, ladeModell, base64ZuArrayBuffer } from './szene.js';
import { aktiviereWaypointWerkzeug } from './waypoint-werkzeug.js';
import { verbindeVideoTextur } from './videotextur.js';

const canvas = document.getElementById('buehne');
const panelEl = document.getElementById('panel');
const titelEl = document.getElementById('titel');
const schwarzEl = document.getElementById('schwarzbild');
const dimmerEl = document.getElementById('dimmer');
const videoOverlayEl = document.getElementById('video-overlay');
const videoGrossEl = document.getElementById('video-gross');
const videoTexturEl = document.getElementById('video-textur');

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
  if (videoTexturEl.paused) videoTexturEl.play().catch(() => {}); // Autoplay erst nach Nutzergeste (Spec §5)
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
let orbitAktiv = null;
function schleife() {
  const delta = uhr.getDelta();
  if (aktuelleFahrt) {
    setzeKamera(aktuelleFahrt.fortschritt(delta));
    if (aktuelleFahrt.fertig) beendeFahrt();
  }
  if (orbitAktiv) orbitAktiv.update();
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

  verbindeVideoTextur(szene, videoTexturEl);

  const gespeichert = ladeStand(sessionStorage);
  if (gespeichert) zustand.setzeStand(gespeichert);
  setzeKamera(poseFuerOrt(leiteAnsichtAb(zustand.aktuell, daten.stationen).ort));
  aktuellerOrt = leiteAnsichtAb(zustand.aktuell, daten.stationen).ort;
  wendeAnsichtAn(true);
  orbitAktiv = aktiviereWaypointWerkzeug(kamera, renderer, szene);
  schleife();
}

start();
