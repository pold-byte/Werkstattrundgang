// Erzeugt aus stationen.json die druckbare Fassung (Spec §7: PDF ist vollwertiges,
// abgabefähiges Dokument — weiße Seiten, identischer Slide-Inhalt, Kopfzeile).
import daten from './stationen.json';

const wurzel = document.getElementById('seiten');

function seite(inhaltBauen) {
  const abschnitt = document.createElement('section');
  abschnitt.className = 'seite';
  const kopf = document.createElement('header');
  kopf.textContent = 'DB Intern / DB internal';
  abschnitt.append(kopf);
  inhaltBauen(abschnitt);
  wurzel.append(abschnitt);
}

// Deckblatt
seite((s) => {
  const h1 = document.createElement('h1');
  h1.textContent = 'Eine Kennzahl — von der Werkstatthalle bis in die Planungsrunde';
  const p = document.createElement('p');
  p.className = 'untertitel';
  p.textContent = '[PLATZHALTER: Untertitel/Name/Datum]';
  s.append(h1, p);
});

// Eine Seite pro Station (inklusive Reservestation 6)
for (const st of daten.stationen) {
  seite((s) => {
    const nummer = document.createElement('div');
    nummer.className = 'stationsnummer';
    nummer.textContent = `Station ${st.nr}${st.im_rundgang === false ? ' (Reserve)' : ''}`;
    const h2 = document.createElement('h2');
    h2.textContent = st.titel;
    const kern = document.createElement('p');
    kern.className = 'kernaussage';
    kern.textContent = st.kernaussage;
    const liste = document.createElement('ul');
    for (const punkt of st.belegpunkte) {
      const li = document.createElement('li');
      li.textContent = punkt;
      liste.append(li);
    }
    const bild = document.createElement('img');
    bild.className = 'thumbnail';
    bild.src = `./standbilder/${st.id}.png`; // Spec §7: Szenen-Thumbnail (Taste P, Task 9)
    bild.alt = '';
    bild.onerror = () => bild.remove(); // solange das Standbild fehlt: ausblenden
    const fuss = document.createElement('div');
    fuss.className = 'kapitel';
    fuss.textContent = `${st.kapitel} · Anschauungsobjekt: ${st.anschauungsobjekt}`;
    s.append(nummer, h2, kern, liste, bild, fuss);
  });
}
