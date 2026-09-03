import * as THREE from 'three';

// Legt das 720p-Video als Textur auf das Mesh "Monitor_Bildschirm" (Namens-Vertrag
// mit Platzhalterszene und Blender-Export). Liefert false, wenn das Mesh fehlt.
//
// Solange das Video nicht spielt (Datei fehlt noch, Autoplay wartet auf die erste
// Nutzergeste, Ladefehler), zeigt der Monitor eine gegreekte Dashboard-Grafik
// "Frage -> Abfrage -> Ergebnis" statt Schwarz. Sie ist deterministisch gezeichnet,
// enthaelt keine Ziffern und keine lesbare Schrift (Regel: nichts erfinden) und
// braucht keine Datei — der Notfall-Build bleibt eine einzige HTML.
export function verbindeVideoTextur(szene, videoEl) {
  const ziel = szene.getObjectByName('Monitor_Bildschirm');
  if (!ziel) return false;
  const video = new THREE.VideoTexture(videoEl);
  video.colorSpace = THREE.SRGBColorSpace; // Spec §5: sonst ausgewaschen
  video.flipY = false; // glTF-UV-Konvention (V-Ursprung oben) — sonst steht das Video ab Task 11 kopf
  const ersatz = erzeugeDashboardTextur();
  const material = new THREE.MeshBasicMaterial({ map: ersatz });
  ziel.material = material;
  const zeigeVideo = () => { material.map = video; material.needsUpdate = true; };
  const zeigeErsatz = () => { material.map = ersatz; material.needsUpdate = true; };
  // Erst wenn wirklich Bilddaten kommen, wechselt der Monitor aufs Video; bricht die
  // Quelle weg, faellt er zurueck. Kein Zustand, in dem er schwarz bleibt.
  videoEl.addEventListener('playing', zeigeVideo);
  videoEl.addEventListener('error', zeigeErsatz);
  videoEl.addEventListener('emptied', zeigeErsatz);
  if (videoEl.readyState >= 2 && !videoEl.paused) zeigeVideo();
  return true;
}

// Gegreektes Dashboard, 1280x720, graustufentauglich, ein roter Akzent.
// Layout: Kopfzeile, links Frage-Feld und Abfrage-Block, rechts Balkendiagramm
// und Ergebnistabelle. Alle "Texte" sind Balken.
export function erzeugeDashboardTextur() {
  const leinwand = document.createElement('canvas');
  leinwand.width = 1280;
  leinwand.height = 720;
  const g = leinwand.getContext('2d');
  if (g) zeichneDashboard(g, leinwand.width, leinwand.height);
  const textur = new THREE.CanvasTexture(leinwand);
  textur.colorSpace = THREE.SRGBColorSpace;
  textur.flipY = false; // wie die Videotextur: Bild oben = V 0
  textur.needsUpdate = true;
  return textur;
}

export function zeichneDashboard(g, b, h) {
  const F = {
    grund: '#f3f4f6', kopf: '#1f2328', feld: '#ffffff', rahmen: '#c9ced4',
    text: '#6b7280', textHell: '#b7bcc4', schluessel: '#3b6ea5', akzent: '#ec0016',
    balken: '#4b5563', balkenHell: '#9aa3ad',
  };
  const balken = (x, y, w, hh, farbe, radius = hh / 2) => {
    g.fillStyle = farbe;
    g.beginPath();
    g.roundRect(x, y, w, hh, radius);
    g.fill();
  };
  const feld = (x, y, w, hh) => {
    g.fillStyle = F.feld;
    g.strokeStyle = F.rahmen;
    g.lineWidth = 2;
    g.beginPath();
    g.roundRect(x, y, w, hh, 10);
    g.fill();
    g.stroke();
  };

  g.fillStyle = F.grund;
  g.fillRect(0, 0, b, h);

  // Kopfzeile: dunkel, links ein Titelbalken, rechts drei Menue-Punkte
  g.fillStyle = F.kopf;
  g.fillRect(0, 0, b, 64);
  balken(28, 24, 210, 16, '#e5e7eb');
  [960, 1050, 1140].forEach((x) => balken(x, 26, 64, 12, '#6b7280'));

  // Linke Spalte: Frage-Feld
  feld(28, 96, 600, 92);
  balken(52, 130, 300, 18, F.text);
  balken(360, 130, 120, 18, F.textHell);
  g.fillStyle = F.akzent; // Cursor als roter Akzent
  g.fillRect(492, 124, 3, 30);
  balken(548, 121, 60, 40, F.schluessel, 8); // "Senden"-Knopf

  // Linke Spalte: generierte Abfrage — Zeilen aus Schluesselwort- und Wertbalken
  feld(28, 212, 600, 296);
  const zeilen = [
    [[0, 90, F.schluessel], [100, 150, F.balken], [260, 40, F.balkenHell]],
    [[0, 70, F.schluessel], [80, 190, F.balken]],
    [[0, 100, F.schluessel], [110, 120, F.balken], [240, 60, F.balkenHell], [310, 90, F.balken]],
    [[40, 80, F.schluessel], [130, 170, F.balken]],
    [[0, 120, F.schluessel], [130, 100, F.balken]],
    [[0, 110, F.schluessel], [120, 60, F.balken], [190, 120, F.balkenHell]],
  ];
  zeilen.forEach((teile, i) => {
    const y = 244 + i * 40;
    teile.forEach(([dx, w, farbe]) => balken(64 + dx, y, w, 14, farbe));
  });
  // Statuszeile unter der Abfrage
  balken(52, 470, 14, 14, '#2f9e44', 7);
  balken(76, 470, 180, 14, F.textHell);

  // Rechte Spalte: Balkendiagramm ohne Zahlen
  feld(660, 96, 592, 300);
  balken(684, 118, 160, 14, F.text);
  const dx0 = 700; const grund = 360; const hoehen = [96, 150, 122, 188, 164, 210, 140];
  g.strokeStyle = F.rahmen;
  g.lineWidth = 1;
  for (let i = 0; i < 4; i++) {
    const y = grund - i * 60;
    g.beginPath(); g.moveTo(dx0, y); g.lineTo(1228, y); g.stroke();
  }
  hoehen.forEach((hh, i) => {
    const x = dx0 + 20 + i * 72;
    g.fillStyle = i === 5 ? F.akzent : F.balken;
    g.fillRect(x, grund - hh, 40, hh);
  });

  // Rechte Spalte: Ergebnistabelle — Kopfzeile + fuenf Zeilen
  feld(660, 420, 592, 268);
  balken(684, 440, 100, 12, F.schluessel);
  balken(820, 440, 120, 12, F.schluessel);
  balken(1000, 440, 90, 12, F.schluessel);
  balken(1130, 440, 90, 12, F.schluessel);
  const breiten = [[80, 110, 60, 70], [96, 90, 50, 80], [70, 120, 70, 60], [104, 80, 40, 76], [88, 100, 64, 66]];
  breiten.forEach((z, i) => {
    const y = 472 + i * 40;
    g.fillStyle = '#eef0f2';
    g.fillRect(672, y - 10, 568, 32);
    balken(684, y, z[0], 12, F.balken);
    balken(820, y, z[1], 12, F.balkenHell);
    balken(1000, y, z[2], 12, F.balkenHell);
    balken(1130, y, z[3], 12, F.balken);
  });
}
