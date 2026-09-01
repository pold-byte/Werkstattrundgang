"""Prueft alle Kamerafahrten (Posen-Paare aus app/src/stationen.json) auf Kollisionen
mit der gebauten Szene. Die App faehrt geradlinig zwischen den Posen (Easing aendert
nur das Timing, nicht den Pfad) — jedes Segment wird gegen alle AABBs getestet,
aufgeblasen um einen Kamera-Radius."""
import bpy
import json
import os
from mathutils import Vector

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in dir() else os.getcwd()
KAMERA_RADIUS = 0.3

# Szene nur bauen, wenn sie nicht schon steht. pruefe_alles.py baut einmal und
# laesst alle drei Pruefungen darauf laufen — der Aufbau kostet 200 s, die
# Pruefungen selbst nur Sekunden.
if "SZENE_BEREIT" not in globals():
    with open(os.path.join(WURZEL, "blender", "blockout.py"), encoding="utf-8") as f:
        code = f.read().replace("bpy.ops.export_scene.gltf(", "(lambda **kw: None)(")
    exec(compile(code, "blockout.py", "exec"))
    SZENE_BEREIT = True

with open(os.path.join(WURZEL, "app", "src", "stationen.json"), encoding="utf-8") as f:
    daten = json.load(f)

posen = {"totale": daten["totale"]["kamera"]["position"]}
for st in daten["stationen"]:
    posen[st["id"]] = st["kamera"]["position"]

# Drei->Blender: (x, -z, y)
def zu_blender(p):
    return Vector((p[0], -p[2], p[1]))


HUELLE = ("Dach_", "Wand_", "Halle_", "Relief_", "Tor_Vorfeld")
boxen = []
for o in bpy.data.objects:
    if o.type != "MESH" or o.name.startswith(HUELLE):
        continue
    ecken = [o.matrix_world @ Vector(e) for e in o.bound_box]
    mn = Vector((min(e.x for e in ecken) - KAMERA_RADIUS,
                 min(e.y for e in ecken) - KAMERA_RADIUS,
                 min(e.z for e in ecken) - KAMERA_RADIUS))
    mx = Vector((max(e.x for e in ecken) + KAMERA_RADIUS,
                 max(e.y for e in ecken) + KAMERA_RADIUS,
                 max(e.z for e in ecken) + KAMERA_RADIUS))
    boxen.append((o.name, mn, mx))


def segment_trifft_box(a, b, mn, mx):
    """Slab-Test: schneidet die Strecke a->b die Box (mn, mx)?"""
    t0, t1 = 0.0, 1.0
    for i in range(3):
        d = b[i] - a[i]
        if abs(d) < 1e-9:
            if a[i] < mn[i] or a[i] > mx[i]:
                return False
        else:
            u0 = (mn[i] - a[i]) / d
            u1 = (mx[i] - a[i]) / d
            if u0 > u1:
                u0, u1 = u1, u0
            t0 = max(t0, u0)
            t1 = min(t1, u1)
            if t0 > t1:
                return False
    return True


# Geflogen wird die geroutete Polylinie aus app/src/fahrtwege.json (falls fuer das
# Paar vorhanden), sonst die direkte Strecke — exakt wie in der App.
wege_datei = os.path.join(WURZEL, "app", "src", "fahrtwege.json")
fahrten = []
if os.path.exists(wege_datei):
    with open(wege_datei, encoding="utf-8") as f:
        fahrten = json.load(f)["fahrten"]


def wegpunkte_fuer(von, nach):
    for f in fahrten:
        if f["von"] == von and f["nach"] == nach:
            return f["wegpunkte"]
        if f["von"] == nach and f["nach"] == von:
            return list(reversed(f["wegpunkte"]))
    return []


namen = list(posen.keys())
print("=== FLUGPFAD-KOLLISIONEN (Kamera-Radius %.2f) ===" % KAMERA_RADIUS)
gesamt = 0
for i in range(len(namen)):
    for j in range(i + 1, len(namen)):
        pfad = ([zu_blender(posen[namen[i]])]
                + [zu_blender(w) for w in wegpunkte_fuer(namen[i], namen[j])]
                + [zu_blender(posen[namen[j]])])
        treffer = []
        for k in range(len(pfad) - 1):
            treffer += [n for (n, mn, mx) in boxen
                        if segment_trifft_box(pfad[k], pfad[k + 1], mn, mx)]
        if treffer:
            gesamt += len(treffer)
            print(f"FAHRT {namen[i]} -> {namen[j]} ({len(pfad) - 2} Wegpunkte): {', '.join(treffer[:6])}"
                  + (f" (+{len(treffer) - 6} weitere)" if len(treffer) > 6 else ""))
print(f"=== FERTIG ({gesamt} Kollisionen) ===")
