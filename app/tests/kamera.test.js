import { describe, it, expect } from 'vitest';
import { glaetten, lerp3, Kamerafahrt } from '../src/kamera.js';

describe('glaetten (kubisches Ease-in-out)', () => {
  it('liefert die Fixpunkte 0, 0.5 und 1', () => {
    expect(glaetten(0)).toBe(0);
    expect(glaetten(0.5)).toBeCloseTo(0.5, 10);
    expect(glaetten(1)).toBe(1);
  });

  it('ist monoton steigend', () => {
    let vorher = -1;
    for (let t = 0; t <= 1.0001; t += 0.01) {
      const e = glaetten(Math.min(t, 1));
      expect(e).toBeGreaterThanOrEqual(vorher);
      vorher = e;
    }
  });
});

describe('lerp3', () => {
  it('interpoliert komponentenweise', () => {
    expect(lerp3([0, 0, 0], [10, -4, 2], 0.5)).toEqual([5, -2, 1]);
    expect(lerp3([1, 2, 3], [1, 2, 3], 0.7)).toEqual([1, 2, 3]);
  });
});

describe('Kamerafahrt', () => {
  const von = { position: [0, 0, 0], blickziel: [0, 0, -1] };
  const nach = { position: [10, 4, -6], blickziel: [12, 1, -9] };

  it('endet exakt auf der Zielpose, unabhängig von der Schrittweite', () => {
    const fahrt = new Kamerafahrt(von, nach, 6);
    let pose;
    // unregelmäßige Frame-Zeiten, Summe > Dauer
    for (const dt of [0.016, 0.4, 1.3, 0.016, 2.0, 3.0]) pose = fahrt.fortschritt(dt);
    expect(fahrt.fertig).toBe(true);
    expect(pose.position).toEqual(nach.position);
    expect(pose.blickziel).toEqual(nach.blickziel);
  });

  it('abbrechen() (Skip) springt hart auf die Zielpose', () => {
    const fahrt = new Kamerafahrt(von, nach, 6);
    fahrt.fortschritt(0.5);
    const pose = fahrt.abbrechen();
    expect(fahrt.fertig).toBe(true);
    expect(pose.position).toEqual(nach.position);
  });

  it('ist bei halber Zeit genau in der Mitte (deterministisch)', () => {
    const fahrt = new Kamerafahrt(von, nach, 4);
    const pose = fahrt.fortschritt(2);
    expect(pose.position[0]).toBeCloseTo(5, 10);
    expect(pose.blickziel[1]).toBeCloseTo(0.5, 10);
  });

  it('folgt Wegpunkten: bei halber Strecke exakt auf dem mittigen Wegpunkt', () => {
    const a = { position: [0, 0, 0], blickziel: [0, 0, -1] };
    const b = { position: [2, 0, 0], blickziel: [4, 0, -1] };
    // Wegpunkt liegt seitlich versetzt genau auf halber Bogenlänge.
    const fahrt = new Kamerafahrt(a, b, 4, [[1, 3, 0]]);
    const pose = fahrt.fortschritt(2); // t=0.5 → e=0.5 → s = halbe Gesamtlänge
    expect(pose.position[0]).toBeCloseTo(1, 10);
    expect(pose.position[1]).toBeCloseTo(3, 10);
    // Blickziel schwenkt weiter direkt von Start- zu Zielblick.
    expect(pose.blickziel[0]).toBeCloseTo(2, 10);
  });

  it('endet auch mit Wegpunkten exakt auf der Zielpose', () => {
    const fahrt = new Kamerafahrt(von, nach, 6, [[0, 5, 0], [10, 5, -6]]);
    let pose;
    for (const dt of [0.7, 1.9, 0.016, 4.0]) pose = fahrt.fortschritt(dt);
    expect(fahrt.fertig).toBe(true);
    expect(pose.position).toEqual(nach.position);
    expect(pose.blickziel).toEqual(nach.blickziel);
  });
});
