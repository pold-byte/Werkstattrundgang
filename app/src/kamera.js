// Zeitbasierte, framerate-unabhängige Kamerafahrt (Spec §5: deterministisch, Skip → Zielpose).
export function glaetten(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export function lerp3(a, b, t) {
  return [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t,
  ];
}

export class Kamerafahrt {
  // wegpunkte: optionale Zwischenpositionen (kollisionsfrei geroutet, siehe
  // blender/berechne_fahrtwege.py). Die Position folgt der Polylinie mit
  // konstanter Bahngeschwindigkeit pro Easing-Fortschritt, das Blickziel
  // schwenkt weiterhin direkt von Start- zu Zielblick.
  constructor(von, nach, dauerS, wegpunkte = []) {
    this.von = von;
    this.nach = nach;
    this.dauerS = dauerS;
    this.zeit = 0;
    this.fertig = false;
    this.pfad = [von.position, ...wegpunkte, nach.position];
    this.laengen = [0];
    for (let i = 1; i < this.pfad.length; i += 1) {
      const [ax, ay, az] = this.pfad[i - 1];
      const [bx, by, bz] = this.pfad[i];
      this.laengen.push(this.laengen[i - 1] + Math.hypot(bx - ax, by - ay, bz - az));
    }
  }

  positionBei(e) {
    const gesamt = this.laengen[this.laengen.length - 1];
    if (gesamt <= 0) return [...this.nach.position];
    const s = e * gesamt;
    let i = 1;
    while (i < this.laengen.length - 1 && this.laengen[i] < s) i += 1;
    const segment = this.laengen[i] - this.laengen[i - 1];
    const anteil = segment <= 0 ? 1 : (s - this.laengen[i - 1]) / segment;
    return lerp3(this.pfad[i - 1], this.pfad[i], anteil);
  }

  fortschritt(deltaS) {
    this.zeit += deltaS;
    const t = this.dauerS <= 0 ? 1 : Math.min(this.zeit / this.dauerS, 1);
    if (t >= 1) {
      this.fertig = true;
      return { position: [...this.nach.position], blickziel: [...this.nach.blickziel] };
    }
    const e = glaetten(t);
    return {
      position: this.positionBei(e),
      blickziel: lerp3(this.von.blickziel, this.nach.blickziel, e),
    };
  }

  abbrechen() {
    this.zeit = this.dauerS;
    this.fertig = true;
    return { position: [...this.nach.position], blickziel: [...this.nach.blickziel] };
  }
}
