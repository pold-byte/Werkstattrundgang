import { describe, it, expect, vi } from 'vitest';
import { leseAoSchalter, erzeugeKomposition } from '../src/komposition.js';

function stubRenderer() {
  return { render: vi.fn(), getSize: (v) => v.set(1600, 900), domElement: {}, capabilities: {} };
}

describe('leseAoSchalter', () => {
  it('ist standardmäßig an', () => { expect(leseAoSchalter('')).toBe(true); });
  it('lässt sich per ao=0 abschalten', () => { expect(leseAoSchalter('?ao=0')).toBe(false); });
  it('akzeptiert ao=1 ausdrücklich', () => { expect(leseAoSchalter('?x=1&ao=1')).toBe(true); });
});

describe('erzeugeKomposition ohne AO', () => {
  it('rendert direkt über den Renderer', () => {
    const r = stubRenderer();
    const k = erzeugeKomposition(r, {}, {}, { ao: false });
    k.render();
    expect(r.render).toHaveBeenCalledTimes(1);
    expect(k.aoAktiv).toBe(false);
  });
});

describe('Überlast-Abschaltung', () => {
  it('schaltet AO ab, wenn die mittlere Bildzeit über der Schwelle liegt', () => {
    let t = 0;
    const jetzt = () => { t += 40; return t; }; // 40 ms pro Bild
    const r = stubRenderer();
    const composer = { render: vi.fn(), setSize: vi.fn() };
    const k = erzeugeKomposition(r, {}, {}, { ao: true, jetzt, messfenster: 5, aoAbschaltenAb: 25, _composerFabrik: () => composer });
    for (let i = 0; i < 6; i += 1) k.render();
    expect(k.aoAktiv).toBe(false);
    expect(r.render).toHaveBeenCalled();
    expect(k.mittlereBildzeit()).toBeGreaterThan(25);
  });
  it('behält AO bei schnellen Bildern', () => {
    let t = 0;
    const jetzt = () => { t += 8; return t; };
    const composer = { render: vi.fn(), setSize: vi.fn() };
    const k = erzeugeKomposition(stubRenderer(), {}, {}, { ao: true, jetzt, messfenster: 5, _composerFabrik: () => composer });
    for (let i = 0; i < 12; i += 1) k.render();
    expect(k.aoAktiv).toBe(true);
    expect(composer.render).toHaveBeenCalledTimes(12);
  });
});
