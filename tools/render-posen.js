// tools/render-posen.js
// In die Browser-Konsole der laufenden App (http://localhost:5199) einfuegen.
// Rendert die sieben Jury-Posen plus zwei freie Blickwinkel in 1600x900 und
// schickt sie an tools/schuss-server.mjs. Braucht die DEV-Globals
// window.__szene/__kamera/__renderer (main.js setzt sie nur im Dev-Modus).
(async () => {
  window.__rafOrig = window.__rafOrig || window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = () => 0; // App-Schleife anhalten, sonst ueberschreibt sie die Kamera
  const s = window.__szene, k = window.__kamera, rn = window.__renderer;
  const c = rn.domElement;
  Array.from(document.body.children).forEach((e) => { if (e !== c) e.style.visibility = 'hidden'; });
  rn.setSize(1600, 900, false); // verborgenes Panel meldet sonst 0x0 und toDataURL liefert 'data:,'
  k.aspect = 16 / 9; k.fov = 50;
  const posen = [
    ['p_totale', [15, 4.6, 4.5], [-8, 0.5, 0.2]],
    ['p_meisterbuero', [-5.2, 2.1, -3.2], [-10.2, 1.2, -6.6]],
    ['p_datenraum', [0.5, 2.2, -2.5], [-3, 1, -6]],
    ['p_terminal', [9.2, 1.6, -1.6], [6.6, 1.2, -4.4]],
    ['p_anzeigetafel', [10.6, 1.9, 2], [8.6, 2, 5.9]],
    ['p_pruefstand', [-1.5, 2.5, 2.5], [2, 1, 6]],
    ['p_besprechung', [-5.5, 2.2, 2.5], [-9, 1, 6]],
    ['p_hero_bahnsteig', [6, 1.7, -5.5], [-2, 1.5, 0]],
    ['p_hero_kranbahn', [-12, 5.5, 6], [4, 1.5, -1]],
  ];
  for (const [name, pos, ziel] of posen) {
    k.position.set(...pos); k.updateProjectionMatrix(); k.lookAt(...ziel); rn.render(s, k);
    const antwort = await fetch('http://localhost:5198/', { method: 'POST', body: JSON.stringify({ name, data: c.toDataURL('image/png') }) });
    console.log(name, antwort.status, await antwort.text());
  }
  console.log('fertig; Seite neu laden, um die App wieder normal zu betreiben');
})();
