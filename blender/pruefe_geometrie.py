"""Objektive Geometrie-Pruefung: Schweber (kein Kontakt) und Durchdringungen (AABB)."""
import bpy
from mathutils import Vector

# Szene nur bauen, wenn sie nicht schon steht. pruefe_alles.py baut einmal und
# laesst alle drei Pruefungen darauf laufen — der Aufbau kostet 200 s, die
# Pruefungen selbst nur Sekunden.
if "SZENE_BEREIT" not in globals():
    with open(r"C:\Users\Leopold\Werkstatrundgang\blender\blockout.py", encoding="utf-8") as f:
        code = f.read().replace("bpy.ops.export_scene.gltf(", "(lambda **kw: None)(")
    exec(compile(code, "blockout.py", "exec"))
    SZENE_BEREIT = True

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



def x_nachbarn(boxen, rand):
    """Sweep-and-prune auf der x-Achse.

    Zwei Boxen koennen sich nur beruehren oder durchdringen, wenn sich ihre
    x-Intervalle (mit Toleranz rand) ueberlappen. Statt aller n*(n-1)/2 Paare
    — bei 1700 Meshes 1.4 Millionen — sammelt ein Sweep nur diese ein. Die
    Auswahl ist eine konservative Obermenge: keine Paarung, die die alte
    Doppelschleife gefunden haette, faellt weg. Die Ergebnisse sind deshalb
    identisch, nur die Laufzeit faellt von quadratisch auf nahezu linear."""
    nachbarn = [[] for _ in boxen]
    ordnung = sorted(range(len(boxen)), key=lambda i: boxen[i][1].x)
    aktiv = []
    for idx in ordnung:
        mn_x = boxen[idx][1].x
        aktiv = [a for a in aktiv if boxen[a][2].x >= mn_x - rand]
        for a in aktiv:
            nachbarn[a].append(idx)
            nachbarn[idx].append(a)
        aktiv.append(idx)
    return nachbarn


NACHBARN = x_nachbarn(boxen, EPS)

# --- Schweber: kein Kontakt zu irgendetwas (inkl. Boden bei z~0, Blender-Z = hoch) ---
print("=== SCHWEBER (kein Kontakt) ===")
for i, (n, mn, mx) in enumerate(boxen):
    if n.startswith(HUELLE):
        continue
    if mn.z <= 0.06:  # steht auf dem Boden
        continue
    kontakt = False
    for j in NACHBARN[i]:
        n2, mn2, mx2 = boxen[j]
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
    # Reihenfolge i < j beibehalten, damit die Paarbenennung in der Ausgabe
    # unveraendert bleibt
    for j in sorted(k for k in NACHBARN[i] if k > i):
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
