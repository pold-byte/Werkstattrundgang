"""Objektive Geometrie-Pruefung: Schweber (kein Kontakt) und Durchdringungen (AABB)."""
import bpy
from mathutils import Vector

with open(r"C:\Users\Leopold\Werkstatrundgang\blender\blockout.py", encoding="utf-8") as f:
    code = f.read().replace("bpy.ops.export_scene.gltf(", "(lambda **kw: None)(")
exec(compile(code, "blockout.py", "exec"))

EPS = 0.08
HUELLE = ("Dach_", "Wand_", "Halle_", "Relief_", "Tor_Vorfeld", "Stuetze_", "Dachbinder", "Empore_", "Buehne_")

boxen = []
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    ecken = [o.matrix_world @ Vector(e) for e in o.bound_box]
    mn = Vector((min(e.x for e in ecken), min(e.y for e in ecken), min(e.z for e in ecken)))
    mx = Vector((max(e.x for e in ecken), max(e.y for e in ecken), max(e.z for e in ecken)))
    boxen.append((o.name, mn, mx))


def ueberlappung(a_mn, a_mx, b_mn, b_mx, rand=0.0):
    d = [min(a_mx[i], b_mx[i]) - max(a_mn[i], b_mn[i]) + rand for i in range(3)]
    if all(v > 0 for v in d):
        return d[0] * d[1] * d[2]
    return 0.0


def volumen(mn, mx):
    return max(1e-9, (mx.x - mn.x) * (mx.y - mn.y) * (mx.z - mn.z))


def familie(name):
    return name.split("_")[0].split(".")[0]


# --- Schweber: kein Kontakt zu irgendetwas (inkl. Boden bei z~0, Blender-Z = hoch) ---
print("=== SCHWEBER (kein Kontakt) ===")
for i, (n, mn, mx) in enumerate(boxen):
    if n.startswith(HUELLE):
        continue
    if mn.z <= 0.06:  # steht auf dem Boden
        continue
    kontakt = False
    for j, (n2, mn2, mx2) in enumerate(boxen):
        if i == j:
            continue
        if ueberlappung(mn, mx, mn2, mx2, rand=EPS) > 0:
            kontakt = True
            break
    if not kontakt:
        print(f"SCHWEBT: {n} unterkante={mn.z:.2f} mitte=({(mn.x+mx.x)/2:.1f},{(mn.y+mx.y)/2:.1f})")

# --- Durchdringungen zwischen fremden Familien ---
print("=== DURCHDRINGUNGEN (>35% des kleineren Objekts) ===")
treffer = []
for i in range(len(boxen)):
    n, mn, mx = boxen[i]
    if n.startswith(HUELLE):
        continue
    for j in range(i + 1, len(boxen)):
        n2, mn2, mx2 = boxen[j]
        if n2.startswith(HUELLE) or familie(n) == familie(n2):
            continue
        ov = ueberlappung(mn, mx, mn2, mx2)
        klein = min(volumen(mn, mx), volumen(mn2, mx2))
        if klein > 0.0005 and ov > 0.35 * klein:
            treffer.append((ov / klein, n, n2))
treffer.sort(reverse=True)
for anteil, n, n2 in treffer[:35]:
    print(f"DURCHDRINGT ({anteil * 100:.0f}%): {n} <-> {n2}")
print(f"=== FERTIG ({len(treffer)} Durchdringungen gesamt) ===")
