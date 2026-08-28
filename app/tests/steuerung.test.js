import { describe, it, expect } from 'vitest';
import { tasteZuAktion, Eingabesperre } from '../src/steuerung.js';
import daten from '../src/stationen.json';

describe('tasteZuAktion (Spec §6)', () => {
  it('belegt weiter/zurueck auf Pfeile, Leertaste und Bild-Tasten', () => {
    expect(tasteZuAktion('ArrowRight', daten.stationen)).toEqual({ typ: 'weiter' });
    expect(tasteZuAktion(' ', daten.stationen)).toEqual({ typ: 'weiter' });
    expect(tasteZuAktion('PageDown', daten.stationen)).toEqual({ typ: 'weiter' });
    expect(tasteZuAktion('ArrowLeft', daten.stationen)).toEqual({ typ: 'zurueck' });
    expect(tasteZuAktion('PageUp', daten.stationen)).toEqual({ typ: 'zurueck' });
  });

  it('übersetzt Ziffern in Stations-Sprünge und 0 in die Totale', () => {
    expect(tasteZuAktion('3', daten.stationen)).toEqual({ typ: 'sprung', stationId: 'terminal' });
    expect(tasteZuAktion('6', daten.stationen)).toEqual({ typ: 'sprung', stationId: 'besprechung' });
    expect(tasteZuAktion('0', daten.stationen)).toEqual({ typ: 'totale' });
    expect(tasteZuAktion('7', daten.stationen)).toBeNull();
  });

  it('belegt S, V und B; Escape ist bewusst NICHT belegt', () => {
    expect(tasteZuAktion('s', daten.stationen)).toEqual({ typ: 'skip' });
    expect(tasteZuAktion('V', daten.stationen)).toEqual({ typ: 'video' });
    expect(tasteZuAktion('b', daten.stationen)).toEqual({ typ: 'schwarz' });
    expect(tasteZuAktion('Escape', daten.stationen)).toBeNull();
  });
});

describe('Eingabesperre (während Kamerafahrt)', () => {
  it('lässt Aktionen ohne Sperre durch', () => {
    const sperre = new Eingabesperre();
    expect(sperre.verarbeite({ typ: 'weiter' })).toEqual({ typ: 'weiter' });
  });

  it('puffert bei aktiver Sperre genau einen weiter-Druck', () => {
    const sperre = new Eingabesperre();
    sperre.sperren();
    expect(sperre.verarbeite({ typ: 'weiter' })).toBeNull();
    expect(sperre.verarbeite({ typ: 'weiter' })).toBeNull(); // zweiter Druck verworfen
    expect(sperre.verarbeite({ typ: 'sprung', stationId: 'terminal' })).toBeNull();
    expect(sperre.entsperren()).toEqual({ typ: 'weiter' }); // genau einer kommt nach
    expect(sperre.entsperren()).toBeNull();
  });

  it('lässt skip und schwarz auch bei Sperre durch', () => {
    const sperre = new Eingabesperre();
    sperre.sperren();
    expect(sperre.verarbeite({ typ: 'skip' })).toEqual({ typ: 'skip' });
    expect(sperre.verarbeite({ typ: 'schwarz' })).toEqual({ typ: 'schwarz' });
  });
});
