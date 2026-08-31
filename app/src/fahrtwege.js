import daten from './fahrtwege.json';

// Liefert die vorberechneten Zwischen-Wegpunkte fuer eine Fahrt zwischen zwei
// Orten (Stations-IDs oder "totale"). Die Tabelle (app/src/fahrtwege.json) ist
// von blender/berechne_fahrtwege.py generiert und symmetrisch nutzbar: fuer die
// Gegenrichtung werden die Wegpunkte umgekehrt. Unbekannte Paare fahren direkt.
export function findeWegpunkte(von, nach, fahrten = daten.fahrten) {
  for (const fahrt of fahrten) {
    if (fahrt.von === von && fahrt.nach === nach) return fahrt.wegpunkte;
    if (fahrt.von === nach && fahrt.nach === von) return [...fahrt.wegpunkte].reverse();
  }
  return [];
}
