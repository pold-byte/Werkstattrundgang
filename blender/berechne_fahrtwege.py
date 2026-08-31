"""Berechnet kollisionsfreie Kamerafahrt-Routen zwischen allen Posen-Paaren.

Die App faehrt Polylinien (app/src/kamera.js); dieses Skript findet fuer jedes
kollidierende Paar 1-2 Zwischen-Wegpunkte aus einem Kandidatenraster und schreibt
das Ergebnis nach app/src/fahrtwege.json. Nach Szenen- oder Posenaenderungen einfach
neu laufen lassen:  blender --background --python blender/berechne_fahrtwege.py
"""
import bpy
import json
import os
from mathutils import Vector

WURZEL = os.getcwd()
KAMERA_RADIUS = 0.3

with open(os.path.join(WURZEL, "blender", "blockout.py"), encoding="utf-8") as f:
    code = f.read().replace("bpy.ops.export_scene.gltf(", "(lambda **kw: None)(")
exec(compile(code, "blockout.py", "exec"))

with open(os.path.join(WURZEL, "app", "src", "stationen.json"), encoding="utf-8") as f:
    daten = json.load(f)

posen = {"totale": daten["totale"]["kamera"]["position"]}
for st in daten["stationen"]:
    posen[st["id"]] = st["kamera"]["position"]

HUELLE = ("Dach_", "Wand_", "Halle_", "Relief_", "Tor_Vorfeld")
boxen = []
for o in bpy.data.objects:
    if o.type != "MESH" or o.name.startswith(HUELLE):
        continue
    ecken = [o.matrix_world @ Vector(e) for e in o.bound_box]
    boxen.append((
        Vector((min(e.x for e in ecken) - KAMERA_RADIUS, min(e.y for e in ecken) - KAMERA_RADIUS,
                min(e.z for e in ecken) - KAMERA_RADIUS)),
        Vector((max(e.x for e in ecken) + KAMERA_RADIUS, max(e.y for e in ecken) + KAMERA_RADIUS,
                max(e.z for e in ecken) + KAMERA_RADIUS)),
    ))


def zu_blender(p):
    return Vector((p[0], -p[2], p[1]))


def segment_frei(a, b):
    for mn, mx in boxen:
        t0, t1 = 0.0, 1.0
        ok = True
        for i in range(3):
            d = b[i] - a[i]
            if abs(d) < 1e-9:
                if a[i] < mn[i] or a[i] > mx[i]:
                    ok = False
                    break
            else:
                u0 = (mn[i] - a[i]) / d
                u1 = (mx[i] - a[i]) / d
                if u0 > u1:
                    u0, u1 = u1, u0
                t0 = max(t0, u0)
                t1 = min(t1, u1)
                if t0 > t1:
                    ok = False
                    break
        if ok:
            return False  # Segment schneidet diese Box
    return True


# Kandidaten in Three.js-Koordinaten: Korridore noerdlich/suedlich des Zugs,
# Ost-/West-Umfahrung der Zugenden, hohe Ebene ueber den Buehnen-Handlaeufen.
kandidaten = []
for y in (1.7, 2.2, 3.4):
    for x in range(-13, 14, 2):
        for z in (-3.6, -1.9, 3.3, 3.9):
            kandidaten.append((x, y, z))
for y in (1.7, 2.2, 2.8):
    for z in (-2.6, -1.2, 0.2, 1.6, 2.8):
        kandidaten.append((10.8, y, z))
        kandidaten.append((11.6, y, z))
        kandidaten.append((12.8, y, z))
        kandidaten.append((-11.5, y, z))
        kandidaten.append((-13.0, y, z))
for x in range(-12, 13, 3):
    for z in (-1.9, 0.0, 3.9):
        kandidaten.append((x, 4.6, z))


def laenge(pfad):
    return sum((pfad[i + 1] - pfad[i]).length for i in range(len(pfad) - 1))


# Sichtbarkeitsgraph ueber den Kandidaten: Knoten = Kandidaten, Kanten = freie
# Segmente bis 8 m Laenge. Pro Posen-Paar kommen die beiden Posen als Knoten dazu,
# dann kuerzester Weg (Dijkstra) und Abkuerzen ueberfluessiger Zwischenknoten.
import heapq

kand_b = [zu_blender(k) for k in kandidaten]
kanten = {i: [] for i in range(len(kand_b))}
for i in range(len(kand_b)):
    for j in range(i + 1, len(kand_b)):
        d = (kand_b[j] - kand_b[i]).length
        if d <= 8.0 and segment_frei(kand_b[i], kand_b[j]):
            kanten[i].append((j, d))
            kanten[j].append((i, d))


def kuerzester_weg(a, b):
    """Dijkstra von Pose a nach Pose b ueber den Kandidatengraphen (Punkte in Blender-Koordinaten)."""
    start_kanten = [(i, (kand_b[i] - a).length) for i in range(len(kand_b))
                    if (kand_b[i] - a).length <= 10.0 and segment_frei(a, kand_b[i])]
    ziel_ok = {i: (kand_b[i] - b).length for i in range(len(kand_b))
               if (kand_b[i] - b).length <= 10.0 and segment_frei(kand_b[i], b)}
    dist = {}
    vorher = {}
    haufen = [(d, i, None) for (i, d) in start_kanten]
    heapq.heapify(haufen)
    beste_ziel = None
    while haufen:
        d, i, vor = heapq.heappop(haufen)
        if i in dist:
            continue
        dist[i] = d
        vorher[i] = vor
        if i in ziel_ok:
            gesamt = d + ziel_ok[i]
            if beste_ziel is None or gesamt < beste_ziel[0]:
                beste_ziel = (gesamt, i)
        for (j, dj) in kanten[i]:
            if j not in dist:
                heapq.heappush(haufen, (d + dj, j, i))
    if beste_ziel is None:
        return None
    knoten = []
    i = beste_ziel[1]
    while i is not None:
        knoten.append(i)
        i = vorher[i]
    knoten.reverse()
    pfad = [a] + [kand_b[i] for i in knoten] + [b]
    drei = [None] + [kandidaten[i] for i in knoten] + [None]
    # Abkuerzen: von jedem Punkt so weit wie moeglich direkt springen
    ergebnis = []
    i = 0
    while i < len(pfad) - 1:
        j = len(pfad) - 1
        while j > i + 1 and not segment_frei(pfad[i], pfad[j]):
            j -= 1
        if 0 < j < len(pfad) - 1:
            ergebnis.append(drei[j])
        i = j
    return ergebnis


namen = list(posen.keys())
fahrtwege = []
uneloest = []
for i in range(len(namen)):
    for j in range(i + 1, len(namen)):
        a = zu_blender(posen[namen[i]])
        b = zu_blender(posen[namen[j]])
        if segment_frei(a, b):
            continue
        wegpunkte = kuerzester_weg(a, b)
        if wegpunkte is not None:
            fahrtwege.append({"von": namen[i], "nach": namen[j],
                              "wegpunkte": [[round(float(v), 2) for v in w] for w in wegpunkte]})
            print(f"ROUTE {namen[i]} -> {namen[j]}: {wegpunkte}")
        else:
            uneloest.append((namen[i], namen[j]))
            print(f"UNGELOEST: {namen[i]} -> {namen[j]}")

ziel = os.path.join(WURZEL, "app", "src", "fahrtwege.json")
with open(ziel, "w", encoding="utf-8") as f:
    json.dump({"kamera_radius": KAMERA_RADIUS, "fahrten": fahrtwege}, f, indent=1)
print(f"GESCHRIEBEN: {ziel} ({len(fahrtwege)} Routen, {len(uneloest)} ungeloest)")
