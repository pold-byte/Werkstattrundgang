import { describe, it, expect, beforeEach } from 'vitest';
import { folien, hauptfolien, zusatzfolien, fusszeile } from '../src/folien-inhalt.js';
import { erzeugeFolienschau, berechneMassstab, FOLIE_BREITE, FOLIE_HOEHE, KLEIN_ANTEIL } from '../src/folien.js';
import { tasteZuAktion } from '../src/steuerung.js';

let wurzel;

beforeEach(() => {
  document.body.innerHTML = '<div id="folienschau" hidden></div>';
  wurzel = document.getElementById('folienschau');
});

describe('Folieninhalt', () => {
  it('enthält alle elf Folien in Reihenfolge', () => {
    expect(folien).toHaveLength(11);
    expect(folien.map((f) => f.nr)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]);
  });

  it('gibt jeder Folie einen Titel und jeder Inhaltsfolie einen Inhalt', () => {
    for (const f of folien) {
      expect(f.titel.length).toBeGreaterThan(3);
      if (f.art !== 'titel') expect(f.spalten || f.breit).toBeTruthy();
    }
  });

  it('teilt sich in sieben Haupt- und vier Ergänzungsfolien', () => {
    expect(hauptfolien.map((f) => f.nr)).toEqual([1, 2, 3, 4, 5, 6, 7]);
    expect(zusatzfolien.map((f) => f.nr)).toEqual([8, 9, 10, 11]);
  });

  it('verteilt die Hauptfolien auf Totale und Stationen, in Reihenfolge des Rundgangs', async () => {
    const { default: daten } = await import('../src/stationen.json');
    const orte = new Set(['totale', ...daten.stationen.map((s) => s.id)]);
    for (const f of hauptfolien) {
      expect(orte.has(f.station), 'Folie ' + f.nr + ': ' + f.station).toBe(true);
    }
    // Jede Station des Rundgangs kommt vor, und die Reihenfolge geht vorwärts.
    const imRundgang = daten.stationen.filter((s) => s.im_rundgang !== false).map((s) => s.id);
    const belegt = hauptfolien.map((f) => f.station).filter((o) => o !== 'totale');
    for (const id of imRundgang) expect(belegt).toContain(id);
    const reihenfolge = belegt.map((o) => imRundgang.indexOf(o));
    expect(reihenfolge).toEqual([...reihenfolge].sort((a, b) => a - b));
  });

  it('lässt die Kamera bei den Ergänzungsfolien stehen', () => {
    for (const f of zusatzfolien) expect(f.station).toBeNull();
  });

  it('behält die Kennzahlen des Vortrags bei', () => {
    const text = JSON.stringify(folien);
    for (const wert of ['82,8', '86,2', '3,4 Prozentpunkte', '540 Messsätze', '25 Tabellen', '12,27 $']) {
      expect(text).toContain(wert);
    }
  });
});

describe('erzeugeFolienschau', () => {
  it('bleibt zunächst verborgen und zeigt beim Öffnen Folie 1', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: folien, zusatz: [] });
    expect(wurzel.hidden).toBe(true);
    expect(schau.istOffen).toBe(false);
    schau.oeffne();
    expect(wurzel.hidden).toBe(false);
    expect(schau.nummer).toBe(1);
    expect(wurzel.querySelector('.f-folie')).not.toBeNull();
    expect(wurzel.querySelector('.f-kopf').textContent).toContain('Projektarbeit T3_2000');
    expect(wurzel.querySelector('.f-fuss').textContent).toContain(fusszeile);
  });

  it('blättert vorwärts und rückwärts und bleibt an den Enden stehen', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: folien, zusatz: [] });
    schau.oeffne();
    expect(schau.zurueck()).toBe(false);
    expect(schau.nummer).toBe(1);
    expect(schau.weiter()).toBe(true);
    expect(schau.nummer).toBe(2);
    for (let i = 0; i < 20; i++) schau.weiter();
    expect(schau.nummer).toBe(11);
    expect(schau.weiter()).toBe(false);
  });

  it('springt zu einer Foliennummer und schaltet um', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: folien, zusatz: [] });
    expect(schau.geheZu(7)).toBe(true);
    expect(schau.geheZu(99)).toBe(false);
    schau.oeffne();
    expect(wurzel.querySelector('.f-titel').textContent).toBe('Streuung und Zurechnung der Fehler');
    expect(schau.umschalten()).toBe(false);
    expect(wurzel.hidden).toBe(true);
  });

  it('rendert Tabellen mit Kopfzeile und allen Zeilen', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: folien, zusatz: [] });
    schau.geheZu(8);
    schau.oeffne();
    const tabelle = wurzel.querySelector('.f-tab');
    expect(tabelle.querySelectorAll('th')).toHaveLength(4);
    expect(tabelle.querySelectorAll('tbody tr')).toHaveLength(7);
    expect(tabelle.textContent).toContain('A-7');
  });

  it('markiert die beiden Modellaufrufe auf der Prozessfolie', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: folien, zusatz: [] });
    schau.geheZu(5);
    schau.oeffne();
    expect(wurzel.querySelectorAll('.f-schritt')).toHaveLength(6);
    expect(wurzel.querySelectorAll('.f-schritt.f-modell')).toHaveLength(2);
  });

  it('setzt die Rubrik des Foliensatzes in den Kopf', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: folien, zusatz: [] });
    schau.geheZu(3);
    schau.oeffne();
    expect(wurzel.querySelector('.f-kopf').textContent).toBe('02 Zielsetzung');
    expect(wurzel.querySelector('.f-folie').classList.contains('f-titelart')).toBe(false);
  });

  it('verwendet textContent, kein HTML aus den Daten', () => {
    const schau = erzeugeFolienschau(wurzel, {
      haupt: [{ nr: 1, titel: '<img src=x>', kern: 'x', spalten: [[{ typ: 'punkte', punkte: ['<b>y</b>'] }]] }],
      zusatz: [],
    });
    schau.oeffne();
    expect(wurzel.querySelector('img')).toBeNull();
    expect(wurzel.querySelector('b')).toBeNull();
  });
});

describe('berechneMassstab', () => {
  it('füllt den Rahmen und behält 16:9', () => {
    expect(berechneMassstab(FOLIE_BREITE, FOLIE_HOEHE)).toBe(1);
    expect(berechneMassstab(2560, 1440)).toBe(2);
    expect(berechneMassstab(1280, 360)).toBe(0.5); // Höhe begrenzt
  });

  it('bleibt bei unbekannter Größe bei 1', () => {
    expect(berechneMassstab(0, 0)).toBe(1);
  });
});

describe('Taste f', () => {
  it('öffnet und schließt die Folienschau', () => {
    expect(tasteZuAktion('f', [])).toEqual({ typ: 'folien' });
    expect(tasteZuAktion('F', [])).toEqual({ typ: 'folien' });
  });
});

describe('Rundgang steuert die Folie', () => {
  it('zeigt eine bestimmte Folie und blendet sie wieder aus', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: hauptfolien, zusatz: zusatzfolien });
    expect(schau.istOffen).toBe(false); // der Rundgang beginnt ohne Folie
    expect(schau.zeigeFolie(4)).toBe(true);
    expect(schau.nummer).toBe(4);
    expect(wurzel.hidden).toBe(false);
    schau.verstecke();
    expect(schau.istOffen).toBe(false);
    expect(schau.zeigeFolie(99)).toBe(false);
  });

  it('blendet mit f die Ergänzungsfolien ein und wieder aus', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: hauptfolien, zusatz: zusatzfolien });
    schau.zeigeFolie(7);
    expect(schau.zusatzUmschalten()).toBe(true);
    expect(schau.modus).toBe('zusatz');
    expect(schau.nummer).toBe(8);
    expect(schau.weiter()).toBe(true);
    expect(schau.nummer).toBe(9);
    expect(schau.zusatzUmschalten()).toBe(false);
    expect(schau.modus).toBe('haupt');
    expect(schau.istOffen).toBe(false); // der Rundgang übernimmt wieder
  });
});

describe('Kleine Begrüßungsfolie', () => {
  it('steht als Karte über der Halle und weicht ab Folie 2 der ganzen Fläche', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: hauptfolien, zusatz: zusatzfolien });
    schau.zeigeFolie(1);
    expect(document.body.classList.contains('folien-klein')).toBe(true);
    expect(wurzel.querySelector('.f-folie').classList.contains('f-titelart')).toBe(true);
    schau.zeigeFolie(2);
    expect(document.body.classList.contains('folien-klein')).toBe(false);
    schau.zeigeFolie(1);
    schau.verstecke();
    expect(document.body.classList.contains('folien-klein')).toBe(false);
  });

  it('misst den Maßstab an der Bühne, damit der Rahmen um die Folie frei bleibt', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: hauptfolien, zusatz: [] });
    // Das Rechteck des Wurzelknotens schliesst die Polsterung ein; nur die
    // Buehne gibt das Innenmass an, in das die Folie passen muss.
    wurzel.getBoundingClientRect = () => ({ width: 1600, height: 900 });
    wurzel.querySelector('.f-buehne').getBoundingClientRect = () => ({ width: 1542, height: 842 });
    schau.zeigeFolie(2);
    expect(wurzel.querySelector('.f-folie').style.transform).toBe('scale(' + 842 / FOLIE_HOEHE + ')');
  });

  it('skaliert sie auf einen Bruchteil des Rahmens', () => {
    expect(KLEIN_ANTEIL).toBeGreaterThan(0.2);
    expect(KLEIN_ANTEIL).toBeLessThan(0.6);
    expect(berechneMassstab(FOLIE_BREITE * KLEIN_ANTEIL, FOLIE_HOEHE * KLEIN_ANTEIL)).toBeCloseTo(KLEIN_ANTEIL);
  });
});

describe('Folien je Station', () => {
  it('legt die Begrüßungsfolie auf die Totale und verteilt die sechs Inhaltsfolien', async () => {
    const { folienJeStation } = await import('../src/folien-inhalt.js');
    const karte = folienJeStation();
    expect(karte.get('totale').map((f) => f.nr)).toEqual([1]);
    expect(karte.get('meisterbuero').map((f) => f.nr)).toEqual([2, 3]);
    expect(karte.get('datenraum').map((f) => f.nr)).toEqual([4]);
    expect(karte.get('terminal').map((f) => f.nr)).toEqual([5]);
    expect(karte.get('anzeigetafel').map((f) => f.nr)).toEqual([6]);
    expect(karte.get('pruefstand').map((f) => f.nr)).toEqual([7]);
  });

  it('baut daraus den Ablauf: erst die Fahrt, dann je Folie ein Schritt', async () => {
    const { baueSchritte } = await import('../src/schritte.js');
    const { folienJeStation } = await import('../src/folien-inhalt.js');
    const { default: daten } = await import('../src/stationen.json');
    const karte = folienJeStation();
    const schritte = baueSchritte(daten.stationen, (st) => (karte.get(st.id) || []).length);
    // 1 Totale + (1+2) + (1+1) + (1+1) + (1+1) + (1+1) + 1 Rückflug = 13
    expect(schritte).toHaveLength(13);
    expect(schritte[0]).toEqual({ typ: 'totale' });
    expect(schritte[1]).toEqual({ typ: 'fahrt', stationId: 'meisterbuero' });
    expect(schritte[2]).toEqual({ typ: 'belegpunkt', stationId: 'meisterbuero', index: 0 });
    expect(schritte[3]).toEqual({ typ: 'belegpunkt', stationId: 'meisterbuero', index: 1 });
    expect(schritte[4]).toEqual({ typ: 'fahrt', stationId: 'datenraum' });
    expect(schritte[5]).toEqual({ typ: 'belegpunkt', stationId: 'datenraum', index: 0 });
    expect(schritte[6]).toEqual({ typ: 'fahrt', stationId: 'terminal' });
  });
});
