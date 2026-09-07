// Baut aus den Stationsdaten die lineare Schrittliste des Vortrags.
// Station mit im_rundgang === false (Reserve) ist nur per Direktsprung erreichbar.
// anzahlFuer(station) bestimmt, wie viele Einblendungen eine Station hat; im
// Vortrag ist das die Zahl ihrer Folien.
export function baueSchritte(stationen, anzahlFuer = (st) => st.belegpunkte.length) {
  const schritte = [{ typ: 'totale' }];
  for (const st of stationen) {
    if (st.im_rundgang === false) continue;
    schritte.push({ typ: 'fahrt', stationId: st.id });
    for (let i = 0; i < anzahlFuer(st); i++) {
      schritte.push({ typ: 'belegpunkt', stationId: st.id, index: i });
    }
  }
  schritte.push({ typ: 'rueckflug' });
  return schritte;
}
