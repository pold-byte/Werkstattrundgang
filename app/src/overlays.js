// DOM-Overlays über dem Canvas (Spec §5): scharfer Browser-Text, keine 3D-Texturen.
// Inhalte kommen aus stationen.json und werden ausschließlich als textContent gesetzt.
export function zeigePanel(panelEl, station, anzahlBelegpunkte) {
  panelEl.replaceChildren();

  const nummer = document.createElement('div');
  nummer.className = 'stationsnummer';
  nummer.textContent = `Station ${station.nr}`;
  panelEl.append(nummer);

  const ueberschrift = document.createElement('h2');
  ueberschrift.textContent = station.titel;
  panelEl.append(ueberschrift);

  const kernaussage = document.createElement('p');
  kernaussage.className = 'kernaussage';
  kernaussage.textContent = station.kernaussage;
  panelEl.append(kernaussage);

  const liste = document.createElement('ul');
  for (const punkt of station.belegpunkte.slice(0, anzahlBelegpunkte)) {
    const li = document.createElement('li');
    li.textContent = punkt;
    liste.append(li);
  }
  panelEl.append(liste);

  const kapitel = document.createElement('div');
  kapitel.className = 'kapitel';
  kapitel.textContent = station.kapitel;
  panelEl.append(kapitel);

  panelEl.classList.add('sichtbar'); // CSS blendet über opacity in ~300 ms ein (Spec §5)
}

export function versteckePanel(panelEl) {
  panelEl.classList.remove('sichtbar');
}

// Dimmt die Szene an Stationen leicht ab (Spec §5); Element: #dimmer.
export function schalteDimmer(dimmerEl, aktiv) {
  dimmerEl.classList.toggle('aktiv', aktiv);
}

export function zeigeTitel(titelEl, sichtbar) {
  titelEl.hidden = !sichtbar;
}

export function schalteSchwarzbild(schwarzEl) {
  schwarzEl.hidden = !schwarzEl.hidden;
  return !schwarzEl.hidden;
}

// Video-Großansicht (Taste V): zeigt/versteckt das Overlay und startet/pausiert das Video.
export function schalteVideoGross(overlayEl, videoEl) {
  if (overlayEl.hidden) {
    overlayEl.hidden = false;
    videoEl.play().catch(() => {}); // fehlende Datei o. Ä. darf den Vortrag nie stoppen
    return true;
  }
  videoEl.pause();
  overlayEl.hidden = true;
  return false;
}
