import * as THREE from 'three';
import daten from './stationen.json';
import { baueSchritte } from './schritte.js';
import { Zustandsmaschine, leiteAnsichtAb } from './zustand.js';
import { Kamerafahrt } from './kamera.js';
import { findeWegpunkte } from './fahrtwege.js';
import { tasteZuAktion, Eingabesperre } from './steuerung.js';
import { speichereStand, ladeStand } from './speicher.js';
import { zeigePanel, versteckePanel, zeigeTitel, schalteSchwarzbild, schalteVideoGross, schalteDimmer } from './overlays.js';
import { erzeugeRenderer, erzeugeSzene, bauePlatzhalter, ladeModell, base64ZuArrayBuffer } from './szene.js';
import { aktiviereWaypointWerkzeug } from './waypoint-werkzeug.js';
import { verbindeVideoTextur } from './videotextur.js';
import { erzeugeKomposition, leseAoSchalter } from './komposition.js';
import { erzeugeFolienschau } from './folien.js';

const canvas = document.getElementById('buehne');
const panelEl = document.getElementById('panel');
const titelEl = document.getElementById('titel');
const schwarzEl = document.getElementById('schwarzbild');
const dimmerEl = document.getElementById('dimmer');
const videoOverlayEl = document.getElementById('video-overlay');
const videoGrossEl = document.getElementById('video-gross');
const videoTexturEl = document.getElementById('video-textur');
const folienEl = document.getElementById('folienschau');

const folienschau = erzeugeFolienschau(folienEl);

const renderer = erzeugeRenderer(canvas);
const szene = erzeugeSzene(renderer);
const kamera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 200);
const komposition = erzeugeKomposition(renderer, szene, kamera, { ao: leseAoSchalter(window.location.search) });

const schritte = baueSchritte(daten.stationen);
const zustand = new Zustandsmaschine(schritte);
const sperre = new Eingabesperre();

let aktuelleFahrt = null;
let aktuellerOrt = 'totale';
// Tastatur erst freigeben, wenn start() den Stand wiederhergestellt hat — sonst
// überschreibt ein früher Druck den sessionStorage-Stand (Spec §10: Reload-Garantie)
// und startet eine Fahrt ab der Kamera-Defaultpose (0,0,0).
let bereit = false;

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
    const wegpunkte = findeWegpunkte(aktuellerOrt, ansicht.ort);
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
      aktuelleFahrt = new Kamerafahrt(von, { position: nach.position, blickziel: nach.blickziel }, dauer, wegpunkte);
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

// Die Kamera fährt an den Ort, den die aufgeschlagene Folie nennt. Das Panel
// bleibt dabei ausgeblendet (body.folien-offen), sichtbar ist nur der Rahmen.
function folgeFolie() {
  const ziel = folienschau.aktuelle.station;
  if (!ziel || ziel === aktuellerOrt) return;
  if (ziel === 'totale') zustand.springeZurTotale();
  else zustand.springeZuStation(ziel);
  wendeAnsichtAn();
}

function fuehreAktionAus(aktion) {
  // Bei offener Folienschau blaettern weiter/zurueck durch die Folien, nicht
  // durch den Rundgang; Taste f zeigt die Halle allein (Spec §6: Escape bleibt frei).
  if (aktion.typ === 'folien') { folienschau.naechsterSatz(); if (folienschau.istOffen) folgeFolie(); return; }
  if (folienschau.istOffen) {
    if (aktion.typ === 'weiter') { if (folienschau.weiter()) folgeFolie(); return; }
    if (aktion.typ === 'zurueck') { if (folienschau.zurueck()) folgeFolie(); return; }
  }
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
  if (!bereit) return;
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
  // Die Folienschau liegt vor der Szene: blaettern und umschalten wirken auch
  // waehrend einer Kamerafahrt, sonst schluckt die Eingabesperre die Taste.
  if (aktion.typ === 'folien' || (folienschau.istOffen && (aktion.typ === 'weiter' || aktion.typ === 'zurueck'))) {
    fuehreAktionAus(aktion);
    return;
  }
  const freigegeben = sperre.verarbeite(aktion);
  if (freigegeben) fuehreAktionAus(freigegeben);
});

window.addEventListener('resize', () => {
  kamera.aspect = window.innerWidth / window.innerHeight;
  kamera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  komposition.setSize(window.innerWidth, window.innerHeight);
  folienschau.passeAn();
});

const uhr = new THREE.Clock();
let orbitAktiv = null;
function schleife() {
  // Delta deckeln: nach Tab-Wechsel/Ruckler liefert getDelta() sonst Sekunden
  // auf einmal und eine laufende Fahrt teleportiert ans Ziel (Spec §6: Härtung).
  const delta = Math.min(uhr.getDelta(), 0.1);
  if (aktuelleFahrt) {
    setzeKamera(aktuelleFahrt.fortschritt(delta));
    if (aktuelleFahrt.fertig) beendeFahrt();
  }
  if (orbitAktiv) orbitAktiv.update();
  komposition.render();
  requestAnimationFrame(schleife);
}

async function start() {
  bauePlatzhalter(szene, daten);
  if (import.meta.env.VITE_NOTFALL === '1') {
    const { szeneGlbBase64 } = await import('./generiert/szene-glb.js');
    if (szeneGlbBase64) await ladeModell(szene, base64ZuArrayBuffer(szeneGlbBase64));
  } else {
    try {
      // Im Dev-Modus Cache-Buster anhaengen — sonst klebt der Browser nach einem
      // Neuexport auf der alten szene.glb.
      await ladeModell(szene, import.meta.env.DEV ? `./szene.glb?v=${Date.now()}` : './szene.glb');
    } catch {
      // Kein Modell vorhanden (vor Task 11): Platzhalter bleibt stehen.
    }
  }

  // Szene und Sonne sind statisch: die 4096er-Schattenkarte einmal rendern, dann
  // einfrieren. Bisher lief sie je Bild zweimal, weil RenderPass und der Normalpass
  // der GTAO beide renderer.render() aufrufen.
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.needsUpdate = true;
  // Erst ab hier ist die Renderlast repraesentativ — alles davor (Platzhalter,
  // Ladezeit, Shader-Kompilierung) faellt aus dem Messfenster des Ueberlastschutzes.
  komposition.messungZuruecksetzen();

  verbindeVideoTextur(szene, videoTexturEl);

  const gespeichert = ladeStand(sessionStorage);
  if (gespeichert) {
    // Sprung auf eine inzwischen unbekannte Stations-ID verwerfen — sonst wirft
    // poseFuerOrt vor dem Start der Renderschleife und jeder Reload crasht erneut.
    const sprungId = gespeichert.sprung?.stationId;
    if (sprungId && !daten.stationen.some((s) => s.id === sprungId)) gespeichert.sprung = null;
    zustand.setzeStand(gespeichert);
  }
  setzeKamera(poseFuerOrt(leiteAnsichtAb(zustand.aktuell, daten.stationen).ort));
  aktuellerOrt = leiteAnsichtAb(zustand.aktuell, daten.stationen).ort;
  wendeAnsichtAn(true);
  folienschau.oeffne(); // Standardansicht: die Folie vorn, die Halle im Rahmen
  bereit = true;
  orbitAktiv = aktiviereWaypointWerkzeug(kamera, renderer, szene);
  if (import.meta.env.DEV) Object.assign(window, { __szene: szene, __renderer: renderer, __kamera: kamera, __komposition: komposition }); // Dev-Inspektion (im Build entfernt)
  schleife();
}

start();
