// Folienschau über der 3D-Szene: die Folie füllt den Bildschirm bis auf einen
// Rahmen, in dem die Halle sichtbar bleibt. Gestaltung nach docs/foliensatz/DESIGN.md,
// Inhalt aus folien-inhalt.js. Die Folie wird in fester Größe (13,333 x 7,5 Zoll,
// also 1280 x 720 px bei 96 dpi) aufgebaut und als Ganzes skaliert, damit alle
// Größenverhältnisse des Foliensatzes erhalten bleiben.
import { hauptfolien, zusatzfolien, fusszeile } from './folien-inhalt.js';

export const FOLIE_BREITE = 1280;
export const FOLIE_HOEHE = 720;

// Folien mit dem Merkmal 'klein' stehen als Karte in der Ecke, damit die Halle
// dahinter vollstaendig sichtbar bleibt. Anteil der Rahmenbreite bzw. -hoehe.
export const KLEIN_ANTEIL = 0.42;

function el(tag, klasse, text) {
  const knoten = document.createElement(tag);
  if (klasse) knoten.className = klasse;
  if (text !== undefined) knoten.textContent = text;
  return knoten;
}

function baueTabelle(block) {
  const halter = el('div', 'f-block');
  if (block.titel) halter.append(el('div', 'f-blocktitel', block.titel));
  const tabelle = el('table', block.zahlen ? 'f-tab f-tab-zahlen' : 'f-tab');
  if (block.breiten) {
    const gruppe = el('colgroup');
    for (const breite of block.breiten) {
      const spalte = el('col');
      if (breite !== 'auto') spalte.style.width = breite;
      gruppe.append(spalte);
    }
    tabelle.append(gruppe);
  }
  const kopf = el('thead');
  const kopfzeile = el('tr');
  for (const zelle of block.kopf) kopfzeile.append(el('th', null, zelle));
  kopf.append(kopfzeile);
  tabelle.append(kopf);
  const koerper = el('tbody');
  for (const zeile of block.zeilen) {
    const tr = el('tr');
    zeile.forEach((zelle, i) => {
      const td = el('td', i === 0 ? 'f-erst' : null, zelle);
      if (block.zahlen && i === zeile.length - 1) td.className = 'f-zahl';
      tr.append(td);
    });
    koerper.append(tr);
  }
  tabelle.append(koerper);
  halter.append(tabelle);
  return halter;
}

function baueBlock(block) {
  switch (block.typ) {
    case 'punkte': {
      const halter = el('div', 'f-block f-punkte');
      for (const punkt of block.punkte) halter.append(el('p', null, punkt));
      return halter;
    }
    case 'gruppe': {
      const halter = el('div', 'f-block');
      halter.append(el('div', 'f-blocktitel', block.titel));
      const punkte = el('div', 'f-punkte');
      for (const punkt of block.punkte) punkte.append(el('p', null, punkt));
      halter.append(punkte);
      return halter;
    }
    case 'tabelle':
      return baueTabelle(block);
    case 'fluss': {
      const halter = el('div', 'f-block f-fluss');
      block.glieder.forEach((glied, i) => {
        if (i > 0) halter.append(el('span', 'f-pfeil')); // Verbindungslinie, kein Pfeilzeichen
        halter.append(el('span', 'f-glied', glied));
      });
      return halter;
    }
    case 'schritte': {
      const halter = el('div', 'f-block f-schritte');
      for (const schritt of block.glieder) {
        const kasten = el('div', schritt.modell ? 'f-schritt f-modell' : 'f-schritt');
        kasten.append(el('span', 'f-schrittnr', schritt.nr));
        kasten.append(el('span', 'f-schrittname', schritt.name));
        kasten.append(el('span', 'f-schritttext', schritt.text));
        halter.append(kasten);
      }
      return halter;
    }
    case 'kasten': {
      const halter = el('div', 'f-block f-kasten');
      if (block.marke) halter.append(el('span', 'f-marke', block.marke + ': '));
      halter.append(document.createTextNode(block.text));
      return halter;
    }
    case 'notiz':
      return el('div', 'f-block f-notiz', block.text);
    default:
      return el('div', 'f-block', String(block.text || ''));
  }
}

function baueFolie(folie, gesamt, position, satzname) {
  const titelart = folie.art === 'titel';
  const knoten = el('article', titelart ? 'f-folie f-titelart' : 'f-folie');
  knoten.setAttribute('aria-label', 'Folie ' + folie.nr);

  // Rubrik oben links, im Foliensatz z. B. "02  Zielsetzung"; auf der Titelfolie
  // steht dort die Einordnung der Arbeit in Versalien.
  const kopf = el('div', titelart ? 'f-kopf f-kopf-titel' : 'f-kopf');
  kopf.textContent = titelart ? folie.kopf || '' : folie.sektion || '';
  knoten.append(kopf);

  if (titelart) {
    const mitte = el('div', 'f-titelfolie');
    mitte.append(el('h1', 'f-haupttitel', folie.titel));
    mitte.append(el('p', 'f-unterzeile', folie.unterzeile));
    mitte.append(el('p', 'f-name', folie.name));
    for (const zeile of folie.meta) mitte.append(el('p', 'f-meta', zeile));
    knoten.append(mitte);
  } else {
    knoten.append(el('h2', 'f-titel', folie.titel));
    if (folie.kern) knoten.append(el('p', 'f-kern', folie.kern));

    const inhalt = el('div', 'f-inhalt');
    for (const block of folie.breit || []) inhalt.append(baueBlock(block));
    if (folie.spalten) {
      const spalten = el('div', 'f-spalten');
      for (const spalte of folie.spalten) {
        const halter = el('div', 'f-spalte');
        for (const block of spalte) halter.append(baueBlock(block));
        spalten.append(halter);
      }
      inhalt.append(spalten);
    }
    if (folie.schluss) inhalt.append(baueBlock(folie.schluss));
    knoten.append(inhalt);
  }

  const fuss = el('div', 'f-fuss');
  fuss.append(el('span', 'f-fuss-l', fusszeile));
  const zaehler = satzname === 'zusatz' ? 'Ergänzung ' + position + ' / ' + gesamt : position + ' / ' + gesamt;
  fuss.append(el('span', 'f-fuss-r', zaehler));
  knoten.append(fuss);
  return knoten;
}

// Skaliert die Folie so, dass sie den Rahmen ausfüllt und 16:9 behält.
export function berechneMassstab(breite, hoehe) {
  if (!(breite > 0) || !(hoehe > 0)) return 1;
  return Math.min(breite / FOLIE_BREITE, hoehe / FOLIE_HOEHE);
}

// saetze: { haupt, zusatz }. Der Vortrag laeuft auf dem Hauptsatz; die Taste f
// schaltet weiter auf den Zusatzsatz und danach auf die Halle ohne Folie.
export function erzeugeFolienschau(wurzelEl, saetze = { haupt: hauptfolien, zusatz: zusatzfolien }) {
  const satz = Array.isArray(saetze) ? { haupt: saetze, zusatz: [] } : saetze;
  const zusatzVorhanden = (satz.zusatz || []).length > 0;
  let modus = 'haupt';
  let daten = satz.haupt;
  let index = 0;
  let offen = false;
  const buehne = el('div', 'f-buehne');
  wurzelEl.append(buehne);
  wurzelEl.hidden = true;

  function zeichne() {
    const kind = baueFolie(daten[index], daten.length, index + 1, modus);
    buehne.replaceChildren(kind);
    document.body.classList.toggle('folien-klein', !!daten[index].klein);
    passeDichteAn(kind);
    passeAn();
  }

  // Dichte Folien (grosse Tabellen) bekommen eine kleinere Schriftstufe, damit
  // nichts abgeschnitten wird. Gemessen wird an der ungescaleten Folie, das
  // Ergebnis haengt daher nicht von der Fenstergroesse ab.
  function passeDichteAn(kind) {
    const inhalt = kind.querySelector('.f-inhalt');
    if (!inhalt || !inhalt.scrollHeight) return;
    let dicht = 1;
    while (inhalt.scrollHeight > inhalt.clientHeight + 1 && dicht > 0.7) {
      dicht = Math.round((dicht - 0.05) * 100) / 100;
      kind.style.setProperty('--f-dicht', String(dicht));
    }
  }

  function passeAn() {
    const kind = buehne.firstElementChild;
    if (!kind) return;
    // Gemessen wird die Buehne, nicht der Wurzelknoten: dessen Rechteck
    // schliesst die Polsterung ein, und die Folie wuerde den Rahmen ueberdecken,
    // in dem die Halle sichtbar bleiben soll.
    const rahmen = buehne.getBoundingClientRect();
    const anteil = daten[index].klein ? KLEIN_ANTEIL : 1;
    const massstab = berechneMassstab(rahmen.width * anteil, rahmen.height * anteil);
    kind.style.transform = 'scale(' + massstab + ')';
  }

  function setzeSatz(name) {
    modus = name;
    daten = name === 'zusatz' ? satz.zusatz : satz.haupt;
    index = 0;
  }

  return {
    get istOffen() { return offen; },
    get modus() { return modus; },
    get nummer() { return daten[index].nr; },
    get aktuelle() { return daten[index]; },
    oeffne() {
      offen = true;
      wurzelEl.hidden = false;
      document.body.classList.add('folien-offen'); // blendet Panel, Titel und Kopfzeile aus
      zeichne();
    },
    schliesse() {
      offen = false;
      wurzelEl.hidden = true;
      document.body.classList.remove('folien-offen');
      document.body.classList.remove('folien-klein');
    },
    // Im Rundgang bestimmt der Vortragsschritt, welche Folie zu sehen ist.
    zeigeFolie(nr) {
      if (modus !== 'haupt') setzeSatz('haupt');
      const treffer = satz.haupt.findIndex((f) => f.nr === nr);
      if (treffer < 0) return false;
      index = treffer;
      this.oeffne();
      return true;
    },
    verstecke() {
      if (offen) this.schliesse();
    },
    // f blendet die Ergaenzungsfolien ein und wieder aus.
    zusatzUmschalten() {
      if (modus === 'zusatz') { setzeSatz('haupt'); this.schliesse(); return false; }
      if (!zusatzVorhanden) return false;
      setzeSatz('zusatz');
      this.oeffne();
      return true;
    },
    umschalten() { if (offen) this.schliesse(); else this.oeffne(); return offen; },
    weiter() {
      if (index >= daten.length - 1) return false; // am Ende bleibt die letzte Folie stehen
      index += 1; zeichne(); return true;
    },
    zurueck() {
      if (index <= 0) return false;
      index -= 1; zeichne(); return true;
    },
    geheZu(nr) {
      const treffer = daten.findIndex((f) => f.nr === nr);
      if (treffer < 0) return false;
      index = treffer; if (offen) zeichne(); return true;
    },
    passeAn,
  };
}
