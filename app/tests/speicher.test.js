import { describe, it, expect } from 'vitest';
import { speichereStand, ladeStand } from '../src/speicher.js';

function attrappenStorage() {
  const daten = new Map();
  return {
    getItem: (k) => (daten.has(k) ? daten.get(k) : null),
    setItem: (k, v) => daten.set(k, String(v)),
  };
}

describe('speichereStand / ladeStand', () => {
  it('speichert und lädt Index und Sprung', () => {
    const storage = attrappenStorage();
    speichereStand(storage, { index: 7, sprung: { typ: 'sprung', stationId: 'pruefstand' } });
    expect(ladeStand(storage)).toEqual({ index: 7, sprung: { typ: 'sprung', stationId: 'pruefstand' } });
  });

  it('liefert null, wenn nichts gespeichert ist', () => {
    expect(ladeStand(attrappenStorage())).toBeNull();
  });

  it('liefert null bei kaputtem JSON statt zu werfen', () => {
    const storage = attrappenStorage();
    storage.setItem('rundgang-stand', '{kaputt');
    expect(ladeStand(storage)).toBeNull();
  });
});
