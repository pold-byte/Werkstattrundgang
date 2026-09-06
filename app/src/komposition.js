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
