// Tastenbelegung laut Spec §6. Escape gehört dem Browser (Vollbild) und wird nie belegt.
export function tasteZuAktion(key, stationen) {
  switch (key) {
    case 'ArrowRight':
    case ' ':
    case 'PageDown':
      return { typ: 'weiter' };
    case 'ArrowLeft':
    case 'PageUp':
      return { typ: 'zurueck' };
    case '0':
      return { typ: 'totale' };
    case 's': case 'S':
      return { typ: 'skip' };
    case 'v': case 'V':
      return { typ: 'video' };
    case 'b': case 'B':
      return { typ: 'schwarz' };
    default: {
      if (/^[1-9]$/.test(key)) {
        const st = stationen.find((s) => s.nr === Number(key));
        return st ? { typ: 'sprung', stationId: st.id } : null;
      }
      return null;
    }
  }
}

// Während einer Fahrt: alles sperren, genau EINEN weiter-Druck puffern (Spec §6).
// skip und schwarz müssen immer sofort wirken.
export class Eingabesperre {
  constructor() {
    this.gesperrt = false;
    this.puffer = null;
  }

  sperren() {
    this.gesperrt = true;
    this.puffer = null;
  }

  entsperren() {
    const gepuffert = this.puffer;
    this.puffer = null;
    this.gesperrt = false;
    return gepuffert;
  }

  verarbeite(aktion) {
    if (!aktion) return null;
    if (!this.gesperrt) return aktion;
    if (aktion.typ === 'skip' || aktion.typ === 'schwarz') return aktion;
    if (aktion.typ === 'weiter' && !this.puffer) this.puffer = aktion;
    return null;
  }
}
