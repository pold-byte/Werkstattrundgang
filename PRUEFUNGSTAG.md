# Checkliste Prüfungstag

## Eine Woche vorher
- [ ] DHBW schriftlich geklärt: eigener Laptop erlaubt? Beamer-Auflösung? HDMI oder VGA
      (Adapter!)? Abgabepflicht Foliensatz (→ PDF aus druck.html)? Rüstzeit vor dem Slot?
- [ ] Presenter-Remote-Tastencodes am eigenen Laptop verifiziert (erwartet: PageUp/PageDown).
- [ ] Generalprobe bei 1024x768 (4:3), 1280x800, 1920x1080 und Windows-Skalierung 125/150 %.
- [ ] Automatische Updates (Windows, Browser) pausiert; Umgebung eingefroren.
- [ ] `npm run build` + Probelauf über `app/start.bat`; `node tools/baue-notfall.mjs` frisch gebaut.
- [ ] USB-Stick 1 und 2: kompletter `app/`-Ordner ohne node_modules ist NICHT nötig — es reichen:
      `app/dist/`, `app/dist-notfall/notfall.html`, PDF-Export aus `druck.html`,
      MP4-Komplettmitschnitt, beide Demo-Videos.
- [ ] Kein `[PLATZHALTER]` mehr sichtbar (Abnahmekriterium Spec §10) — vorher Inhalte-Phase abschließen.

## Am Tag
- [ ] Laptop: Netzteil, HDMI-Adapter, Energiesparmodus aus, Benachrichtigungen aus, Flugmodus an.
- [ ] Bildschirm DUPLIZIEREN (nicht erweitern), dann `app/start.bat`.
- [ ] Startprobe: eine Fahrt hin und zurück, Taste B testen, dann auf Totale (Taste 0) parken.

## Wenn etwas hakt (Fallback-Leiter, Spec §7)
1. App startet nicht über start.bat → `app/dist-notfall/notfall.html` per Doppelklick.
2. WebGL/3D versagt → PDF-Foliensatz (identische Inhalte) in beliebigem PDF-Reader.
3. Laptop versagt → USB-Stick an Fremdrechner: PDF oder MP4-Mitschnitt.

## Tastenkarte (ausdrucken)
Pfeile/Leertaste/Bild-Tasten = weiter/zurück · 1–6 = Direktflug (6 = Reserve) · 0 = Totale
S = Fahrt überspringen · V = Demo-Video groß/klein · B = Schwarzbild · Esc = NICHT belegt
