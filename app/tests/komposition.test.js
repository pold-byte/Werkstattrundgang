import { describe, it, expect, vi } from 'vitest';
import { leseAoSchalter, erzeugeKomposition } from '../src/komposition.js';

function stubRenderer() {
  return { render: vi.fn(), getSize: (v) => v.set(1600, 900), getPixelRatio: () => 1, domElement: {}, capabilities: {} };
}

// Der Stub-Composer verbraucht auf der Fake-Uhr Zeit — der Ueberlastschutz misst
// die Dauer des Renderaufrufs, nicht mehr den Abstand zwischen zwei Aufrufen.
function stubTeile(uhr, kosten) {
  const composer = {
    render: vi.fn(() => { uhr.t += typeof kosten === 'function' ? kosten() : kosten; }),
    setSize: vi.fn(),
    setPixelRatio: vi.fn(),
    dispose: vi.fn(),
  };
  return { composer, gtao: { dispose: vi.fn() }, output: { dispose: vi.fn() } };
}

function baueKomposition(kosten, optionen = {}) {
  const uhr = { t: 0 };
  const renderer = stubRenderer();
  const teile = stubTeile(uhr, kosten);
  const fabrik = vi.fn(() => teile);
  const k = erzeugeKomposition(renderer, {}, {}, {
    ao: true, jetzt: () => uhr.t, messfenster: 5, aoAbschaltenAb: 25, _composerFabrik: fabrik, ...optionen,
  });
  return { k, uhr, renderer, teile, fabrik };
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
  it('setSize wirft ohne Composer nicht', () => {
    const k = erzeugeKomposition(stubRenderer(), {}, {}, { ao: false });
    expect(() => k.setSize(800, 600)).not.toThrow();
  });
});

describe('Überlast-Abschaltung', () => {
  it('schaltet AO ab, wenn die mittlere Bildzeit über der Schwelle liegt', () => {
    const { k, renderer } = baueKomposition(40); // 40 ms Renderkosten
    for (let i = 0; i < 5; i += 1) k.render();
    expect(k.aoAktiv).toBe(true); // erstes Fenster ist Aufwaermen
    for (let i = 0; i < 5; i += 1) k.render();
    expect(k.aoAktiv).toBe(false);
    expect(k.mittlereBildzeit()).toBeGreaterThan(25);
    k.render();
    expect(renderer.render).toHaveBeenCalled();
  });

  it('behält AO bei schnellen Bildern', () => {
    const { k, teile } = baueKomposition(8);
    for (let i = 0; i < 12; i += 1) k.render();
    expect(k.aoAktiv).toBe(true);
    expect(teile.composer.render).toHaveBeenCalledTimes(12);
  });

  it('verwirft einen einzelnen Ausreißer von 3000 ms', () => {
    let i = 0;
    const { k } = baueKomposition(() => (i++ === 7 ? 3000 : 8)); // ein Ruckler mitten in schnellen Bildern
    for (let n = 0; n < 20; n += 1) k.render();
    expect(k.aoAktiv).toBe(true);
    expect(k.mittlereBildzeit()).toBeLessThan(25);
  });

  it('bleibt nach dem Trip abgeschaltet, auch wenn schnelle Bilder folgen', () => {
    const uhr = { t: 0 };
    let kosten = 40;
    const renderer = stubRenderer();
    const teile = stubTeile(uhr, () => kosten);
    const k = erzeugeKomposition(renderer, {}, {}, {
      ao: true, jetzt: () => uhr.t, messfenster: 5, aoAbschaltenAb: 25, _composerFabrik: () => teile,
    });
    for (let n = 0; n < 10; n += 1) k.render();
    expect(k.aoAktiv).toBe(false);
    kosten = 2;
    for (let n = 0; n < 30; n += 1) k.render();
    expect(k.aoAktiv).toBe(false);
    expect(teile.composer.render).toHaveBeenCalledTimes(10);
  });

  it('gibt Composer, GTAO und OutputPass nach dem Trip frei', () => {
    const { k, teile } = baueKomposition(40);
    for (let n = 0; n < 10; n += 1) k.render();
    expect(k.aoAktiv).toBe(false);
    expect(teile.gtao.dispose).toHaveBeenCalledTimes(1);
    expect(teile.output.dispose).toHaveBeenCalledTimes(1);
    expect(teile.composer.dispose).toHaveBeenCalledTimes(1);
  });

  it('meldet 0 ms, solange kein volles Messfenster vorliegt', () => {
    const { k } = baueKomposition(40);
    for (let n = 0; n < 4; n += 1) k.render();
    expect(k.mittlereBildzeit()).toBe(0);
    k.render(); // Aufwaermfenster voll — wird verworfen, kein Mittelwert
    expect(k.mittlereBildzeit()).toBe(0);
  });

  it('baut den Composer genau einmal', () => {
    const { k, fabrik } = baueKomposition(8);
    for (let n = 0; n < 20; n += 1) k.render();
    expect(fabrik).toHaveBeenCalledTimes(1);
  });

  it('leert das Messfenster bei visibilitychange', () => {
    const { k } = baueKomposition(40);
    for (let n = 0; n < 5; n += 1) k.render(); // Aufwaermfenster
    for (let n = 0; n < 4; n += 1) k.render();
    document.dispatchEvent(new Event('visibilitychange'));
    for (let n = 0; n < 4; n += 1) k.render(); // ohne Reset waere hier laengst getrippt
    expect(k.aoAktiv).toBe(true);
  });

  it('messungZuruecksetzen beginnt ein neues Aufwärmfenster', () => {
    const { k } = baueKomposition(40);
    for (let n = 0; n < 5; n += 1) k.render();
    k.messungZuruecksetzen();
    for (let n = 0; n < 5; n += 1) k.render(); // wieder Aufwaermen
    expect(k.aoAktiv).toBe(true);
    for (let n = 0; n < 5; n += 1) k.render();
    expect(k.aoAktiv).toBe(false);
  });
});

describe('setSize mit Composer', () => {
  it('reicht PixelRatio und Größe an den Composer weiter', () => {
    const { k, teile } = baueKomposition(8);
    k.setSize(1600, 900);
    expect(teile.composer.setPixelRatio).toHaveBeenCalledWith(1);
    expect(teile.composer.setSize).toHaveBeenCalledWith(1600, 900);
  });
});
