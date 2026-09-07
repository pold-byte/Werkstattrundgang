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
  // Eigenes Ziel mit 4x MSAA: das Default-Target des EffectComposer ist nicht
  // multisampled, dadurch treppten im Composer-Pfad alle Kanten (Gelaender,
  // Kranträger, Zugkante) trotz antialias:true am Renderer.
  const pr = renderer.getPixelRatio();
  const ziel = new THREE.WebGLRenderTarget(groesse.x * pr, groesse.y * pr, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, ziel);
  composer.addPass(new RenderPass(szene, kamera));
  const gtao = new GTAOPass(szene, kamera, groesse.x, groesse.y);
  gtao.output = GTAOPass.OUTPUT.Default;
  // Werkstattmassstab: Fugen und Fussleisten sollen dunkel werden, nicht ganze Waende.
  // Weicher abgestimmt als in Fassung 2: groesserer Radius, kleinere Staerke und ein
  // breiterer Denoise-Kern — die harten Baender am Dach/Pfetten-Stoss und an den
  // Treppenwangen lasen sonst wie Wasserflecken.
  gtao.updateGtaoMaterial({ radius: 0.5, distanceExponent: 1.0, thickness: 1.0, scale: 0.9, samples: 12, distanceFallOff: 1.0, screenSpaceRadius: false });
  gtao.updatePdMaterial({ lumaPhi: 14, depthPhi: 2, normalPhi: 3, radius: 6, radiusExponent: 1, rings: 3, samples: 16 });
  gtao.blendIntensity = 0.5;
  composer.addPass(gtao);
  const output = new OutputPass();
  composer.addPass(output);
  return { composer, gtao, output };
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
  let teile = aoAktiv ? _composerFabrik() : null;
  let composer = teile ? teile.composer : null;
  const zeiten = [];
  let mittel = 0;
  // Das erste volle Fenster ist Aufwaermen (Shader-Kompilierung, erster Schattenwurf)
  // und wird verworfen; main.js setzt die Messung nach dem Laden des Modells zurueck.
  let aufwaermen = true;

  function schalteAoAb() {
    aoAktiv = false;
    if (teile) {
      teile.gtao.dispose();
      teile.output.dispose();
      teile.composer.dispose();
    }
    teile = null;
    composer = null;
    console.info(`AO abgeschaltet: mittlere Bildzeit ${mittel.toFixed(1)} ms`);
  }

  // Gemessen wird die Dauer des Renderaufrufs selbst, nicht der Abstand zwischen
  // zwei Aufrufen: ein Tab-Wechsel oder ein verdecktes Fenster (Folien ueber dem
  // Browser) erzeugte sonst Luecken von Sekunden und schaltete die AO dauerhaft ab.
  function verbuche(dauer) {
    if (dauer > aoAbschaltenAb * 4) return; // Ausreisser (Shader-Kompilierung, Ruckler) zaehlen nicht
    zeiten.push(dauer);
    if (zeiten.length < messfenster) return;
    if (aufwaermen) { zeiten.length = 0; aufwaermen = false; return; }
    mittel = zeiten.reduce((s, z) => s + z, 0) / zeiten.length;
    zeiten.length = 0;
    if (aoAktiv && mittel > aoAbschaltenAb) schalteAoAb();
  }

  function messungZuruecksetzen() {
    zeiten.length = 0;
    aufwaermen = true;
  }

  // Nach einem Tab-Wechsel ist das halbe Fenster mit gedrosselten Bildern gefuellt.
  if (typeof document !== 'undefined' && document.addEventListener) {
    document.addEventListener('visibilitychange', messungZuruecksetzen);
  }

  return {
    render() {
      const t0 = jetzt();
      if (aoAktiv && composer) composer.render();
      else renderer.render(szene, kamera);
      verbuche(jetzt() - t0);
    },
    setSize(breite, hoehe) {
      if (composer) {
        composer.setPixelRatio(renderer.getPixelRatio()); // zieht das MSAA-Ziel mit
        composer.setSize(breite, hoehe);
      }
    },
    messungZuruecksetzen,
    get aoAktiv() { return aoAktiv; },
    mittlereBildzeit() { return mittel; },
  };
}
