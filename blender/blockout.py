"""Blockout der Instandhaltungswerkstatt (Stil C: Low-Poly, entsaettigte Farben).

Layout orientiert an blender/referenz-werkstatt.webp (isometrische Bahn-Werkstatt):
Hallenfachwerk mit Fensterbaendern an Nord- und Westwand, Tor in der Ostwand mit
ausfuehrendem Gleis, Bodenmarkierungen entlang der Gleiszone, Arbeitszonen und Regale
an den Waenden, heller Triebzug mit dezentem Verkehrsrot-Streifen (Spec §2: Rot nur
am Zug, Rest grau-blau, graustufentauglich). Sued- und Ostwand-Bereich bleiben als
Cutaway niedrig, damit die Totale (Kamera von Suedost oben) in die Halle schaut.

Koordinaten-Vertrag: Three.js ist Y-up, Blender Z-up; der glTF-Exporter konvertiert
automatisch (+Y up). Die Hilfsfunktion pos() nimmt daher Three.js-Koordinaten
(x, y, z wie in stationen.json) und uebersetzt sie nach Blender (x, -z, y); quader()
nimmt die Groesse als (breite_x, tiefe_z, hoehe_y) in Three.js-Achsen.
Objektnamen folgen dem Vertrag Station_<nr>_<id> bzw. Monitor_Bildschirm.
"""
import bpy
import os

ZIEL = os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd(),
                    "app", "public", "szene.glb")


def pos(x, y, z):
    return (x, -z, y)


def material(name, farbe, rauheit=0.85):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*farbe, 1.0)
    bsdf.inputs["Roughness"].default_value = rauheit
    return mat


def quader(name, groesse, position, mat, drehung=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (groesse[0], groesse[1], groesse[2])
    if drehung:
        obj.rotation_euler = drehung
    obj.data.materials.append(mat)
    return obj


def kasten(name, dx, dz, dy, x, y, z, mat, drehung=None):
    """quader in Three.js-Achsen: Groesse (dx, dz, dy), Mittelpunkt (x, y, z)."""
    return quader(name, (dx, dz, dy), pos(x, y, z), mat, drehung)


# ---- Szene leeren -----------------------------------------------------------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

GRAU_BODEN = (0.55, 0.58, 0.60)
GRAU_GLEISZONE = (0.42, 0.45, 0.47)
GRAU_WAND = (0.76, 0.79, 0.81)
GRAU_OBJEKT = (0.62, 0.66, 0.69)
GRAU_DUNKEL = (0.30, 0.32, 0.34)
STAHL = (0.45, 0.50, 0.55)
FENSTER = (0.82, 0.88, 0.94)
BLAU = (0.35, 0.45, 0.58)      # entsaettigtes Blau (Leitstand/Regal, wie Referenz)
MARKIERUNG = (0.72, 0.66, 0.38)  # entsaettigtes Gelb der Bodenmarkierung
ROT_ZUG = (0.55, 0.16, 0.20)   # entsaettigtes Verkehrsrot, nur am Triebzug (Spec §2)
WEISS_ZUG = (0.85, 0.86, 0.88)

m_boden = material("Boden", GRAU_BODEN)
m_gleiszone = material("Gleiszone", GRAU_GLEISZONE)
m_wand = material("Wand", GRAU_WAND)
m_objekt = material("Objekt", GRAU_OBJEKT)
m_dunkel = material("Dunkel", GRAU_DUNKEL)
m_stahl = material("Stahl", STAHL)
m_fenster = material("Fenster", FENSTER, rauheit=0.3)
m_blau = material("Blau", BLAU)
m_markierung = material("Markierung", MARKIERUNG)
m_zug = material("Zug", ROT_ZUG)
m_zugweiss = material("ZugWeiss", WEISS_ZUG, rauheit=0.5)

# ---- Halle: Boden, Gleiszone, Markierungen ----------------------------------
kasten("Halle_Boden", 34, 20, 0.2, 0, -0.1, 0, m_boden)
kasten("Halle_Gleiszone", 34, 3.6, 0.04, 0, 0.02, 0, m_gleiszone)
kasten("Halle_Markierung_Nord", 30, 0.1, 0.02, 0, 0.045, -1.9, m_markierung)
kasten("Halle_Markierung_Sued", 30, 0.1, 0.02, 0, 0.045, 1.9, m_markierung)

# ---- Nordwand mit Fensterband (Referenz: Oberlichter) -----------------------
kasten("Wand_Nord_Unten", 34, 0.3, 3.5, 0, 1.75, -10, m_wand)
kasten("Wand_Nord_Fenster", 34, 0.1, 1.8, 0, 4.4, -10.08, m_fenster)
kasten("Wand_Nord_Oben", 34, 0.3, 0.7, 0, 5.65, -10, m_wand)
for i, fx in enumerate(range(-16, 17, 4)):
    kasten(f"Wand_Nord_Sprosse_{i}", 0.15, 0.3, 1.8, fx, 4.4, -10, m_stahl)

# ---- Westwand mit Fensterband ----------------------------------------------
kasten("Wand_West_Unten", 0.3, 20, 3.5, -17, 1.75, 0, m_wand)
kasten("Wand_West_Fenster", 0.1, 20, 1.8, -17.08, 4.4, 0, m_fenster)
kasten("Wand_West_Oben", 0.3, 20, 0.7, -17, 5.65, 0, m_wand)
for i, fz in enumerate(range(-8, 9, 4)):
    kasten(f"Wand_West_Sprosse_{i}", 0.3, 0.15, 1.8, -17, 4.4, fz, m_stahl)

# ---- Suedwand: niedriger Sockel (Cutaway fuer die Totale) -------------------
kasten("Wand_Sued_Sockel", 34, 0.3, 1.0, 0, 0.5, 10, m_wand)

# ---- Ostwand mit Tor, Gleis fuehrt hinaus (Referenz: Ausfahrt rechts) -------
kasten("Wand_Ost_Nord", 0.3, 8.2, 6, 17, 3, -5.9, m_wand)
kasten("Wand_Ost_Sued", 0.3, 8.2, 6, 17, 3, 5.9, m_wand)
kasten("Wand_Ost_Sturz", 0.3, 3.6, 1.8, 17, 5.1, 0, m_wand)
kasten("Tor_Pfosten_Nord", 0.25, 0.25, 4.4, 16.8, 2.2, -1.9, m_dunkel)
kasten("Tor_Pfosten_Sued", 0.25, 0.25, 4.4, 16.8, 2.2, 1.9, m_dunkel)
kasten("Tor_Balken", 0.25, 4.3, 0.25, 16.8, 4.35, 0, m_dunkel)

# ---- Stahlbau: Stuetzen, Binder, Rohre, Leuchten (Referenz: offenes Dach) ---
for i, sx in enumerate((-13.6, -6.8, 0, 6.8, 13.6)):
    kasten(f"Stuetze_Nord_{i}", 0.3, 0.3, 6, sx, 3, -9.7, m_stahl)
for i, sz in enumerate((-6.7, 0, 6.7)):
    kasten(f"Stuetze_West_{i}", 0.3, 0.3, 6, -16.7, 3, sz, m_stahl)
for i, tx in enumerate((-12, -6, 0, 6, 12)):
    kasten(f"Dachbinder_{i}", 0.22, 19.4, 0.28, tx, 5.7, 0, m_stahl)
    # Stuetze an der offenen Suedkante, damit der Binder im Cutaway nicht frei endet
    kasten(f"Stuetze_Sued_{i}", 0.25, 0.25, 5.7, tx, 2.85, 9.55, m_stahl)
kasten("Rohr_Blau", 33, 0.18, 0.18, 0, 5.1, -9.3, m_blau)
kasten("Rohr_Grau", 33, 0.16, 0.16, 0, 4.8, -9.0, m_stahl)
for i, lx in enumerate((-10, -4.5, 1, 6.5, 12)):
    kasten(f"Leuchte_{i}", 0.9, 0.35, 0.12, lx, 4.6, 0, m_fenster)

# ---- Gleis (fuehrt durch das Tor nach draussen) -----------------------------
kasten("Gleis_Schiene_Nord", 38, 0.15, 0.15, 2, 0.08, -0.7, m_dunkel)
kasten("Gleis_Schiene_Sued", 38, 0.15, 0.15, 2, 0.08, 0.7, m_dunkel)
for i in range(16):
    kasten(f"Gleis_Schwelle_{i}", 0.22, 1.8, 0.06, -14.5 + i * 2.4, 0.03, 0, m_dunkel)

# ---- Triebzug: heller Korpus, Verkehrsrot-Streifen (Referenz + Spec §2) -----
kasten("Triebzug_Unterbau", 14, 2.2, 0.5, 0.5, 0.45, 0, m_dunkel)
kasten("Triebzug_Korpus", 14, 2.4, 1.5, 0.5, 1.45, 0, m_zugweiss)
kasten("Triebzug_Streifen_Nord", 14, 0.06, 0.35, 0.5, 1.05, -1.23, m_zug)
kasten("Triebzug_Streifen_Sued", 14, 0.06, 0.35, 0.5, 1.05, 1.23, m_zug)
kasten("Triebzug_Fensterband_Nord", 11.5, 0.06, 0.55, 0, 1.8, -1.23, m_dunkel)
kasten("Triebzug_Fensterband_Sued", 11.5, 0.06, 0.55, 0, 1.8, 1.23, m_dunkel)
kasten("Triebzug_Dach", 13.6, 2.2, 0.3, 0.5, 2.35, 0, m_stahl)
for i, kx in enumerate((-4, 0.5, 5)):
    kasten(f"Triebzug_Klima_{i}", 1.4, 1.4, 0.25, kx, 2.6, 0, m_dunkel)
kasten("Triebzug_Front", 1.2, 2.2, 1.4, 8.1, 1.4, 0, m_zugweiss)
kasten("Triebzug_Windschutz", 0.15, 1.6, 0.6, 8.65, 1.9, 0, m_dunkel)
for i, tx in enumerate((-3, 4)):
    kasten(f"Triebzug_Tuer_Nord_{i}", 0.9, 0.05, 1.3, tx, 1.35, -1.24, m_stahl)
    kasten(f"Triebzug_Tuer_Sued_{i}", 0.9, 0.05, 1.3, tx, 1.35, 1.24, m_stahl)

# ---- Station 1: Meisterbuero mit Pinnwand (Referenz: Bueroecke links) -------
kasten("Station_1_meisterbuero", 4, 3, 2.6, -10.5, 1.3, -7.5, m_wand)
kasten("Station_1_buerofenster", 2.6, 0.06, 0.9, -10.5, 1.9, -5.95, m_dunkel)
kasten("Station_1_pinnwand", 2.4, 0.08, 1.3, -10, 1.8, -5.2, m_objekt)
kasten("Station_1_pinnwand_pfosten_west", 0.1, 0.1, 2.3, -11.0, 1.15, -5.2, m_dunkel)
kasten("Station_1_pinnwand_pfosten_ost", 0.1, 0.1, 2.3, -9.0, 1.15, -5.2, m_dunkel)
for i in range(6):
    zx = -10.9 + (i % 3) * 0.9
    zy = 2.1 - (i // 3) * 0.55
    kasten(f"Station_1_zettel_{i}", 0.32, 0.03, 0.42, zx, zy, -5.14, m_fenster)
kasten("Station_1_schreibtisch", 1.6, 0.7, 0.12, -8.2, 0.72, -5.4, m_objekt)
kasten("Station_1_schreibtisch_fuss", 0.25, 0.6, 0.66, -8.2, 0.33, -5.4, m_dunkel)

# ---- Station 2: Datenraum-Regal, Chaos davor / Ordnung darin (Spec §4) ------
kasten("Station_2_datenraum", 0.08, 1.0, 2.2, -4.2, 1.1, -6, m_blau)
kasten("Station_2_regalwange", 0.08, 1.0, 2.2, -1.8, 1.1, -6, m_blau)
for i, by in enumerate((0.35, 0.95, 1.55, 2.15)):
    kasten(f"Station_2_regalbrett_{i}", 2.5, 1.0, 0.06, -3, by, -6, m_dunkel)
for i in range(6):  # geordnete Ordnerreihe im Regal (oberes Fach)
    kasten(f"Station_2_ordner_{i}", 0.2, 0.4, 0.5, -3.9 + i * 0.36, 1.85, -6, m_objekt)
for i in range(5):  # geordnete Kisten im mittleren Fach
    kasten(f"Station_2_kiste_{i}", 0.34, 0.5, 0.4, -3.8 + i * 0.42, 1.2, -6, m_wand)
chaos = [(-4.1, -4.9, 0.5, 0.35), (-3.4, -5.2, 0.45, -0.5), (-2.7, -4.7, 0.55, 0.9),
         (-2.1, -5.1, 0.4, -0.2), (-3.0, -4.5, 0.35, 1.3)]
for i, (cx, cz, cg, cr) in enumerate(chaos):
    kasten(f"Station_2_chaos_{i}", cg, cg, cg, cx, cg / 2, cz, m_objekt, drehung=(0, 0, cr))
kasten("Station_2_fass_1", 0.42, 0.42, 0.6, -1.4, 0.3, -5.0, m_dunkel)
kasten("Station_2_fass_2", 0.42, 0.42, 0.6, -1.0, 0.3, -5.5, m_blau)

# ---- Station 3: Bedienterminal (Referenz: blauer Leitstand) -----------------
kasten("Station_3_terminal_saeule", 0.5, 0.5, 1.2, 7, 0.6, -5, m_dunkel)
kasten("Station_3_terminal_gehaeuse", 1.8, 0.35, 1.05, 7, 1.5, -4.15, m_blau)
kasten("Station_3_terminal_pult", 1.4, 0.5, 0.1, 7, 0.95, -4.45, m_stahl)
bpy.ops.mesh.primitive_plane_add(size=1, location=pos(7, 1.5, -3.95))
monitor = bpy.context.active_object
monitor.name = "Monitor_Bildschirm"
monitor.scale = (1.6, 0.9, 1)
monitor.rotation_euler = (1.5708, 0, 0)  # senkrecht, Front Richtung Sueden
monitor.data.materials.append(m_dunkel)

# ---- Station 4: Anzeigetafel auf Pfosten ------------------------------------
kasten("Station_4_anzeigetafel", 3.2, 0.15, 1.8, 9, 2, 5.8, m_dunkel)
kasten("Station_4_pfosten_west", 0.15, 0.15, 2.9, 7.6, 1.45, 5.8, m_stahl)
kasten("Station_4_pfosten_ost", 0.15, 0.15, 2.9, 10.4, 1.45, 5.8, m_stahl)

# ---- Station 5: Pruefstand (Referenz: Maschine mit blauem Aufbau) -----------
kasten("Station_5_pruefstand", 2.8, 1.2, 0.5, 2, 0.25, 6, m_stahl)
kasten("Station_5_aufbau", 1.4, 0.9, 0.9, 1.6, 1.15, 6, m_blau)
kasten("Station_5_rolle_1", 0.35, 1.0, 0.35, 2.6, 0.7, 6, m_dunkel)
kasten("Station_5_rolle_2", 0.35, 1.0, 0.35, 3.1, 0.7, 6, m_dunkel)
kasten("Station_5_panel", 0.4, 0.05, 0.3, 1.3, 1.5, 5.5, m_fenster)

# ---- Station 6: Besprechung (Planungsrunde) ---------------------------------
kasten("Station_6_besprechung_tisch", 2.4, 1.2, 0.1, -9, 0.72, 6, m_objekt)
kasten("Station_6_tischfuss", 0.3, 0.3, 0.67, -9, 0.34, 6, m_dunkel)
stuehle = [(-10.1, 5.2), (-7.9, 5.2), (-10.1, 6.8), (-7.9, 6.8)]
for i, (sx, sz) in enumerate(stuehle):
    kasten(f"Station_6_stuhl_{i}_sitz", 0.45, 0.45, 0.08, sx, 0.45, sz, m_dunkel)
    lehne_z = sz + (0.24 if sz > 6 else -0.24)
    kasten(f"Station_6_stuhl_{i}_lehne", 0.45, 0.06, 0.5, sx, 0.75, lehne_z, m_dunkel)
kasten("Station_6_sideboard", 1.6, 0.5, 0.8, -11.5, 0.4, 7, m_objekt)

# ---- Requisiten an den Waenden (Referenz: Faesser, Palette, Werkbank) -------
kasten("Requisite_Fass_1", 0.45, 0.45, 0.62, -15.6, 0.31, -8.2, m_blau)
kasten("Requisite_Fass_2", 0.45, 0.45, 0.62, -15.0, 0.31, -8.5, m_dunkel)
kasten("Requisite_Fass_3", 0.45, 0.45, 0.62, -15.3, 0.31, -7.6, m_stahl)
kasten("Requisite_Palette", 1.2, 1.0, 0.12, -6.5, 0.06, -8.6, m_objekt)
kasten("Requisite_Palette_Kiste_1", 0.55, 0.5, 0.5, -6.7, 0.37, -8.7, m_wand)
kasten("Requisite_Palette_Kiste_2", 0.4, 0.45, 0.35, -6.2, 0.3, -8.4, m_blau)
kasten("Requisite_Werkbank", 2.2, 0.7, 0.85, -16.2, 0.43, 3, m_stahl)
kasten("Requisite_Werkbank_Platte", 2.2, 0.75, 0.08, -16.2, 0.9, 3, m_dunkel)
kasten("Requisite_Wagen", 0.9, 0.5, 0.55, -13, 0.28, -2, m_blau)
kasten("Requisite_Schrank_1", 0.8, 0.4, 1.8, 13.5, 0.9, -9.6, m_objekt)
kasten("Requisite_Schrank_2", 0.8, 0.4, 1.8, 14.4, 0.9, -9.6, m_blau)

# ---- Stationsschilder: dunkler Wuerfel + helle Ziffer (Spec §4 Startbild) ---
# Die Ziffer haengt auf der kamerazugewandten Seite: Nord-Stationen (z<0) werden von
# Sueden betrachtet (Ziffer bei z+0.28, Front nach Sueden), Sued-Stationen (z>0) von
# Norden (Ziffer bei z-0.28, um 180 Grad gedreht) — sonst verdeckt der eigene Wuerfel
# die Ziffer in den Stationsansichten 4-6.
for nr, (x, z) in {1: (-10, -5), 2: (-3, -6), 3: (7, -5), 4: (9, 5), 5: (2, 6), 6: (-9, 6)}.items():
    quader(f"Schild_{nr}", (0.5, 0.5, 0.5), pos(x, 3.4, z), m_dunkel)
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
    # aufrecht; Front nach Sueden (Three +z) bzw. fuer Sued-Stationen nach Norden
    ziffer.rotation_euler = (1.5708, 0, 3.14159 if nach_norden else 0)
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
