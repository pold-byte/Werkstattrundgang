import { describe, it, expect, beforeEach } from 'vitest';
import { folien, hauptfolien, zusatzfolien, fusszeile } from '../src/folien-inhalt.js';
import { erzeugeFolienschau, berechneMassstab, FOLIE_BREITE, FOLIE_HOEHE } from '../src/folien.js';
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

  it('verteilt die Hauptfolien auf die Stationen des Rundgangs', async () => {
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
    expect(wurzel.querySelector('.f-kopf').textContent).toContain('DB INTERN / DB INTERNAL');
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

describe('Taste f schaltet den Satz weiter', () => {
  it('geht vom Haupt- auf den Zusatzsatz, dann auf die Halle und zurück', () => {
    const schau = erzeugeFolienschau(wurzel, { haupt: hauptfolien, zusatz: zusatzfolien });
    schau.oeffne();
    expect(schau.nummer).toBe(1);
    schau.naechsterSatz();
    expect(schau.modus).toBe('zusatz');
    expect(schau.nummer).toBe(8);
    expect(schau.weiter()).toBe(true);
    expect(schau.nummer).toBe(9);
    schau.naechsterSatz();
    expect(schau.istOffen).toBe(false); // Halle ohne Folie
    schau.naechsterSatz();
    expect(schau.modus).toBe('haupt');
    expect(schau.nummer).toBe(1);
    expect(schau.istOffen).toBe(true);
  });
});
