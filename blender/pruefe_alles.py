"""Baut die Szene EINMAL und laesst alle drei Pruefungen darauf laufen.

Hintergrund: Gemessen an einer Szene mit 1687 Objekten kostet der Aufbau
(exec von blockout.py) 200 Sekunden, die eigentlichen Pruefungen zusammen
nur wenige. Wer die drei Werkzeuge einzeln aufruft, baut die Szene dreimal
und wartet zehn Minuten statt dreieinhalb.

Aufruf aus der Projektwurzel:
    blender --background --python blender/pruefe_alles.py

Die Einzelskripte bleiben eigenstaendig lauffaehig — sie bauen die Szene nur
dann selbst, wenn SZENE_BEREIT nicht schon gesetzt ist.
"""
import os
import time

import bpy

WURZEL = os.getcwd()
SKRIPTE = ("pruefe_geometrie.py", "berechne_fahrtwege.py", "pruefe_flugpfade.py")

t0 = time.time()
with open(os.path.join(WURZEL, "blender", "blockout.py"), encoding="utf-8") as f:
    code = f.read().replace("bpy.ops.export_scene.gltf(", "(lambda **kw: None)(")
exec(compile(code, "blockout.py", "exec"))
print(f"=== SZENE GEBAUT ({time.time() - t0:.0f} s, "
      f"{sum(1 for o in bpy.data.objects if o.type == 'MESH')} Meshes) ===")

for name in SKRIPTE:
    pfad = os.path.join(WURZEL, "blender", name)
    with open(pfad, encoding="utf-8") as f:
        quelle = f.read()
    # Jedes Skript bekommt einen eigenen Namensraum, damit sich die gleichnamigen
    # Globals (boxen, HUELLE, ueberlappung) nicht gegenseitig ueberschreiben. Die
    # gebaute Szene liegt in bpy.data und wird davon nicht beruehrt.
    t = time.time()
    exec(compile(quelle, name, "exec"), {"__name__": "__main__", "SZENE_BEREIT": True})
    print(f"=== {name} FERTIG ({time.time() - t:.0f} s) ===")

print(f"=== ALLES FERTIG ({time.time() - t0:.0f} s gesamt) ===")
