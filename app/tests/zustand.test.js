import { describe, it, expect } from 'vitest';
import { Zustandsmaschine, leiteAnsichtAb } from '../src/zustand.js';
import { baueSchritte } from '../src/schritte.js';
import daten from '../src/stationen.json';

const schritte = baueSchritte(daten.stationen);

describe('Zustandsmaschine', () => {
  it('startet auf der Totale und geht mit weiter()/zurueck() durch die Liste', () => {
    const z = new Zustandsmaschine(schritte);
    expect(z.aktuell).toEqual({ typ: 'totale' });
    expect(z.weiter()).toEqual({ typ: 'fahrt', stationId: 'meisterbuero' });
    expect(z.weiter()).toEqual({ typ: 'belegpunkt', stationId: 'meisterbuero', index: 0 });
    expect(z.zurueck()).toEqual({ typ: 'fahrt', stationId: 'meisterbuero' });
  });

  it('läuft an den Enden nicht aus der Liste', () => {
    const z = new Zustandsmaschine(schritte);
    expect(z.zurueck()).toEqual({ typ: 'totale' });
    for (let i = 0; i < 100; i++) z.weiter();
    expect(z.aktuell).toEqual({ typ: 'rueckflug' });
  });

  it('Direktsprung überlagert den linearen Stand, weiter() kehrt dorthin zurück', () => {
    const z = new Zustandsmaschine(schritte);
    z.weiter(); // fahrt meisterbuero (index 1)
    expect(z.springeZuStation('besprechung')).toEqual({ typ: 'sprung', stationId: 'besprechung' });
    expect(z.index).toBe(1); // linearer Stand unverändert
    // weiter() räumt nur den Sprung ab und kehrt zum linearen Stand (schritte[1]) zurück
    expect(z.weiter()).toEqual({ typ: 'fahrt', stationId: 'meisterbuero' });
  });

  it('springeZurTotale() zeigt die Totale, ohne den Stand zu verlieren', () => {
    const z = new Zustandsmaschine(schritte);
    z.weiter(); z.weiter();
    expect(z.springeZurTotale()).toEqual({ typ: 'sprung-totale' });
    expect(z.index).toBe(2);
  });

  it('setzeStand() stellt Index und Sprung wieder her (für sessionStorage)', () => {
    const z = new Zustandsmaschine(schritte);
    z.setzeStand({ index: 5, sprung: { typ: 'sprung', stationId: 'terminal' } });
    expect(z.index).toBe(5);
    expect(z.aktuell).toEqual({ typ: 'sprung', stationId: 'terminal' });
    z.setzeStand({ index: 999, sprung: null }); // ungültig → ignoriert
    expect(z.index).toBe(5);
  });
});

describe('leiteAnsichtAb', () => {
  it('Totale und Rückflug zeigen die Totale ohne Panel', () => {
    expect(leiteAnsichtAb({ typ: 'totale' }, daten.stationen)).toEqual({ ort: 'totale', belegpunkte: 0 });
    expect(leiteAnsichtAb({ typ: 'rueckflug' }, daten.stationen)).toEqual({ ort: 'totale', belegpunkte: 0 });
  });

  it('Fahrt zeigt die Station mit 0 Belegpunkten, Belegpunkt i zeigt i+1', () => {
    expect(leiteAnsichtAb({ typ: 'fahrt', stationId: 'terminal' }, daten.stationen))
      .toEqual({ ort: 'terminal', belegpunkte: 0 });
    expect(leiteAnsichtAb({ typ: 'belegpunkt', stationId: 'terminal', index: 1 }, daten.stationen))
      .toEqual({ ort: 'terminal', belegpunkte: 2 });
  });

  it('Sprung zeigt alle Belegpunkte der Station', () => {
    expect(leiteAnsichtAb({ typ: 'sprung', stationId: 'besprechung' }, daten.stationen))
      .toEqual({ ort: 'besprechung', belegpunkte: 3 });
    expect(leiteAnsichtAb({ typ: 'sprung-totale' }, daten.stationen))
      .toEqual({ ort: 'totale', belegpunkte: 0 });
  });
});
