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
from mathutils import Euler, Matrix, Vector

WURZEL = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
ZIEL = os.path.join(WURZEL, "app", "public", "szene.glb")
BODEN_PNG = os.path.join(WURZEL, "blender", "gen_boden.png")


def pos(x, y, z):
    return (x, -z, y)


def _png_speichern(pfad, groesse, pixelzeilen):
    def chunk(typ, daten):
        return (struct.pack(">I", len(daten)) + typ + daten
                + struct.pack(">I", zlib.crc32(typ + daten) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", groesse, groesse, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(pixelzeilen))
    png += chunk(b"IEND", b"")
    with open(pfad, "wb") as f:
        f.write(png)


def schreibe_noise_png(pfad, groesse=256, basis=(178, 180, 182), spann=10, seed=7, koernung=0):
    """Material-Textur als Value-Noise-PNG (zwei Oktaven Flecken + feine Koernung)."""
    random.seed(seed)

    def gitter(g):
        return [[random.random() for _ in range(g)] for _ in range(g)]

    def wert(knoten, g, u, v):
        x = u * (g - 1)
        y = v * (g - 1)
        x0, y0 = int(x), int(y)
        fx, fy = x - x0, y - y0
        x1, y1 = min(x0 + 1, g - 1), min(y0 + 1, g - 1)
        a = knoten[y0][x0] * (1 - fx) + knoten[y0][x1] * fx
        b = knoten[y1][x0] * (1 - fx) + knoten[y1][x1] * fx
        return a * (1 - fy) + b * fy

    grob, fein = gitter(9), gitter(33)
    zeilen = b""
    for j in range(groesse):
        zeile = b"\x00"
        for i in range(groesse):
            u, v = i / groesse, j / groesse
            n = 0.65 * wert(grob, 9, u, v) + 0.35 * wert(fein, 33, u, v)
            f = int((n - 0.5) * 2 * spann)
            if koernung:
                f += random.randint(-koernung, koernung)
            zeile += bytes(max(0, min(255, c + f)) for c in basis)
        zeilen += zeile
    _png_speichern(pfad, groesse, zeilen)


def schreibe_riffelblech_png(pfad, groesse=128, basis=214, raster=16):
    """Riffelblech-Optik: diagonales Kreuzmuster auf hellem Metallgrund."""
    zeilen = b""
    for j in range(groesse):
        zeile = b"\x00"
        for i in range(groesse):
            h = basis
            if (i + j) % raster < 2 or (i - j) % raster < 2:
                h = basis - 26
            elif (i + j) % raster < 4 or (i - j) % raster < 4:
                h = basis + 14
            zeile += bytes((h, h, min(255, h + 3)))
        zeilen += zeile
    _png_speichern(pfad, groesse, zeilen)


def material(name, farbe, rauheit=0.85, metall=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*farbe, 1.0)
    bsdf.inputs["Roughness"].default_value = rauheit
    bsdf.inputs["Metallic"].default_value = metall
    return mat


KACHEL = {}  # Materialname -> Kachelgroesse in Metern (siehe _kachel_uv)


def material_mit_textur(name, pfad, rauheit=0.9, metall=0.0, kachel=2.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rauheit
    bsdf.inputs["Metallic"].default_value = metall
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(pfad)
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    KACHEL[name] = kachel
    return mat


def _kachel_uv(obj, kachel):
    """Box-Projektion in Weltkoordinaten.

    Die Primitive kommen mit 0..1-UVs pro Flaeche — eine Textur wird damit ueber
    jede Flaeche gezogen, egal ob sie 0.2 m oder 20 m misst. Der Betonboden bekam
    so genau EINE Kachel auf 17 m (= Schlieren statt Struktur). Hier erhaelt jede
    Flaeche stattdessen UVs in Metern/Kachelgroesse: die Kachel ist auf allen
    Objekten gleich gross und passt ueber Objektgrenzen hinweg zusammen.
    Die Skalierung steckt bewusst in den UVs statt in einem Mapping-Node, weil der
    glTF-Export nur Basis-Nodetrees zuverlaessig uebernimmt."""
    mesh = obj.data
    if not mesh.polygons or kachel <= 0:
        return
    uv = mesh.uv_layers.active or mesh.uv_layers.new(name="UVMap")
    mw = obj.matrix_world
    normalen = mw.to_3x3()
    for poly in mesh.polygons:
        n = normalen @ poly.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for li in poly.loop_indices:
            v = mw @ mesh.vertices[mesh.loops[li].vertex_index].co
            if az >= ax and az >= ay:
                u, w = v.x, v.y  # Draufsicht: Boden, Plattformen, Stufen
            elif ax >= ay:
                u, w = v.y, v.z  # Ost-/Westflanken
            else:
                u, w = v.x, v.z  # Nord-/Suedflanken
            uv.data[li].uv = (u / kachel, w / kachel)


# --- Primitive ohne bpy.ops -------------------------------------------------
# Gemessen: ein bpy.ops.mesh.primitive_cube_add kostete im Schnitt 96 ms, weil
# jeder Operator einen szenenweiten Abhaengigkeits-Update ausloest, der mit jedem
# zusaetzlichen Objekt teurer wird — der Aufbau war dadurch faktisch quadratisch
# (1172 Kaesten = 113 s, 408 Zylinder = 47 s von 197 s gesamt).
# Statt selbst zu parametrisieren wird je Form EINE Vorlage ueber bpy.ops gebaut
# und danach nur noch kopiert und skaliert. Das ist wichtig: Blender legt den
# ersten Zylindervertex bei (0, 1, -1) an, also auf der +Y-Achse. Eine eigene
# Parametrisierung ab 0 Grad wuerde alle Facetten verdrehen — bei 16-eckigen
# Staplerraedern sichtbar, obwohl jede Boundingbox stimmt.
_VORLAGEN = {}


def _vorlage(schluessel, bauen):
    if schluessel not in _VORLAGEN:
        bauen()
        tmp = bpy.context.active_object
        daten = tmp.data
        daten.use_fake_user = True  # ueberlebt das Loeschen des Hilfsobjekts
        bpy.data.objects.remove(tmp, do_unlink=True)
        _VORLAGEN[schluessel] = daten
    return _VORLAGEN[schluessel]


def _aus_vorlage(name, daten, skalierung, ort, drehung=None):
    """Vorlage kopieren, Skalierung in die Vertices backen, Objekt einhaengen.

    Die Skalierung wandert in die Koordinaten statt in obj.scale — damit entfaellt
    das frueher noetige bpy.ops.object.transform_apply. matrix_world wird direkt
    gesetzt, weil obj.location ohne Abhaengigkeits-Update nicht zuverlaessig in
    matrix_world durchschlaegt und _kachel_uv genau darauf angewiesen ist."""
    mesh = daten.copy()
    mesh.name = name
    sx, sy, sz = skalierung
    if (sx, sy, sz) != (1.0, 1.0, 1.0):
        for v in mesh.vertices:
            v.co.x *= sx
            v.co.y *= sy
            v.co.z *= sz
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    m = Matrix.Translation(Vector(ort))
    if drehung:
        m = m @ Euler(drehung, "XYZ").to_matrix().to_4x4()
    obj.matrix_world = m
    # Aufrufstellen wie treppe(), rohr_mit_bogen() und gabelstapler() greifen
    # direkt nach dem Helferaufruf auf bpy.context.active_object zu
    bpy.context.view_layer.objects.active = obj
    return obj


def _abschliessen(obj, mat, fase):
    """UV-Kachelung setzen und Bevel-Modifier anlegen."""
    _kachel_uv(obj, KACHEL.get(mat.name, 2.0))
    if fase > 0:
        mod = obj.modifiers.new("Fase", "BEVEL")
        mod.width = fase
        mod.segments = 1
        mod.limit_method = "NONE"
    obj.data.materials.append(mat)
    return obj


def kasten(name, dx, dz, dy, x, y, z, mat, drehung=None, fase=0.02):
    """Quader in Three.js-Achsen: Groesse (dx, dz, dy), Mittelpunkt (x, y, z)."""
    daten = _vorlage("wuerfel", lambda: bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)))
    obj = _aus_vorlage(name, daten, (dx, dz, dy), pos(x, y, z), drehung)
    return _abschliessen(obj, mat, fase)


def zylinder(name, radius, laenge, x, y, z, mat, achse="y", ecken=16, fase=0.0):
    """Zylinder; achse in Three.js: 'x' laengs, 'y' senkrecht, 'z' quer."""
    daten = _vorlage(("zylinder", ecken), lambda: bpy.ops.mesh.primitive_cylinder_add(
        vertices=ecken, radius=1.0, depth=1.0, location=(0, 0, 0)))
    drehung = None
    if achse == "x":
        drehung = (0, 1.5708, 0)
    elif achse == "z":
        drehung = (1.5708, 0, 0)
    obj = _aus_vorlage(name, daten, (radius, radius, laenge), pos(x, y, z), drehung)
    return _abschliessen(obj, mat, fase)


def kugel(name, radius, x, y, z, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=radius,
                                         location=pos(x, y, z))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def kegel(name, radius, hoehe, x, y, z, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=radius, radius2=0.05,
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


def lade_asset(datei, name, x, y, z, dreh_y=0.0, ziel_hoehe=None, ziel_breite=None, einfaerbung=None):
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
    if einfaerbung is not None:
        # Kenney-Fremdfarben (Tuerkis/Lila/Tan/Rosa) auf die Szenen-Palette ziehen
        for o in meshes:
            for slot in o.material_slots:
                slot.material = einfaerbung
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
GRAU_OBJEKT = (0.72, 0.73, 0.72)      # RAL 7035 Lichtgrau, leicht gedeckt: Maschinen- und Geraetegrau
GRAU_DUNKEL = (0.29, 0.30, 0.32)
STAHL = (0.55, 0.57, 0.60)
FENSTER = (0.87, 0.91, 0.96)
BLAU = (0.10, 0.33, 0.56)             # RAL 5010 Enziablau, der Maschinenlack der Werkstatt
ORANGE = (0.89, 0.35, 0.13)           # RAL 2004 Reinorange, Faesser und Warnkoerper
MARKIERUNG = (0.95, 0.72, 0.05)       # RAL 1023 Verkehrsgelb, Bodenmarkierung und Rammschutz
STAHL_HELL = (0.85, 0.86, 0.88)
GRUEN = (0.12, 0.33, 0.26)            # RAL 6005 Moosgruen, Schweissschutzwaende
GRUBE = (0.09, 0.10, 0.11)
ROT_ZUG = (0.72, 0.12, 0.16)
WEISS_ZUG = (0.90, 0.90, 0.91)
WAND_RELIEF = (0.62, 0.61, 0.58)
DECKE = (0.84, 0.83, 0.81)
SOCKEL = (0.44, 0.45, 0.45)           # RAL 7037 Staubgrau: abwaschbarer Wandsockel

# Materialien mit ablesbarer Materialitaet: Beton matt+fleckig (Textur), Stahl
# metallisch-glaenzend (Metalness, Reflexe kommen aus der Environment-Map im Viewer),
# Lack seidig, Glas glatt.
m_objekt = material("Objekt", GRAU_OBJEKT, rauheit=0.7, metall=0.15)
m_dunkel = material("Dunkel", GRAU_DUNKEL, rauheit=0.5, metall=0.25)
m_stahl = material("Stahl", STAHL, rauheit=0.45, metall=0.85)
m_fenster = material("Fenster", FENSTER, rauheit=0.08)
m_blau = material("Blau", BLAU, rauheit=0.5, metall=0.2)
m_orange = material("Orange", ORANGE, rauheit=0.5, metall=0.2)
m_markierung = material("Markierung", MARKIERUNG, rauheit=0.55, metall=0.15)
m_stahlhell = material("StahlHell", STAHL_HELL, rauheit=0.35, metall=0.7)
m_gruen = material("Gruen", GRUEN, rauheit=0.5, metall=0.2)
m_grube = material("Grube", GRUBE, rauheit=0.85)
m_zug = material("Zug", ROT_ZUG, rauheit=0.35, metall=0.3)
m_zugweiss = material("ZugWeiss", WEISS_ZUG, rauheit=0.3, metall=0.25)
# Dach dunkel absetzen: es lief bisher auf m_stahlhell (0.85) gegen den Kasten (0.90) —
# fuenf Prozent Unterschied, aus Beamerabstand also gar keine Dachkante. Der Zug hatte
# damit keine Oberkante und franste oben in die helle Halle aus.
# Hellgrau wie beim Vorbild: ein dunkles Dach laesst den Zug als Regionaltriebwagen
# lesen. Die Oberkante entsteht jetzt ueber die Dachwoelbung, nicht ueber Farbe.
m_zugdach = material("ZugDach", (0.70, 0.71, 0.73), rauheit=0.5, metall=0.30)
m_relief = material("WandRelief", WAND_RELIEF)
m_decke = material("Decke", DECKE)
m_sockel = material("Sockel", SOCKEL, rauheit=0.75)
# Unterflur-Staffelung: Schiene blank gefahren, Schwelle stumpfes Beton-Grau,
# Gummi tief und matt, Unterflurtechnik dunkel-seidig. Vorher war alles m_dunkel/m_stahl,
# dadurch verschmolzen Rad, Rahmen, Schiene und Schwelle zu einem grauen Block.
m_schiene = material("Schiene", (0.62, 0.58, 0.52), rauheit=0.30, metall=0.35)
m_schwelle = material("Schwelle", (0.36, 0.35, 0.33), rauheit=0.95)
m_gummi = material("Gummi", (0.085, 0.085, 0.095), rauheit=0.95)
m_unterflur = material("Unterflur", (0.16, 0.17, 0.18), rauheit=0.70)
# Hallenverglasung eigenstaendig, damit sie als Glas liest, ohne die vielen
# anderen m_fenster-Verwendungen (Leuchten, Zettel, Schilder) mitzuziehen.
m_hallenglas = material("Hallenglas", (0.78, 0.85, 0.92), rauheit=0.05)
# Gruener Betriebsweg — der klassische Werkstattmarker fuer die Fussgaengerspur.
m_weg = material("Weg", (0.20, 0.42, 0.28), rauheit=0.9)
m_oelfleck = material("Oelfleck", (0.16, 0.15, 0.14), rauheit=0.35)

GLEIS_PNG = os.path.join(WURZEL, "blender", "gen_gleiszone.png")
WAND_PNG = os.path.join(WURZEL, "blender", "gen_wand.png")
RIFFEL_PNG = os.path.join(WURZEL, "blender", "gen_riffelblech.png")
# Beton deutlich abgedunkelt: der Boden war die hellste grosse Flaeche der Halle und
# zog dadurch alle Aufmerksamkeit; echter Werkstattbeton liegt klar unter den Waenden.
schreibe_noise_png(BODEN_PNG, basis=(104, 106, 110), spann=30, seed=7, koernung=6)
schreibe_noise_png(GLEIS_PNG, basis=(74, 76, 80), spann=22, seed=11, koernung=8)
schreibe_noise_png(WAND_PNG, basis=(206, 202, 194), spann=7, seed=5, koernung=2)
schreibe_riffelblech_png(RIFFEL_PNG)
def fass(name, x, z, y_boden, farbe):
    """Oelfass mit zwei Sickenringen und hellem Deckel — mehr Kontur pro Objekt."""
    zylinder(f"{name}", 0.23, 0.62, x, y_boden + 0.31, z, farbe, ecken=32)
    zylinder(f"{name}_ring_oben", 0.245, 0.04, x, y_boden + 0.46, z, m_stahl, ecken=32)
    zylinder(f"{name}_ring_unten", 0.245, 0.04, x, y_boden + 0.16, z, m_stahl, ecken=32)
    zylinder(f"{name}_deckel", 0.2, 0.03, x, y_boden + 0.63, z, m_stahlhell, ecken=32)


def auffangwanne(name, x0, x1, z0, z1):
    """Flacher gelber Wannenrand um eine Fassgruppe. Faesser ohne Auffangwanne sind
    der Fehler, den jeder Werkstattpraktiker zuerst sieht."""
    xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
    for k, (bx, bz, dx, dz) in enumerate(((xm, z0, x1 - x0, 0.06), (xm, z1, x1 - x0, 0.06),
                                          (x0, zm, 0.06, z1 - z0), (x1, zm, 0.06, z1 - z0))):
        kasten(f"{name}_{k}", dx, dz, 0.05, bx, 0.025, bz, m_markierung, fase=0)


m_boden = material_mit_textur("Boden", BODEN_PNG, rauheit=0.92, kachel=4.0)
m_gleiszone = material_mit_textur("Gleiszone", GLEIS_PNG, rauheit=0.92, kachel=3.0)
m_wand = material_mit_textur("Wand", WAND_PNG, rauheit=0.85, kachel=3.0)
m_riffel = material_mit_textur("Riffelblech", RIFFEL_PNG, rauheit=0.4, metall=0.7, kachel=0.5)

# ---- Halle: Boden, Gleiszone, Markierungen ----------------------------------
# Boden- und Gleiszonenplatten mit Aussparung fuer die Untersuchungsgrube (x -7..0, z -1..1)
kasten("Halle_Boden_West", 10, 20, 0.2, -12, -0.1, 0, m_boden, fase=0)
kasten("Halle_Boden_Ost", 17, 20, 0.2, 8.5, -0.1, 0, m_boden, fase=0)
kasten("Halle_Boden_GrubeNord", 7, 9, 0.2, -3.5, -0.1, -5.5, m_boden, fase=0)
kasten("Halle_Boden_GrubeSued", 7, 9, 0.2, -3.5, -0.1, 5.5, m_boden, fase=0)
kasten("Halle_Gleiszone_West", 10, 3.6, 0.006, -12, 0.003, 0, m_gleiszone, fase=0)
kasten("Halle_Gleiszone_Ost", 17, 3.6, 0.006, 8.5, 0.003, 0, m_gleiszone, fase=0)
kasten("Halle_Gleiszone_GrubeNord", 7, 0.8, 0.006, -3.5, 0.003, -1.4, m_gleiszone, fase=0)
kasten("Halle_Gleiszone_GrubeSued", 7, 0.8, 0.006, -3.5, 0.003, 1.4, m_gleiszone, fase=0)
kasten("Halle_Markierung_Nord", 30, 0.12, 0.02, 0, 0.012, -1.9, m_markierung, fase=0)
kasten("Halle_Markierung_Sued", 30, 0.12, 0.02, 0, 0.012, 1.9, m_markierung, fase=0)
# Plattenraster mit Dehnfugen (5-m-Raster) und gelbe Sicherheitslinie 1.0 m neben der
# Gleiszone: der Hallenboden liest sonst als eine einzige Betonflaeche.
for i, fx in enumerate((-15.0, -10.0, -5.0, 5.0, 10.0, 15.0)):
    for seite, z0, z1 in (("n", -9.85, -1.9), ("s", 1.9, 9.85)):
        kasten(f"Bodenfuge_x_{i}_{seite}", 0.02, z1 - z0, 0.002, fx, 0.001, (z0 + z1) / 2, m_dunkel, fase=0)
for i, fz in enumerate((-7.0, -4.0, 4.0, 7.0)):
    kasten(f"Bodenfuge_z_{i}", 34.0, 0.02, 0.002, 0, 0.001, fz, m_dunkel, fase=0)
for seite, sz in (("nord", -2.8), ("sued", 2.8)):
    kasten(f"Sicherheitsabstand_{seite}", 30.0, 0.10, 0.002, 0, 0.001, sz, m_markierung, fase=0)
# Fussweg liegt VOR Rammschutz und Maschinenfront (z -7.6..-6.5). Vorher lief er am
# Wandfuss unter den Maschinen und durchs Meisterbuero. Luecke am Fuss der Buehnentreppe.
kasten("Halle_Weg_Nord_W", 10.5, 1.1, 0.03, -3.05, 0.02, -7.05, m_weg, fase=0)
kasten("Halle_Weg_Nord_O", 13.1, 1.1, 0.03, 10.15, 0.02, -7.05, m_weg, fase=0)
# Fugenraster: Querfugen alle 4 m, Laengsfugen ausserhalb der Gleiszone. Erst mit
# dem abgedunkelten Gleiszonen-Material werden sie ueberhaupt sichtbar und geben
# der 8.5 x 13 m grossen Bodenflaeche einen Massstab.
for i, fx in enumerate(range(-16, 17, 4)):
    if -7.0 < fx < 0.0:  # Grubenoeffnung aussparen, sonst schwebt die Fuge ueber dem Loch
        for j, zm in enumerate((-5.4, 5.4)):
            kasten(f"Bodenfuge_q{i}_{j}", 0.06, 8.6, 0.015, fx, 0.012, zm, m_gleiszone, fase=0)
    else:
        kasten(f"Bodenfuge_q{i}", 0.06, 19.4, 0.015, fx, 0.012, 0, m_gleiszone, fase=0)
for i, fz in enumerate((-6.5, -3.5, 3.5, 6.5, 9.5)):
    kasten(f"Bodenfuge_l{i}", 33.4, 0.06, 0.015, 0, 0.012, fz, m_gleiszone, fase=0)
# Gebrauchsspuren: eine Werkstatt ist benutzt. Zwei Oelflecken in der Gleiszone
# (Oberkante 0.04) und einer auf dem Hallenboden (Oberkante 0.0).
zylinder("Oelfleck_1", 0.28, 0.012, -4.5, 0.012, 1.5, m_oelfleck)
zylinder("Oelfleck_2", 0.33, 0.012, 5.5, 0.012, -1.2, m_oelfleck)
zylinder("Oelfleck_3", 0.3, 0.012, -9.5, 0.006, 2.6, m_oelfleck)

# ---- Waende mit Fensterbaendern (Nord, West, Sued), Ostwand mit Tor ---------
def wand_mit_fenster(seite, laenge, cx, cz, entlang_x):
    if entlang_x:
        kasten(f"Wand_{seite}_Unten", laenge, 0.3, 3.5, cx, 1.75, cz, m_wand)
        kasten(f"Wand_{seite}_Fenster", laenge, 0.1, 1.8, cx, 4.4, cz + (0.08 if cz > 0 else -0.08), m_hallenglas)
        kasten(f"Wand_{seite}_Oben", laenge, 0.3, 0.7, cx, 5.65, cz, m_wand)
        for i, fx in enumerate(range(-16, 17, 4)):
            kasten(f"Wand_{seite}_Sprosse_{i}", 0.15, 0.3, 1.8, fx, 4.4, cz, m_stahl)
        kasten(f"Wand_{seite}_Quersprosse", laenge, 0.24, 0.08, cx, 4.4, cz, m_stahl)
        # Abwaschbarer Sockelanstrich bis 1.2 m: die kraeftigste Horizontale jeder Werkstattwand
        kasten(f"Relief_{seite}_Sockel", laenge, 0.08, 1.2, cx, 0.6, cz + (-0.2 if cz > 0 else 0.2), m_sockel)
        kasten(f"Relief_{seite}_Traeger", laenge, 0.26, 0.55, cx, 3.55, cz + (-0.25 if cz > 0 else 0.25), m_relief)
        for i, px in enumerate(range(-15, 16, 3)):
            kasten(f"Relief_{seite}_Pilaster_{i}", 0.28, 0.14, 3.3, px, 1.75, cz + (-0.2 if cz > 0 else 0.2), m_relief)
    else:
        kasten(f"Wand_{seite}_Unten", 0.3, laenge, 3.5, cx, 1.75, cz, m_wand)
        kasten(f"Wand_{seite}_Fenster", 0.1, laenge, 1.8, cx - 0.08, 4.4, cz, m_hallenglas)
        kasten(f"Wand_{seite}_Oben", 0.3, laenge, 0.7, cx, 5.65, cz, m_wand)
        for i, fz in enumerate(range(-8, 9, 4)):
            kasten(f"Wand_{seite}_Sprosse_{i}", 0.3, 0.15, 1.8, cx, 4.4, fz, m_stahl)
        kasten(f"Wand_{seite}_Quersprosse", 0.24, laenge, 0.08, cx, 4.4, cz, m_stahl)
        kasten(f"Relief_{seite}_Sockel", 0.08, laenge, 1.2, cx + 0.2, 0.6, cz, m_sockel)
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
    # gelber Anfahrschutz am Stuetzenfuss (Werkstatt-typische Kontur + Farbe)
    kasten(f"Stuetze_Nord_{i}_schutz", 0.38, 0.38, 0.55, sx, 0.275, -9.7, m_markierung, fase=0.03)
    kasten(f"Stuetze_Sued_{i}_schutz", 0.38, 0.38, 0.55, sx, 0.275, 9.7, m_markierung, fase=0.03)
for i, sz in enumerate((-6.7, 0, 6.7)):
    kasten(f"Stuetze_West_{i}", 0.3, 0.3, 6, -16.7, 3, sz, m_stahl)
    kasten(f"Stuetze_West_{i}_schutz", 0.38, 0.38, 0.55, -16.7, 0.275, sz, m_markierung, fase=0.03)

kasten("Dach_Decke", 34, 20, 0.12, 0, 6.3, 0, m_decke, fase=0)
for i, tx in enumerate((-12, -6, 0, 6, 12)):
    i_traeger(f"Dachbinder_{i}", 19.4, 0.5, 0.24, tx, 5.85, 0, m_stahlhell, achse="z")
for i in range(11):
    kasten(f"Dach_Rippe_{i}", 34, 0.1, 0.2, 0, 6.14, -9 + i * 1.8, m_relief, fase=0)
for i, (ox, oz) in enumerate(((-12, -4.6), (-4, -4.6), (4, -4.6), (12, -4.6),
                              (-12, 4.4), (-4, 4.4), (4, 4.4), (12, 4.4))):
    kasten(f"Dach_Oberlicht_{i}", 2.4, 1.5, 0.06, ox, 6.21, oz, m_fenster, fase=0)
    kasten(f"Dach_Oberlicht_{i}_rahmen", 2.6, 1.7, 0.05, ox, 6.19, oz, m_relief, fase=0)

# ---- Haustechnik unter der Decke: Rohre, Kabeltrasse, Sprinkler, Lueftung ---
zylinder("Rohr_Blau", 0.1, 33.7, 0, 5.15, -9.3, m_blau, achse="x")
zylinder("Rohr_Grau", 0.09, 33.7, 0, 4.85, -9.0, m_stahlhell, achse="x")
zylinder("Rohr_Orange", 0.07, 33.7, 0, 4.6, -9.15, m_orange, achse="x")
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
# Lichtbaender statt Pendel-Kegel: eine Instandhaltungshalle wird mit durchgehenden
# Leuchtenbaendern unter den Dachbindern beleuchtet. Vier Reihen auf den Rippen
# 2/4/6/8 (z +-5.4, +-1.8), je drei Baender a 7 m; die Luecke bei x -12.9 haelt
# die Kranbahnbruecke (y 4.47..5.09) frei, die Reihen +-1.8 halten die
# Fahrleitungshaenger auf z 0 frei.
for zi, lz in enumerate((-5.4, -1.8, 1.8, 5.4)):
    for xi, lx in enumerate((-8.0, 0.0, 8.0)):
        kasten(f"Lichtband_{zi}_{xi}", 7.0, 0.18, 0.10, lx, 4.95, lz, m_stahlhell, fase=0.01)
        kasten(f"Lichtband_{zi}_{xi}_wanne", 6.8, 0.12, 0.02, lx, 4.89, lz, m_fenster, fase=0)
        for k, hx in enumerate((lx - 3.0, lx + 3.0)):
            zylinder(f"Lichtband_{zi}_{xi}_haenger_{k}", 0.012, 1.04, hx, 5.52, lz, m_dunkel)  # 5.00..6.04

# ---- Empore an der Westwand mit Treppe --------------------------------------
kasten("Empore_Plattform", 3.0, 10, 0.15, -15.5, 3.05, -5, m_riffel)
kasten("Empore_Blende", 0.06, 10, 0.22, -14.02, 3.05, -5, m_relief, fase=0)
for i, ez in enumerate((-9.5, -6.5, -3.5, -0.6)):
    kasten(f"Empore_Stuetze_{i}", 0.2, 0.2, 3.0, -14.2, 1.5, ez, m_stahl)
for i, gz in enumerate((-9.5, -7.2, -4.9, -2.6, -0.4)):
    zylinder(f"Empore_Gelaenderpfosten_{i}", 0.03, 1.0, -14.1, 3.6, gz, m_dunkel)
zylinder("Empore_Handlauf", 0.035, 9.6, -14.1, 4.1, -5, m_dunkel, achse="z")
def treppe(name, x, z, hoehe, richtung_z=1, breite=1.0, mat=None):
    """Offene Stahltreppe: Trittstufen auf zwei Wangen, dazu ein abgestuetztes Gelaender.

    Frueher war jede Stufe ein Vollquader vom Boden bis zur Stufenhoehe — die Treppe
    stand damit als massiver dunkler Keil im Bild und verriegelte bei Station 3 die
    halbe Ansicht. Jetzt traegt sie sich auf Wangen und man sieht hindurch."""
    mat = mat or m_stahlhell  # heller Stahl: dunkler Stahl liest als schwarzes Band im Bild
    stufen = max(4, int(hoehe / 0.19))
    lauf = hoehe * 1.6
    tiefe = lauf / stufen
    winkel = 0.5586  # atan(hoehe / lauf) — konstant, weil lauf = 1.6 * hoehe
    for i in range(stufen):
        sh = hoehe * (i + 1) / stufen
        sz = z + richtung_z * (lauf / 2 - lauf * (i + 0.5) / stufen)
        kasten(f"{name}_stufe_{i}", breite, tiefe + 0.02, 0.05, x, sh - 0.025, sz, m_riffel, fase=0)
        # Setzstufe schliesst die Vorderkante, damit die Treppe nicht durchsichtig wirkt
        kasten(f"{name}_setzstufe_{i}", breite, 0.03, tiefe * 0.85, x, sh - 0.05 - tiefe * 0.42,
               sz + richtung_z * tiefe / 2, mat, fase=0)
    for seite in (-1, 1):
        wx = x + seite * (breite / 2 + 0.03)
        kasten(f"{name}_wange_{'w' if seite < 0 else 'o'}", 0.05, (lauf ** 2 + hoehe ** 2) ** 0.5,
               0.30, wx, hoehe / 2 - 0.02, z, mat, fase=0, drehung=(richtung_z * winkel, 0, 0))
    for seite in (-1, 1):
        gx = x + seite * (breite / 2 + 0.03)
        zylinder(f"{name}_handlauf_{'w' if seite < 0 else 'o'}", 0.03,
                 (lauf ** 2 + hoehe ** 2) ** 0.5, gx, hoehe / 2 + 0.9, z, m_markierung)
        h = bpy.context.active_object
        h.rotation_mode = "QUATERNION"
        h.rotation_quaternion = Vector((0, richtung_z * lauf, hoehe)).to_track_quat("Z", "Y")
        for t in (0.05, 0.35, 0.65, 0.95):  # Gelaenderpfosten bis unter die Handlaufenden
            zylinder(f"{name}_gpfosten_{'w' if seite < 0 else 'o'}_{t}".replace(".", ""), 0.02, 0.82,
                     gx, hoehe * t + 0.45, z + richtung_z * (lauf / 2 - lauf * t), m_markierung)


treppe("Empore_Treppe", -15.5, 1.0, 3.05, richtung_z=1)
kasten("Empore_Kiste_1", 0.6, 0.55, 0.5, -15.9, 3.4, -8.4, m_blau)
kasten("Empore_Kiste_2", 0.45, 0.4, 0.4, -15.3, 3.33, -7.9, m_orange)
kasten("Empore_Palette", 1.2, 1.0, 0.12, -15.5, 3.19, -2.5, m_objekt, fase=0)
kasten("Empore_Palette_Kiste", 0.5, 0.45, 0.45, -15.6, 3.48, -2.6, m_wand)
# Lagerzone unter der Empore: Wandregal + Faesser
kasten("UnterEmpore_Wange_1", 0.08, 0.9, 1.9, -16.35, 0.95, -4.6, m_blau)
kasten("UnterEmpore_Wange_2", 0.08, 0.9, 1.9, -16.35, 0.95, -2.4, m_blau)
for i, ry in enumerate((0.4, 1.0, 1.6)):
    kasten(f"UnterEmpore_Brett_{i}", 0.08, 2.1, 0.05, -16.35, ry, -3.5, m_dunkel, fase=0)
for i, (bz, bm) in enumerate(((-4.2, m_orange), (-3.5, m_wand), (-2.8, m_blau))):
    kasten(f"UnterEmpore_Kiste_{i}", 0.4, 0.5, 0.4, -16.3, 0.65, bz, bm, fase=0)
fass("UnterEmpore_Fass_1", -16.2, -1.3, 0, m_blau)
fass("UnterEmpore_Fass_2", -15.8, -0.8, 0, m_dunkel)

# ---- Gleis + Untersuchungsgrube ---------------------------------------------
# Flachbodengleis: in einer Instandhaltungshalle liegen die Schienen BUENDIG im
# Boden (Schienenkopf 6 mm ueber der Deckschicht), ohne Schotter und ohne
# sichtbare Schwellen. Vorher lag die Schienenoberkante 15.5 cm ueber dem Boden
# auf Schwellen wie auf freier Strecke.
SCHIENE_OK = 0.012
GLEIS_SENKUNG = 0.155 - SCHIENE_OK
kasten("Gleis_Schiene_Nord", 38, 0.15, 0.15, 2, SCHIENE_OK - 0.075, -0.7, m_schiene, fase=0)
kasten("Gleis_Schiene_Sued", 38, 0.15, 0.15, 2, SCHIENE_OK - 0.075, 0.7, m_schiene, fase=0)
# Vorfeld-Platte hinter dem Tor, damit das Gleis nicht im Nichts endet
kasten("Tor_Vorfeld", 5.0, 5.0, 0.2, 19.5, -0.1, 0, m_gleiszone, fase=0)

# Grube liegt UNTER dem Zug — als ECHTE Vertiefung (Boden abgesenkt, Waende, Licht)
kasten("Grube_Boden", 7, 2.0, 0.06, -3.5, -0.72, 0, m_grube, fase=0)
kasten("Grube_Wand_Nord", 7, 0.1, 0.70, -3.5, -0.35, -0.95, m_grube, fase=0)   # Oberkante 0.000
kasten("Grube_Wand_Sued", 7, 0.1, 0.70, -3.5, -0.35, 0.95, m_grube, fase=0)
kasten("Grube_Wand_West", 0.1, 1.8, 0.70, -6.95, -0.35, 0, m_grube, fase=0)
kasten("Grube_Wand_Ost", 0.1, 1.8, 0.70, -0.05, -0.35, 0, m_grube, fase=0)
kasten("Grube_Quersteg_1", 0.4, 1.9, 0.04, -5.3, -0.015, 0, m_stahl, fase=0)   # Gitterrost buendig
kasten("Grube_Quersteg_2", 0.4, 1.9, 0.04, -1.8, -0.015, 0, m_stahl, fase=0)
kasten("Grube_Leuchte_Nord", 5.5, 0.06, 0.06, -3.5, -0.25, -0.82, m_fenster, fase=0)
kasten("Grube_Leuchte_Sued", 5.5, 0.06, 0.06, -3.5, -0.25, 0.82, m_fenster, fase=0)
# Grubenleiter fuehrt in die Vertiefung (an der Ost-Innenwand)
for i, lz in enumerate((-0.35, 0.35)):
    kasten(f"Grube_Leiter_holm_{i}", 0.05, 0.05, 1.4, -0.18, 0.0, lz, m_orange, fase=0)
for i in range(4):
    kasten(f"Grube_Leiter_sprosse_{i}", 0.04, 0.66, 0.04, -0.18, -0.55 + i * 0.28, 0, m_orange, fase=0)


def warnstreifen(name, laenge, x, z, entlang_x=True):
    n = int(laenge / 0.5)
    for i in range(n):
        m = m_markierung if i % 2 == 0 else m_dunkel
        if entlang_x:
            kasten(f"{name}_{i}", 0.5, 0.14, 0.012, x - laenge / 2 + 0.25 + i * 0.5, 0.04, z, m, fase=0)
        else:
            kasten(f"{name}_{i}", 0.14, 0.5, 0.012, x, 0.04, z - laenge / 2 + 0.25 + i * 0.5, m, fase=0)


warnstreifen("Grube_Kante_Nord", 7, -3.5, -1.12)
warnstreifen("Grube_Kante_Sued", 7, -3.5, 1.12)
warnstreifen("Grube_Kante_West", 2, -7.05, 0, entlang_x=False)
warnstreifen("Grube_Kante_Ost", 2, 0.05, 0, entlang_x=False)

# ---- Triebzug v3: realistische Hoehe (3 m Dachkante), sichtbare Raeder ------
m_zugglas = material("ZugGlas", (0.045, 0.06, 0.075), rauheit=0.06)
ZUG_X = 0.5
# Wagenkasten 0.20 m angehoben (Unterkante 0.75 -> 0.95) und der Unterbau schmaler:
# vorher steckte die Radoberkante 0.165 m im Korpus und das Drehgestell in der Schiene.
# Jetzt stehen die Raeder frei unter dem Wagen — die Voraussetzung dafuer, dass man
# ueberhaupt ein Drehgestell erkennen kann.
kasten("Triebzug_Unterbau", 14, 1.1, 0.3, ZUG_X, 0.8, 0, m_unterflur)
# Drehzapfenabstand nach Vorbild: der ICE 4 hat 19.50 m bei 29.106 m Wagenlaenge,
# also 67 Prozent, Ueberhang je Ende 16.5 Prozent. Unsere Drehgestelle standen auf
# 10.0 m bei 18.9 m Laenge (53 Prozent, Ueberhang 23.5) — dadurch wirkte der Wagen
# kuerzer und die Enden zu lang. Mit -5.9 / 6.9 sind es 12.8 m und 16.1 Prozent.
for i, bx in enumerate((-5.9, 6.9)):
    # Aussenliegender Drehgestellrahmen mit Achslagern, Primaerfedern, Bremsscheiben
    # und Sandstreurohren — vorher war das eine dunkle Platte mit vier Scheiben davor.
    # Rahmen auf y 0.80..0.95 gehoben: vorher kappte er die Raeder 5.5 cm ueber der
    # Radmitte und sie lasen als Hufeisen. Die Achsfuehrung ueberbrueckt die Luecke
    # zum Achslager — ohne sie waere der Rahmen ein Schweber. In der Mitte sitzen
    # jetzt Fahrmotor und Bremszangen statt eines Durchblicks.
    kasten(f"Triebzug_DG_{i}_quertraeger", 0.6, 2.0, 0.26, bx, 0.63, 0, m_stahl)
    zylinder(f"Triebzug_DG_{i}_motor", 0.2, 0.8, bx + 0.45, 0.62, 0, m_stahl, achse="z")
    for s, seite in ((-1, "nord"), (1, "sued")):
        kasten(f"Triebzug_DG_{i}_rahmen_{seite}", 2.3, 0.16, 0.15, bx, 0.875, s * 0.98, m_stahl)
        for j, rx in enumerate((-0.7, 0.7)):
            kasten(f"Triebzug_DG_{i}_achslager_{seite}_{j}", 0.3, 0.34, 0.24, bx + rx, 0.55, s * 1.0, m_unterflur)
            kasten(f"Triebzug_DG_{i}_fuehrung_{seite}_{j}", 0.14, 0.16, 0.22, bx + rx, 0.74, s * 0.98, m_stahl)
            kasten(f"Triebzug_DG_{i}_bremszange_{seite}_{j}", 0.12, 0.08, 0.28, bx + rx, 0.58, s * 0.505, m_stahl)
            zylinder(f"Triebzug_DG_{i}_feder_{seite}_{j}", 0.1, 0.14, bx + rx, 0.74, s * 1.06, m_stahlhell)
            zylinder(f"Triebzug_DG_{i}_sandrohr_{seite}_{j}", 0.03, 0.42, bx + rx, 0.4, s * 0.88, m_dunkel)
            zylinder(f"Triebzug_Rad_{i}_{j}_{seite}", 0.4, 0.12, bx + rx, 0.535, s * 0.78, m_unterflur, achse="z", ecken=32)
            zylinder(f"Triebzug_Radscheibe_{i}_{j}_{seite}", 0.24, 0.13, bx + rx, 0.535, s * 0.78, m_stahlhell, achse="z", ecken=32)
            zylinder(f"Triebzug_DG_{i}_bremsscheibe_{seite}_{j}", 0.24, 0.05, bx + rx, 0.535, s * 0.45, m_stahlhell, achse="z")
    for j, rx in enumerate((-0.7, 0.7)):
        zylinder(f"Triebzug_DG_{i}_welle_{j}", 0.06, 2.1, bx + rx, 0.535, 0, m_stahl, achse="z")
# Unterflur-Aggregate: unter dem Zug lag 7.4 m Bauchraum voellig leer, obwohl die
# begehbare Untersuchungsgrube genau dorthin blickt. Alle Kaesten haengen mit
# Oberkante 0.65 am Untergestell und bleiben bei |z| <= 0.85 innerhalb der
# Drehgestellrahmen und ausserhalb der Grubenwaende.
kasten("Triebzug_UF_Trafo", 2.6, 1.55, 0.4, -1.8, 0.45, 0, m_unterflur, fase=0.03)
kasten("Triebzug_UF_Umrichter", 2.4, 1.5, 0.38, 1.9, 0.46, 0, m_dunkel, fase=0.03)
kasten("Triebzug_UF_Batterie", 1.15, 1.2, 0.3, 3.7, 0.5, 0, m_stahl, fase=0.03)
kasten("Triebzug_UF_Kasten_West", 0.9, 1.2, 0.3, -6.0, 0.5, 0, m_unterflur, fase=0.03)
kasten("Triebzug_UF_Luftpresser", 0.8, 1.2, 0.32, 7.05, 0.49, 0, m_dunkel, fase=0.03)
zylinder("Triebzug_UF_Lufttank", 0.17, 1.2, -0.1, 0.48, 0.7, m_stahl, achse="x")
for s in (-1, 1):
    kasten(f"Triebzug_UF_Gitter_{s}", 1.1, 0.03, 0.26, -1.8, 0.46, s * 0.79, m_stahlhell, fase=0)
kasten("Triebzug_Korpus", 14, 2.4, 1.75, ZUG_X, 1.825, 0, m_zugweiss, fase=0.06)
# Schmale hohe Linie statt breiter Bauchbinde: beim Vorbild sind es rund 10 Prozent
# der Flankenhoehe knapp unter den Fenstern, unterhalb davon ist alles weiss.
kasten("Triebzug_Streifen_Nord", 14, 0.06, 0.18, ZUG_X, 1.64, -1.23, m_zug, fase=0)
kasten("Triebzug_Streifen_Sued", 14, 0.06, 0.18, ZUG_X, 1.64, 1.23, m_zug, fase=0)
# Schmales Fensterband oben (viel Weiss darunter), Tueren stechen mit weissem Rahmen heraus
# Flanke: die 0.77 m hohe, 14 m lange weisse Leerflaeche unter dem Fensterband bekommt
# Lueftungsgitter, Wartungsklappen, Tankstutzen und zwei umlaufende Sicken. Die
# Laengselemente sind dreigeteilt, damit sie nicht durch die beiden Tueren laufen
# (belegt: x -3.08..-2.02 und 4.62..5.68).
# Flanke neu proportioniert. Vorher: Fensterband nur 0.42 m hoch dicht unter der
# Dachkante, darunter 0.67 m leeres Weiss ueber 14 m — 56 Prozent der Flanke waren weiss
# und der Zug las sich als Container. Jetzt ist das Band 0.72 m hoch und tiefer gesetzt,
# die Bauchbinde 0.46 m breit. Das Band ist in drei Laeufe zwischen den Tueren geteilt,
# damit keine Rest-Schlitze von 30 cm mehr entstehen; die Pfosten werden je Lauf
# gleichmaessig eingerechnet statt fest gesetzt.
# Ein durchgehendes Band; die beiden Tueren teilen es auf natuerliche Weise in drei
# Laeufe, sodass mit nur sechs Pfosten neun gleich breite Scheiben zu 0.97 m entstehen.
# Vorher lagen dort vier Rest-Schlitze zwischen 0.32 und 0.54 m.
FLANKE_ABSCHNITTE = ((3.32, -4.74), (6.64, 1.30), (1.82, 6.59))
DACHRAND_ABSCHNITTE = ((3.42, -4.79), (6.64, 1.30), (1.82, 6.59))
for seite, sz in (("nord", -1.24), ("sued", 1.24)):
    aussen = 1 if sz > 0 else -1
    fz = sz * 0.9758  # Fensterband 3 cm eingelassen -> echte Schattenkante an den Pfosten
    kasten(f"Triebzug_Fensterband_{seite}", 11.84, 0.05, 0.58, 0.73, 2.15, fz, m_zugglas, fase=0)
    for i, px in enumerate((-4.13, -0.97, 0.17, 1.3, 2.43, 3.56)):
        kasten(f"Triebzug_Fensterpfosten_{seite}_{i}", 0.16, 0.06, 0.58, px, 2.15, sz, m_zugweiss, fase=0)
    for i, (fl, fx) in enumerate(FLANKE_ABSCHNITTE):
        kasten(f"Triebzug_Fensterleiste_u_{seite}_{i}", fl, 0.03, 0.05, fx, 1.83, sz, m_zugweiss, fase=0)
        kasten(f"Triebzug_Fensterleiste_o_{seite}_{i}", fl, 0.03, 0.05, fx, 2.47, sz, m_zugweiss, fase=0)
    # Dachrandprofil und Regenrinne: die kraeftigste Horizontale der Seitenansicht,
    # deckt zugleich den Absatz zwischen Dach (|z| 1.15) und Flanke (1.20) ab.
    for i, (dl, dcx) in enumerate(DACHRAND_ABSCHNITTE):
        kasten(f"Triebzug_Dachfascie_{seite}_{i}", dl, 0.12, 0.1, dcx, 2.65, sz * 0.9839, m_zugdach, fase=0.03)
        kasten(f"Triebzug_Regenrinne_{seite}_{i}", dl, 0.05, 0.03, dcx, 2.585, sz * 0.9919, m_dunkel, fase=0)
    # Senkrechte Stossleisten gliedern die weisse Zone zwischen Bauchbinde und Band
    for i, lx in enumerate((-5.3, -3.6, -1.53, 0.45, 2.5, 5.9)):
        kasten(f"Triebzug_Stossleiste_{seite}_{i}", 0.045, 0.05, 0.3, lx, 1.3, sz * 0.9879, m_zugweiss, fase=0)
    # Gitter zurueckgesetzt, Lamellen davor — vorher steckten die Lamellen dahinter
    for i, gx in enumerate((-4.6, -0.9, 6.4)):
        kasten(f"Triebzug_Gitter_{seite}_{i}", 0.72, 0.03, 0.32, gx, 1.28, sz * 0.9758, m_dunkel, fase=0)
        for j in range(4):
            kasten(f"Triebzug_Gitterlamelle_{seite}_{i}_{j}", 0.68, 0.05, 0.035, gx, 1.1525 + j * 0.085, sz, m_stahlhell, fase=0)
    for i, kx in enumerate((1.9, 4.0)):
        kasten(f"Triebzug_Klappe_{seite}_{i}", 0.8, 0.025, 0.32, kx, 1.28, sz, m_zugweiss, fase=0)
        kasten(f"Triebzug_Klappenfuge_{seite}_{i}", 0.82, 0.02, 0.02, kx, 1.12, sz, m_dunkel, fase=0)
    zylinder(f"Triebzug_Tankstutzen_{seite}", 0.09, 0.06, -1.9, 1.3, sz, m_stahl, achse="z")
    for i, tx in enumerate((-2.55, 5.15)):
        kasten(f"Triebzug_Tuerrahmen_{seite}_{i}", 1.06, 0.07, 1.75, tx, 1.825, sz, m_zugweiss, fase=0)
        kasten(f"Triebzug_Tuer_{seite}_{i}", 0.95, 0.09, 1.65, tx, 1.8, sz, m_stahl, fase=0)
        kasten(f"Triebzug_Tuerfenster_{seite}_{i}", 0.6, 0.14, 0.58, tx, 2.15, sz, m_zugglas, fase=0)
        kasten(f"Triebzug_Tuerfuge_{seite}_{i}", 0.02, 0.04, 1.65, tx, 1.8, sz * 1.05, m_dunkel, fase=0)
        kasten(f"Triebzug_Tuergriff_{seite}_{i}", 0.12, 0.11, 0.04, tx + 0.36, 1.55, sz, m_dunkel, fase=0)
        kasten(f"Triebzug_Trittstufe_{seite}_{i}", 0.95, 0.16, 0.05, tx, 0.93, sz - 0.03 * aussen, m_riffel, fase=0)
        # Gummidichtungen und Statusleuchte — die Tueren lasen als graue Platten
        for s in (-1, 1):
            kasten(f"Triebzug_Tuerdichtung_{seite}_{i}_{s}", 0.035, 0.1, 1.65, tx + s * 0.4725, 1.8, sz, m_gummi, fase=0)
        kasten(f"Triebzug_Tuerleuchte_{seite}_{i}", 0.16, 0.05, 0.05, tx, 2.57, sz * 1.028, m_gruen, fase=0)
    for i, ax in enumerate((-6.0, 3.0)):  # Anschriftenfelder (gegreekt, keine echten Nummern)
        kasten(f"Triebzug_Anschrift_{seite}_{i}", 0.6, 0.01, 0.12, ax, 1.6, sz * 1.008, m_dunkel, fase=0)
# Dachkrone statt flacher Platte: acht duenne Schichten ziehen sich nach oben ein
# (Halbbreite 1.18 -> 1.06 nach w(t) = 1.18 - 0.12*t**1.6). Aus dem Kasten mit
# scharfer Kante wird im Querschnitt eine Roehre — das ist der Unterschied zwischen
# Regionaltriebwagen und ICE. Die Verjuengung ist bewusst flach gewaehlt: bei |z| 1.09,
# wo die sechs Klappbruecken aufsetzen, liegt die Dachflaeche weiterhin auf y 3.00,
# sonst haetten die Bruecken im Leeren geendet.
# Wie beim Bug ohne Fase — eine Fase je Schicht wuerde acht Schattenfugen werfen.
# Dachkrone als EINE glatte Schale. Vorher acht Schichten a 3.75 cm: aus der Totale
# lasen die als Treppe, und direkt hinter dem geloftetem Kopf fiel das doppelt auf.
# Gleiche Kurve w(t) = 1.18 - 0.12*t**1.6 wie bisher (die Kopfschale schliesst mit
# exakt dieser Breite an, die Klappbruecken landen weiterhin bei |z| 1.09 auf ~2.96).
_DK_N = 14
_dk_halb = [(1.18 - 0.12 * (_k / _DK_N) ** 1.6, 2.70 + 0.32 * (_k / _DK_N)) for _k in range(_DK_N + 1)]
_dk_prof = [(-_z, _y) for _z, _y in _dk_halb] + [(_z, _y) for _z, _y in reversed(_dk_halb)]
_dk_verts, _dk_faces = [], []
for _x in (ZUG_X - 6.8, ZUG_X + 6.8):
    for _z, _y in _dk_prof:
        _dk_verts.append((_x, -_z, _y))          # three (x, y, z) -> Blender (x, -z, y)
_dk_n = len(_dk_prof)
for _i in range(_dk_n - 1):
    # Reihenfolge so, dass die Normalen nach AUSSEN zeigen (three.js cullt Rueckseiten)
    _dk_faces.append([_i, _i + 1, _dk_n + _i + 1, _dk_n + _i])
_dk_mesh = bpy.data.meshes.new("Triebzug_Dachkrone")
_dk_mesh.from_pydata(_dk_verts, [], _dk_faces)
_dk_mesh.update()
_dk_mesh.materials.append(m_zugdach)
for _p in _dk_mesh.polygons:
    _p.use_smooth = True
_dk_mesh.uv_layers.new(name="UVMap")
_dk_obj = bpy.data.objects.new("Triebzug_Dachkrone", _dk_mesh)
bpy.context.collection.objects.link(_dk_obj)
bpy.context.view_layer.objects.active = _dk_obj
# Dachtechnik auf hellen Stahl umgestellt — auf dem jetzt dunklen Dach waere sie
# in m_dunkel unsichtbar geworden. Kontrast dreht sich um, Geometrie bleibt.
# Dachdurchfuehrung mit Kabel zum Stromabnehmer: die alte Dachleitung lief auf z -0.8
# quer am Panto (z 0) vorbei und beruehrte ihn nie — es gab keinen Weg vom Schleifstueck
# ins Fahrzeug. Die Durchfuehrung sitzt in der Luecke zwischen Klima_0 und dem Panto.
zylinder("Triebzug_Dachdurchfuehrung", 0.09, 0.34, -3.05, 3.17, -0.55, m_stahlhell)
kasten("Triebzug_Dachdurchfuehrung_flansch", 0.3, 0.3, 0.05, -3.05, 3.025, -0.55, m_dunkel, fase=0)
rohr_mit_bogen("Triebzug_Dachkabel", [(-3.05, 3.34, -0.55), (-2.7, 3.4, -0.48), (-2.38, 3.33, -0.4)], 0.035, m_dunkel)
# Dachrand, Laufstege und Blechstoesse — die sechs Klappbruecken endeten auf blankem Blech
for seite, dz in (("nord", -1.0), ("sued", 1.0)):
    kasten(f"Triebzug_Laufsteg_{seite}", 12.8, 0.3, 0.02, ZUG_X, 3.01, dz * 0.95, m_riffel, fase=0)
for i, nx in enumerate((-5.6, -2.55, -1.35, 2.05, 3.45, 6.3, 6.95)):
    kasten(f"Triebzug_Dachnaht_{i}", 0.05, 1.4, 0.012, nx, 3.006, 0, m_stahlhell, fase=0)
for i, (ex, ez) in enumerate(((-5.9, -0.6), (-5.9, 0.6), (6.6, -0.6), (6.6, 0.6))):
    zylinder(f"Triebzug_Erdung_{i}", 0.05, 0.04, ex, 3.02, ez, m_markierung)
for i, lx in enumerate((3.2, 6.5)):
    kasten(f"Triebzug_Dachluke_{i}", 0.6, 0.6, 0.035, lx, 3.017, 0, m_stahl, fase=0.01)
# Klimaanlagen mit Sockelrahmen, Ansaug- und Ausblasgittern statt nackter Platten
for i, kx in enumerate((-4, 0.5, 5)):
    kasten(f"Triebzug_Klima_{i}_sockel", 1.56, 1.46, 0.06, kx, 3.02, 0, m_dunkel, fase=0)
    kasten(f"Triebzug_Klima_{i}", 1.44, 1.44, 0.24, kx, 3.11, 0, m_stahlhell)
    for s in (-1, 1):
        kasten(f"Triebzug_Klima_{i}_gitter_{s}", 0.05, 1.16, 0.14, kx + s * 0.72, 3.09, 0, m_dunkel, fase=0)
    kasten(f"Triebzug_Klima_{i}_ausblas", 0.86, 0.86, 0.04, kx, 3.215, 0, m_dunkel, fase=0)
    for j in range(5):
        kasten(f"Triebzug_Klima_{i}_steg_{j}", 0.82, 0.09, 0.03, kx, 3.232, -0.34 + j * 0.17, m_stahlhell, fase=0)
# Scherenstromabnehmer: er schwebte 0.23 m ueber dem Blech und kreuzte sich zum X, weil
# Unter- und Oberarm gespiegelte Vorzeichen hatten. Jetzt tragen ihn vier Isolatoren, und
# beide Arme teilen sich einen Gelenkpunkt (Knie bei x -2.78, y 3.78).
for i, (px, pz) in enumerate(((-2.38, -0.4), (-2.38, 0.4), (-1.62, -0.4), (-1.62, 0.4))):
    zylinder(f"Triebzug_Panto_Isolator_{i}", 0.045, 0.24, px, 3.12, pz, m_stahlhell)
    for j in range(3):
        zylinder(f"Triebzug_Panto_Isolator_{i}_schirm_{j}", 0.085, 0.03, px, 3.05 + j * 0.07, pz, m_stahlhell)
for i, pz in enumerate((-0.4, 0.4)):
    kasten(f"Triebzug_Panto_Holm_{i}", 0.95, 0.08, 0.09, -2.0, 3.285, pz, m_stahlhell, fase=0)
    zylinder(f"Triebzug_Panto_Fusslager_{i}", 0.05, 0.1, -1.55, 3.33, pz, m_stahlhell, achse="z")
for i, px in enumerate((-2.38, -1.62)):
    kasten(f"Triebzug_Panto_Querholm_{i}", 0.08, 0.88, 0.09, px, 3.285, 0, m_stahlhell, fase=0)
kasten("Triebzug_Panto_Unterarm", 0.09, 0.09, 1.31, -2.165, 3.555, 0, m_dunkel, drehung=(0, -1.22, 0), fase=0)
kasten("Triebzug_Panto_Oberarm", 0.06, 0.06, 0.98, -2.315, 3.94, 0, m_dunkel, drehung=(0, 1.24, 0), fase=0)
zylinder("Triebzug_Panto_Knielager", 0.055, 0.2, -2.78, 3.78, 0, m_stahlhell, achse="z")
kasten("Triebzug_Panto_Absenkzylinder", 0.4, 0.09, 0.09, -1.95, 3.47, 0.24, m_markierung, drehung=(0, -0.6, 0), fase=0)
kasten("Triebzug_Panto_Wippe", 0.1, 1.3, 0.06, -1.85, 4.105, 0, m_dunkel, fase=0)
for i, sx in enumerate((-1.96, -1.74)):
    kasten(f"Triebzug_Panto_Schleifleiste_{i}", 0.07, 1.1, 0.045, sx, 4.155, 0, m_stahlhell, fase=0)
for i, hz in enumerate((-0.68, 0.68)):
    kasten(f"Triebzug_Panto_Horn_{i}", 0.3, 0.26, 0.05, -1.85, 4.16, hz, m_dunkel,
           drehung=(-0.6 if hz < 0 else 0.6, 0, 0), fase=0)
# Bremswiderstand mit offenem Rippenpaket — sein einziges Erkennungsmerkmal
kasten("Triebzug_Widerstand_sockel", 1.06, 1.16, 0.1, -5.3, 3.05, 0, m_dunkel, fase=0)
for j in range(11):
    kasten(f"Triebzug_Widerstand_rippe_{j}", 0.05, 1.02, 0.3, -5.72 + j * 0.084, 3.25, 0, m_stahlhell, fase=0)
for i, wx in enumerate((-5.78, -4.82)):
    kasten(f"Triebzug_Widerstand_wange_{i}", 0.05, 1.1, 0.36, wx, 3.28, 0, m_dunkel, fase=0)
kasten("Triebzug_Widerstand_haube", 1.1, 1.16, 0.05, -5.3, 3.485, 0, m_dunkel, fase=0)
zylinder("Triebzug_Antenne_1", 0.05, 0.35, 3.2, 3.17, 0.5, m_stahlhell)
zylinder("Triebzug_Antenne_2", 0.05, 0.35, -0.6, 3.17, -0.5, m_stahlhell)
for i, (ax, az) in enumerate(((3.2, 0.5), (-0.6, -0.5))):
    kasten(f"Triebzug_Antennenfuss_{i}", 0.16, 0.16, 0.03, ax, 3.015, az, m_stahlhell, fase=0)
# Fuehrerstaende an BEIDEN Enden; rote Bauchbinde laeuft ueber die Kabinenflanke durch
def fuehrerstand(kennung, r):
    """r = +1 fuer das Ost-Ende (Front), -1 fuer das West-Ende (Heck).

    Der Kopf ist EINE geloftete Schale vom Bugboden bis zur Dachkante. Es gibt keine
    Kabine, keine Maske und keine Nase als eigene Koerper mehr — beim Vorbild faellt
    das Dach nach vorn ab, geht ohne Absatz in die Scheibe ueber und laeuft weiter in
    den Bug. Frontscheibe, Leuchtenfeld, rote Bauchbinde und Dachblech sind deshalb
    MATERIALZONEN auf dieser Flaeche, keine aufgesetzten Bauteile.

    VIER REGELN, die je einmal teuer verletzt wurden:

    (1) KOORDINATEN. _TAB und _profil() rechnen in WELT-x, kasten() und zylinder()
        dagegen in 0.5 + u. Wer ein Teil auf die Haut setzt, braucht u = X_haut - 0.5.
        Ohne das stehen Lampen und Wischer einen halben Meter vor der Nase in der Luft —
        und der Pruefer meldet es nicht, weil sie sich gegenseitig halten.

    (2) ANSCHLUSS AN DEN WAGENKASTEN. Der Kasten reicht bis x 7.5 mit Halbbreite 1.20,
        die Dachkrone bis 7.3. Die Schale muss INNERHALB davon beginnen und von 1.20
        aus verjuengen. Beginnt sie weiter vorn oder schmaler, steht der Kasten seitlich
        vor ihr und erzeugt genau die Schulterkante, die den Kopf als aufgesetzte Beule
        lesen laesst.

    (3) VOLLKOERPER. Ein Bauteil mit kleinerem |x| als die umgebende Schalenflaeche
        verschwindet restlos darin (so wurde einmal die Frontscheibe unsichtbar). Die
        rote Bauchbinde ist EINE Zone mit EINER Vorderkante; ueber zwei Schichten gelegt
        zerfaellt sie in Stufen und der Bug liest als Tortenetage.

    (4) MATERIALGRENZEN. Eine schraege Grenze kann nur entlang Ringkanten laufen und
        treppt sonst. Gegenmittel ist Aufloesung — mehr Ringe und Bogenspalten —, nicht
        eine flachere Kurve. Dieselbe Lehre wie frueher bei den gestapelten Nasenschichten,
        wo eine Fase je Schicht acht Schattenfugen warf.

    Formregel des Nutzers, die den Durchbruch brachte: es geht vom Dach schraeg herunter
    und bildet unten eine runde Spitze. Der vorderste Punkt liegt also TIEF, nicht auf
    halber Hoehe, und im Grundriss ist die Stirn breit und stumpf — eine Ellipse mit
    kurzer x-Halbachse, kein Halbkreis, der zwangslaeufig spitz zulaeuft.
    """
    import math as _m


    # Stuetzstellen (Hoehe y, vordere Halbbreite, vorderster Punkt in WELT-x).
    _TAB = ((0.60, 0.82, 10.02),  # Kinn — die Spitze faellt SENKRECHT zum Boden
            (0.74, 0.95, 10.09),
            (0.88, 1.01, 10.12),  # Scheitel — GANZ unten, direkt ueber dem Kinn
            (1.05, 1.035, 10.08),
            (1.25, 1.05, 9.93),
            (1.35, 1.055, 9.81),  # Ende der Spitzenrundung — ab hier ist die Schraege
            (1.50, 1.06, 9.61),   # eine GERADE: alle Stuetzen bis zur
            (1.75, 1.07, 9.28),   # Scheibenoberkante liegen kollinear (53 Grad)
            (1.95, 1.08, 9.01),
            (2.12, 1.09, 8.79),   # Scheibenunterkante — liegt AUF der Geraden
            (2.45, 1.10, 8.35),
            (2.70, 1.08, 8.02),   # Scheibenoberkante — Ende der Geraden
            (2.88, 1.03, 7.72),    # Dachanlauf
            (3.02, 0.90, 7.45))

    _BOGEN = 30
    _TAPER = 10
    _RUECK = 7.30
    _ELL = 0.62      # x-Halbachse des Bugbogens als Anteil der Halbbreite
    _N = 3.4         # Superellipsen-Exponent oben: 2 waere eine Ellipse (Ei). 3.4 macht
                     # die Stirn zum fast ebenen Schild mit engen Schulterkanten.

    def _n(y):
        """Exponent je Hoehe: oben 3.4 (kantiges Schild), unterhalb der Binde weich
        auf 2.1 (RUNDE Spitze wie im Werkstattfoto — dort ist der Bug unten eine
        breite, weiche Rundung, kein Kasten). Uebergang zwischen 0.95 und 1.50."""
        if y <= 0.95:
            return 2.1
        if y >= 1.50:
            return _N
        return 2.1 + (_N - 2.1) * (y - 0.95) / 0.55

    def _profil(y):
        """Vordere Halbbreite und vorderster Punkt auf Hoehe y (linear zwischen _TAB)."""
        if y <= _TAB[0][0]:
            return _TAB[0][1], _TAB[0][2]
        for _k in range(len(_TAB) - 1):
            _y0, _w0, _x0 = _TAB[_k]
            _y1, _w1, _x1 = _TAB[_k + 1]
            if y <= _y1:
                _t = (y - _y0) / (_y1 - _y0)
                return _w0 + (_w1 - _w0) * _t, _x0 + (_x1 - _x0) * _t
        return _TAB[-1][1], _TAB[-1][2]

    def _kastenbreite(y):
        """Halbbreite an der Ringhinterkante — folgt exakt dem Wagenkasten (1.20) und
        oberhalb 2.70 der Dachkrone w(t) = 1.18 - 0.12*t**1.6. Waere sie dort konstant
        1.20 geblieben, stuende die Schale 7 cm breiter als das Dach dahinter."""
        if y <= 2.55:
            return 1.20
        if y <= 2.70:
            return 1.20 - 0.02 * (y - 2.55) / 0.15
        return 1.18 - 0.12 * ((y - 2.70) / 0.32) ** 1.6

    _P = 2 * _TAPER + _BOGEN + 1     # Punkte je Ring

    def _spalte(j):
        """Spaltenparameter: (0, f, vorzeichen) fuer die Flanke, (1, theta, 0) fuer den Bug."""
        if j <= _TAPER - 1:
            return 0, j / _TAPER, 1.0
        if j <= _TAPER + _BOGEN:
            return 1, _m.pi / 2 - _m.pi * (j - _TAPER) / _BOGEN, 0.0
        return 0, (_P - 1 - j) / _TAPER, -1.0

    def _punkt(j, y):
        """Punkt der Spalte j auf Hoehe y. Die Flanke laeuft mit Smoothstep von der
        Wagenkastenbreite auf die Bugbreite zu; ohne diese Verjuengung stuende der
        Kasten (Halbbreite 1.20 bis x 7.5) seitlich vor der Schale."""
        _hw, _vor = _profil(y)
        _a = _ELL * _hw
        _xc = _vor - _a
        _art, _p, _vz = _spalte(j)
        if _art == 0:
            _kb = _kastenbreite(y)
            # Spaete Verjuengung (p^1.7): die Flanke bleibt lange auf Kastenbreite
            # und zieht erst kurz vor dem Bogen ein — flache Seitenwand, enge
            # Schulter. Der symmetrische Smoothstep verteilte die Verjuengung ueber
            # die ganze Kopflaenge und rundete die Seite sichtbar aus.
            _g = _p ** 1.7
            _z = _kb + (_hw - _kb) * _g * _g * (3 - 2 * _g)
            return _RUECK + (_xc - _RUECK) * _p, _vz * _z
        _nn = _n(y)
        _cs = _m.cos(_p) ** (2.0 / _nn)
        _sn = _m.copysign(abs(_m.sin(_p)) ** (2.0 / _nn), _m.sin(_p))
        return _xc + _a * _cs, _hw * _sn

    # ---- Farbgrenzen sind NETZKANTEN, keine Auswahl auf waagerechten Ringen ----
    # Vorher liefen die Ringe waagerecht und die rote Binde wurde als Flaechenauswahl
    # darauf eingefaerbt. Eine schraege Grenze kann dann nur an Ring- UND Spaltenkanten
    # springen und liest zwangslaeufig als Treppe — gemessen 4 cm Setzstufe je Spalte.
    # Mehr Aufloesung macht die Treppe nur feiner, nie weg. Jetzt laufen die Ringe
    # ENTLANG der Grenzen: je Spalte werden zehn Ebenen bestimmt, zwischen denen
    # unterteilt wird. Die Grenze ist damit exakt, und das Netz wird dabei kleiner
    # statt groesser (rund 2000 statt 7900 Vierecken je Kopf).
    _zband = [abs(_punkt(_j, 1.40)[1]) for _j in range(_P)]   # Bezugsbreite Bauchbinde
    _zsch = [abs(_punkt(_j, 2.40)[1]) for _j in range(_P)]    # Bezugsbreite Scheibe

    def _ebenen(j):
        """Zehn Hoehen je Spalte, streng steigend. Die Bindenmitte trifft in der Flanke
        (z 1.20) genau den Zierstreifen des Wagenkastens auf 1.64, bleibt ueber die
        Stirn aber nahezu waagerecht auf 1.10 — der Schwung entsteht also aus der Netzform selbst."""
        _yc = 1.10 + 0.54 * (_zband[j] / 1.20) ** 5
        _ys = 2.12 + 0.18 * (_zsch[j] / 1.10) ** 3
        _b = _yc + 0.09
        # Das Leuchtenband folgt der Scheibenunterkante in konstantem Abstand (6 bis
        # 42 cm darunter) und NEIGT sich damit wie sie: innen tief, aussen hoch. Beim
        # Vorbild sitzen die Leuchten als geneigte Felder direkt unter den
        # Scheibenecken — waagerechte Rechtecke lasen als aufgeklebte Pflaster.
        return (0.60, 0.78, _yc - 0.09, _b, _ys - 0.42, _ys - 0.06, _ys, 2.70, 2.88, 3.02)

    _UNTER = (3, 7, 4, 6, 5, 2, 6, 3, 3)   # Unterringe je Ebenenintervall
    _SLOT = (2, 0, 1, 0, 3, 0, 3, 0, 4)    # Grundmaterial je Intervall

    _ebs = [_ebenen(_j) for _j in range(_P)]
    _verts, _ringe = [], []
    for _k in range(len(_UNTER)):
        for _t in range(_UNTER[_k]):
            _f = _t / _UNTER[_k]
            _ring = []
            for _j in range(_P):
                _y = _ebs[_j][_k] + (_ebs[_j][_k + 1] - _ebs[_j][_k]) * _f
                _px, _pz = _punkt(_j, _y)
                _ring.append(len(_verts))
                # three.js (x, y hoch, z quer) -> Blender (x, -z, y)
                _verts.append((0.5 + r * (_px - 0.5), -_pz, _y))
            _ringe.append(_ring)
    _ring = []
    for _j in range(_P):
        _px, _pz = _punkt(_j, _ebs[_j][-1])
        _ring.append(len(_verts))
        _verts.append((0.5 + r * (_px - 0.5), -_pz, _ebs[_j][-1]))
    _ringe.append(_ring)

    _faces, _mats, _weich = [], [], []
    _i = 0
    for _k in range(len(_UNTER)):
        for _t in range(_UNTER[_k]):
            for _j in range(_P):
                _j2 = (_j + 1) % _P
                _f = [_ringe[_i][_j], _ringe[_i][_j2],
                      _ringe[_i + 1][_j2], _ringe[_i + 1][_j]]
                _slot = _SLOT[_k]
                _zs = (_zsch[_j] + _zsch[_j2]) / 2
                if _k == 4:
                    # Das dunkle Feld ist die FORTSETZUNG der Metallschiene nach
                    # unten: dieselben Spalten (0.58..0.72), dieselbe Breite — die
                    # Strebe endet in der Leuchteneinheit (Werkstattfoto). Dazwischen
                    # bleibt die Stirn weiss.
                    _slot = 3 if (0.58 < _zs <= 0.72
                                  and _TAPER <= _j <= _TAPER + _BOGEN) else 0
                elif _k == 5:
                    # Schmale helle Schwelle direkt unter dem Glas
                    _slot = 5 if (_zs <= 0.72 and _TAPER <= _j <= _TAPER + _BOGEN) else 0
                elif _k == 6:
                    # Die Scheibe sitzt MITTIG (|z| bis 0.78) und wird links und
                    # rechts von einer METALLSCHIENE gefasst (0.58..0.72) — wie im
                    # Werkstattfoto. Vorher lief das Glas um die Kopfecke.
                    if _zs <= 0.58 and _TAPER <= _j <= _TAPER + _BOGEN:
                        _slot = 3
                    elif _zs <= 0.72 and _TAPER <= _j <= _TAPER + _BOGEN:
                        _slot = 5
                    else:
                        _slot = 0
                elif _k in (7, 8):
                    # Das dunkle Feld laeuft in Scheibenbreite ueber den Dachanlauf
                    # — das schwarze Dachpanel des ICE 4.
                    _slot = 3 if (_zs <= 0.55 and _TAPER <= _j <= _TAPER + _BOGEN) else _SLOT[_k]
                _faces.append(_f[::-1] if r < 0 else _f)  # Spiegelung dreht die Wicklung
                _mats.append(_slot)
                # Die letzte Spalte ist die flache Rueckwand im Wagenkasten — hart
                # lassen, sonst schmiert die weiche Schattierung ueber die Kante.
                _weich.append(_j != _P - 1)
            _i += 1

    # Deckel oben und unten: die geloftete Schale ist ein offener Schlauch. Der obere
    # Deckel IST die Dachflaeche des Fuehrerhauses, der untere schliesst den Bug.
    for _ring, _oben in ((_ringe[-1], True), (_ringe[0], False)):
        _f = list(_ring) if _oben else list(reversed(_ring))
        _faces.append(_f[::-1] if r < 0 else _f)
        _mats.append(3 if _oben else 2)
        _weich.append(False)

    _mesh = bpy.data.meshes.new(f"Triebzug_Bugschale_{kennung}")
    _mesh.from_pydata(_verts, [], _faces)
    _mesh.update()
    for _mat in (m_zugweiss, m_zug, m_unterflur, m_zugglas, m_zugdach, m_stahlhell):
        _mesh.materials.append(_mat)
    for _p, _slot, _w in zip(_mesh.polygons, _mats, _weich):
        _p.material_index = _slot
        _p.use_smooth = _w
    # ---- Sichtkanten ----
    # "Kantiger": drei Kantenzuege sind ECHTE harte Kanten (sharp_edge-Attribut,
    # von Blender in den Split-Normalen beruecksichtigt und vom glTF-Export
    # uebernommen): Ober- und Unterkante der Scheibe sowie die beiden Schulterkanten
    # vom Leuchtenband bis zur Scheibenoberkante. Zusammen mit der Superellipse liest
    # der Bug damit als Flaechenverbund mit Kanten statt als Ei.
    _rE, _acc = [], 0
    for _u_ in _UNTER:
        _rE.append(_acc)
        _acc += _u_
    _rE.append(_acc)   # _rE[k] = Ringindex der Ebene k
    _scharf = set()
    for _j in range(_TAPER, _TAPER + _BOGEN):
        if (_zsch[_j] + _zsch[_j + 1]) / 2 <= 0.58:
            _scharf.add(frozenset((_ringe[_rE[6]][_j], _ringe[_rE[6]][_j + 1])))
            _scharf.add(frozenset((_ringe[_rE[7]][_j], _ringe[_rE[7]][_j + 1])))
    for _j in (_TAPER, _TAPER + _BOGEN):
        for _i2 in range(_rE[4], _rE[7]):
            _scharf.add(frozenset((_ringe[_i2][_j], _ringe[_i2 + 1][_j])))
    for _j in range(_P - 1):
        _zl2 = (_zsch[_j] + _zsch[_j + 1]) / 2
        if 0.58 < _zl2 <= 0.72 and _TAPER <= _j <= _TAPER + _BOGEN:
            _scharf.add(frozenset((_ringe[_rE[4]][_j], _ringe[_rE[4]][_j + 1])))
            _scharf.add(frozenset((_ringe[_rE[5]][_j], _ringe[_rE[5]][_j + 1])))
    _attr = _mesh.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
    for _ei, _e in enumerate(_mesh.edges):
        if frozenset(_e.vertices) in _scharf:
            _attr.data[_ei].value = True
    _mesh.uv_layers.new(name="UVMap")
    _schale = bpy.data.objects.new(f"Triebzug_Bugschale_{kennung}", _mesh)
    bpy.context.collection.objects.link(_schale)
    bpy.context.view_layer.objects.active = _schale

    # ---- Grosse Bugklappe: aufgesetztes Feld mit Fugenschatten ----
    # Beim Vorbild ist fast die ganze Stirn unterhalb der Leuchten EINE grosse
    # Klappe (dahinter sitzt die Kupplung); ihre Fuge zeichnet das Werkstattfoto
    # deutlich. Das Feld ist ein zweiter, um 18 mm vorgesetzter Ausschnitt der
    # Schale (y 0.98..1.64, |z| bis 0.85); sein Rand faellt auf die Haut zurueck,
    # die harte Randfacette liest als Fuge. Die rote Binde laeuft mit derselben
    # Formel ueber die Klappe wie ueber die Schale — eine Kante, eine Linie.
    _kSp = [_j for _j in range(_TAPER, _TAPER + _BOGEN + 1)
            if abs(_punkt(_j, 1.30)[1]) <= 0.85]
    _kNC = len(_kSp)
    _kNR = 8
    _kVerts, _kIdx = [], {}
    for _cj, _j in enumerate(_kSp):
        _yc2 = 1.10 + 0.54 * (_zband[_j] / 1.20) ** 5
        _stufen = []
        for _a2, _b2, _n2 in ((0.98, _yc2 - 0.09, 2),
                              (_yc2 - 0.09, _yc2 + 0.09, 3),
                              (_yc2 + 0.09, 1.64, 2)):
            for _k2 in range(_n2):
                _stufen.append(_a2 + (_b2 - _a2) * _k2 / _n2)
        _stufen.append(1.64)
        for _ri, _y in enumerate(_stufen):
            _px, _pz = _punkt(_j, _y)
            _rand = _ri in (0, _kNR - 1) or _cj in (0, _kNC - 1)
            _off = 0.0 if _rand else 0.018
            _kIdx[(_cj, _ri)] = len(_kVerts)
            _kVerts.append((0.5 + r * (_px + _off - 0.5), -_pz, _y))
    _kFaces, _kMats, _kWeich = [], [], []
    for _cj in range(_kNC - 1):
        for _ri in range(_kNR - 1):
            _f = [_kIdx[(_cj, _ri)], _kIdx[(_cj + 1, _ri)],
                  _kIdx[(_cj + 1, _ri + 1)], _kIdx[(_cj, _ri + 1)]]
            _kFaces.append(_f[::-1] if r < 0 else _f)
            _kMats.append(1 if _ri in (2, 3, 4) else 0)
            _kWeich.append(not (_ri in (0, _kNR - 2) or _cj in (0, _kNC - 2)))
    _kMesh = bpy.data.meshes.new(f"Triebzug_Bugklappe_gross_{kennung}")
    _kMesh.from_pydata(_kVerts, [], _kFaces)
    _kMesh.update()
    for _mat in (m_zugweiss, m_zug):
        _kMesh.materials.append(_mat)
    for _p, _slot, _w in zip(_kMesh.polygons, _kMats, _kWeich):
        _p.material_index = _slot
        _p.use_smooth = _w
    _kMesh.uv_layers.new(name="UVMap")
    _kObj = bpy.data.objects.new(f"Triebzug_Bugklappe_gross_{kennung}", _kMesh)
    bpy.context.collection.objects.link(_kObj)
    bpy.context.view_layer.objects.active = _schale
    # Kabine und Dachklotz sind entfallen: der Wagenkasten reicht ohnehin bis x 7.5 und
    # die Dachkrone bis 7.3, beide Kaesten lagen restlos darin. Die Schale beginnt bei
    # 7.30 — 20 cm INNERHALB der Kastenstirn, damit ihre flache Rueckwand verdeckt ist.
    for i, s in enumerate((-1, 1)):
        kasten(f"Triebzug_Kopf_Dachrand_{kennung}_{i}", 0.4, 0.09, 0.07, 0.5 + r * 7.0, 3.02, s * 1.11, m_stahlhell, fase=0.01)
    kasten(f"Triebzug_Kopf_Makrofon_{kennung}", 0.3, 0.46, 0.1, 0.5 + r * 6.4, 3.07, 0, m_stahlhell, fase=0.02)
    # Schwarzes Dachpanel: das dunkle Frontfeld endet beim Vorbild als gerundetes
    # Feld AUF dem Kabinendach — es verbindet sich optisch mit der Scheibe.
    kasten(f"Triebzug_Dachpanel_{kennung}", 0.55, 1.0, 0.03, 0.5 + r * 6.95, 3.03, 0, m_zugglas, fase=0.01)

    # ---- Details AUF der Schale ----
    # Frontmaske, Scheibenrahmen, Frontscheibe, Mittelpfosten und Eckglas sind
    # ersatzlos entfallen: die Scheibe ist jetzt die dunkle Materialzone der Schale
    # (y 2.25..2.62) und laeuft dort um die Ecke, statt als geneigter Kasten vor
    # einem Quader zu stehen. Aufgesetzte Kaesten wuerden in der Schale verschwinden
    # (Vollkoerperregel) oder als Kante davorstehen.
    # Wischer liegen flach auf der stark geneigten Scheibe (Neigung dort rund 61 Grad
    # gegen die Senkrechte), nicht mehr senkrecht davor. x-Rolle bleibt konstant:
    # unter der Spiegelkonvention der Szene dreht sie am Westende nicht mit.
    # Wischer parken OBEN haengend am Scheibenkopf, Lager an der Scheibenoberkante —
    # beim Vorbild haengen beide Arme aus dem dunklen Dachpanel herab.
    for i, (wz, wu, wl) in enumerate(((-0.32, 7.777, 7.623), (0.44, 7.771, 7.617))):
        kasten(f"Triebzug_Wischer_{kennung}_{i}", 0.03, 0.06, 0.30, 0.5 + r * wu, 2.50, wz * r, m_dunkel,
               fase=0, drehung=(0, -r * 0.93, 0))
        zylinder(f"Triebzug_Wischerlager_{kennung}_{i}", 0.04, 0.05, 0.5 + r * wl, 2.62, wz * r, m_dunkel, achse="x")

    # ---- Leuchten im dunklen Feld der Schale ----
    # Die grossen Gehaeusekaesten sind entfallen: auf einer gewoelbten Flaeche stand ein
    # flacher Quader am Aussenrand 28 cm vor der Haut und hing dort sichtbar frei.
    # Das dunkle Feld ist Teil der Schale und folgt der Scheibenunterkante; nur die
    # Lampen selbst sitzen als kurze Zylinder knapp davor. Flaechenwerte nachgerechnet:
    # bei |z| 0.64 liegt die Haut auf x 8.988 (y 1.94), bei 0.675 auf 9.142 (y 1.82),
    # bei 0.598 auf 9.157 (y 1.82) — Superellipse Exponent 3.4, nicht Ellipse!
    for i, s in enumerate((-1, 1)):
        zylinder(f"Triebzug_Spitzenlicht_{kennung}_{i}", 0.06, 0.06, 0.5 + r * 8.498, 1.94, s * 0.64, m_fenster, achse="x")
        zylinder(f"Triebzug_Spitzenlicht2_{kennung}_{i}", 0.045, 0.06, 0.5 + r * 8.652, 1.82, s * 0.675, m_fenster, achse="x")
        # Lamellengitter im oberen Teil des dunklen Felds (Werkstattfoto: drei helle
        # Schlitze direkt unter der Scheibenecke). Haut je z nachgerechnet.
        for gi, (gz, gu) in enumerate(((0.61, 8.387), (0.675, 8.374))):
            kasten(f"Triebzug_Lamelle_{kennung}_{i}_{gi}", 0.02, 0.035, 0.14,
                   0.5 + r * gu, 2.03, s * gz, m_stahlhell, fase=0, drehung=(0, -r * 0.93, 0))
        zylinder(f"Triebzug_Schlusslicht_{kennung}_{i}", 0.03, 0.06, 0.5 + r * 8.667, 1.82, s * 0.598, m_zug, achse="x")
        # Lueftungsgitter sitzt auf der Korpusflanke hinter der Schale (|z| 1.215),
        # nicht mehr auf der verjuengten Bugflanke, wo es darin verschwaende.
        kasten(f"Triebzug_Frontgitter_{kennung}_{i}", 0.4, 0.06, 0.09, 0.5 + r * 6.95, 1.79, s * 1.215, m_dunkel, fase=0)
    # Drittes Spitzenlicht mittig oben im dunklen Dachfeld (Haut dort x 7.643)
    zylinder(f"Triebzug_Spitzenlicht3_{kennung}", 0.05, 0.06, 0.5 + r * 7.148, 2.92, 0, m_fenster, achse="x")

    # ---- DB-Logo auf der Stirn — ausdruecklicher Nutzerwunsch, die EINZIGE
    # Ausnahme von der Greek-Regel (sonst keine Logos/Schrift in der Szene).
    # Rote Tafel buendig auf der 53-Grad-Geraden (Haut bei y 1.88: x 9.1045),
    # Buchstaben als blockige, SPIEGELSYMMETRISCHE Ringe: D = Ring, B = Ring mit
    # Mittelbalken. So liest das gespiegelte Westende nicht seitenverkehrt; nur
    # die Buchstabenplaetze tauschen ueber r. In-Ebene-Versatz dv wird ueber die
    # Neigung umgerechnet: dy = dv*cos(0.925), du = -dv*sin(0.925).
    _LOGO_W = 0.925
    _lsin, _lcos = _m.sin(_LOGO_W), _m.cos(_LOGO_W)
    kasten(f"Triebzug_Logo_{kennung}", 0.016, 0.46, 0.30, 0.5 + r * 8.609, 1.88, 0,
           m_zug, fase=0.007, drehung=(0, -r * _LOGO_W, 0))

    def _logo_strich(nr, za, dv, dzs, dvh):
        kasten(f"Triebzug_Logo_{kennung}_{nr}", 0.014, dzs, dvh,
               0.5 + r * (8.621 - dv * _lsin), 1.88 + dv * _lcos, za,
               m_zugweiss, fase=0, drehung=(0, -r * _LOGO_W, 0))

    for _bi, _bz in ((0, r * 0.065), (1, -r * 0.065)):   # 0 = D (links), 1 = B (rechts)
        _logo_strich(f"{_bi}l", _bz + 0.042, 0, 0.03, 0.15)
        _logo_strich(f"{_bi}r", _bz - 0.042, 0, 0.03, 0.15)
        _logo_strich(f"{_bi}o", _bz, 0.068, 0.115, 0.03)
        _logo_strich(f"{_bi}u", _bz, -0.068, 0.115, 0.03)
    _logo_strich("1m", -r * 0.065, 0, 0.07, 0.03)   # Mittelbalken macht das B

    # ---- Rote Bauchlinie ----
    # Sie ist vollstaendig Materialzone der Schale (siehe _slot == 1 oben). Die frueheren
    # vier gedrehten Flankenabschnitte sind entfallen: sie sassen bei |z| 1.235, waehrend
    # die Schale dort nach der Verschlankung nur noch rund 1.14 breit ist — sie haetten
    # 7 cm vor der Haut gehangen und der Pruefer haette es durchgewinkt, weil sie sich
    # gegenseitig hielten.
    # ---- Kabinenflanke: dunkles Band als Fortsetzung des Fensterbands ----
    for i, s in enumerate((-1, 1)):
        kasten(f"Triebzug_Kopf_Seitenband_{kennung}_{i}", 1.08, 0.05, 0.58, 0.5 + r * 6.66, 2.15, s * 1.21, m_zugglas, fase=0)
        # Pfosten stehen 0.035 VOR dem Band (wie am Wagenkasten) — deckungsgleiche
        # Aussenflaechen haetten geflimmert
        for j, pu in enumerate((6.2, 7.02)):
            kasten(f"Triebzug_Kopf_Bandpfosten_{kennung}_{i}_{j}", 0.13, 0.06, 0.58, 0.5 + r * pu, 2.15, s * 1.24, m_zugweiss, fase=0)
        kasten(f"Triebzug_Kopf_Dachfascie_{kennung}_{i}", 0.4, 0.12, 0.1, 0.5 + r * 7.0, 2.65, s * 1.22, m_zugdach, fase=0.03)
        kasten(f"Triebzug_Kopf_Regenrinne_{kennung}_{i}", 0.4, 0.05, 0.03, 0.5 + r * 7.0, 2.585, s * 1.23, m_dunkel, fase=0)
        # Fuehrerraumtuer statt blosser Fuge
        kasten(f"Triebzug_Kopf_Tuer_{kennung}_{i}", 0.72, 0.05, 1.5, 0.5 + r * 6.75, 1.79, s * 1.215, m_zugweiss, fase=0)
        kasten(f"Triebzug_Kopf_Tuerfuge_{kennung}_{i}", 0.74, 0.035, 0.02, 0.5 + r * 6.75, 1.05, s * 1.2175, m_dunkel, fase=0)
        zylinder(f"Triebzug_Kopf_Tuergriff_{kennung}_{i}", 0.02, 0.12, 0.5 + r * 6.94, 1.72, s * 1.245, m_stahlhell, achse="z")
        zylinder(f"Triebzug_Spiegelarm_{kennung}_{i}", 0.025, 0.24, 0.5 + r * 7.2, 2.52, s * 1.26, m_stahlhell, achse="z")
        kasten(f"Triebzug_Spiegel_{kennung}_{i}", 0.09, 0.08, 0.28, 0.5 + r * 7.2, 2.52, s * 1.36, m_dunkel, fase=0.02)

    # ---- Unterbau, Schuerze, Kupplung ----
    # Schuerze und Frontanbauten sind mit der Nase nach vorn gewandert (+0.35), damit
    # unter dem 0.85 m laengeren Bug nicht ins Leere gegriffen wird.
    kasten(f"Triebzug_Frontschuerze_{kennung}", 1.55, 1.6, 0.63, 0.5 + r * 8.175, 0.635, 0, m_unterflur, fase=0.05)
    kasten(f"Triebzug_Kopftraeger_{kennung}", 0.42, 1.3, 0.3, 0.5 + r * 7.18, 0.8, 0, m_unterflur)
    for i, bz in enumerate((-0.62, 0.62)):
        kasten(f"Triebzug_Bahnraeumer_{kennung}_{i}", 0.15, 0.5, 0.3, 0.5 + r * 9.005, 0.38, bz, m_unterflur, fase=0)
    for i, gz in enumerate((-0.82, 0.82)):
        kasten(f"Triebzug_Rangiertritt_{kennung}_{i}", 0.34, 0.24, 0.06, 0.5 + r * 8.7, 0.295, gz, m_riffel, fase=0)
        zylinder(f"Triebzug_Rangiergriff_{kennung}_{i}", 0.025, 0.42, 0.5 + r * 8.995, 0.395, gz, m_stahlhell)
    for i, cz in enumerate((-0.6, 0.6)):
        kasten(f"Triebzug_Bugklappe_{kennung}_{i}", 0.05, 0.36, 0.36, 0.5 + r * 8.995, 0.6, cz, m_dunkel, fase=0)
        kasten(f"Triebzug_Bugscharnier_{kennung}_{i}", 0.05, 0.12, 0.07, 0.5 + r * 9.015, 0.74, cz * 0.77, m_stahlhell, fase=0)
    kasten(f"Triebzug_Kupplungskasten_{kennung}", 0.3, 0.5, 0.3, 0.5 + r * 9.08, 0.5, 0, m_dunkel, fase=0)
    zylinder(f"Triebzug_Kuppelschaft_{kennung}", 0.075, 0.34, 0.5 + r * 9.3, 0.5, 0, m_stahl, achse="x")
    kasten(f"Triebzug_Kuppelkopf_{kennung}", 0.13, 0.46, 0.36, 0.5 + r * 9.435, 0.5, 0, m_stahl, fase=0.02)
    zylinder(f"Triebzug_Kuppelkegel_{kennung}", 0.055, 0.12, 0.5 + r * 9.44, 0.56, -0.11 * r, m_stahlhell, achse="x")
    zylinder(f"Triebzug_Kuppeltrichter_{kennung}", 0.075, 0.1, 0.5 + r * 9.43, 0.56, 0.11 * r, m_dunkel, achse="x")
    kasten(f"Triebzug_EKupplung_{kennung}", 0.12, 0.34, 0.16, 0.5 + r * 9.43, 0.70, 0, m_stahlhell, fase=0.02)

fuehrerstand("ost", 1)
fuehrerstand("west", -1)

# Der Zug steht auf der Schiene: mit dem Flachbodengleis rueckt ALLES, was
# Triebzug_ heisst, um die Senkung der Schienenoberkante nach unten. Ein Nachlauf
# statt hunderter geaenderter y-Literale; wer Zugteile anlegt, tut das VOR dieser
# Zeile, damit sie mitwandern.
for _o in bpy.data.objects:
    if _o.type == "MESH" and _o.name.startswith("Triebzug_"):
        _o.matrix_world = Matrix.Translation((0, 0, -GLEIS_SENKUNG)) @ _o.matrix_world

# ---- Dacharbeitsbuehnen, Kranbahn, Rollgerueste -----------------------------
for i, bx in enumerate((-6.5, -3.9, 1.7, 4)):  # Luecke bei x~0: Sichtachse der Station-2-Kamera
    for j, bz in enumerate((-2.7, 2.7)):
        kasten(f"Buehne_Stuetze_{i}_{j}", 0.18, 0.18, 3.2, bx, 1.6, bz, m_stahlhell)
        kasten(f"Buehne_Stuetze_{i}_{j}_fuss", 0.26, 0.26, 0.18, bx, 0.09, bz, m_markierung, fase=0)
kasten("Buehne_Plattform_Nord", 11.5, 0.85, 0.1, -1.25, 3.25, -2.7, m_riffel)
kasten("Buehne_Plattform_Sued", 11.5, 0.85, 0.1, -1.25, 3.25, 2.7, m_riffel)
kasten("Buehne_Fussleiste_Nord", 11.5, 0.05, 0.12, -1.25, 3.36, -3.1, m_markierung, fase=0)
kasten("Buehne_Fussleiste_Sued", 11.5, 0.05, 0.12, -1.25, 3.36, 3.1, m_markierung, fase=0)
for j, bz in enumerate((-3.08, 3.08)):
    zylinder(f"Buehne_Handlauf_{j}", 0.035, 11.5, -1.25, 4.25, bz, m_stahlhell, achse="x")
    for i, px in enumerate((-6.5, -3.75, -1, 1.75, 4)):
        zylinder(f"Buehne_Gelaenderpfosten_{j}_{i}", 0.025, 0.95, px, 3.78, bz, m_stahlhell)
for i, tx in enumerate((-6.5, 4)):
    kasten(f"Buehne_Quertraeger_{i}", 0.16, 5.4, 0.2, tx, 3.9, 0, m_stahlhell)
# Nordseite, OSTende — dort blockiert sie weder Station 1/2 noch die Totale
treppe("Buehne_Treppe", 2.9, -5.3, 3.3, richtung_z=-1, breite=0.85)
# Klappbruecken von der Dacharbeitsbuehne auf das Zugdach — vorher endete die Buehne
# 1.08 m vor dem Zug und niemand kam hinueber. Die Bruecke faellt von der Plattform
# (Oberkante 3.30) auf die Dachkante (3.00); Winkel 0.218 rad, Vorzeichen folgt der
# Seite, weil pos() die three.js-z-Achse auf Blender -y abbildet.
for s in (-1, 1):
    for i, bx in enumerate((-5.2, -2.6, 0.4)):
        kasten(f"Dachbruecke_{'n' if s < 0 else 's'}_{i}", 1.25, 1.2, 0.05, bx, 3.08, s * 1.71,
               m_riffel, fase=0, drehung=(-s * 0.343, 0, 0))
        zylinder(f"Dachbruecke_{'n' if s < 0 else 's'}_{i}_scharnier", 0.05, 1.3, bx, 3.28, s * 2.26,
                 m_stahl, achse="x")
# Druckluft-Ringleitung mit Schlauchtrommeln und Medienstelen: ohne Anschluesse
# wirkte die Halle wie eine Ausstellung statt wie ein Arbeitsplatz.
# Hallen-Fahrleitung: Deckenstromschiene ueber dem Gleis, an Dach_Rippe_5 (z 0)
# abgehaengt. Ohne sie stand der ausgefahrene Stromabnehmer sinnlos in der Luft,
# und in der Totale las das darueber liegende Druckluftrohr als Fahrdraht. Unterkante
# 4.20, Schleifleiste endet bei 4.18: 2 cm Luft, kein Durchdringen.
kasten("Fahrleitung_Schiene", 21, 0.08, 0.12, -1, 4.26 - GLEIS_SENKUNG, 0, m_stahl, fase=0)
for i, s in enumerate((-1, 1)):
    kasten(f"Fahrleitung_Horn_{i}", 0.6, 0.08, 0.06, -1 + s * 10.75, 4.31 - GLEIS_SENKUNG, 0, m_stahl, fase=0,
           drehung=(0, s * 0.25, 0))
for i, hx in enumerate((-10, -4, 2, 8)):   # zwischen den Dachbindern
    zylinder(f"Fahrleitung_Haenger_{i}", 0.025, 1.72 + GLEIS_SENKUNG, hx, 5.18 - GLEIS_SENKUNG / 2, 0, m_stahl)
    zylinder(f"Fahrleitung_Isolator_{i}", 0.06, 0.16, hx, 4.40 - GLEIS_SENKUNG, 0, m_objekt)
for s in (-1, 1):
    seite = "n" if s < 0 else "s"
    # Druckluft-Sammler direkt unter Dach_Rippe_3 bzw. _7 (z +-3.6); die Enden fuehren
    # als Steigleitung an die Rippe statt stumpf in der Luft aufzuhoeren
    zylinder(f"Druckluft_Sammler_{seite}", 0.06, 24, -1, 5.30, s * 3.6, m_blau, achse="x")
    for i, hx in enumerate((-9, -3, 3, 9)):
        zylinder(f"Druckluft_Haenger_{seite}_{i}", 0.02, 0.74, hx, 5.67, s * 3.6, m_stahl)
    for i, xe in enumerate((-13, 11)):
        zylinder(f"Druckluft_Steig_{seite}_{i}", 0.06, 0.74, xe, 5.67, s * 3.6, m_blau)
    for i, bx in enumerate((-6.5, 1.7)):  # nur diese beiden Stuetzen sind rollgeruestfrei
        kasten(f"Trommel_Konsole_{seite}_{i}", 0.2, 0.7, 0.12, bx, 2.6, s * 2.35, m_stahl, fase=0)
        zylinder(f"Trommel_{seite}_{i}", 0.22, 0.34, bx, 2.6, s * 1.95, m_orange, achse="z", ecken=32)
        zylinder(f"Trommel_{seite}_{i}_schlauch", 0.03, 1.0, bx, 2.1, s * 1.75, m_gummi)
    for i, gx in enumerate((-6.2, -3.5, -0.8)):
        kasten(f"Medienstele_{seite}_{i}", 0.22, 0.22, 0.9, gx, 0.45, s * 1.5, m_stahlhell)
        kasten(f"Medienstele_{seite}_{i}_kopf", 0.26, 0.26, 0.1, gx, 0.95, s * 1.5, m_blau, fase=0.02)
        zylinder(f"Medienstele_{seite}_{i}_hahn", 0.04, 0.12, gx, 0.75, s * 1.63, m_zug, achse="z")

# Echter Brueckenkran statt eines einzelnen Traegers im Deckengrau: zwei Kranbahnen
# auf Konsolen an den Hallenstuetzen, dazwischen eine verfahrbare Bruecke mit Katze,
# Seilen und Unterflasche. Die Bruecke steht bewusst am WESTENDE (x -12.9): die Totale
# blickt von x=15 nach Westen, dort saesse eine Bruecke sonst 2 m vor der Linse.
# Konsolen auf y 4.20 — darueber liegen Rohr_Orange (4.53) und die Rohrhalter-Fuesse.
for j, kz in enumerate((-8.6, 8.6)):
    i_traeger(f"Kranbahn_{j}", 33, 0.5, 0.34, 0, 4.75, kz, m_stahlhell, achse="x")
    kasten(f"Kranbahn_Schiene_{j}", 33, 0.12, 0.08, 0, 5.04, kz, m_schiene, fase=0)
    for i, sx in enumerate((-13.6, -6.8, 0, 6.8, 13.6)):
        kasten(f"Kranbahn_Konsole_{j}_{i}", 0.3, 1.3, 0.4, sx, 4.2, kz + (0.55 if kz > 0 else -0.55), m_stahlhell)
KRAN_X, KATZ_Z = -12.9, -2.0
# Brueckentraeger in hellem Stahl statt Signalgelb: als 17-m-Balken wuerde Gelb
# die ganze Halle dominieren. Gelb bleibt den beweglichen Teilen vorbehalten.
i_traeger("Kran_Bruecke", 17.2, 0.62, 0.34, KRAN_X, 4.78, 0, m_stahlhell, achse="z")
for j, kz in enumerate((-8.6, 8.6)):
    kasten(f"Kran_Kopftraeger_{j}", 1.4, 0.5, 0.38, KRAN_X, 5.27, kz, m_stahlhell)
kasten("Kran_Katze", 0.9, 1.0, 0.45, KRAN_X, 5.32, KATZ_Z, m_markierung)
zylinder("Kran_Trommel", 0.16, 0.7, KRAN_X, 5.35, KATZ_Z, m_stahl, achse="z")
for i, (sx, sz) in enumerate(((-0.2, -0.25), (0.2, -0.25), (-0.2, 0.25), (0.2, 0.25))):
    zylinder(f"Kran_Seil_{i}", 0.012, 0.74, KRAN_X + sx, 4.72, KATZ_Z + sz, m_dunkel)
# Unterflasche haengt hoch (Deckentechnik) — tiefer wuerde sie in Stationsblicke ragen
kasten("Kran_Unterflasche", 0.5, 0.45, 0.3, KRAN_X, 4.2, KATZ_Z, m_markierung)
kasten("Kran_Haken", 0.12, 0.12, 0.28, KRAN_X, 3.91, KATZ_Z, m_dunkel)
zylinder("Kran_Steuerleitung", 0.015, 1.1, KRAN_X + 0.55, 4.55, KATZ_Z, m_dunkel)
kasten("Kran_Steuerbirne", 0.09, 0.14, 0.28, KRAN_X + 0.55, 3.86, KATZ_Z, m_markierung, fase=0.02)


def rollgeruest(name, x, z):
    for i, (gx, gz) in enumerate(((-0.55, -0.35), (0.55, -0.35), (-0.55, 0.35), (0.55, 0.35))):
        zylinder(f"{name}_holm_{i}", 0.035, 3.0, x + gx, 1.5, z + gz, m_stahlhell)
        zylinder(f"{name}_rolle_{i}", 0.09, 0.06, x + gx, 0.07, z + gz, m_dunkel, achse="z")
    kasten(f"{name}_buehne_1", 1.25, 0.8, 0.06, x, 1.25, z, m_stahlhell)
    kasten(f"{name}_buehne_2", 1.25, 0.8, 0.06, x, 2.35, z, m_stahlhell)
    zylinder(f"{name}_handlauf", 0.03, 1.25, x, 2.95, z + 0.38, m_markierung, achse="x")
    kasten(f"{name}_diagonale", 0.05, 0.05, 1.5, x, 1.8, z - 0.38, m_stahlhell, drehung=(0, 0.6, 0), fase=0)


rollgeruest("Rollgeruest_1", 4.2, -2.2)
rollgeruest("Rollgeruest_2", -4.2, 2.2)

# ---- Fahrzeuge und Geraete ---------------------------------------------------
# 1.5 m nach Westen gerueckt: an der alten Stelle schnitten die beiden Tankscheiben
# als zusammenhanglose Zylinder ins untere Bilddrittel der Station-4-Ansicht.
kasten("Servicewagen_Korpus", 1.3, 0.85, 1.0, 9.0, 0.62, 2.9, m_zugweiss)
zylinder("Servicewagen_Tank_1", 0.18, 0.5, 8.7, 1.35, 2.75, m_blau)
zylinder("Servicewagen_Tank_2", 0.18, 0.5, 9.3, 1.35, 2.75, m_blau)
rohr_mit_bogen("Servicewagen_Schlauch", [(8.5, 0.9, 2.5), (7.7, 0.5, 2.0), (7.0, 0.06, 1.5)], 0.05, m_gummi)
for i, (rx, rz) in enumerate(((-0.5, -0.3), (0.5, -0.3), (-0.5, 0.3), (0.5, 0.3))):
    zylinder(f"Servicewagen_rad_{i}", 0.09, 0.07, 9.0 + rx, 0.09, 2.9 + rz, m_gummi, achse="z")
kasten("Werkstattwagen_Korpus", 1.0, 0.65, 0.9, 12.5, 0.55, -3.5, m_zug)
kasten("Werkstattwagen_Griff", 0.06, 0.55, 0.6, 13.05, 0.9, -3.5, m_dunkel, fase=0)
for i, (rx, rz) in enumerate(((-0.38, -0.24), (0.38, -0.24), (-0.38, 0.24), (0.38, 0.24))):
    zylinder(f"Werkstattwagen_rad_{i}", 0.08, 0.06, 12.5 + rx, 0.08, -3.5 + rz, m_gummi, achse="z")
kasten("Werkbank2", 2.0, 0.7, 0.85, 2.5, 0.43, -9.4, m_stahl)
kasten("Werkbank2_Platte", 2.0, 0.75, 0.08, 2.5, 0.9, -9.4, m_dunkel)
# farbige Schubladenfronten mit Griffen
for i, (wx, wm) in enumerate(((1.95, m_blau), (2.5, m_orange), (3.05, m_blau))):
    kasten(f"Werkbank2_schublade_{i}", 0.46, 0.05, 0.6, wx, 0.5, -9.03, wm, fase=0.02)
    kasten(f"Werkbank2_griff_{i}", 0.2, 0.04, 0.04, wx, 0.68, -9.0, m_dunkel, fase=0)
kasten("Werkbank2_Schraubstock", 0.25, 0.3, 0.25, 3.2, 1.06, -9.35, m_dunkel)
kasten("Werkbank2_Werkzeugkasten", 0.5, 0.3, 0.3, 2.0, 1.09, -9.4, m_zug)
kasten("Oel_Wanne", 1.7, 1.3, 0.15, 12.15, 0.08, -8.7, m_markierung)
for i, (fx, fz, fm) in enumerate(((11.85, -8.9, m_dunkel), (12.45, -8.9, m_blau),
                                  (11.85, -8.4, m_orange), (12.45, -8.4, m_zug))):
    fass(f"Oel_Fass_{i}", fx, fz, 0.15, fm)
kasten("Kabel_Trommel", 0.5, 0.5, 0.5, -1.6, 0.25, -8.2, m_blau)
zylinder("Kabel_Trommel_Kern", 0.12, 0.56, -1.6, 0.25, -8.2, m_dunkel, achse="z")

# ---- Radsatzlager: Zug-Radsaetze auf Lagerschienen (Suedseite) --------------
def radsatz(name, x, z_mitte, y_achse=0.5):
    """Zug-Radsatz: Achswelle + zwei Raeder mit heller Radscheibe."""
    zylinder(f"{name}_achse", 0.055, 1.02, x, y_achse, z_mitte, m_stahl, achse="z")
    for seite, dz in (("n", -0.55), ("s", 0.55)):
        zylinder(f"{name}_rad_{seite}", 0.38, 0.11, x, y_achse, z_mitte + dz, m_unterflur, achse="z", ecken=32)
        zylinder(f"{name}_scheibe_{seite}", 0.2, 0.12, x, y_achse, z_mitte + dz, m_stahlhell, achse="z", ecken=32)


for i, rz in enumerate((2.45, 3.55)):
    kasten(f"Radsatzlager_schiene_{i}", 3.4, 0.14, 0.12, -0.6, 0.06, rz, m_stahl, fase=0)
for i, rx in enumerate((-1.7, -0.6, 0.5)):
    radsatz(f"Radsatz_{i}", rx, 3.0)
warnstreifen("Radsatzlager_kante", 3.5, -0.6, 4.0)

# ---- Bodenmarkierungen, Signale, Sicherheit ---------------------------------
# Markierte Zone als Kenney-Bodendekal (liest sich eindeutig als Markierung)
lade_asset("factory_indicator-special-lines.glb", "Schraffur_Dekal_1", 6.4, 0.03, 3.6, ziel_breite=2.3)
lade_asset("factory_indicator-special-lines.glb", "Schraffur_Dekal_2", 8.6, 0.03, 3.6, ziel_breite=2.3)
for i, (ax, az) in enumerate(((-10, 2.4), (-3, 2.4), (5.2, 2.4), (11, 2.4))):
    zylinder(f"Absperrpfosten_{i}", 0.07, 0.9, ax, 0.45, az, m_orange)
    zylinder(f"Absperrpfosten_{i}_ring", 0.075, 0.08, ax, 0.75, az, m_stahlhell)
zylinder("Muelleimer_1", 0.22, 0.7, -6.6, 0.35, -4.0, m_orange)
zylinder("Muelleimer_2", 0.22, 0.7, 2.7, 0.35, 4.7, m_orange)
# Warnaufsteller stehen am Boden vor der Wand (die Modelle haben eigene Fuesse)
lade_asset("factory_warning-orange.glb", "Warntafel_0", -8, 0, -9.45, ziel_hoehe=0.85, einfaerbung=m_markierung)
lade_asset("factory_warning-traffic.glb", "Warntafel_1", -2.2, 0, -9.45, ziel_hoehe=0.85, einfaerbung=m_orange)
lade_asset("factory_warning-orange.glb", "Warntafel_2", 6.7, 0, -9.45, ziel_hoehe=0.85, einfaerbung=m_markierung)
for i, (sx, sz) in enumerate(((-9.8, 1.6), (1, -1.6), (10.6, 1.6))):
    zylinder(f"Signal_{i}_mast", 0.04, 1.0, sx, 0.5, sz, m_dunkel)
    kasten(f"Signal_{i}_rot", 0.13, 0.13, 0.13, sx, 1.06, sz, m_zug, fase=0)
    kasten(f"Signal_{i}_gelb", 0.13, 0.13, 0.13, sx, 1.19, sz, m_markierung, fase=0)
    kasten(f"Signal_{i}_gruen", 0.13, 0.13, 0.13, sx, 1.32, sz, m_gruen, fase=0)
kasten("Rettungszeichen_Tor", 0.05, 0.5, 0.3, 16.78, 3.0, -2.6, m_gruen, fase=0)
kasten("Rettungszeichen_Tor_symbol", 0.06, 0.2, 0.06, 16.76, 3.0, -2.6, m_fenster, fase=0)
kasten("Rettungszeichen_West", 0.05, 0.5, 0.3, -16.78, 2.3, 2.0, m_gruen, fase=0)
kasten("Rettungszeichen_West_symbol", 0.06, 0.2, 0.06, -16.76, 2.3, 2.0, m_fenster, fase=0)
kasten("Konsole_1", 0.9, 0.35, 0.06, -13.5, 2.2, -9.7, m_stahlhell, fase=0)
kasten("Konsole_2", 0.9, 0.35, 0.06, 9.5, 2.4, -9.7, m_stahlhell, fase=0)
# Kabelkanal + Rohr entlang der Nordwand auf Arbeitshoehe (fuellt die kahle Wandzone)
kasten("Nordwand_Kabelkanal", 22, 0.06, 0.14, 3, 1.5, -9.8, m_dunkel, fase=0)
zylinder("Nordwand_Rohr", 0.05, 22, 3, 2.4, -9.8, m_stahlhell, achse="x")

# Personaltueren (die Halle hatte ausser dem Tor keine Tuer) mit Exit-Schild
kasten("Personaltuer_Nord", 1.0, 0.08, 2.05, -4.6, 1.025, -9.82, m_blau, fase=0.02)
kasten("Personaltuer_Nord_rahmen", 1.14, 0.06, 2.15, -4.6, 1.075, -9.83, m_relief, fase=0)
kasten("Personaltuer_Nord_klinke", 0.12, 0.06, 0.04, -4.25, 1.05, -9.77, m_dunkel, fase=0)
kasten("Personaltuer_Nord_exit", 0.4, 0.04, 0.24, -4.6, 2.62, -9.8, m_gruen, fase=0)
kasten("Personaltuer_West", 0.08, 1.0, 2.05, -16.82, 1.025, 5.2, m_blau, fase=0.02)
kasten("Personaltuer_West_rahmen", 0.06, 1.14, 2.15, -16.83, 1.075, 5.2, m_relief, fase=0)
kasten("Personaltuer_West_klinke", 0.06, 0.12, 0.04, -16.77, 1.05, 4.85, m_dunkel, fase=0)
kasten("Personaltuer_West_exit", 0.04, 0.4, 0.24, -16.8, 2.4, 5.2, m_gruen, fase=0)

# Gasflaschen-Gestell an der Nordwand (Werkstatt-Klassiker)
kasten("Gasflaschen_Gestell", 0.75, 0.32, 1.0, -10.6, 0.5, -9.6, m_stahl)
zylinder("Gasflasche_1", 0.11, 1.3, -10.78, 0.65, -9.58, m_orange)
zylinder("Gasflasche_2", 0.11, 1.3, -10.42, 0.65, -9.58, m_blau)
zylinder("Gasflasche_1_ventil", 0.04, 0.12, -10.78, 1.36, -9.58, m_stahl)
zylinder("Gasflasche_2_ventil", 0.04, 0.12, -10.42, 1.36, -9.58, m_stahl)
kasten("Gasflaschen_Kette", 0.72, 0.04, 0.05, -10.6, 1.05, -9.44, m_dunkel, fase=0)

# Hallenuhr ueber dem Tor
zylinder("Hallenuhr", 0.32, 0.06, 16.8, 5.35, 0, m_fenster, achse="x")
zylinder("Hallenuhr_rahmen", 0.36, 0.04, 16.82, 5.35, 0, m_dunkel, achse="x")
kasten("Hallenuhr_zeiger_1", 0.02, 0.03, 0.2, 16.76, 5.42, 0, m_dunkel, fase=0)
kasten("Hallenuhr_zeiger_2", 0.02, 0.14, 0.03, 16.76, 5.35, 0.08, m_dunkel, fase=0)

# Prellbock am West-Gleisende
for i, pz in enumerate((-0.5, 0.5)):
    kasten(f"Prellbock_strebe_{i}", 0.9, 0.12, 0.12, -16.35, 0.35, pz, m_dunkel, fase=0, drehung=(0, 0.55, 0))
    kasten(f"Prellbock_fuss_{i}", 0.5, 0.2, 0.06, -16.2, 0.03, pz, m_dunkel, fase=0)
kasten("Prellbock_balken", 0.14, 1.6, 0.4, -15.95, 0.6, 0, m_zug, fase=0.03)

# Erste-Hilfe-Kasten + Fluchtplan neben der Personaltuer Nord
kasten("ErsteHilfe", 0.35, 0.06, 0.35, -3.7, 1.7, -9.8, m_fenster, fase=0.02)
kasten("ErsteHilfe_kreuz_1", 0.2, 0.04, 0.06, -3.7, 1.7, -9.76, m_gruen, fase=0)
kasten("ErsteHilfe_kreuz_2", 0.06, 0.04, 0.2, -3.7, 1.7, -9.76, m_gruen, fase=0)
kasten("Fluchtplan", 0.3, 0.04, 0.4, -5.6, 1.7, -9.8, m_fenster, fase=0)
kasten("Fluchtplan_gruen", 0.1, 0.03, 0.08, -5.66, 1.6, -9.77, m_gruen, fase=0)
kasten("Fluchtplan_grundriss", 0.22, 0.03, 0.2, -5.6, 1.78, -9.77, m_gleiszone, fase=0)

# Ventilhandraeder an der Nordwand-Rohrleitung
for i, vx in enumerate((-5, 5)):
    zylinder(f"Ventilrad_{i}", 0.09, 0.05, vx, 5.15, -9.24, m_orange, achse="z")
    kasten(f"Ventilrad_{i}_gehaeuse", 0.12, 0.1, 0.12, vx, 5.15, -9.32, m_stahl, fase=0)

# Gelbe Rammschutzbuegel vor den Nordwand-Maschinen
for i, rx in enumerate((5.0, 8.4)):
    for j, dz in enumerate((-0.45, 0.45)):
        kasten(f"Rammschutz_{i}_pfosten_{j}", 0.08, 0.08, 0.6, rx + dz, 0.3, -7.75, m_markierung, fase=0.02)
    kasten(f"Rammschutz_{i}_buegel", 0.98, 0.08, 0.08, rx, 0.62, -7.75, m_markierung, fase=0.02)

# Feuerloescher auch an Sued- und Westwand
zylinder("Feuerloescher_sued", 0.07, 0.45, 0, 1.05, 9.46, m_zug)
kasten("Feuerloescher_sued_schild", 0.2, 0.02, 0.25, 0, 1.42, 9.53, m_zug, fase=0)
zylinder("Feuerloescher_west", 0.07, 0.45, -16.42, 1.05, 0, m_zug)
kasten("Feuerloescher_west_schild", 0.02, 0.2, 0.25, -16.49, 1.42, 0, m_zug, fase=0)

# Schalterkaesten neben den Personaltueren
kasten("Schalter_Nord", 0.12, 0.05, 0.18, -3.85, 1.1, -9.79, m_dunkel, fase=0)
kasten("Schalter_West", 0.05, 0.12, 0.18, -16.79, 1.1, 4.45, m_dunkel, fase=0)

# Kabelbruecke ueber dem Servicewagen-Schlauch + Stellplatz-Markierung fuer den Stapler
kasten("Kabelbruecke", 0.9, 0.5, 0.07, 7.4, 0.035, 1.55, m_markierung, fase=0.02)
for ex, ez in ((-1.1, -0.9), (1.1, -0.9), (-1.1, 0.9), (1.1, 0.9)):
    kasten(f"Stellplatz_L1_{ex}_{ez}".replace(".", ""), 0.4, 0.06, 0.012, -12.8 + ex - 0.17 * (1 if ex > 0 else -1), 0.012, -5.2 + ez, m_fenster, fase=0)
    kasten(f"Stellplatz_L2_{ex}_{ez}".replace(".", ""), 0.06, 0.4, 0.012, -12.8 + ex, 0.012, -5.2 + ez - 0.17 * (1 if ez > 0 else -1), m_fenster, fase=0)
# Feuerloescher an den Nordstuetzen — der klassische Werkstatt-Glaubwuerdigkeitsanker
for i, fx in enumerate((-6.8, 0, 6.8)):
    zylinder(f"Feuerloescher_{i}", 0.07, 0.45, fx, 1.05, -9.46, m_zug)
    kasten(f"Feuerloescher_{i}_schild", 0.2, 0.02, 0.25, fx, 1.42, -9.53, m_zug, fase=0)

# Sued-Requisiten gegen die toten Zonen (Kritik: leere Suedost- und Suedwest-Wand)
for i, (sx, sm) in enumerate(((11.8, m_objekt), (12.7, m_blau))):
    kasten(f"Sued_Schrank_{i}", 0.8, 0.4, 1.8, sx, 0.9, 9.4, sm)
    kasten(f"Sued_Schrank_{i}_sockel", 0.84, 0.44, 0.12, sx, 0.06, 9.4, m_dunkel, fase=0)
kasten("Sued_Palette", 1.2, 1.0, 0.12, 14.2, 0.06, 8.9, m_objekt, fase=0)
kasten("Sued_Palette_Kiste", 0.55, 0.5, 0.5, 14.1, 0.37, 8.95, m_wand)
fass("Sued_Fass_1", 10.7, 9.3, 0, m_blau)
fass("Sued_Fass_2", 10.2, 9.5, 0, m_orange)
auffangwanne("Sued_wanne_a", 9.85, 11.05, 8.95, 9.85)
# Aus dem dunklen Kasten wird eine Werkbank: Fuesse, Untergestell mit Ablage,
# Schubladenfront mit Griffen, Schraubstock, Werkzeugkasten und Werkzeugtafel.
for i, (bx, bz) in enumerate(((-3.4, 9.05), (-1.6, 9.05), (-3.4, 9.55), (-1.6, 9.55))):
    kasten(f"Sued_Werkbank_fuss_{i}", 0.08, 0.08, 0.3, bx, 0.15, bz, m_stahl, fase=0)
kasten("Sued_Werkbank", 1.9, 0.66, 0.56, -2.5, 0.58, 9.3, m_stahl)
kasten("Sued_Werkbank_Platte", 2.0, 0.75, 0.08, -2.5, 0.9, 9.3, m_dunkel)
kasten("Sued_Werkbank_Ablage", 1.8, 0.6, 0.04, -2.5, 0.16, 9.3, m_objekt, fase=0)
for i, (sx, sm) in enumerate(((-3.05, m_blau), (-2.5, m_orange), (-1.95, m_blau))):
    kasten(f"Sued_Werkbank_schublade_{i}", 0.46, 0.05, 0.34, sx, 0.62, 9.66, sm, fase=0.02)
    kasten(f"Sued_Werkbank_griff_{i}", 0.2, 0.04, 0.04, sx, 0.74, 9.63, m_dunkel, fase=0)
kasten("Sued_Werkbank_Schraubstock", 0.25, 0.3, 0.25, -1.7, 1.065, 9.35, m_dunkel)
kasten("Sued_Werkbank_Werkzeugkasten", 0.5, 0.3, 0.3, -3.0, 1.09, 9.3, m_zug)
kasten("Sued_Werkzeugtafel", 1.6, 0.06, 0.9, -2.5, 1.75, 9.78, m_dunkel, fase=0)
for i, (wx, wy, wm) in enumerate(((-3.1, 1.95, m_orange), (-2.7, 1.85, m_stahl),
                                  (-2.3, 2.0, m_orange), (-1.9, 1.6, m_objekt))):
    kasten(f"Sued_Werkzeug_{i}", 0.1, 0.05, 0.3, wx, wy, 9.72, wm, fase=0)
fass("Sued_Fass_3", -4.1, 9.3, 0, m_dunkel)
auffangwanne("Sued_wanne_b", -4.45, -3.75, 8.95, 9.65)
lade_asset("factory_box-large.glb", "Sued_Kiste", -5.6, 0, 9.0, dreh_y=0.5, ziel_hoehe=0.7, einfaerbung=m_blau)

# ---- Station 1: Meisterbuero -------------------------------------------------
kasten("Station_1_meisterbuero", 4, 3, 2.6, -10.5, 1.3, -7.5, m_wand)
kasten("Station_1_buerodach", 4.3, 3.3, 0.1, -10.5, 2.65, -7.5, m_dunkel)
# Tuer auf der OSTSEITE: die alte Suedtuer stand komplett hinter dem Schreibtisch,
# niemand kam ins Buero. Fenster schmaler und nach Norden gerueckt, dazwischen
# ein 40-cm-Pfeiler.
kasten("Station_1_buerofenster", 0.06, 1.4, 0.9, -8.47, 1.9, -8.1, m_hallenglas, fase=0)
kasten("Station_1_buerotuer", 0.06, 0.8, 1.9, -8.44, 0.95, -6.6, m_blau, fase=0)   # 2.5 cm VOR dem Rahmen
kasten("Station_1_buerotuer_rahmen", 0.05, 0.9, 2.0, -8.46, 1.0, -6.6, m_relief, fase=0)
kasten("Station_1_tuerklinke", 0.06, 0.1, 0.04, -8.40, 1.0, -6.32, m_dunkel, fase=0)
# Pinnwand haengt jetzt an der SUEDfront des Bueros, also frontal zur Stationskamera.
# An der Ostflanke lag sie zu drei Vierteln hinter dem Text-Panel; das Buerofenster
# ist dafuer auf die Ostflanke gewandert.
kasten("Station_1_pinnwand", 2.8, 0.08, 1.15, -10.85, 2.0, -5.9, m_objekt)
kasten("Station_1_pinnwand_rahmen", 2.92, 0.05, 1.27, -10.85, 2.0, -5.93, m_stahlhell, fase=0)
# Zettel nur oberhalb der Schrank-Oberkante (1.90) — darunter waeren sie verdeckt
# und staeken geometrisch im Schrank.
for i in range(6):
    zx = -11.75 + (i % 3) * 0.9
    zy = 2.42 - (i // 3) * 0.32
    kasten(f"Station_1_zettel_{i}", 0.3, 0.03, 0.28, zx, zy, -5.845, m_fenster, fase=0)
    kasten(f"Station_1_zettel_{i}_zeile", 0.22, 0.035, 0.04, zx, zy + 0.07, -5.827, m_objekt, fase=0)
lade_asset("furniture_desk.glb", "Station_1_schreibtisch", -7.8, 0, -5.3, dreh_y=3.14159, ziel_breite=1.6, einfaerbung=m_objekt)
# Desk-Platte real: x -9.38..-7.78, z -5.32..-4.47, Oberkante 0.837 (Eckpivot)
lade_asset("furniture_chairDesk.glb", "Station_1_buerostuhl", -8.55, 0, -4.2, ziel_hoehe=0.95, einfaerbung=m_blau)
lade_asset("furniture_computerScreen.glb", "Station_1_monitor", -8.6, 0.84, -5.1, ziel_hoehe=0.45, einfaerbung=m_dunkel)
lade_asset("furniture_computerKeyboard.glb", "Station_1_tastatur", -8.35, 0.84, -4.72, ziel_breite=0.4, einfaerbung=m_dunkel)
# Gemessen: der Schrank belegt ab dem Anker x +1.92 und z -0.60 (Kenney-Eckpivot).
# Vorher stand er zu einem Drittel in der Bueroaussenwand und schnitt durch die
# Pinnwand; jetzt steht er sauber davor und staffelt den Vordergrund.
lade_asset("furniture_bookcaseClosedWide.glb", "Station_1_aktenschrank", -12.05, 0, -5.24, ziel_hoehe=1.9, einfaerbung=m_objekt)

# ---- Station 2: Datenraum-Regal ---------------------------------------------
kasten("Station_2_datenraum", 0.08, 1.0, 2.2, -4.2, 1.1, -6, m_blau)
kasten("Station_2_regalwange", 0.08, 1.0, 2.2, -1.8, 1.1, -6, m_blau)
kasten("Station_2_kopfblende", 2.56, 1.04, 0.1, -3, 2.25, -6, m_dunkel)
for i, by in enumerate((0.35, 0.95, 1.55, 2.15)):
    kasten(f"Station_2_regalbrett_{i}", 2.5, 1.0, 0.06, -3, by, -6, m_dunkel, fase=0)
ordner_farben = (m_blau, m_orange, m_zug, m_gruen, m_blau, m_orange)
for i in range(6):
    kasten(f"Station_2_ordner_{i}", 0.2, 0.4, 0.5, -3.9 + i * 0.36, 1.85, -6, ordner_farben[i], fase=0)
kisten_farben = (m_wand, m_blau, m_orange, m_wand, m_blau)
for i in range(5):
    kasten(f"Station_2_kiste_{i}", 0.3, 0.5, 0.4, -3.8 + i * 0.42, 1.2, -6, kisten_farben[i], fase=0)
for i in range(4):  # unterstes Fach nicht leer lassen
    kasten(f"Station_2_kiste_u_{i}", 0.34, 0.5, 0.4, -3.7 + i * 0.5, 0.6, -6, (m_wand, m_orange, m_wand, m_blau)[i], fase=0)
# Die losen Wuerfel lesen jetzt als Transportkisten: Deckelrand und zwei Spanngurte.
# Zwei der fuenf sind auf eine Palette gestapelt — das erzaehlt "Chaos wird sortiert",
# statt nur nackte Kuben auf den Boden zu legen.
chaos = [(-4.3, -4.8, 0.5, 0.35, m_objekt), (-2.7, -4.7, 0.55, 0.9, m_objekt),
         (-2.1, -5.1, 0.4, -0.2, m_blau)]
for i, (cx, cz, cg, cr, cm) in enumerate(chaos):
    kasten(f"Station_2_chaos_{i}", cg, cg, cg, cx, cg / 2, cz, cm, drehung=(0, 0, cr))
    kasten(f"Station_2_chaos_{i}_deckel", cg * 1.05, cg * 1.05, 0.04, cx, cg - 0.02, cz, m_dunkel,
           drehung=(0, 0, cr), fase=0)
    for j, gy in enumerate((cg * 0.32, cg * 0.7)):
        kasten(f"Station_2_chaos_{i}_gurt_{j}", cg * 1.03, cg * 1.03, 0.025, cx, gy, cz, m_markierung,
               drehung=(0, 0, cr), fase=0)
kasten("Station_2_palette", 1.2, 1.0, 0.12, -3.35, 0.06, -5.15, m_objekt, fase=0)
kasten("Station_2_stapel_1", 0.5, 0.45, 0.45, -3.35, 0.345, -5.15, m_orange)
kasten("Station_2_stapel_2", 0.45, 0.4, 0.35, -3.35, 0.745, -5.15, m_blau)
fass("Station_2_fass_1", -1.4, -5.0, 0, m_dunkel)
fass("Station_2_fass_2", -1.0, -5.5, 0, m_blau)
auffangwanne("Station_2_wanne", -1.75, -0.65, -5.85, -4.65)
kasten("Station_2_zettel_am_regal", 0.03, 0.28, 0.38, -4.26, 1.5, -5.8, m_fenster, fase=0)

# ---- Station 3: Bedienterminal ----------------------------------------------
# Bedienterminal in Menschengroesse: Saeule mittig, Pult VOR dem Schirm (kamerasichtbar)
kasten("Station_3_terminal_saeule", 0.5, 0.5, 1.2, 7, 0.6, -4.3, m_dunkel)
kasten("Station_3_terminal_gehaeuse", 1.0, 0.35, 0.65, 7, 1.35, -4.15, m_blau)
kasten("Station_3_terminal_pult", 1.2, 0.5, 0.1, 7, 0.95, -3.95, m_stahl)
kasten("Station_3_tastatur", 0.6, 0.28, 0.05, 7, 1.02, -3.9, m_dunkel, fase=0)
kasten("Station_3_bodenplatte", 2.2, 1.6, 0.03, 7, 0.02, -4.0, m_riffel, fase=0)  # hell: dunkel las als Loch
bpy.ops.mesh.primitive_plane_add(size=1, location=pos(7, 1.35, -3.95))
monitor = bpy.context.active_object
monitor.name = "Monitor_Bildschirm"
monitor.scale = (0.8, 0.5, 1)
monitor.rotation_euler = (1.5708, 0, 0)  # senkrecht, Front Richtung Sueden
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
monitor.data.materials.append(material("Bildschirm", (0.10, 0.12, 0.16), rauheit=0.25))

# ---- Station 4: Anzeigetafel ------------------------------------------------
kasten("Station_4_anzeigetafel", 3.2, 0.15, 1.8, 9, 2, 5.8, m_dunkel)
kasten("Station_4_rahmen_oben", 3.3, 0.18, 0.08, 9, 2.92, 5.8, m_stahlhell, fase=0)
kasten("Station_4_rahmen_unten", 3.3, 0.18, 0.08, 9, 1.08, 5.8, m_stahlhell, fase=0)
kasten("Station_4_rahmen_west", 0.08, 0.18, 1.92, 7.36, 2, 5.8, m_stahlhell, fase=0)
kasten("Station_4_rahmen_ost", 0.08, 0.18, 1.92, 10.64, 2, 5.8, m_stahlhell, fase=0)
for i in range(4):
    breite = 2.6 - (i % 2) * 0.5
    kasten(f"Station_4_zeile_{i}", breite, 0.04, 0.14, 9.2, 2.42 - i * 0.36, 5.71, m_stahl, fase=0)
kasten("Station_4_titelzeile", 1.8, 0.04, 0.2, 9.5, 2.74, 5.71, m_markierung, fase=0)
# Rueckseite mit Streben (Totale schaut von hinten drauf) + Standzone davor
kasten("Station_4_strebe_1", 3.2, 0.05, 0.12, 9, 1.5, 5.92, m_stahlhell, fase=0)
kasten("Station_4_strebe_2", 3.2, 0.05, 0.12, 9, 2.5, 5.92, m_stahlhell, fase=0)
kasten("Station_4_bodenplatte", 2.4, 1.6, 0.03, 9, 0.02, 4.6, m_riffel, fase=0)  # hell: dunkel las als Loch
# Suedwand-Umfeld der Station 4 fuellen
kasten("Station_4_werkzeugtafel", 1.6, 0.06, 1.0, 6.8, 1.7, 9.78, m_dunkel, fase=0)
for i, (wx2, wy2, wm2) in enumerate(((6.3, 1.9, m_orange), (6.7, 1.8, m_stahl), (7.1, 1.95, m_orange), (7.3, 1.55, m_objekt))):
    kasten(f"Station_4_werkzeug_{i}", 0.1, 0.05, 0.3, wx2, wy2, 9.72, wm2, fase=0)
fass("Station_4_fass_1", 8.3, 9.4, 0, m_blau)
fass("Station_4_fass_2", 8.8, 9.2, 0, m_dunkel)
auffangwanne("Station_4_wanne", 7.95, 9.15, 8.85, 9.75)
kasten("Station_4_pfosten_west", 0.15, 0.15, 2.9, 7.6, 1.45, 5.8, m_stahl)
kasten("Station_4_pfosten_ost", 0.15, 0.15, 2.9, 10.4, 1.45, 5.8, m_stahl)
# Ersatz-Mittelgrund fuer den weggerueckten Servicewagen (z=8.5, damit die
# Sued-Schraenke ab z 9.18 frei bleiben)
kasten("Station_4_palette", 1.2, 1.0, 0.12, 11.4, 0.06, 8.5, m_objekt, fase=0)
kasten("Station_4_kiste_1", 0.5, 0.45, 0.45, 11.2, 0.345, 8.4, m_blau)
kasten("Station_4_kiste_2", 0.5, 0.45, 0.45, 11.65, 0.345, 8.65, m_orange)

# ---- Station 5: Pruefstand ---------------------------------------------------
# Der Pruefstand prueft jetzt sichtbar etwas: ein Radsatz liegt auf zwei Laufrollen.
# Platte 0.4 m tiefer gemacht (1.2 -> 1.6), damit die Rollenboecke neben den Rollen
# Platz auf der Platte haben statt in ihnen zu stecken.
kasten("Station_5_pruefstand", 2.8, 1.6, 0.5, 2, 0.25, 6, m_stahl)
kasten("Station_5_warnkante_west", 0.08, 1.64, 0.52, 0.64, 0.26, 6, m_markierung, fase=0)
kasten("Station_5_warnkante_ost", 0.08, 1.64, 0.52, 3.36, 0.26, 6, m_markierung, fase=0)
kasten("Station_5_aufbau", 1.4, 0.9, 0.9, 1.6, 0.95, 6, m_blau)
kasten("Station_5_aufbau_blende", 1.44, 0.06, 0.3, 1.6, 1.25, 5.55, m_dunkel, fase=0)
zylinder("Station_5_drehknopf", 0.06, 0.06, 1.3, 1.0, 5.52, m_orange, achse="z")
kasten("Station_5_panel", 0.4, 0.05, 0.3, 1.3, 1.05, 5.56, m_fenster, fase=0)
# Schaltschrank-Front: Lueftungsschlitze, Tuerfuge, Griff, Taster — alles unterhalb
# der Blende (y 1.10-1.40) und oestlich des Panels (x 1.10-1.50), damit nichts steckt.
for i, sy in enumerate((0.72, 0.80, 0.88)):
    kasten(f"Station_5_schlitz_{i}", 0.5, 0.03, 0.03, 1.9, sy, 5.52, m_dunkel, fase=0)
kasten("Station_5_tuerfuge", 0.03, 0.02, 0.52, 1.62, 0.80, 5.53, m_dunkel, fase=0)
kasten("Station_5_griff", 0.1, 0.05, 0.04, 1.92, 0.80, 5.5, m_dunkel, fase=0)
for i, tx in enumerate((1.62, 1.74, 1.86)):
    zylinder(f"Station_5_taster_{i}", 0.035, 0.06, tx, 1.05, 5.5,
             (m_gruen, m_zug, m_markierung)[i], achse="z")
zylinder("Station_5_warnleuchte", 0.06, 0.1, 1.6, 1.45, 6.0, m_orange)
# Laufrollen auf Boecken, darauf der Pruefling. Achshoehe analytisch: die Rolle
# (r 0.18) traegt das Rad (r 0.38) im Abstand 0.25 -> dy = sqrt(0.56^2 - 0.25^2).
for i, rx in enumerate((2.6, 3.1)):
    zylinder(f"Station_5_rolle_{i}", 0.18, 1.26, rx, 0.8, 6, m_dunkel, achse="z", ecken=32)
    for j, bz in enumerate((5.3, 6.7)):
        kasten(f"Station_5_rollenbock_{i}_{j}", 0.3, 0.16, 0.3, rx, 0.65, bz, m_stahlhell)
radsatz("Station_5_pruefling", 2.85, 6.0, y_achse=1.301)
# Messarm greift von der Schaltschrank-Oberkante zum Rad, ohne es zu beruehren
rohr_mit_bogen("Station_5_messarm", [(2.1, 1.45, 6.0), (2.35, 1.45, 6.0), (2.45, 1.6, 6.0)], 0.03, m_dunkel)
kasten("Station_5_trittrost", 2.8, 0.8, 0.03, 2.0, 0.025, 7.2, m_riffel, fase=0)
kasten("Station_5_kabelkanal", 2.6, 0.18, 0.08, 2, 0.06, 5.3, m_dunkel, fase=0)
# Ablagebock westlich des Stands — fuellt die leere linke Bildhaelfte der Stationsansicht
for i, (bx, bz) in enumerate(((4.2, 4.95), (5.8, 4.95), (4.2, 5.45), (5.8, 5.45))):
    kasten(f"Station_5_bockfuss_{i}", 0.08, 0.08, 0.18, bx, 0.09, bz, m_stahl, fase=0)
kasten("Station_5_ablagebock", 1.7, 0.66, 0.62, 5.0, 0.49, 5.2, m_stahl)
kasten("Station_5_ablageplatte", 1.8, 0.75, 0.08, 5.0, 0.84, 5.2, m_dunkel)
kasten("Station_5_ablage_kiste", 0.4, 0.4, 0.24, 4.5, 1.0, 5.2, m_blau)
zylinder("Station_5_ablage_rolle", 0.09, 0.5, 5.5, 0.97, 5.2, m_gummi, achse="z")
# Strom-/Kabelanbindung des Pruefstands zur Suedwand (westlich am Schweissplatz vorbei)
rohr_mit_bogen("Station_5_kabel", [(1.3, 0.1, 6.9), (1.2, 0.1, 8.6), (1.2, 0.45, 9.6)], 0.04, m_dunkel)
kasten("Station_5_anschluss", 0.5, 0.15, 0.7, 1.2, 0.9, 9.78, m_objekt)

# ---- Datenspur: Werkstattdaten dort zeigen, wo sie entstehen ------------------
# Die Dramaturgie ist eine Data-Science-Geschichte (eine Kennzahl von der Halle bis
# in die Planungsrunde), aber die Requisiten waren rein physisch. Jetzt tragen die
# Stationsposen ihre Datenquellen: Scanner und Tablet im Meisterbuero (Auftraege,
# Stoermeldungen), Datenkatalog-Poster im Datenraum (Quellen -> Tabellen),
# Messprotokoll, Messschieber und ein Datenlogger am Pruefling (Messwerte).
# Alles gegreekt: Balken statt Schrift, keine Ziffern.

# Station 1 — Handscanner und Tablet auf dem Schreibtisch (Platte x -9.38..-7.78,
# z -5.32..-4.47, Oberkante 0.84 wie der Monitorfuss)
kasten("Station_1_tablet", 0.27, 0.19, 0.012, -8.0, 0.846, -5.05, m_dunkel, fase=0)
kasten("Station_1_tablet_schirm", 0.245, 0.165, 0.004, -8.0, 0.854, -5.05, m_stahlhell, fase=0)
kasten("Station_1_tablet_zeile_0", 0.16, 0.02, 0.003, -8.03, 0.8575, -5.10, m_blau, fase=0)
kasten("Station_1_tablet_zeile_1", 0.12, 0.02, 0.003, -8.05, 0.8575, -5.04, m_stahl, fase=0)
kasten("Station_1_tablet_zeile_2", 0.14, 0.02, 0.003, -8.04, 0.8575, -4.98, m_stahl, fase=0)
kasten("Station_1_scanner_griff", 0.045, 0.035, 0.11, -7.95, 0.895, -4.65, m_dunkel, fase=0.01)
kasten("Station_1_scanner_kopf", 0.17, 0.075, 0.06, -7.92, 0.98, -4.65, m_dunkel, fase=0.015)
kasten("Station_1_scanner_fenster", 0.02, 0.05, 0.03, -7.835, 0.98, -4.65, m_zug, fase=0)

# Station 2 — Datenkatalog-Tafel an der oestlichen Regalwange (x -1.76), frontal zur
# Datenraum-Kamera. An der Nordwand verschwand sie aus dieser Pose hinter dem
# Lueftungskanal. Links (Betrachter: +z) verstreute Quellen, ein Uebergangsbalken,
# rechts zwei geordnete Tabellenraster — Chaos wird Struktur, in einem Bild.
kasten("Station_2_datenkatalog_rahmen", 0.02, 0.96, 0.66, -1.75, 1.45, -6.0, m_dunkel, fase=0)
kasten("Station_2_datenkatalog", 0.03, 0.9, 0.6, -1.745, 1.45, -6.0, m_fenster, fase=0)
for i, (qy, qz, qm) in enumerate(((1.62, -5.62, m_blau), (1.66, -5.78, m_zug), (1.52, -5.92, m_gruen),
                                  (1.45, -5.66, m_orange), (1.34, -5.84, m_markierung),
                                  (1.27, -5.98, m_stahl), (1.25, -5.62, m_blau))):
    kasten(f"Station_2_datenkatalog_quelle_{i}", 0.02, 0.06, 0.06, -1.72, qy, qz, qm, fase=0)
kasten("Station_2_datenkatalog_pfeil", 0.02, 0.08, 0.02, -1.72, 1.45, -6.03, m_stahl, fase=0)
for t, ty in enumerate((1.66, 1.40)):
    kasten(f"Station_2_datenkatalog_kopf_{t}", 0.02, 0.28, 0.025, -1.72, ty, -6.25, m_blau, fase=0)
    for z, dy in enumerate((0.06, 0.11, 0.16)):
        kasten(f"Station_2_datenkatalog_zeile_{t}_{z}", 0.02, 0.28, 0.015, -1.72, ty - dy, -6.25, m_stahl, fase=0)

# Station 5 — Messprotokoll-Klemmbrett und Messschieber auf der Ablage (Oberkante 0.88),
# Datenlogger mit gruener LED auf der Achse des Prueflings, Kabel in den Aufbau
kasten("Station_5_klemmbrett", 0.32, 0.23, 0.01, 5.0, 0.885, 4.97, m_dunkel, fase=0)
kasten("Station_5_klemmbrett_blatt", 0.29, 0.20, 0.004, 5.0, 0.892, 4.97, m_fenster, fase=0)
for i, lz in enumerate((5.04, 5.00, 4.96, 4.92, 4.88)):
    kasten(f"Station_5_klemmbrett_zeile_{i}", 0.20 if i % 2 else 0.24, 0.012, 0.003, 4.98, 0.8955, lz, m_stahl, fase=0)
kasten("Station_5_klemmbrett_clip", 0.08, 0.04, 0.02, 5.13, 0.9, 4.97, m_stahlhell, fase=0)
kasten("Station_5_messschieber", 0.22, 0.025, 0.008, 4.95, 0.884, 5.5, m_stahlhell, fase=0)
kasten("Station_5_messschieber_schieber", 0.03, 0.05, 0.02, 4.9, 0.89, 5.5, m_stahl, fase=0)
kasten("Station_5_logger", 0.08, 0.07, 0.06, 2.85, 1.386, 5.75, m_dunkel, fase=0.01)
kasten("Station_5_logger_led", 0.015, 0.015, 0.008, 2.85, 1.42, 5.72, m_gruen, fase=0)
rohr_mit_bogen("Station_5_logger_kabel", [(2.85, 1.37, 5.72), (2.85, 1.15, 5.62), (2.25, 1.0, 5.62)], 0.012, m_dunkel)

# Schweissplatz an der Suedwand — ersetzt die orange Kenney-Haube, die als
# unlesbarer Bogen die linke untere Ecke der Totale dominierte.
for i, (wx, wz, wdx, wdz) in enumerate(((4.3, 9.7, 1.56, 0.06), (3.52, 9.25, 0.06, 0.9), (5.08, 9.25, 0.06, 0.9))):
    kasten(f"Schweiss_Wand_{i}", wdx, wdz, 1.9, wx, 1.15, wz, m_gruen, fase=0)
for i, (fx, fz) in enumerate(((3.52, 8.85), (5.08, 8.85), (3.52, 9.67), (5.08, 9.67))):
    kasten(f"Schweiss_Wandfuss_{i}", 0.1, 0.1, 0.2, fx, 0.1, fz, m_stahl, fase=0)
kasten("Schweiss_Tisch", 1.2, 0.7, 0.75, 4.3, 0.375, 9.35, m_stahl)
kasten("Schweiss_Tisch_platte", 1.3, 0.8, 0.06, 4.3, 0.78, 9.35, m_dunkel)
kasten("Schweiss_Absaugkonsole", 0.3, 0.24, 0.3, 4.3, 2.6, 9.84, m_stahl)
rohr_mit_bogen("Schweiss_Absaugarm", [(4.3, 2.6, 9.78), (4.3, 2.1, 9.55), (4.3, 1.6, 9.35)], 0.07, m_stahlhell)
kegel("Schweiss_Haube", 0.26, 0.24, 4.3, 1.46, 9.35, m_stahlhell)
kasten("Schweiss_Filter", 0.5, 0.45, 0.9, 5.6, 0.45, 9.5, m_objekt)
kasten("Schweiss_Geraet", 0.5, 0.4, 0.75, 3.0, 0.495, 8.9, m_orange)
for i, (gx, gz) in enumerate(((-0.17, -0.13), (0.17, -0.13), (-0.17, 0.13), (0.17, 0.13))):
    zylinder(f"Schweiss_Geraet_rad_{i}", 0.06, 0.05, 3.0 + gx, 0.06, 8.9 + gz, m_gummi, achse="z")
rohr_mit_bogen("Schweiss_Schlauch", [(3.2, 0.8, 8.95), (3.7, 0.7, 9.15), (4.0, 0.82, 9.3)], 0.035, m_gummi)

# ---- Station 6: Besprechung (Kenney-Moebel) ---------------------------------
lade_asset("furniture_table.glb", "Station_6_besprechung_tisch", -9, 0, 6, ziel_breite=2.2, einfaerbung=m_objekt)
# Kenney-Stuhl hat Eck-Pivot: bei dreh=0 belegt er (x..x+0.4, z-0.4..z),
# bei dreh=pi (x-0.4..x, z..z+0.4). Lehnen zeigen vom Tisch WEG (Sitz zum Tisch);
# Anker so umgerechnet, dass die Standflaechen unveraendert bleiben.
stuehle = [(-8.7, 4.82, 0), (-7.5, 4.82, 0), (-8.3, 6.01, 3.14159), (-7.1, 6.01, 3.14159)]
for i, (sx, sz, dreh) in enumerate(stuehle):
    lade_asset("furniture_chair.glb", f"Station_6_stuhl_{i}", sx, 0, sz, dreh_y=dreh, ziel_hoehe=0.95, einfaerbung=m_blau)
# Laptop als Eigenbau (das Kenney-Modell liest sich aus der Stationskamera nicht)
# Tischplatte real: x -9.0..-6.8, z 4.83..6.0, Oberkante 0.854 (Kenney-Eckpivot!)
kasten("Station_6_laptop_basis", 0.35, 0.25, 0.02, -8.2, 0.865, 5.6, m_dunkel, fase=0)
kasten("Station_6_laptop_deckel", 0.35, 0.02, 0.24, -8.2, 0.965, 5.48, m_dunkel, fase=0, drehung=(0.5, 0, 0))
kasten("Station_6_papier", 0.3, 0.21, 0.015, -7.4, 0.862, 5.6, m_fenster, fase=0)
zylinder("Station_6_becher_1", 0.04, 0.1, -7.2, 0.905, 5.15, m_fenster)
zylinder("Station_6_becher_2", 0.04, 0.1, -8.7, 0.905, 5.3, m_blau)
for i, om in enumerate((m_blau, m_orange, m_gruen)):
    kasten(f"Station_6_ordner_{i}", 0.08, 0.28, 0.32, -11.8 + i * 0.3, 0.96, 7, om, fase=0)
kasten("Station_6_teppich", 3.4, 2.8, 0.02, -9, 0.015, 6, m_gleiszone, fase=0)
for i, (my, mm) in enumerate(((1.85, m_blau), (1.7, m_zug), (1.55, m_gruen))):
    kasten(f"Station_6_marker_{i}", 0.5 - i * 0.12, 0.02, 0.05, -11.3, my, 8.16, mm, fase=0)
lade_asset("furniture_pottedPlant.glb", "Station_6_pflanze", -12.5, 0, 8.4, ziel_hoehe=1.1)
kasten("Station_6_sideboard", 1.6, 0.5, 0.8, -11.5, 0.4, 7, m_objekt)
lade_asset("furniture_kitchenCoffeeMachine.glb", "Station_6_kaffee", -11.15, 0.8, 6.85, dreh_y=1.5708, ziel_hoehe=0.38)
kasten("Station_6_whiteboard", 1.6, 0.06, 1.0, -11.2, 1.7, 8.2, m_fenster)
kasten("Station_6_whiteboard_fuss_1", 0.08, 0.08, 1.2, -11.9, 0.6, 8.2, m_dunkel, fase=0)
kasten("Station_6_whiteboard_fuss_2", 0.08, 0.08, 1.2, -10.5, 0.6, 8.2, m_dunkel, fase=0)

# ---- Requisiten --------------------------------------------------------------
for i, (fx, fz, fm) in enumerate(((-15.6, -8.2, m_blau), (-15.0, -8.5, m_dunkel), (-15.3, -7.6, m_orange))):
    fass(f"Requisite_Fass_{i}", fx, fz, 0, fm)
kasten("Requisite_Palette", 1.2, 1.0, 0.12, -6.5, 0.06, -8.6, m_objekt, fase=0)
kasten("Requisite_Werkbank", 2.2, 0.7, 0.85, -16.2, 0.43, 3, m_stahl)
kasten("Requisite_Werkbank_Platte", 2.2, 0.75, 0.08, -16.2, 0.9, 3, m_dunkel)
kasten("Requisite_Werkzeugtafel", 0.06, 1.8, 1.0, -16.85, 1.7, 3, m_dunkel, fase=0)
werkzeuge = ((-16.8, 2.0, 2.5, m_orange), (-16.8, 1.9, 2.8, m_stahl), (-16.8, 2.05, 3.1, m_orange),
             (-16.8, 1.85, 3.4, m_objekt), (-16.8, 1.5, 2.6, m_stahl), (-16.8, 1.45, 3.3, m_orange))
for i, (wx, wy, wz, wm) in enumerate(werkzeuge):
    kasten(f"Requisite_Werkzeug_{i}", 0.05, 0.1, 0.3, wx, wy, wz, wm, fase=0)
kasten("Requisite_Wagen", 0.9, 0.5, 0.55, -13, 0.28, -3.4, m_blau)
kasten("Requisite_Wagen_Griff", 0.06, 0.4, 0.5, -13.45, 0.75, -3.4, m_dunkel, fase=0)
for i, (sx, sm) in enumerate(((13.5, m_objekt), (14.4, m_blau))):
    kasten(f"Requisite_Schrank_{i}", 0.8, 0.4, 1.8, sx, 0.9, -9.6, sm)
    kasten(f"Requisite_Schrank_{i}_sockel", 0.84, 0.44, 0.12, sx, 0.06, -9.6, m_dunkel, fase=0)
    kasten(f"Requisite_Schrank_{i}_fuge", 0.03, 0.05, 1.5, sx, 0.95, -9.38, m_dunkel, fase=0)
    for j, gy in enumerate((0.8, 1.1)):
        kasten(f"Requisite_Schrank_{i}_griff_{j}", 0.12, 0.05, 0.04, sx - 0.12, gy, -9.38, m_dunkel, fase=0)
kasten("Requisite_Leiter", 0.5, 0.08, 2.4, 15.5, 1.2, -9.7, m_orange, fase=0)

# ---- Kenney-Industriemodelle: Maschinenpark, Ventil, Tor, Kleinteile --------
lade_asset("factory_machine.glb", "Maschine_Nord_1", 5.0, 0, -9.2, ziel_hoehe=1.8, einfaerbung=m_blau)
lade_asset("factory_machine-window.glb", "Maschine_Nord_2", 8.4, 0, -9.2, ziel_hoehe=1.8, einfaerbung=m_blau)
lade_asset("factory_machine-fortified.glb", "Maschine_West", -16.1, 0, 7.5, dreh_y=1.5708, ziel_hoehe=1.8, einfaerbung=m_blau)
lade_asset("factory_pipe-large-valve.glb", "Ventil_Ost", 16.5, 0, -6.5, dreh_y=-1.5708, ziel_hoehe=1.5, einfaerbung=m_stahlhell)
# Aufgeschobenes Schiebetorblatt (Eigenbau — das Kenney-Tor hat einen kaputten Pivot)
kasten("Tor_Blatt", 0.12, 3.6, 4.2, 17.12, 2.1, 4.1, m_orange, fase=0.03)
kasten("Tor_Blatt_Riegel", 0.14, 3.4, 0.18, 17.11, 2.1, 4.1, m_dunkel, fase=0)
kasten("Tor_Schiene", 0.06, 8.0, 0.08, 17.15, 4.45, 2.2, m_dunkel, fase=0)
for i, (cx, cz) in enumerate(((-8.2, 1.55), (-12, 1.5), (-15.6, 1.5), (5.8, 2.6))):
    lade_asset("factory_cone.glb", f"Pylone_{i}", cx, 0, cz, ziel_hoehe=0.5, einfaerbung=m_orange)
lade_asset("factory_box-large.glb", "Kiste_Palette", -6.5, 0.12, -8.6, dreh_y=0.2, ziel_hoehe=0.7)  # Plane-Kiste AUF der Palette
lade_asset("factory_box-long.glb", "Kiste_Werkbank", -15.9, 0, 4.6, ziel_hoehe=0.5)
lade_asset("factory_box-small.glb", "Kiste_Empore", -16.2, 3.13, -6.9, dreh_y=0.8, ziel_hoehe=0.45)

# ---- Gabelstapler (Eigenbau — unverwechselbare Silhouette, passt zur Palette) ----
def gabelstapler(name, x, z, dreh_y=0.0, farbe=None):
    """Klassischer Stapler, Fahrtrichtung +x (Mast und Gabeln vorn)."""
    farbe = farbe or m_markierung
    import math
    c, s = math.cos(dreh_y), math.sin(dreh_y)

    def p(dx, dz):
        return x + dx * c - dz * s, z + dx * s + dz * c

    def teil(tname, laenge, tiefe, hoehe, dx, y, dz, mat, fase=0.03):
        px, pz = p(dx, dz)
        kasten(f"{name}_{tname}", laenge, tiefe, hoehe, px, y, pz, mat,
               drehung=(0, 0, -dreh_y), fase=fase)

    teil("chassis", 1.15, 0.95, 0.5, -0.1, 0.5, 0, farbe, fase=0.06)
    teil("gegengewicht", 0.4, 0.9, 0.55, -0.75, 0.55, 0, farbe, fase=0.08)
    teil("sitz", 0.4, 0.45, 0.35, -0.25, 0.93, 0, m_dunkel)
    teil("lenksaeule", 0.06, 0.06, 0.4, 0.25, 1.0, 0, m_dunkel, fase=0)
    teil("lenkrad", 0.16, 0.16, 0.05, 0.28, 1.2, 0, m_dunkel, fase=0)
    for dx, dz in ((0.28, -0.38), (0.28, 0.38), (-0.62, -0.38), (-0.62, 0.38)):
        teil(f"dachpfosten_{dx}_{dz}".replace(".", ""), 0.06, 0.06, 1.1, dx, 1.3, dz, m_dunkel, fase=0)
    teil("schutzdach", 0.95, 0.9, 0.07, -0.17, 1.9, 0, farbe)
    teil("warnleuchte", 0.1, 0.1, 0.1, -0.55, 1.99, 0, m_orange, fase=0)
    for dz in (-0.28, 0.28):  # Mast
        teil(f"mast_{'n' if dz < 0 else 's'}", 0.08, 0.08, 1.85, 0.62, 0.93, dz, m_dunkel, fase=0)
    teil("mast_steg_1", 0.08, 0.62, 0.07, 0.62, 1.7, 0, m_dunkel, fase=0)
    teil("mast_steg_2", 0.08, 0.62, 0.07, 0.62, 0.9, 0, m_dunkel, fase=0)
    teil("gabeltraeger", 0.07, 0.85, 0.3, 0.7, 0.35, 0, m_stahl, fase=0)
    for dz in (-0.25, 0.25):  # Gabeln
        teil(f"gabel_{'n' if dz < 0 else 's'}", 0.85, 0.1, 0.05, 1.18, 0.06, dz, m_stahl, fase=0)
    # Echte runde Raeder mit Felgen — Achse folgt der Fahrzeugdrehung (Track-Quaternion)
    achse_blender = Vector((-s, -c, 0))
    for dx, dz in ((0.35, -0.5), (0.35, 0.5), (-0.6, -0.5), (-0.6, 0.5)):
        r = 0.2 if dx < 0 else 0.17
        px, pz = p(dx, dz)
        for suffix, radius, dicke, mat in (("reifen", r, 0.16, m_gummi), ("felge", r * 0.55, 0.17, m_stahlhell)):
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=dicke,
                                                location=pos(px, r, pz))
            rad = bpy.context.active_object
            rad.name = f"{name}_{suffix}_{dx}_{dz}".replace(".", "")
            rad.rotation_mode = "QUATERNION"
            rad.rotation_quaternion = achse_blender.to_track_quat("Z", "Y")
            rad.data.materials.append(mat)


gabelstapler("Stapler_1", -12.8, -5.2, dreh_y=0.9)
gabelstapler("Stapler_2", 13.2, 4.6, dreh_y=2.5, farbe=m_orange)
# Ersatzrad als wartendes Teil an der Westwand
lade_asset("car_wheel-truck.glb", "Ersatzrad", -15.8, 0, 5.6, ziel_breite=0.6)

# ---- Mehr Werkstatt-Ausstattung (Factory Kit) -------------------------------
kasten("Foerderband_Sockel", 2.4, 0.75, 0.45, 0.3, 0.225, -8.55, m_stahl)
lade_asset("factory_conveyor-long.glb", "Foerderband", 0.3, 0.45, -8.55, ziel_breite=2.6, einfaerbung=m_blau)
lade_asset("factory_box-small.glb", "Foerderband_Kiste", 0.1, 0.82, -8.55, dreh_y=0.3, ziel_hoehe=0.4)
lade_asset("factory_screen-panel-wide.glb", "Leitstand_Panel", 10.4, 0, -9.35, ziel_hoehe=1.6, einfaerbung=m_dunkel)
lade_asset("factory_hopper-square.glb", "Trichter", 15.3, 0, -8.3, ziel_hoehe=1.9, einfaerbung=m_stahlhell)

# ---- Stationsschilder (Ziffer kamerazugewandt, Sued-Stationen gedreht) ------
# Aus dem schwebenden blauen Wuerfel wird ein abgehaengtes Schild: Tafel mit
# Rahmen, zwei Haengern, Traverse und Seil bis zur Deckenunterkante (6.24), dazu
# eine Hutzenleuchte. Die Ziffer steht auf beiden Seiten.
for nr, (x, z) in {1: (-10, -5), 2: (-3, -6), 3: (7, -5), 4: (9, 5.8), 5: (2, 6), 6: (-9, 6)}.items():
    nach_norden = z > 0
    kasten(f"Schild_{nr}", 0.9, 0.08, 0.6, x, 3.4, z, m_blau)
    kasten(f"Schild_{nr}_rahmen", 0.98, 0.04, 0.68, x, 3.4, z + (0.07 if nach_norden else -0.07),
           m_stahlhell, fase=0)
    kasten(f"Schild_{nr}_leuchte", 0.5, 0.14, 0.08, x, 3.74, z + (0.11 if nach_norden else -0.11),
           m_stahlhell, fase=0)
    for i, hx in enumerate((-0.35, 0.35)):
        zylinder(f"Schild_{nr}_haenger_{i}", 0.02, 1.6, x + hx, 4.5, z, m_dunkel)
    kasten(f"Schild_{nr}_traverse", 0.86, 0.06, 0.06, x, 5.3, z, m_stahl, fase=0)
    zylinder(f"Schild_{nr}_seil", 0.02, 0.94, x, 5.77, z, m_dunkel)  # Abhaengung zur Decke
    for seite, versatz in (("v", -0.045), ("h", 0.045)):
        bpy.ops.object.text_add(location=pos(x, 3.4, z + versatz))
        ziffer = bpy.context.active_object
        ziffer.name = f"Schild_{nr}_ziffer_{seite}"
        ziffer.data.body = str(nr)
        ziffer.data.size = 0.35
        ziffer.data.extrude = 0.02
        ziffer.data.align_x = "CENTER"
        ziffer.data.align_y = "CENTER"
        ziffer.rotation_euler = (1.5708, 0, 3.14159 if versatz < 0 else 0)
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
