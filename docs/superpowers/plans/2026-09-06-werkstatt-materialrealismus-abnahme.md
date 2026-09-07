# Gesamtabnahme und Sichtprotokoll — Werkstatt ohne Comic-Look

Abnahme zu Task 7 des Plans `2026-09-06-werkstatt-materialrealismus.md`. Bezugspunkt für "davor" ist
`blender/renders/p_*_v2vorher.png` (Snapshot vom 2026-09-06 22:05, unmittelbar nach Task 0 Step 5, also
vor Task 1–6 dieses Plans). "Danach" sind die frischen Renders vom 2026-09-07 09:56 auf HEAD `8ea0588`.

## 1. Messwerte

### Prüfer, Exporter, Tests

```
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python blender/pruefe_alles.py 2>/dev/null \
  | grep -E "SCHWEBT|Durchdringungen gesamt|Routen|Kollisionen"
```
Ausgabe:
```
=== FERTIG (11 Durchdringungen gesamt) ===
GESCHRIEBEN: .../app/src/fahrtwege.json (20 Routen, 0 ungeloest)
=== FERTIG (0 Kollisionen) ===
```
Kein `SCHWEBT`-Eintrag. `app/src/fahrtwege.json` wurde vom Prüfer neu geschrieben, aber inhaltlich nicht
verändert (`git status`/`git diff` zeigen keine Differenz danach) — nicht neu committet.

```
node tools/glb-info.mjs app/public/szene.glb | tail -3
```
```
images: 14 (1038987 bytes)
extensionsUsed: KHR_materials_clearcoat, KHR_materials_emissive_strength
size: 7762936 bytes
```
`size` = 7 762 936 Byte, unter der 8 000 000-Byte-Grenze (≈ 97 % des Budgets ausgeschöpft, siehe
"Offene Punkte"). Beide geforderten Extensions sind vorhanden.

```
cd app && npm test --silent
```
```
Test Files  10 passed (10)
     Tests  48 passed (48)
```

### Bildzeit im Browser (Dev-Server, Pixel-Ratio 1 und 2)

Gemessen mit `window.__komposition.mittlereBildzeit()` und `window.__komposition.aoAktiv` bei
1920×1080, Browser-Tab im Vordergrund (sonst wird `requestAnimationFrame` gedrosselt und die Werte
sind bedeutungslos).

Erste Messung (Tab bereits offen, kein frischer Reload, 20 s gewartet): `aoAktiv = false`,
`mittlereBildzeit() = 13.85 ms`. Ein anschließender frischer Reload mit demselben Tab im Vordergrund
und erneut 20 s Wartezeit ergab `aoAktiv = true`, `mittlereBildzeit() = 17.21 ms`. Da die
Überlastprüfung erst nach 120 gemessenen Frames auswertet (`messfenster = 120` in `komposition.js`)
und AO danach nie wieder reaktiviert wird, reicht offenbar ein einzelnes langsames erstes Messfenster
direkt nach dem Laden (Textur-/GLB-Decode, Shader-Kompilierung), um AO für die restliche Sitzung
dauerhaft abzuschalten — auch wenn die eingeschwungene Bildzeit danach klar unter dem Zielwert liegt.
Für die restlichen Messungen und für die Renders wurde deshalb vor jeder Messung ein frischer Reload
gemacht und `aoAktiv` unmittelbar davor geprüft.

| Messung | Pixel-Ratio | `aoAktiv` | `mittlereBildzeit()` |
|---|---|---|---|
| 1920×1080, frischer Reload, 20 s gewartet | 1 | `true` | 17.21 ms |
| gleiche Seite, `setPixelRatio(2)` + `setSize`, 20 s gewartet | 2 | `true` | 16.19 ms |

Zielwert aus den Global Constraints ist ≤ 16.7 ms bei 1920×1080 und Pixel-Ratio ≤ 2. Der DPR-1-Wert
(17.21 ms) liegt knapp (≈ 3 %) über diesem Zielwert, der DPR-2-Wert (16.19 ms) knapp darunter; beide
liegen weit unter der Abschaltschwelle von 25 ms, `aoAktiv` blieb in beiden Fällen `true`.
`window.__renderer.getPixelRatio()` bestätigte 1 bzw. 2 während der jeweiligen Messung. Nach den
Messungen wurde Pixel-Ratio auf 1 zurückgesetzt und die Fenstergröße auf das Standard-Preset.

`document.visibilityState` war während aller gewerteten Messungen `visible`; der beschriebene
Drosselungs-Fall (verstecktes Panel) trat nicht auf, daher war der `gl.finish()`-Ersatzbenchmark nicht
nötig.

## 2. Renders und Posen-Vergleich

Alle neun Posen über `tools/render-posen.js` gerendert (`p_totale`, `p_meisterbuero`, `p_datenraum`,
`p_terminal`, `p_anzeigetafel`, `p_pruefstand`, `p_besprechung`, `p_hero_bahnsteig`,
`p_hero_kranbahn`), mit `aoAktiv === true` unmittelbar vor und nach dem Render-Lauf bestätigt. Jedes
`p_<pose>.png` wurde gegen `p_<pose>_v2vorher.png` verglichen (Sichtprüfung plus Pixel-Differenz als
Kontrollwert: mittlere Kanaldifferenz und Anteil der Pixel mit Differenz > 15/255 je Kanal, gemessen
mit Pillow). Referenz für die sieben Ausgangsbefunde ist der Abschnitt "Ausgangsbefund" des Plans.

| Pose | Bewertung | Pixel-Diff (Anteil verändert) | Sichtbar behobene Befunde | Was noch "Comic" aussieht |
|---|---|---|---|---|
| p_totale | besser | 80.4 % | 1 (Boden-Fugen/Noise bei Nahsicht sichtbar), 4/6 (Fässer mit Sicken-Bändern und Rauheitszeichnung statt glattem Zylinder) | Wand über dem Zug bleibt unter dem Fensterlicht nahezu weiß/flach; Absperrhut-Orange und Fass-Blau bleiben reine Einheitsfarbe |
| p_meisterbuero | besser | 90.2 % | 1 (Boden-Fliesenraster mit Fugenlinien statt gleichmäßig grauer Fläche), 5 (Fenster zeigt einen leichten Verlauf statt Flatterfläche) | Bürotür, -stuhl, Schreibtisch bleiben glatt einfarbig (Blau/Weiß) ohne erkennbare Gebrauchsspur |
| p_datenraum | besser | 91.4 % | 1 (Fliesenfugen), 2 (Kontaktschatten an der Kistenkante/am Pylon-Sockel im Zoom sichtbar, vorher kaum), 6 (Fässer mit Sicken) | Regalboxen (Rot/Grün/Orange/Weiß) bleiben makellos gesättigt und untereinander identisch; Regalkorpus einfarbig Blau |
| p_terminal | besser | 88.0 % | 1 (Boden-Fliesenraster) | Beide blauen Maschinengehäuse exakt im selben Farbton nebeneinander (Befund 3 hier nicht sichtbar behoben); kein auffälliger Kontaktschatten am Terminalsockel |
| p_anzeigetafel | gleich | 66.8 % (geringster Wert der neun Posen) | 6 (Fässer mit Sicken, linker Bildrand) | Wand hinter der Tafel wirkt durch das neue Tageslicht eher flacher/heller als vorher, nicht strukturierter; Tafelgestell, grüner Spind und orange Kiste bleiben Einheitsfarbe |
| p_pruefstand | besser | 71.4 % | 2 (deutlich schärfer abgegrenzter Kontaktschatten unter dem Prüfstand-Sockel — die klarste Verbesserung der neun Posen) | Prüfstand-Gehäuse selbst bleibt einfarbig Blau/Orange, Hintergrundwand bleibt flach; das 5-m-Plattenraster des Bodens (`blockout.py:444`) liegt in dieser Kameraposition so, dass bei Nachprüfung (Zoom-Crops) keine Fugenlinie im sichtbaren Bodenbereich zu erkennen war — Befund 1 ist hier trotz insgesamt reduziertem Wolken-Rauschen nicht überzeugend als "klar sichtbar" belegt |
| p_besprechung | gleich | 71.6 % | 1 (Boden-Fliesenraster minimal deutlicher) | Alle vier Stühle exakt im selben gesättigten Blauton nebeneinander — verletzt das Fertig-Kriterium "keine gesättigte Einheitsfarbe an mehr als zwei benachbarten Requisiten"; Wand und Pressenverkleidung bleiben flach |
| p_hero_bahnsteig | besser | 83.2 % | 1 (Bodenfugen), 3/4 (Zugkarosserie wirkt durch Klarlack/Rauheit weniger reinweiß-glänzend als vorher) | Handlauf-Gelb, Rohrleitungen Blau/Rot und Signalsäule (Rot/Gelb/Grün) bleiben satte Einheitsfarben |
| p_hero_kranbahn | besser | 81.9 % | 1 (Bodenfugen) | Gabelstapler-Orange, grüner Spind, blaue Kiste bleiben gesättigte Einheitsfarben; Kranbahn-Lauffläche und Hintergrundwand bleiben flach |

Ergebnis: 7 von 9 Posen "besser", 2 von 9 "gleich" (`p_anzeigetafel`, `p_besprechung`), keine
"schlechter". Die Pixel-Differenz ist in allen neun Posen groß (67–91 % der Pixel verändert um mehr
als 15/255 je Kanalsumme), d. h. Licht/Material/Textur wirken flächendeckend; visuell fällt der
Unterschied bei Normalansicht der Jury-Distanz aber deutlich schwächer aus als bei Nahsicht/Zoom, weil
die neuen Rauheits- und Albedo-Texturen bei 512–1024 px auf mehrere Meter Kantenlänge fein sind.

Kriterium aus dem Plan ("in keiner Jury-Pose ein Objekt ohne Kontaktschatten, keine unstrukturierte
Großfläche, keine gesättigte Einheitsfarbe an mehr als zwei benachbarten Requisiten") ist **nicht
vollständig erfüllt**: `p_besprechung` zeigt vier benachbarte Stühle in identischer gesättigter
Einheitsfarbe, und mehrere Wandflächen (`p_anzeigetafel`, `p_besprechung`, Hintergrund von
`p_meisterbuero`) lesen sich auf Jury-Distanz weiterhin als unstrukturierte Fläche.

## 3. Offene Punkte für einen Folgeplan

- **Vier identische blaue Stühle in `p_besprechung`.** Verletzt das Fertig-Kriterium direkt; Task 4
  (Palette entsättigen/variieren) wurde offenbar nur auf Lackflächen des Zugs und auf Fässer
  angewendet, nicht auf Möbel-Requisiten wie Stühle.
- **Wandflächen bleiben auf Jury-Distanz flach.** Die neue Wandtextur (Task 2) ist erst bei
  Nahsicht/Zoom als Struktur erkennbar; in `p_anzeigetafel` wirkt die Wand durch das neue
  Fenstertageslicht (Task 6) sogar heller/flacher als in der `_v2vorher`-Referenz. Befund 1 ist für
  Wandflächen nur teilweise gelöst.
- **Einheitsfarben an weiteren Requisiten.** Handlauf-Gelb, Signalfarben (Rot/Grün am Signalpfosten),
  Absperrhut-Orange, Regalbox-Rot/Grün/Orange/Weiß und die blauen Maschinengehäuse in `p_terminal`
  bleiben durchgängig in reiner, identischer Sättigung ohne die in Task 4 eingeführte
  Chargenvariation.
- **AO-Überlastschutz ohne Reaktivierung und ohne Warm-up.** Ein einzelnes langsames erstes
  Messfenster direkt nach dem Laden (Asset-Decode) kann AO dauerhaft abschalten, obwohl die
  eingeschwungene Bildzeit danach weit unter dem Zielwert liegt (beobachtet: ein Reload lieferte
  `aoAktiv = false` bei `mittel = 13.85 ms`, ein zweiter Reload derselben Seite `aoAktiv = true` bei
  `mittel = 17.21 ms`). Ein Vorschlag für einen Folgeplan: die ersten Messfenster nach dem Laden von
  der Überlastprüfung ausnehmen oder einen Reaktivierungspfad ergänzen.
- **Bildzeit bei Pixel-Ratio 1 knapp über dem Zielwert.** 17.21 ms gegenüber einem Zielwert von
  ≤ 16.7 ms (≈ 3 % Überschreitung), bei Pixel-Ratio 2 dagegen 16.19 ms (im Ziel). Kein akuter
  Handlungsbedarf (weit unter der 25-ms-Abschaltschwelle), aber wenig Reserve für künftige
  GTAO-Parameter oder zusätzliche Postprocessing-Schritte.
- **Texturbudget fast ausgeschöpft.** `szene.glb` liegt bei 7 762 936 Byte, also ≈ 97 % der
  8-MB-Grenze aus den Global Constraints. Weitere Texturdetails (z. B. für die oben genannten
  Requisiten) brauchen entweder kleinere Kantenlängen oder Kompression, sonst wird die Grenze
  überschritten.
- **Kontaktschatten nicht an allen Requisiten geprüft.** Der Nachweis für Befund 2 stützt sich auf
  Stichproben-Zooms (`p_datenraum`, `p_pruefstand`); ob wirklich jedes Objekt in jeder Jury-Pose einen
  Kontaktschatten zeigt (Kriterium aus dem Plan), wurde nicht Objekt für Objekt verifiziert.

## Referenzen

- Vorher-Renders: `blender/renders/p_*_v2vorher.png` (nicht versioniert, Snapshot 2026-09-06 22:05).
- Nachher-Renders für dieses Protokoll: `blender/renders/p_*.png`, erzeugt 2026-09-07 09:56 auf HEAD
  `8ea0588` mit `tools/render-posen.js`.
- Ausgangsbefund und Global Constraints: `docs/superpowers/plans/2026-09-06-werkstatt-materialrealismus.md`.
