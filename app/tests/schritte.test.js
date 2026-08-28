import { describe, it, expect } from 'vitest';
import { baueSchritte } from '../src/schritte.js';
import daten from '../src/stationen.json';

describe('baueSchritte', () => {
  const schritte = baueSchritte(daten.stationen);

  it('beginnt mit der Totale und endet mit dem Rückflug', () => {
    expect(schritte[0]).toEqual({ typ: 'totale' });
    expect(schritte[schritte.length - 1]).toEqual({ typ: 'rueckflug' });
  });

  it('nimmt Station 6 (im_rundgang: false) nicht in den linearen Ablauf auf', () => {
    expect(schritte.some((s) => s.stationId === 'besprechung')).toBe(false);
  });

  it('erzeugt pro Rundgang-Station eine Fahrt plus einen Schritt je Belegpunkt', () => {
    // 1 Totale + 5 Stationen * (1 Fahrt + 3 Belegpunkte) + 1 Rückflug = 22
    expect(schritte).toHaveLength(22);
    expect(schritte[1]).toEqual({ typ: 'fahrt', stationId: 'meisterbuero' });
    expect(schritte[2]).toEqual({ typ: 'belegpunkt', stationId: 'meisterbuero', index: 0 });
    expect(schritte[4]).toEqual({ typ: 'belegpunkt', stationId: 'meisterbuero', index: 2 });
    expect(schritte[5]).toEqual({ typ: 'fahrt', stationId: 'datenraum' });
  });
});
