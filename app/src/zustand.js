// Linearer Vortragsstand plus überlagernder Direktsprung (Fragerunde).
// weiter()/zurueck() räumen einen aktiven Sprung ab und arbeiten auf der Liste.
export class Zustandsmaschine {
  constructor(schritte) {
    this.schritte = schritte;
    this.index = 0;
    this.sprung = null;
  }

  get aktuell() {
    return this.sprung ?? this.schritte[this.index];
  }

  weiter() {
    if (this.sprung) {
      this.sprung = null;
      return this.aktuell;
    }
    if (this.index < this.schritte.length - 1) this.index++;
    return this.aktuell;
  }

  zurueck() {
    if (this.sprung) {
      this.sprung = null;
      return this.aktuell;
    }
    if (this.index > 0) this.index--;
    return this.aktuell;
  }

  springeZuStation(stationId) {
    this.sprung = { typ: 'sprung', stationId };
    return this.aktuell;
  }

  springeZurTotale() {
    this.sprung = { typ: 'sprung-totale' };
    return this.aktuell;
  }

  setzeStand(stand) {
    if (!stand || typeof stand.index !== 'number') return;
    if (stand.index < 0 || stand.index >= this.schritte.length) return;
    this.index = stand.index;
    this.sprung = stand.sprung ?? null;
  }
}

// Übersetzt den aktuellen Schritt in das, was Kamera und Panel zeigen sollen.
export function leiteAnsichtAb(schritt, stationen) {
  switch (schritt.typ) {
    case 'totale':
    case 'rueckflug':
    case 'sprung-totale':
      return { ort: 'totale', belegpunkte: 0 };
    case 'fahrt':
      return { ort: schritt.stationId, belegpunkte: 0 };
    case 'belegpunkt':
      return { ort: schritt.stationId, belegpunkte: schritt.index + 1 };
    case 'sprung': {
      const st = stationen.find((s) => s.id === schritt.stationId);
      return { ort: schritt.stationId, belegpunkte: st ? st.belegpunkte.length : 0 };
    }
    default:
      return { ort: 'totale', belegpunkte: 0 };
  }
}
