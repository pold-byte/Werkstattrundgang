"""Werkstatt-Szene im Stil der isometrischen Referenz (blender/referenz-werkstatt.webp).

Stilentscheidung aus der Brainstorming-Session: durchgehend stilisiert und farbig
(Iso-Referenz), Detailtiefe ueber vier Hebel:
  1. Schatten/AO — im Viewer (szene.js: Shadow-Mapping + Hemisphaerenlicht)
  2. Rundgeometrie + Fasen — Zylinder-Rohre mit Kugelboegen, I-Profil-Traeger,
     Bevel auf allen Kanten (transform_apply + Bevel-Modifier, Export wendet an)
  3. Texturen — prozedural generiertes Boden-PNG (Value-Noise, ohne Abhaengigkeiten)
  4. Asset-Packs — separat, erst nach Freigabe
Prioritaet: Zug + Gleisumfeld, Decke + Haustechnik.

Koordinaten-Vertrag: Three.js ist Y-up, Blender Z-up; der glTF-Exporter konvertiert
automatisch (+Y up). pos() nimmt Three.js-Koordinaten (x, y, z wie in stationen.json)
und uebersetzt nach Blender (x, -z, y); kasten() nimmt (breite_x, tiefe_z, hoehe_y).
Objektnamen folgen dem Vertrag Station_<nr>_<id> bzw. Monitor_Bildschirm.
"""
import bpy
import os
import random
import struct
import zlib
from mathutils import Vector

WURZEL = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
ZIEL = os.path.join(WURZEL, "app", "public", "szene.glb")
BODEN_PNG = os.path.join(WURZEL, "blender", "gen_boden.png")


def pos(x, y, z):
    return (x, -z, y)


def schreibe_noise_png(pfad, groesse=256, basis=(178, 180, 182), spann=10):
    """Weiche Betonflecken als Value-Noise-PNG — nur Standardbibliothek."""
    random.seed(7)
    g = 9
    knoten = [[random.random() for _ in range(g)] for _ in range(g)]

    def wert(u, v):
        x = u * (g - 1)
        y = v * (g - 1)
        x0, y0 = int(x), int(y)
        fx, fy = x - x0, y - y0
        x1, y1 = min(x0 + 1, g - 1), min(y0 + 1, g - 1)
        a = knoten[y0][x0] * (1 - fx) + knoten[y0][x1] * fx
        b = knoten[y1][x0] * (1 - fx) + knoten[y1][x1] * fx
        return a * (1 - fy) + b * fy

    zeilen = b""
    for j in range(groesse):
        zeile = b"\x00"
        for i in range(groesse):
            f = int((wert(i / groesse, j / groesse) - 0.5) * 2 * spann)
            zeile += bytes(max(0, min(255, c + f)) for c in basis)
        zeilen += zeile

    def chunk(typ, daten):
        return (struct.pack(">I", len(daten)) + typ + daten
                + struct.pack(">I", zlib.crc32(typ + daten) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", groesse, groesse, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(zeilen))
    png += chunk(b"IEND", b"")
    with open(pfad, "wb") as f:
        f.write(png)


def material(name, farbe, rauheit=0.85):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*farbe, 1.0)
    bsdf.inputs["Roughness"].default_value = rauheit
    return mat


def material_mit_textur(name, pfad, rauheit=0.9):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rauheit
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(pfad)
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _abschliessen(obj, mat, fase):
    """Skalierung einbrennen (gleichmaessige Fase) und Bevel-Modifier anlegen."""
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if fase > 0:
        mod = obj.modifiers.new("Fase", "BEVEL")
        mod.width = fase
        mod.segments = 1
        mod.limit_method = "NONE"
    obj.data.materials.append(mat)
    return obj


def kasten(name, dx, dz, dy, x, y, z, mat, drehung=None, fase=0.02):
    """Quader in Three.js-Achsen: Groesse (dx, dz, dy), Mittelpunkt (x, y, z)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos(x, y, z))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (dx, dz, dy)
    if drehung:
        obj.rotation_euler = drehung
    return _abschliessen(obj, mat, fase)


def zylinder(name, radius, laenge, x, y, z, mat, achse="y", ecken=16, fase=0.0):
    """Zylinder; achse in Three.js: 'x' laengs, 'y' senkrecht, 'z' quer."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=ecken, radius=radius, depth=laenge,
                                        location=pos(x, y, z))
    obj = bpy.context.active_object
    obj.name = name
    if achse == "x":
        obj.rotation_euler = (0, 1.5708, 0)
    elif achse == "z":
        obj.rotation_euler = (1.5708, 0, 0)
    return _abschliessen(obj, mat, fase)


def kugel(name, radius, x, y, z, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=radius,
                                         location=pos(x, y, z))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def kegel(name, radius, hoehe, x, y, z, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=radius, radius2=0.05,
                                    depth=hoehe, location=pos(x, y, z))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def i_traeger(name, laenge, hoehe, breite, x, y, z, mat, achse="x"):
    """I-Profil aus drei Kaesten: Ober-/Untergurt + Steg."""
    steg = 0.06
    gurt = 0.07
    if achse == "x":
        kasten(f"{name}_obergurt", laenge, breite, gurt, x, y + hoehe / 2 - gurt / 2, z, mat)
        kasten(f"{name}_untergurt", laenge, breite, gurt, x, y - hoehe / 2 + gurt / 2, z, mat)
        kasten(f"{name}_steg", laenge, steg, hoehe - 2 * gurt, x, y, z, mat)
    else:  # quer (z-Richtung)
        kasten(f"{name}_obergurt", breite, laenge, gurt, x, y + hoehe / 2 - gurt / 2, z, mat)
        kasten(f"{name}_untergurt", breite, laenge, gurt, x, y - hoehe / 2 + gurt / 2, z, mat)
        kasten(f"{name}_steg", steg, laenge, hoehe - 2 * gurt, x, y, z, mat)


ASSETS = os.path.join(WURZEL, "blender", "assets", "kenney")


def lade_asset(datei, name, x, y, z, dreh_y=0.0, ziel_hoehe=None, ziel_breite=None):
    """Importiert ein CC0-Kenney-GLB und haengt es unter ein Anker-Empty.

    Die Hierarchie bleibt erhalten (geriggte Modelle wie der Roboterarm kollabieren
    beim Joinen). Kenney-Ursprung liegt an der Standflaeche — y ist die Bodenhoehe.
    ziel_hoehe/ziel_breite skalieren das Modell auf ein Wunschmass in Metern."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, datei))
    neu = list(bpy.context.selected_objects)
    meshes = [o for o in neu if o.type == "MESH"]
    if not meshes:
        return None
    wurzeln = [o for o in neu if o.parent is None or o.parent not in neu]
    # Gesamtmass ueber die Welt-Boundingboxen aller Meshes
    ecken = [o.matrix_world @ Vector(e) for o in meshes for e in o.bound_box]
    dx = max(e.x for e in ecken) - min(e.x for e in ecken)
    dy = max(e.y for e in ecken) - min(e.y for e in ecken)
    dz = max(e.z for e in ecken) - min(e.z for e in ecken)
    faktor = 1.0
    if ziel_hoehe and dz > 0:
        faktor = ziel_hoehe / dz
    elif ziel_breite and max(dx, dy) > 0:
        faktor = ziel_breite / max(dx, dy)
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    anker = bpy.context.active_object
    anker.name = name
    for w in wurzeln:
        w.parent = anker  # Anker steht in der Welt-Null — Welttransform bleibt erhalten
    anker.scale = (faktor, faktor, faktor)
    anker.rotation_euler = (0, 0, dreh_y)
    anker.location = pos(x, y, z)
    return anker


def rohr_mit_bogen(name, punkte, radius, mat):
    """Rohrzug aus Zylindersegmenten zwischen Punkten (beliebige Richtungen),
    Kugelgelenke an den Knicken. Punkte in Three.js-Koordinaten."""
    for i in range(len(punkte) - 1):
        a = Vector(pos(*punkte[i]))
        b = Vector(pos(*punkte[i + 1]))
        richtung = b - a
        mitte = (a + b) / 2
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=radius,
                                            depth=richtung.length, location=mitte)
        obj = bpy.context.active_object
        obj.name = f"{name}_seg_{i}"
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = richtung.to_track_quat("Z", "Y")
        obj.data.materials.append(mat)
        if i < len(punkte) - 2:
            kugel(f"{name}_bogen_{i}", radius * 1.25, *punkte[i + 1], mat)


# ---- Szene leeren -----------------------------------------------------------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# Iso-Referenz-Palette: helle Halle, satte Blau-/Orange-Akzente, Rot nur am Zug.
GRAU_GLEISZONE = (0.48, 0.50, 0.52)
GRAU_WAND = (0.80, 0.79, 0.76)
GRAU_OBJEKT = (0.64, 0.65, 0.66)
GRAU_DUNKEL = (0.29, 0.30, 0.32)
STAHL = (0.55, 0.57, 0.60)
FENSTER = (0.87, 0.91, 0.96)
BLAU = (0.30, 0.47, 0.75)
ORANGE = (0.92, 0.48, 0.10)
MARKIERUNG = (0.90, 0.76, 0.16)
STAHL_HELL = (0.85, 0.86, 0.88)
GRUEN = (0.30, 0.55, 0.32)
GRUBE = (0.16, 0.17, 0.18)
ROT_ZUG = (0.72, 0.12, 0.16)
WEISS_ZUG = (0.90, 0.90, 0.91)
WAND_RELIEF = (0.70, 0.69, 0.66)
DECKE = (0.84, 0.83, 0.81)

m_gleiszone = material("Gleiszone", GRAU_GLEISZONE)
m_wand = material("Wand", GRAU_WAND)
m_objekt = material("Objekt", GRAU_OBJEKT)
m_dunkel = material("Dunkel", GRAU_DUNKEL)
m_stahl = material("Stahl", STAHL)
m_fenster = material("Fenster", FENSTER, rauheit=0.3)
m_blau = material("Blau", BLAU)
m_orange = material("Orange", ORANGE)
m_markierung = material("Markierung", MARKIERUNG)
m_stahlhell = material("StahlHell", STAHL_HELL, rauheit=0.6)
m_gruen = material("Gruen", GRUEN)
m_grube = material("Grube", GRUBE)
m_zug = material("Zug", ROT_ZUG)
m_zugweiss = material("ZugWeiss", WEISS_ZUG, rauheit=0.5)
m_relief = material("WandRelief", WAND_RELIEF)
m_decke = material("Decke", DECKE)

schreibe_noise_png(BODEN_PNG)
m_boden = material_mit_textur("Boden", BODEN_PNG)

# ---- Halle: Boden, Gleiszone, Markierungen ----------------------------------
kasten("Halle_Boden", 34, 20, 0.2, 0, -0.1, 0, m_boden, fase=0)
kasten("Halle_Gleiszone", 34, 3.6, 0.04, 0, 0.02, 0, m_gleiszone, fase=0)
kasten("Halle_Markierung_Nord", 30, 0.12, 0.02, 0, 0.045, -1.9, m_markierung, fase=0)
kasten("Halle_Markierung_Sued", 30, 0.12, 0.02, 0, 0.045, 1.9, m_markierung, fase=0)
kasten("Halle_Weg_Nord", 34, 1.6, 0.03, 0, 0.02, -8.9, m_wand, fase=0)
for i, fx in enumerate((-8.5, 0, 8.5)):
    kasten(f"Bodenfuge_{i}", 0.06, 19.4, 0.015, fx, 0.012, 0, m_gleiszone, fase=0)
kasten("Bodenfuge_Laengs", 33.4, 0.06, 0.015, 0, 0.012, -6.5, m_gleiszone, fase=0)

# ---- Waende mit Fensterbaendern (Nord, West, Sued), Ostwand mit Tor ---------
def wand_mit_fenster(seite, laenge, cx, cz, entlang_x):
    if entlang_x:
        kasten(f"Wand_{seite}_Unten", laenge, 0.3, 3.5, cx, 1.75, cz, m_wand)
        kasten(f"Wand_{seite}_Fenster", laenge, 0.1, 1.8, cx, 4.4, cz + (0.08 if cz > 0 else -0.08), m_fenster)
        kasten(f"Wand_{seite}_Oben", laenge, 0.3, 0.7, cx, 5.65, cz, m_wand)
        for i, fx in enumerate(range(-16, 17, 4)):
            kasten(f"Wand_{seite}_Sprosse_{i}", 0.15, 0.3, 1.8, fx, 4.4, cz, m_stahl)
        kasten(f"Wand_{seite}_Quersprosse", laenge, 0.24, 0.08, cx, 4.4, cz, m_stahl)
        kasten(f"Relief_{seite}_Sockel", laenge, 0.08, 0.4, cx, 0.2, cz + (-0.2 if cz > 0 else 0.2), m_relief)
        kasten(f"Relief_{seite}_Traeger", laenge, 0.26, 0.55, cx, 3.55, cz + (-0.25 if cz > 0 else 0.25), m_relief)
        for i, px in enumerate(range(-15, 16, 3)):
            kasten(f"Relief_{seite}_Pilaster_{i}", 0.28, 0.14, 3.3, px, 1.75, cz + (-0.2 if cz > 0 else 0.2), m_relief)
    else:
        kasten(f"Wand_{seite}_Unten", 0.3, laenge, 3.5, cx, 1.75, cz, m_wand)
        kasten(f"Wand_{seite}_Fenster", 0.1, laenge, 1.8, cx - 0.08, 4.4, cz, m_fenster)
        kasten(f"Wand_{seite}_Oben", 0.3, laenge, 0.7, cx, 5.65, cz, m_wand)
        for i, fz in enumerate(range(-8, 9, 4)):
            kasten(f"Wand_{seite}_Sprosse_{i}", 0.3, 0.15, 1.8, cx, 4.4, fz, m_stahl)
        kasten(f"Wand_{seite}_Quersprosse", 0.24, laenge, 0.08, cx, 4.4, cz, m_stahl)
        kasten(f"Relief_{seite}_Sockel", 0.08, laenge, 0.4, cx + 0.2, 0.2, cz, m_relief)
        kasten(f"Relief_{seite}_Traeger", 0.26, laenge, 0.55, cx + 0.25, 3.55, cz, m_relief)
        for i, pz in enumerate(range(-8, 9, 4)):
            kasten(f"Relief_{seite}_Pilaster_{i}", 0.14, 0.28, 3.3, cx + 0.2, 1.75, pz, m_relief)


wand_mit_fenster("Nord", 34, 0, -10, True)
wand_mit_fenster("Sued", 34, 0, 10, True)
wand_mit_fenster("West", 20, -17, 0, False)

kasten("Wand_Ost_Nord", 0.3, 8.2, 6, 17, 3, -5.9, m_wand)
kasten("Wand_Ost_Sued", 0.3, 8.2, 6, 17, 3, 5.9, m_wand)
kasten("Wand_Ost_Sturz", 0.3, 3.6, 1.8, 17, 5.1, 0, m_wand)
kasten("Relief_Ost_Sockel_Nord", 0.08, 8.2, 0.4, 16.8, 0.2, -5.9, m_relief)
kasten("Relief_Ost_Sockel_Sued", 0.08, 8.2, 0.4, 16.8, 0.2, 5.9, m_relief)
kasten("Relief_Ost_Traeger_Nord", 0.26, 8.2, 0.55, 16.75, 3.55, -5.9, m_relief)
kasten("Relief_Ost_Traeger_Sued", 0.26, 8.2, 0.55, 16.75, 3.55, 5.9, m_relief)
kasten("Tor_Pfosten_Nord", 0.25, 0.25, 4.4, 16.8, 2.2, -1.9, m_orange)
kasten("Tor_Pfosten_Sued", 0.25, 0.25, 4.4, 16.8, 2.2, 1.9, m_orange)
kasten("Tor_Balken", 0.25, 4.3, 0.25, 16.8, 4.35, 0, m_orange)

# ---- Stahlbau: Stuetzen (I-Profil-Optik), Decke mit Bindern und Oberlichtern ----
for i, sx in enumerate((-13.6, -6.8, 0, 6.8, 13.6)):
    kasten(f"Stuetze_Nord_{i}", 0.3, 0.3, 6, sx, 3, -9.7, m_stahl)
    kasten(f"Stuetze_Sued_{i}", 0.3, 0.3, 6, sx, 3, 9.7, m_stahl)
for i, sz in enumerate((-6.7, 0, 6.7)):
    kasten(f"Stuetze_West_{i}", 0.3, 0.3, 6, -16.7, 3, sz, m_stahl)

kasten("Dach_Decke", 34, 20, 0.12, 0, 6.3, 0, m_decke, fase=0)
for i, tx in enumerate((-12, -6, 0, 6, 12)):
    i_traeger(f"Dachbinder_{i}", 19.4, 0.5, 0.24, tx, 5.85, 0, m_stahlhell, achse="z")
for i in range(11):
    kasten(f"Dach_Rippe_{i}", 34, 0.1, 0.2, 0, 6.14, -9 + i * 1.8, m_relief, fase=0)
for i, (ox, oz) in enumerate(((-12, -4.6), (-4, -4.6), (4, -4.6), (12, -4.6),
                              (-12, 4.4), (-4, 4.4), (4, 4.4), (12, 4.4))):
    kasten(f"Dach_Oberlicht_{i}", 2.4, 1.5, 0.06, ox, 6.2, oz, m_fenster, fase=0)
    kasten(f"Dach_Oberlicht_{i}_rahmen", 2.6, 1.7, 0.05, ox, 6.25, oz, m_relief, fase=0)

# ---- Haustechnik unter der Decke: Rohre, Kabeltrasse, Sprinkler, Lueftung ---
zylinder("Rohr_Blau", 0.1, 33, 0, 5.15, -9.3, m_blau, achse="x")
zylinder("Rohr_Grau", 0.09, 33, 0, 4.85, -9.0, m_stahlhell, achse="x")
zylinder("Rohr_Orange", 0.07, 33, 0, 4.6, -9.15, m_orange, achse="x")
for i, hx in enumerate((-14, -7, 0, 7, 14)):
    kasten(f"Rohr_Halter_{i}", 0.06, 0.5, 1.7, hx, 5.4, -9.15, m_stahl, fase=0)  # bis zur Decke
zylinder("Sprinkler_Leitung", 0.035, 30, 0, 6.0, 3.5, m_zug, achse="x")
for i in range(6):
    zylinder(f"Sprinkler_Kopf_{i}", 0.03, 0.12, -12.5 + i * 5, 5.93, 3.5, m_dunkel)
# Kabeltrasse als Gitterrinne an der Nordseite
kasten("Trasse_Schiene_1", 28, 0.05, 0.08, 0, 4.32, -8.2, m_stahl, fase=0)
kasten("Trasse_Schiene_2", 28, 0.05, 0.08, 0, 4.32, -7.8, m_stahl, fase=0)
for i in range(15):
    kasten(f"Trasse_Steg_{i}", 0.05, 0.45, 0.06, -13.5 + i * 1.95, 4.3, -8.0, m_stahl, fase=0)
# Lueftungskanal mit S-Schwung und Flanschen
kasten("Lueftung_Fall_Oben", 0.55, 0.55, 1.4, -1.5, 5.5, -7.2, m_stahlhell)
kasten("Lueftung_Flansch_1", 0.62, 0.62, 0.08, -1.5, 4.82, -7.2, m_stahl, fase=0)
kasten("Lueftung_Schwung", 0.5, 0.5, 1.3, -1.5, 4.35, -6.8, m_stahlhell, drehung=(0.6, 0, 0))
kasten("Lueftung_Flansch_2", 0.58, 0.58, 0.08, -1.5, 3.85, -6.5, m_stahl, fase=0)
kasten("Lueftung_Fall_Unten", 0.5, 0.5, 1.2, -1.5, 3.3, -6.45, m_stahlhell)
kasten("Lueftung_Auslass", 0.78, 0.78, 0.25, -1.5, 2.6, -6.45, m_stahl)
# Rohrlaeufe mit Boegen an Nord- und Ostwand
rohr_mit_bogen("Rohrlauf_Nord", [(-16, 0.6, -9.7), (-16, 3.0, -9.7), (-6, 3.0, -9.7), (-6, 0.6, -9.7)], 0.07, m_stahlhell)
rohr_mit_bogen("Rohrlauf_Ost", [(16.7, 0.6, -8.4), (16.7, 2.6, -8.4), (16.7, 2.6, -3.4), (16.7, 0.6, -3.4)], 0.06, m_stahlhell)
# Kegel-Haengelampen
for i, (lx, lz) in enumerate(((-12, 0), (-6, 0), (0, 0), (6, 0), (12, 0),
                              (-9, -6.5), (-1, -6.5), (7, -6.5),
                              (-8, 5.2), (1, 5.2), (10, 5.2))):
    kegel(f"Lampe_{i}_schirm", 0.38, 0.45, lx, 4.85, lz, m_stahlhell)
    zylinder(f"Lampe_{i}_glut", 0.16, 0.06, lx, 4.62, lz, m_fenster)
    zylinder(f"Lampe_{i}_seil", 0.015, 1.2, lx, 5.65, lz, m_dunkel)

# ---- Empore an der Westwand mit Treppe --------------------------------------
kasten("Empore_Plattform", 3.0, 10, 0.15, -15.5, 3.05, -5, m_objekt)
kasten("Empore_Blende", 0.06, 10, 0.22, -14.02, 3.05, -5, m_relief, fase=0)
for i, ez in enumerate((-9.5, -6.5, -3.5, -0.6)):
    kasten(f"Empore_Stuetze_{i}", 0.2, 0.2, 3.0, -14.2, 1.5, ez, m_stahl)
for i, gz in enumerate((-9.5, -7.2, -4.9, -2.6, -0.4)):
    zylinder(f"Empore_Gelaenderpfosten_{i}", 0.03, 1.0, -14.1, 3.6, gz, m_dunkel)
zylinder("Empore_Handlauf", 0.035, 9.6, -14.1, 4.1, -5, m_dunkel, achse="z")
def treppe(name, x, z, hoehe, richtung_z=1, breite=1.0, mat=None):
    """Gerade Blocktreppe mit Gelaender; steigt von +z nach -z (richtung_z=1) an."""
    mat = mat or m_stahl
    stufen = max(4, int(hoehe / 0.35))
    lauf = hoehe * 1.35
    for i in range(stufen):
        sh = hoehe * (i + 1) / stufen
        sz = z + richtung_z * (lauf / 2 - lauf * (i + 0.5) / stufen)
        kasten(f"{name}_stufe_{i}", breite, lauf / stufen + 0.02, sh, x, sh / 2, sz, mat, fase=0)
    for seite in (-1, 1):
        gx = x + seite * (breite / 2 + 0.03)
        zylinder(f"{name}_handlauf_{'w' if seite < 0 else 'o'}", 0.03,
                 (lauf ** 2 + hoehe ** 2) ** 0.5, gx, hoehe / 2 + 0.9, z, m_markierung)
        h = bpy.context.active_object
        h.rotation_mode = "QUATERNION"
        h.rotation_quaternion = Vector((0, richtung_z * lauf, hoehe)).to_track_quat("Z", "Y")


treppe("Empore_Treppe", -15.5, 1.4, 3.05, richtung_z=1)
kasten("Empore_Kiste_1", 0.6, 0.55, 0.5, -15.9, 3.4, -8.4, m_blau)
kasten("Empore_Kiste_2", 0.45, 0.4, 0.4, -15.3, 3.33, -7.9, m_orange)

# ---- Gleis + Untersuchungsgrube ---------------------------------------------
kasten("Gleis_Schiene_Nord", 38, 0.15, 0.15, 2, 0.08, -0.7, m_dunkel, fase=0)
kasten("Gleis_Schiene_Sued", 38, 0.15, 0.15, 2, 0.08, 0.7, m_dunkel, fase=0)
for i in range(16):
    sx = -14.5 + i * 2.4
    if -15.5 < sx < -8.5:
        continue
    kasten(f"Gleis_Schwelle_{i}", 0.22, 1.8, 0.06, sx, 0.03, 0, m_dunkel, fase=0)

kasten("Grube_Boden", 7, 2.0, 0.03, -12, 0.045, 0, m_grube, fase=0)
kasten("Grube_Absatz_Nord", 7, 0.18, 0.05, -12, 0.07, -0.92, m_dunkel, fase=0)
kasten("Grube_Absatz_Sued", 7, 0.18, 0.05, -12, 0.07, 0.92, m_dunkel, fase=0)
kasten("Grube_Quersteg_1", 0.4, 1.9, 0.04, -13.8, 0.075, 0, m_stahl, fase=0)
kasten("Grube_Quersteg_2", 0.4, 1.9, 0.04, -10.3, 0.075, 0, m_stahl, fase=0)
kasten("Grube_Leuchte_Nord", 5.5, 0.06, 0.06, -12, 0.05, -0.9, m_fenster, fase=0)
kasten("Grube_Leuchte_Sued", 5.5, 0.06, 0.06, -12, 0.05, 0.9, m_fenster, fase=0)
kasten("Grube_Leiter", 0.4, 0.08, 0.9, -8.7, 0.45, 0.7, m_orange)


def warnstreifen(name, laenge, x, z, entlang_x=True):
    n = int(laenge / 0.5)
    for i in range(n):
        m = m_markierung if i % 2 == 0 else m_dunkel
        if entlang_x:
            kasten(f"{name}_{i}", 0.5, 0.14, 0.012, x - laenge / 2 + 0.25 + i * 0.5, 0.04, z, m, fase=0)
        else:
            kasten(f"{name}_{i}", 0.14, 0.5, 0.012, x, 0.04, z - laenge / 2 + 0.25 + i * 0.5, m, fase=0)


warnstreifen("Grube_Kante_Nord", 7, -12, -1.12)
warnstreifen("Grube_Kante_Sued", 7, -12, 1.12)
warnstreifen("Grube_Kante_West", 2, -15.55, 0, entlang_x=False)
warnstreifen("Grube_Kante_Ost", 2, -8.45, 0, entlang_x=False)

# ---- Triebzug v2: Fenster, Tueren, Radsaetze, Details -----------------------
ZUG_X = 0.5
kasten("Triebzug_Unterbau", 14, 2.2, 0.5, ZUG_X, 0.5, 0, m_dunkel)
for i, bx in enumerate((-4.5, 5.5)):
    kasten(f"Triebzug_Drehgestell_{i}", 2.0, 1.9, 0.4, bx, 0.3, 0, m_dunkel)
    for j, rx in enumerate((-0.7, 0.7)):
        zylinder(f"Triebzug_Rad_{i}_{j}_nord", 0.38, 0.12, bx + rx, 0.38, -0.85, m_stahl, achse="z")
        zylinder(f"Triebzug_Rad_{i}_{j}_sued", 0.38, 0.12, bx + rx, 0.38, 0.85, m_stahl, achse="z")
kasten("Triebzug_Korpus", 14, 2.4, 1.5, ZUG_X, 1.5, 0, m_zugweiss, fase=0.06)
kasten("Triebzug_Streifen_Nord", 14, 0.06, 0.35, ZUG_X, 1.08, -1.23, m_zug, fase=0)
kasten("Triebzug_Streifen_Sued", 14, 0.06, 0.35, ZUG_X, 1.08, 1.23, m_zug, fase=0)
for seite, sz in (("nord", -1.24), ("sued", 1.24)):
    for i, fx in enumerate((-5.2, -3.9, -1.2, 0.1, 2.8, 4.1, 6.2)):
        kasten(f"Triebzug_Fenster_{seite}_{i}", 0.85, 0.06, 0.6, fx, 1.85, sz, m_dunkel, fase=0)
    for i, tx in enumerate((-2.55, 5.15)):
        kasten(f"Triebzug_Tuer_{seite}_{i}", 0.95, 0.08, 1.35, tx, 1.4, sz, m_stahl, fase=0)
        kasten(f"Triebzug_Tuerfenster_{seite}_{i}", 0.6, 0.1, 0.45, tx, 1.85, sz, m_dunkel, fase=0)
kasten("Triebzug_Dach", 13.6, 2.2, 0.3, ZUG_X, 2.4, 0, m_stahl)
zylinder("Triebzug_Dachleitung", 0.05, 12.5, 0, 2.62, -0.8, m_dunkel, achse="x")
for i, kx in enumerate((-4, 0.5, 5)):
    kasten(f"Triebzug_Klima_{i}", 1.4, 1.4, 0.25, kx, 2.65, 0, m_dunkel)
kasten("Triebzug_Panto_Basis", 0.8, 1.0, 0.1, -2, 2.83, 0, m_dunkel, fase=0)
kasten("Triebzug_Panto_Arm", 0.08, 0.08, 0.9, -2, 3.25, 0, m_dunkel, drehung=(0.5, 0, 0), fase=0)
kasten("Triebzug_Panto_Buegel", 0.06, 1.3, 0.05, -2, 3.65, 0.2, m_dunkel, fase=0)
kasten("Triebzug_Front", 1.2, 2.2, 1.4, 8.1, 1.45, 0, m_zugweiss, fase=0.08)
kasten("Triebzug_Front_Streifen", 1.26, 2.1, 0.3, 8.1, 1.0, 0, m_zug, fase=0)
kasten("Triebzug_Windschutz", 0.5, 1.6, 0.7, 8.5, 1.95, 0, m_dunkel, drehung=(0, -0.35, 0), fase=0)
for i, lz in enumerate((-0.7, 0.7)):
    zylinder(f"Triebzug_Scheinwerfer_{i}", 0.09, 0.06, 8.72, 1.05, lz, m_fenster, achse="x")
kasten("Triebzug_Kupplung", 0.5, 0.25, 0.25, 8.85, 0.55, 0, m_dunkel)
kasten("Triebzug_Schuerze", 1.1, 1.9, 0.35, 8.15, 0.45, 0, m_dunkel, fase=0)

# ---- Dacharbeitsbuehnen, Kranbahn, Rollgerueste -----------------------------
for i, bx in enumerate((-6.5, -3, 0.5, 4)):
    for j, bz in enumerate((-2.7, 2.7)):
        kasten(f"Buehne_Stuetze_{i}_{j}", 0.18, 0.18, 3.2, bx, 1.6, bz, m_stahlhell)
        kasten(f"Buehne_Stuetze_{i}_{j}_fuss", 0.26, 0.26, 0.18, bx, 0.09, bz, m_markierung, fase=0)
kasten("Buehne_Plattform_Nord", 11.5, 0.85, 0.1, -1.25, 3.25, -2.7, m_stahlhell)
kasten("Buehne_Plattform_Sued", 11.5, 0.85, 0.1, -1.25, 3.25, 2.7, m_stahlhell)
kasten("Buehne_Fussleiste_Nord", 11.5, 0.05, 0.12, -1.25, 3.36, -3.1, m_markierung, fase=0)
kasten("Buehne_Fussleiste_Sued", 11.5, 0.05, 0.12, -1.25, 3.36, 3.1, m_markierung, fase=0)
for j, bz in enumerate((-3.08, 3.08)):
    zylinder(f"Buehne_Handlauf_{j}", 0.035, 11.5, -1.25, 4.25, bz, m_stahlhell, achse="x")
    for i, px in enumerate((-6.5, -3.75, -1, 1.75, 4)):
        zylinder(f"Buehne_Gelaenderpfosten_{j}_{i}", 0.025, 0.95, px, 3.78, bz, m_stahlhell)
for i, tx in enumerate((-6.5, 4)):
    kasten(f"Buehne_Quertraeger_{i}", 0.16, 5.4, 0.2, tx, 3.9, 0, m_stahlhell)
treppe("Buehne_Treppe", -7.6, 4.6, 3.3, richtung_z=1, breite=0.85, mat=m_stahlhell)

i_traeger("Kran_Traeger", 15, 0.4, 0.3, 0.5, 5.4, 0, m_stahlhell, achse="x")
for i, kx in enumerate((-2.5, 4)):
    kasten(f"Kran_Laufkatze_{i}", 0.55, 0.6, 0.4, kx, 5.0, 0, m_markierung)
    zylinder(f"Kran_Seil_{i}", 0.02, 0.5, kx, 4.6, 0, m_dunkel)
    kasten(f"Kran_Haken_{i}", 0.1, 0.05, 0.15, kx, 4.3, 0, m_dunkel, fase=0)


def rollgeruest(name, x, z):
    for i, (gx, gz) in enumerate(((-0.55, -0.35), (0.55, -0.35), (-0.55, 0.35), (0.55, 0.35))):
        zylinder(f"{name}_holm_{i}", 0.035, 2.6, x + gx, 1.3, z + gz, m_stahlhell)
        zylinder(f"{name}_rolle_{i}", 0.09, 0.06, x + gx, 0.07, z + gz, m_dunkel, achse="z")
    kasten(f"{name}_buehne_1", 1.25, 0.8, 0.06, x, 1.25, z, m_stahlhell)
    kasten(f"{name}_buehne_2", 1.25, 0.8, 0.06, x, 2.35, z, m_stahlhell)
    zylinder(f"{name}_handlauf", 0.03, 1.25, x, 2.95, z + 0.38, m_markierung, achse="x")
    kasten(f"{name}_diagonale", 0.05, 0.05, 1.5, x, 1.8, z - 0.38, m_stahlhell, drehung=(0, 0.6, 0), fase=0)


rollgeruest("Rollgeruest_1", 4.2, -2.2)
rollgeruest("Rollgeruest_2", -4.2, 2.2)

# ---- Fahrzeuge und Geraete ---------------------------------------------------
kasten("Servicewagen_Korpus", 1.3, 0.85, 1.0, 10.5, 0.62, 2.9, m_zugweiss)
zylinder("Servicewagen_Tank_1", 0.18, 0.5, 10.2, 1.35, 2.75, m_blau)
zylinder("Servicewagen_Tank_2", 0.18, 0.5, 10.8, 1.35, 2.75, m_blau)
rohr_mit_bogen("Servicewagen_Schlauch", [(10.0, 0.9, 2.5), (9.2, 0.5, 2.0), (8.5, 0.25, 1.5)], 0.05, m_dunkel)
for i, (rx, rz) in enumerate(((-0.5, -0.3), (0.5, -0.3), (-0.5, 0.3), (0.5, 0.3))):
    zylinder(f"Servicewagen_rad_{i}", 0.09, 0.07, 10.5 + rx, 0.09, 2.9 + rz, m_dunkel, achse="z")
kasten("Werkstattwagen_Korpus", 1.0, 0.65, 0.9, 12.5, 0.55, -3.5, m_zug)
kasten("Werkstattwagen_Griff", 0.06, 0.55, 0.6, 13.05, 0.9, -3.5, m_dunkel, fase=0)
for i, (rx, rz) in enumerate(((-0.38, -0.24), (0.38, -0.24), (-0.38, 0.24), (0.38, 0.24))):
    zylinder(f"Werkstattwagen_rad_{i}", 0.08, 0.06, 12.5 + rx, 0.08, -3.5 + rz, m_dunkel, achse="z")
kasten("Werkbank2", 2.0, 0.7, 0.85, 2.5, 0.43, -9.4, m_stahl)
kasten("Werkbank2_Platte", 2.0, 0.75, 0.08, 2.5, 0.9, -9.4, m_dunkel)
kasten("Werkbank2_Schraubstock", 0.25, 0.3, 0.25, 3.2, 1.06, -9.35, m_dunkel)
kasten("Werkbank2_Werkzeugkasten", 0.5, 0.3, 0.3, 2.0, 1.09, -9.4, m_zug)
kasten("Oel_Wanne", 1.7, 1.3, 0.15, 11.5, 0.08, -8.7, m_markierung)
for i, (fx, fz, fm) in enumerate(((11.2, -8.9, m_dunkel), (11.8, -8.9, m_blau),
                                  (11.2, -8.4, m_orange), (11.8, -8.4, m_dunkel))):
    zylinder(f"Oel_Fass_{i}", 0.23, 0.62, fx, 0.46, fz, fm)
    zylinder(f"Oel_Fass_{i}_ring", 0.24, 0.04, fx, 0.56, fz, m_stahl)
kasten("Kabel_Trommel", 0.5, 0.5, 0.5, 0.2, 0.25, -8.3, m_blau)
zylinder("Kabel_Trommel_Kern", 0.12, 0.56, 0.2, 0.25, -8.3, m_dunkel, achse="z")

# ---- Bodenmarkierungen, Signale, Sicherheit ---------------------------------
# Markierte Zone als Kenney-Bodendekal (liest sich eindeutig als Markierung)
lade_asset("factory_indicator-special-lines.glb", "Schraffur_Dekal_1", 3.6, 0.03, 3.4, ziel_breite=2.3)
lade_asset("factory_indicator-special-lines.glb", "Schraffur_Dekal_2", 6.0, 0.03, 3.4, ziel_breite=2.3)
for i, (ax, az) in enumerate(((-10, 2.4), (-3, 2.4), (4, 2.4), (11, 2.4))):
    zylinder(f"Absperrpfosten_{i}", 0.07, 0.9, ax, 0.45, az, m_orange)
    zylinder(f"Absperrpfosten_{i}_ring", 0.075, 0.08, ax, 0.75, az, m_stahlhell)
zylinder("Muelleimer_1", 0.22, 0.7, -6.6, 0.35, -4.0, m_orange)
zylinder("Muelleimer_2", 0.22, 0.7, 5.2, 0.35, 4.4, m_orange)
# Warnaufsteller stehen am Boden vor der Wand (die Modelle haben eigene Fuesse)
lade_asset("factory_warning-orange.glb", "Warntafel_0", -8, 0, -9.45, ziel_hoehe=0.85)
lade_asset("factory_warning-traffic.glb", "Warntafel_1", 0.8, 0, -9.45, ziel_hoehe=0.85)
lade_asset("factory_warning-orange.glb", "Warntafel_2", 8.2, 0, -9.45, ziel_hoehe=0.85)
for i, (sx, sz) in enumerate(((-8, 1.6), (1, -1.6), (9, 1.6))):
    zylinder(f"Signal_{i}_mast", 0.04, 1.0, sx, 0.5, sz, m_dunkel)
    kasten(f"Signal_{i}_rot", 0.13, 0.13, 0.13, sx, 1.06, sz, m_zug, fase=0)
    kasten(f"Signal_{i}_gelb", 0.13, 0.13, 0.13, sx, 1.19, sz, m_markierung, fase=0)
    kasten(f"Signal_{i}_gruen", 0.13, 0.13, 0.13, sx, 1.32, sz, m_gruen, fase=0)
kasten("Rettungszeichen_Tor", 0.5, 0.05, 0.3, 15.8, 3.0, -1.6, m_gruen, fase=0)
kasten("Rettungszeichen_West", 0.05, 0.5, 0.3, -16.8, 3.0, -4, m_gruen, fase=0)
kasten("Konsole_1", 0.9, 0.35, 0.06, -13.5, 2.2, -9.7, m_stahlhell, fase=0)
kasten("Konsole_2", 0.9, 0.35, 0.06, 9.5, 2.4, -9.7, m_stahlhell, fase=0)

# ---- Station 1: Meisterbuero -------------------------------------------------
kasten("Station_1_meisterbuero", 4, 3, 2.6, -10.5, 1.3, -7.5, m_wand)
kasten("Station_1_buerodach", 4.3, 3.3, 0.1, -10.5, 2.65, -7.5, m_dunkel)
kasten("Station_1_buerofenster", 2.6, 0.06, 0.9, -10.5, 1.9, -5.95, m_fenster, fase=0)
kasten("Station_1_buerotuer", 0.8, 0.06, 1.9, -8.9, 0.95, -5.95, m_dunkel, fase=0)
kasten("Station_1_pinnwand", 2.4, 0.08, 1.3, -10, 1.8, -5.2, m_objekt)
kasten("Station_1_pinnwand_pfosten_west", 0.1, 0.1, 2.3, -11.0, 1.15, -5.2, m_dunkel)
kasten("Station_1_pinnwand_pfosten_ost", 0.1, 0.1, 2.3, -9.0, 1.15, -5.2, m_dunkel)
for i in range(6):
    zx = -10.9 + (i % 3) * 0.9
    zy = 2.1 - (i // 3) * 0.55
    kasten(f"Station_1_zettel_{i}", 0.32, 0.03, 0.42, zx, zy, -5.14, m_fenster, fase=0)
    kasten(f"Station_1_zettel_{i}_zeile", 0.24, 0.035, 0.05, zx, zy + 0.1, -5.14, m_objekt, fase=0)
lade_asset("furniture_desk.glb", "Station_1_schreibtisch", -8.2, 0, -5.3, dreh_y=3.14159, ziel_breite=1.6)
lade_asset("furniture_chairDesk.glb", "Station_1_buerostuhl", -8.2, 0, -4.5, ziel_hoehe=0.95)
lade_asset("furniture_computerScreen.glb", "Station_1_monitor", -8.4, 0.76, -5.45, ziel_hoehe=0.45)
lade_asset("furniture_computerKeyboard.glb", "Station_1_tastatur", -8.0, 0.76, -5.2, ziel_breite=0.4)
lade_asset("furniture_bookcaseClosedWide.glb", "Station_1_aktenschrank", -12.2, 0, -5.6, ziel_hoehe=1.9)

# ---- Station 2: Datenraum-Regal ---------------------------------------------
kasten("Station_2_datenraum", 0.08, 1.0, 2.2, -4.2, 1.1, -6, m_blau)
kasten("Station_2_regalwange", 0.08, 1.0, 2.2, -1.8, 1.1, -6, m_blau)
kasten("Station_2_kopfblende", 2.56, 1.04, 0.1, -3, 2.25, -6, m_dunkel)
for i, by in enumerate((0.35, 0.95, 1.55, 2.15)):
    kasten(f"Station_2_regalbrett_{i}", 2.5, 1.0, 0.06, -3, by, -6, m_dunkel, fase=0)
ordner_farben = (m_blau, m_orange, m_objekt, m_blau, m_orange, m_objekt)
for i in range(6):
    kasten(f"Station_2_ordner_{i}", 0.2, 0.4, 0.5, -3.9 + i * 0.36, 1.85, -6, ordner_farben[i], fase=0)
for i in range(5):
    kasten(f"Station_2_kiste_{i}", 0.34, 0.5, 0.4, -3.8 + i * 0.42, 1.2, -6, m_wand, fase=0)
chaos = [(-4.1, -4.9, 0.5, 0.35, m_objekt), (-3.4, -5.2, 0.45, -0.5, m_wand),
         (-2.7, -4.7, 0.55, 0.9, m_objekt), (-2.1, -5.1, 0.4, -0.2, m_blau),
         (-3.0, -4.5, 0.35, 1.3, m_wand)]
for i, (cx, cz, cg, cr, cm) in enumerate(chaos):
    kasten(f"Station_2_chaos_{i}", cg, cg, cg, cx, cg / 2, cz, cm, drehung=(0, 0, cr))
zylinder("Station_2_fass_1", 0.21, 0.6, -1.4, 0.3, -5.0, m_dunkel)
zylinder("Station_2_fass_2", 0.21, 0.6, -1.0, 0.3, -5.5, m_blau)
kasten("Station_2_zettel_am_regal", 0.28, 0.03, 0.38, -4.24, 1.5, -5.45, m_fenster, fase=0)

# ---- Station 3: Bedienterminal ----------------------------------------------
kasten("Station_3_terminal_saeule", 0.5, 0.5, 1.2, 7, 0.6, -5, m_dunkel)
kasten("Station_3_terminal_gehaeuse", 1.8, 0.35, 1.05, 7, 1.5, -4.15, m_blau)
kasten("Station_3_terminal_pult", 1.4, 0.5, 0.1, 7, 0.95, -4.45, m_stahl)
kasten("Station_3_tastatur", 0.7, 0.28, 0.05, 7, 1.02, -4.45, m_dunkel, fase=0)
kasten("Station_3_bodenplatte", 2.2, 1.6, 0.03, 7, 0.02, -4.4, m_gleiszone, fase=0)
bpy.ops.mesh.primitive_plane_add(size=1, location=pos(7, 1.5, -3.95))
monitor = bpy.context.active_object
monitor.name = "Monitor_Bildschirm"
monitor.scale = (1.6, 0.9, 1)
monitor.rotation_euler = (1.5708, 0, 0)  # senkrecht, Front Richtung Sueden
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
monitor.data.materials.append(m_dunkel)

# ---- Station 4: Anzeigetafel ------------------------------------------------
kasten("Station_4_anzeigetafel", 3.2, 0.15, 1.8, 9, 2, 5.8, m_dunkel)
kasten("Station_4_rahmen_oben", 3.3, 0.18, 0.08, 9, 2.92, 5.8, m_stahlhell, fase=0)
kasten("Station_4_rahmen_unten", 3.3, 0.18, 0.08, 9, 1.08, 5.8, m_stahlhell, fase=0)
kasten("Station_4_rahmen_west", 0.08, 0.18, 1.92, 7.36, 2, 5.8, m_stahlhell, fase=0)
kasten("Station_4_rahmen_ost", 0.08, 0.18, 1.92, 10.64, 2, 5.8, m_stahlhell, fase=0)
for i in range(4):
    breite = 2.6 - (i % 2) * 0.5
    kasten(f"Station_4_zeile_{i}", breite, 0.04, 0.14, 8.8, 2.55 - i * 0.38, 5.71, m_stahl, fase=0)
kasten("Station_4_titelzeile", 1.8, 0.04, 0.2, 8.5, 2.62, 5.71, m_markierung, fase=0)
kasten("Station_4_pfosten_west", 0.15, 0.15, 2.9, 7.6, 1.45, 5.8, m_stahl)
kasten("Station_4_pfosten_ost", 0.15, 0.15, 2.9, 10.4, 1.45, 5.8, m_stahl)

# ---- Station 5: Pruefstand ---------------------------------------------------
kasten("Station_5_pruefstand", 2.8, 1.2, 0.5, 2, 0.25, 6, m_stahl)
kasten("Station_5_aufbau", 1.4, 0.9, 0.9, 1.6, 1.15, 6, m_blau)
zylinder("Station_5_rolle_1", 0.18, 1.0, 2.6, 0.7, 6, m_dunkel, achse="z")
zylinder("Station_5_rolle_2", 0.18, 1.0, 3.1, 0.7, 6, m_dunkel, achse="z")
kasten("Station_5_panel", 0.4, 0.05, 0.3, 1.3, 1.5, 5.5, m_fenster, fase=0)
lade_asset("factory_machine.glb", "Station_5_maschine", 3.9, 0, 4.9, dreh_y=2.9, ziel_hoehe=1.5)
kasten("Station_5_kabelkanal", 2.6, 0.18, 0.08, 2, 0.06, 5.3, m_dunkel, fase=0)

# ---- Station 6: Besprechung (Kenney-Moebel) ---------------------------------
lade_asset("furniture_table.glb", "Station_6_besprechung_tisch", -9, 0, 6, ziel_breite=2.2)
stuehle = [(-9.6, 5.1, 3.14159), (-8.4, 5.1, 3.14159), (-9.6, 6.9, 0), (-8.4, 6.9, 0)]
for i, (sx, sz, dreh) in enumerate(stuehle):
    lade_asset("furniture_chair.glb", f"Station_6_stuhl_{i}", sx, 0, sz, dreh_y=dreh, ziel_hoehe=0.95)
lade_asset("furniture_laptop.glb", "Station_6_laptop", -9.3, 0.75, 6, dreh_y=0.5, ziel_breite=0.45)
lade_asset("furniture_pottedPlant.glb", "Station_6_pflanze", -11.8, 0, 8.2, ziel_hoehe=1.1)
kasten("Station_6_sideboard", 1.6, 0.5, 0.8, -11.5, 0.4, 7, m_objekt)
kasten("Station_6_whiteboard", 1.6, 0.06, 1.0, -11.2, 1.7, 8.2, m_fenster)
kasten("Station_6_whiteboard_fuss_1", 0.08, 0.08, 1.2, -11.9, 0.6, 8.2, m_dunkel, fase=0)
kasten("Station_6_whiteboard_fuss_2", 0.08, 0.08, 1.2, -10.5, 0.6, 8.2, m_dunkel, fase=0)

# ---- Requisiten --------------------------------------------------------------
for i, (fx, fz, fm) in enumerate(((-15.6, -8.2, m_blau), (-15.0, -8.5, m_dunkel), (-15.3, -7.6, m_orange))):
    zylinder(f"Requisite_Fass_{i}", 0.23, 0.62, fx, 0.31, fz, fm)
    zylinder(f"Requisite_Fass_{i}_ring", 0.24, 0.04, fx, 0.45, fz, m_stahl)
kasten("Requisite_Palette", 1.2, 1.0, 0.12, -6.5, 0.06, -8.6, m_objekt, fase=0)
kasten("Requisite_Palette_Kiste_1", 0.55, 0.5, 0.5, -6.7, 0.37, -8.7, m_wand)
kasten("Requisite_Palette_Kiste_2", 0.4, 0.45, 0.35, -6.2, 0.3, -8.4, m_blau)
kasten("Requisite_Werkbank", 2.2, 0.7, 0.85, -16.2, 0.43, 3, m_stahl)
kasten("Requisite_Werkbank_Platte", 2.2, 0.75, 0.08, -16.2, 0.9, 3, m_dunkel)
kasten("Requisite_Werkzeugtafel", 0.06, 1.8, 1.0, -16.85, 1.7, 3, m_dunkel, fase=0)
werkzeuge = ((-16.8, 2.0, 2.5, m_orange), (-16.8, 1.9, 2.8, m_stahl), (-16.8, 2.05, 3.1, m_orange),
             (-16.8, 1.85, 3.4, m_objekt), (-16.8, 1.5, 2.6, m_stahl), (-16.8, 1.45, 3.3, m_orange))
for i, (wx, wy, wz, wm) in enumerate(werkzeuge):
    kasten(f"Requisite_Werkzeug_{i}", 0.05, 0.1, 0.3, wx, wy, wz, wm, fase=0)
kasten("Requisite_Wagen", 0.9, 0.5, 0.55, -13, 0.28, -2, m_blau)
kasten("Requisite_Wagen_Griff", 0.06, 0.4, 0.5, -13.45, 0.75, -2, m_dunkel, fase=0)
kasten("Requisite_Schrank_1", 0.8, 0.4, 1.8, 13.5, 0.9, -9.6, m_objekt)
kasten("Requisite_Schrank_2", 0.8, 0.4, 1.8, 14.4, 0.9, -9.6, m_blau)
kasten("Requisite_Leiter", 0.5, 0.08, 2.4, 15.5, 1.2, -9.7, m_orange, fase=0)

# ---- Kenney-Industriemodelle: Maschinenpark, Ventil, Tor, Kleinteile --------
lade_asset("factory_machine.glb", "Maschine_Nord_1", 5.6, 0, -9.2, ziel_hoehe=1.8)
lade_asset("factory_machine-window.glb", "Maschine_Nord_2", 7.2, 0, -9.2, ziel_hoehe=1.8)
lade_asset("factory_machine-fortified.glb", "Maschine_West", -16.1, 0, 7.5, dreh_y=1.5708, ziel_hoehe=1.8)
lade_asset("factory_pipe-large-valve.glb", "Ventil_Ost", 16.5, 0, -6.5, dreh_y=-1.5708, ziel_hoehe=1.5)
lade_asset("factory_door-wide-open.glb", "Tor_Fluegel", 16.9, 0, 0, dreh_y=1.5708, ziel_breite=4.0)
for i, (cx, cz) in enumerate(((-8.2, 1.55), (-12, 1.5), (-15.6, 1.5), (5.8, 2.6))):
    lade_asset("factory_cone.glb", f"Pylone_{i}", cx, 0, cz, ziel_hoehe=0.5)
lade_asset("factory_box-large.glb", "Kiste_Palette", -5.6, 0, -8.6, dreh_y=0.4, ziel_hoehe=0.7)
lade_asset("factory_box-long.glb", "Kiste_Werkbank", -15.9, 0, 4.6, ziel_hoehe=0.5)
lade_asset("factory_box-small.glb", "Kiste_Empore", -16.2, 3.13, -6.9, dreh_y=0.8, ziel_hoehe=0.45)

# ---- Fahrzeuge und Ersatzteile (Kenney Car Kit) -----------------------------
lade_asset("car_tractor-shovel.glb", "Radlader", -13.5, 0, -3.2, dreh_y=0.7, ziel_breite=2.6)
lade_asset("car_delivery.glb", "Lieferwagen", 13.4, 0, 4.6, dreh_y=1.9, ziel_breite=3.0)
# Ersatzraeder als wartende Teile (die "debris"-Modelle sind Unfallschrott — ungeeignet)
lade_asset("car_wheel-truck.glb", "Ersatzrad", -15.8, 0, 5.6, ziel_breite=0.6)

# ---- Mehr Werkstatt-Ausstattung (Factory Kit) -------------------------------
lade_asset("factory_conveyor-long.glb", "Foerderband", 0.3, 0, -8.55, ziel_breite=2.6)
lade_asset("factory_box-small.glb", "Foerderband_Kiste", 0.1, 0.55, -8.55, dreh_y=0.3, ziel_hoehe=0.4)
lade_asset("factory_screen-panel-wide.glb", "Leitstand_Panel", 9.2, 0, -9.35, ziel_hoehe=1.6)
lade_asset("factory_hopper-square.glb", "Trichter", 15.3, 0, -8.3, ziel_hoehe=1.9)

# ---- Stationsschilder (Ziffer kamerazugewandt, Sued-Stationen gedreht) ------
for nr, (x, z) in {1: (-10, -5), 2: (-3, -6), 3: (7, -5), 4: (9, 5), 5: (2, 6), 6: (-9, 6)}.items():
    kasten(f"Schild_{nr}", 0.5, 0.5, 0.5, x, 3.4, z, m_blau)
    nach_norden = z > 0
    versatz = -0.28 if nach_norden else 0.28
    bpy.ops.object.text_add(location=pos(x, 3.4, z + versatz))
    ziffer = bpy.context.active_object
    ziffer.name = f"Schild_{nr}_ziffer"
    ziffer.data.body = str(nr)
    ziffer.data.size = 0.35
    ziffer.data.extrude = 0.02
    ziffer.data.align_x = "CENTER"
    ziffer.data.align_y = "CENTER"
    ziffer.rotation_euler = (1.5708, 0, 3.14159 if nach_norden else 0)
    ziffer.data.materials.append(m_wand)
    bpy.ops.object.convert(target="MESH")

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
