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
  constructor(von, nach, dauerS) {
    this.von = von;
    this.nach = nach;
    this.dauerS = dauerS;
    this.zeit = 0;
    this.fertig = false;
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
      position: lerp3(this.von.position, this.nach.position, e),
      blickziel: lerp3(this.von.blickziel, this.nach.blickziel, e),
    };
  }

  abbrechen() {
    this.zeit = this.dauerS;
    this.fertig = true;
    return { position: [...this.nach.position], blickziel: [...this.nach.blickziel] };
  }
}
