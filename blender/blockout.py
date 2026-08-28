"""Blockout der Instandhaltungswerkstatt (Stil C: Low-Poly, entsaettigte Farben).

Koordinaten-Vertrag: Three.js ist Y-up, Blender Z-up; der glTF-Exporter konvertiert
automatisch (+Y up). Die Hilfsfunktion pos() nimmt daher Three.js-Koordinaten
(x, y, z wie in stationen.json) und uebersetzt sie nach Blender (x, -z, y).
Objektnamen folgen dem Vertrag Station_<nr>_<id> bzw. Monitor_Bildschirm.
"""
import bpy
import os

ZIEL = os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd(),
                    "app", "public", "szene.glb")


def pos(x, y, z):
    return (x, -z, y)


def material(name, farbe):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*farbe, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def quader(name, groesse, position, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (groesse[0], groesse[1], groesse[2])
    obj.data.materials.append(mat)
    return obj


# ---- Szene leeren -----------------------------------------------------------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

GRAU_BODEN = (0.55, 0.58, 0.60)
GRAU_WAND = (0.76, 0.79, 0.81)
GRAU_OBJEKT = (0.62, 0.66, 0.69)
GRAU_DUNKEL = (0.30, 0.32, 0.34)
ROT_ZUG = (0.55, 0.16, 0.20)  # entsaettigtes Verkehrsrot, nur am Triebzug (Spec §2)

m_boden = material("Boden", GRAU_BODEN)
m_wand = material("Wand", GRAU_WAND)
m_objekt = material("Objekt", GRAU_OBJEKT)
m_dunkel = material("Dunkel", GRAU_DUNKEL)
m_zug = material("Zug", ROT_ZUG)

# ---- Halle ------------------------------------------------------------------
quader("Halle_Boden", (34, 20, 0.2), pos(0, -0.1, 0), m_boden)
quader("Halle_Wand_Nord", (34, 0.3, 6), pos(0, 3, -10), m_wand)
quader("Halle_Wand_Sued", (34, 0.3, 6), pos(0, 3, 10), m_wand)
quader("Halle_Wand_West", (0.3, 20, 6), pos(-17, 3, 0), m_wand)
quader("Halle_Wand_Ost", (0.3, 20, 6), pos(17, 3, 0), m_wand)

# ---- Gleis + Triebzug (quer durch die Halle bei z=0) ------------------------
quader("Gleis_Schiene_1", (30, 0.15, 0.15), pos(0, 0.08, -0.7), m_dunkel)
quader("Gleis_Schiene_2", (30, 0.15, 0.15), pos(0, 0.08, 0.7), m_dunkel)
quader("Triebzug_Korpus", (14, 1.6, 2.4), pos(1, 1.4, 0), m_zug)
quader("Triebzug_Dach", (13.4, 1.5, 0.4), pos(1, 2.4, 0), m_dunkel)

# ---- Stationen (Positionen = blickziel aus stationen.json) ------------------
quader("Station_1_meisterbuero", (3, 2.4, 2.6), pos(-10, 1.3, -5), m_objekt)
quader("Station_1_pinnwand", (2.2, 0.1, 1.2), pos(-10, 1.8, -6.2), m_wand)

quader("Station_2_datenraum", (2.6, 1.2, 2.4), pos(-3, 1.2, -6), m_objekt)
for i, dx in enumerate((-0.8, 0.0, 0.8)):
    quader(f"Station_2_regalbrett_{i}", (2.2, 1.0, 0.08), pos(-3, 0.6 + i * 0.7, -6), m_dunkel)

quader("Station_3_terminal_saeule", (0.6, 0.6, 1.4), pos(7, 0.7, -5), m_dunkel)
bpy.ops.mesh.primitive_plane_add(size=1, location=pos(7, 1.5, -3.95))
monitor = bpy.context.active_object
monitor.name = "Monitor_Bildschirm"
monitor.scale = (1.6, 0.9, 1)
monitor.rotation_euler = (1.5708, 0, 0)  # senkrecht stellen, Front Richtung Sued
monitor.data.materials.append(m_dunkel)

quader("Station_4_anzeigetafel", (3.2, 0.15, 1.8), pos(9, 2, 5.8), m_dunkel)
quader("Station_5_pruefstand", (2.8, 1.4, 1.0), pos(2, 0.5, 6), m_objekt)
quader("Station_6_besprechung_tisch", (2.4, 1.2, 0.75), pos(-9, 0.4, 6), m_objekt)

# ---- Stationsschilder: dunkler Wuerfel + helle Ziffer (Spec §4 Startbild) ---
for nr, (x, z) in {1: (-10, -5), 2: (-3, -6), 3: (7, -5), 4: (9, 5), 5: (2, 6), 6: (-9, 6)}.items():
    quader(f"Schild_{nr}", (0.5, 0.5, 0.5), pos(x, 3.4, z), m_dunkel)
    bpy.ops.object.text_add(location=pos(x, 3.4, z + 0.28))
    ziffer = bpy.context.active_object
    ziffer.name = f"Schild_{nr}_ziffer"
    ziffer.data.body = str(nr)
    ziffer.data.size = 0.35
    ziffer.data.extrude = 0.02
    ziffer.data.align_x = "CENTER"
    ziffer.data.align_y = "CENTER"
    ziffer.rotation_euler = (1.5708, 0, 0)  # aufrecht, Front nach Sueden (Three +z)
    ziffer.data.materials.append(m_wand)
    bpy.ops.object.convert(target="MESH")  # glTF exportiert Text-Objekte nicht zuverlaessig

# ---- Export -----------------------------------------------------------------
os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=ZIEL,
    export_format="GLB",
    export_lights=False,
    export_cameras=False,
    export_apply=True,
)
print(f"Export fertig: {ZIEL}")
