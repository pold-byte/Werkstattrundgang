# blender/frage_szene.py
"""Weltboxen einzelner Objekte in three.js-Koordinaten.

Baut die Szene EINMAL ohne Export (Muster wie pruefe_flugpfade.py) und druckt fuer
jedes Argument hinter '--' (Objektname oder Praefix) eine Zeile
    Name|minx,miny,minz|maxx,maxy,maxz
zwischen den Markern AABB-ANFANG und AABB-ENDE. '--alle' druckt alle Meshes;
das ist der Vorher/Nachher-Dump fuer Regressionsdiffs.

Aufruf:
  blender --background --python blender/frage_szene.py -- Gleis_Schiene_Nord Triebzug_DG_0_
  blender --background --python blender/frage_szene.py -- --alle > /tmp/vorher.txt
"""
import bpy
import os
import sys
from mathutils import Vector

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if "SZENE_BEREIT" not in globals():
    with open(os.path.join(WURZEL, "blender", "blockout.py"), encoding="utf-8") as f:
        code = f.read().replace("bpy.ops.export_scene.gltf(", "(lambda **kw: None)(")
    exec(compile(code, "blockout.py", "exec"))
    SZENE_BEREIT = True

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def weltbox(o):
    ecken = [o.matrix_world @ Vector(e) for e in o.bound_box]
    # Blender (x, y, z) -> three.js (x, z, -y)
    xs = [p.x for p in ecken]
    ys = [p.z for p in ecken]
    zs = [-p.y for p in ecken]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


zeilen = []
for o in sorted(bpy.data.objects, key=lambda ob: ob.name):
    if o.type != "MESH":
        continue
    if args and "--alle" not in args and not any(o.name == a or o.name.startswith(a) for a in args):
        continue
    mn, mx = weltbox(o)
    zeilen.append("%s|%.3f,%.3f,%.3f|%.3f,%.3f,%.3f" % (o.name, mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]))

print("AABB-ANFANG")
print("\n".join(zeilen))
print("AABB-ENDE")
