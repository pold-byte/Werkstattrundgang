# Übergabe-Notiz für die nächste Claude-Session

Stand: 2026-08-28 · Branch: `feature/werkstattrundgang-app` · Übergabe vom Laptop auf den PC.

## Was das hier ist

Live navigierbare 3D-Präsentations-App (Three.js) für die Verteidigung einer DHBW-Projektarbeit
(DB Regio, Text-to-SQL-Datenplattform). Alle Grundlagen sind fertig und verbindlich:

- **Design-Spec:** `docs/superpowers/specs/2026-08-25-werkstattrundgang-praesentation-design.md`
- **Implementierungsplan (14 Tasks):** `docs/superpowers/plans/2026-08-25-werkstattrundgang-app.md`
  — vollständig ausformuliert (Code in jedem Schritt, TDD), adversarial verifiziert.
- **Briefing des Nutzers:** `BRIEFING_praesentation.md` (Stationen, Gestaltungsregeln — bindend).
- `BATCH_01_Vorabklaerung_Antworten.docx`: Quellmaterial zu Planungsdialog-Folien;
  Verwendungszweck noch nicht geklärt (vermutlich spätere Inhalte-Phase).

## Aktueller Stand

- **Task 1 (Projektgerüst) ist FERTIG** inkl. bestandenem Spec-Review, bestandenem
  Qualitäts-Review und umgesetzten Review-Fixes (Commits `bf311ac` + `d538c6e`).
  Verifiziert: `npm test` → 2 passed; `npm run build` → grün.
- **Nächster Schritt: Task 2** (Stationsdaten & Schrittliste) — dann 3…14 der Reihe nach.

## So geht es weiter (Anleitung an Claude)

1. Arbeite den Plan Task für Task ab. Der Plan-Header verlangt das Skill
   `superpowers:subagent-driven-development` (empfohlen) bzw. `superpowers:executing-plans`;
   falls das superpowers-Plugin hier nicht installiert ist, folge dem Plan manuell und
   diszipliniert: pro Task exakt die Steps (Test zuerst, dann Implementierung, dann Commit).
2. Pro Task nach dem Commit: Spec-Abgleich und Qualitäts-Review (bei subagent-driven-development
   automatisch; sonst Selbst-Review gegen Spec-Abschnitt und Task-Text).
3. Nach jedem abgeschlossenen Task pushen (`origin` ist eingerichtet).
4. Task 11 braucht Blender (idealerweise mit MCP-Anbindung) auf dem ausführenden Rechner.
5. Explizit NICHT Teil des Plans (kommt später als eigene Phasen): Slide-Inhalte befüllen
   (Quelldateien TextV14.docx, Fragenkatalog_v4.docx, Messprotokolle fehlen noch im Repo!),
   Station-5-Ergebnisgrafik, Demo-Video-Aufnahme, Ausbaustufe D, Generalprobe.
6. Platzhalter-Politik: `[PLATZHALTER: …]`-Texte sind Absicht. Keine Zahlen erfinden — nie.

## Koordination

Die bisherige Session (Laptop) hat die Arbeit hier GESTOPPT und dispatcht keine weiteren
Tasks. Es gilt: nur eine Maschine committet auf dem Branch. Diese Notiz darf gelöscht
werden, sobald sie gelesen und verstanden ist.
