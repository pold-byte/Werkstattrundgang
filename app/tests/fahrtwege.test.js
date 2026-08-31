import { describe, it, expect } from 'vitest';
import { findeWegpunkte } from '../src/fahrtwege.js';
import daten from '../src/fahrtwege.json';
import stationen from '../src/stationen.json';

const beispiel = [
  { von: 'a', nach: 'b', wegpunkte: [[1, 2, 3], [4, 5, 6]] },
];

describe('findeWegpunkte', () => {
  it('liefert die Wegpunkte in Fahrtrichtung', () => {
    expect(findeWegpunkte('a', 'b', beispiel)).toEqual([[1, 2, 3], [4, 5, 6]]);
  });

  it('kehrt die Wegpunkte für die Gegenrichtung um, ohne die Tabelle zu verändern', () => {
    expect(findeWegpunkte('b', 'a', beispiel)).toEqual([[4, 5, 6], [1, 2, 3]]);
    expect(beispiel[0].wegpunkte).toEqual([[1, 2, 3], [4, 5, 6]]);
  });

  it('liefert für unbekannte Paare eine leere Liste (direkte Fahrt)', () => {
    expect(findeWegpunkte('a', 'x', beispiel)).toEqual([]);
  });

  it('kennt in der generierten Tabelle nur echte Orte', () => {
    const orte = new Set(['totale', ...stationen.stationen.map((s) => s.id)]);
    for (const fahrt of daten.fahrten) {
      expect(orte.has(fahrt.von)).toBe(true);
      expect(orte.has(fahrt.nach)).toBe(true);
      for (const w of fahrt.wegpunkte) expect(w).toHaveLength(3);
    }
  });
});
