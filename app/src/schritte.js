// Baut aus den Stationsdaten die lineare Schrittliste des Vortrags.
// Station mit im_rundgang === false (Reserve) ist nur per Direktsprung erreichbar.
export function baueSchritte(stationen) {
  const schritte = [{ typ: 'totale' }];
  for (const st of stationen) {
    if (st.im_rundgang === false) continue;
    schritte.push({ typ: 'fahrt', stationId: st.id });
    for (let i = 0; i < st.belegpunkte.length; i++) {
      schritte.push({ typ: 'belegpunkt', stationId: st.id, index: i });
    }
  }
  schritte.push({ typ: 'rueckflug' });
  return schritte;
}
