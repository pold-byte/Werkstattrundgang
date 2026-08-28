// Reload-Sicherheit (Spec §6): Stand überlebt ein versehentliches F5.
// storage ist injizierbar (sessionStorage in der App, Attrappe im Test).
const SCHLUESSEL = 'rundgang-stand';

export function speichereStand(storage, stand) {
  storage.setItem(SCHLUESSEL, JSON.stringify({ index: stand.index, sprung: stand.sprung ?? null }));
}

export function ladeStand(storage) {
  const roh = storage.getItem(SCHLUESSEL);
  if (!roh) return null;
  try {
    const stand = JSON.parse(roh);
    if (typeof stand.index !== 'number') return null;
    return { index: stand.index, sprung: stand.sprung ?? null };
  } catch {
    return null;
  }
}
