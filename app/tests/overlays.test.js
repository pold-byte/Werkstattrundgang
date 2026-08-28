import { describe, it, expect, beforeEach } from 'vitest';
import { zeigePanel, versteckePanel, schalteSchwarzbild, zeigeTitel, schalteDimmer } from '../src/overlays.js';
import daten from '../src/stationen.json';

let panel, schwarz, titel, dimmer;

beforeEach(() => {
  document.body.innerHTML =
    '<div id="titel" hidden></div><div id="dimmer"></div><aside id="panel"></aside><div id="schwarzbild" hidden></div>';
  panel = document.getElementById('panel');
  schwarz = document.getElementById('schwarzbild');
  titel = document.getElementById('titel');
  dimmer = document.getElementById('dimmer');
});

describe('zeigePanel', () => {
  const station = daten.stationen.find((s) => s.id === 'terminal');

  it('rendert Nummer, Titel, Kernaussage und nur die sichtbaren Belegpunkte', () => {
    zeigePanel(panel, station, 2);
    expect(panel.classList.contains('sichtbar')).toBe(true);
    expect(panel.querySelector('.stationsnummer').textContent).toBe('Station 3');
    expect(panel.querySelector('h2').textContent).toBe('Fragen statt Formeln');
    expect(panel.querySelector('.kernaussage').textContent).toContain('PLATZHALTER');
    expect(panel.querySelectorAll('li')).toHaveLength(2);
    expect(panel.querySelector('.kapitel').textContent).toBe('Kap. 3.4, 4.3');
  });

  it('rendert bei 0 sichtbaren Belegpunkten eine leere Liste', () => {
    zeigePanel(panel, station, 0);
    expect(panel.querySelectorAll('li')).toHaveLength(0);
  });

  it('verwendet textContent (kein HTML-Injection über JSON-Inhalte)', () => {
    zeigePanel(panel, { ...station, kernaussage: '<img src=x>' }, 0);
    expect(panel.querySelector('.kernaussage img')).toBeNull();
  });
});

describe('versteckePanel / zeigeTitel / schalteSchwarzbild / schalteDimmer', () => {
  it('versteckt das Panel über die Sichtbarkeitsklasse', () => {
    panel.classList.add('sichtbar');
    versteckePanel(panel);
    expect(panel.classList.contains('sichtbar')).toBe(false);
  });

  it('zeigt und versteckt den Titel', () => {
    zeigeTitel(titel, true);
    expect(titel.hidden).toBe(false);
    zeigeTitel(titel, false);
    expect(titel.hidden).toBe(true);
  });

  it('schaltet das Schwarzbild um und meldet den neuen Zustand', () => {
    expect(schalteSchwarzbild(schwarz)).toBe(true);
    expect(schwarz.hidden).toBe(false);
    expect(schalteSchwarzbild(schwarz)).toBe(false);
    expect(schwarz.hidden).toBe(true);
  });

  it('schaltet den Dimmer über die aktiv-Klasse', () => {
    schalteDimmer(dimmer, true);
    expect(dimmer.classList.contains('aktiv')).toBe(true);
    schalteDimmer(dimmer, false);
    expect(dimmer.classList.contains('aktiv')).toBe(false);
  });
});
