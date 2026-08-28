"""Blockout der Instandhaltungswerkstatt (Low-Poly, Stil nach blender/referenz-werkstatt.webp).

Layout orientiert an der isometrischen Referenz (gamifizierter Look) und einem Foto
eines echten ICE-Instandhaltungswerks: Hallenfachwerk mit Fensterbaendern, Teildach
(Cutaway), Tor mit ausfuehrendem Gleis, Empore mit Treppe, Untersuchungsgrube mit
gelb-schwarzen Warnkanten, weisse Dacharbeitsbuehnen ueber dem Zug, Kranbahn mit
Laufkatzen, Rollgerueste, Service-/Werkstattwagen, Oelfaesser auf Auffangwanne,
orange Schraffur-Zone, Signalsaeulen, Kabeltrassen. Farbakzente in entsaettigtem
Blau/Orange/Sicherheitsgelb; alle Toene bleiben graustufentauglich.

Konturen: ausgewaehlte Objekte bekommen eine Inverted-Hull-Silhouette (Duplikat mit
umgedrehten Normalen, schwarz, backface-culled) — ergibt den illustrierten Look der
Referenz und funktioniert ohne Shader in Three.js (Material exportiert single-sided).

Koordinaten-Vertrag: Three.js ist Y-up, Blender Z-up; der glTF-Exporter konvertiert
automatisch (+Y up). pos() nimmt Three.js-Koordinaten (x, y, z wie in stationen.json)
und uebersetzt nach Blender (x, -z, y); kasten() nimmt (breite_x, tiefe_z, hoehe_y).
Objektnamen folgen dem Vertrag Station_<nr>_<id> bzw. Monitor_Bildschirm.
"""
import bpy
import bmesh
import os

ZIEL = os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd(),
                    "app", "public", "szene.glb")

KONTUR_DICKE = 0.035


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


def zeichne_kontur(obj):
    """Inverted-Hull-Silhouette: groesseres Duplikat, Normalen umgedreht, schwarz."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=obj.location)
    k = bpy.context.active_object
    k.name = obj.name + "_kontur"
    k.scale = tuple(s + 2 * KONTUR_DICKE for s in obj.scale)
    k.rotation_euler = obj.rotation_euler
    bm = bmesh.new()
    bm.from_mesh(k.data)
    for f in bm.faces:
        f.normal_flip()
    bm.to_mesh(k.data)
    bm.free()
    k.data.materials.append(m_kontur)
    return k


def kasten(name, dx, dz, dy, x, y, z, mat, drehung=None, kontur=False):
    """quader in Three.js-Achsen: Groesse (dx, dz, dy), Mittelpunkt (x, y, z)."""
    obj = quader(name, (dx, dz, dy), pos(x, y, z), mat, drehung)
    if kontur:
        zeichne_kontur(obj)
    return obj


# ---- Szene leeren -----------------------------------------------------------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

GRAU_BODEN = (0.55, 0.58, 0.60)
GRAU_GLEISZONE = (0.40, 0.43, 0.46)
GRAU_WAND = (0.78, 0.80, 0.82)
GRAU_OBJEKT = (0.62, 0.66, 0.69)
GRAU_DUNKEL = (0.28, 0.30, 0.33)
STAHL = (0.46, 0.51, 0.56)
FENSTER = (0.72, 0.84, 0.95)
BLAU = (0.28, 0.44, 0.66)        # Leitstand/Regal/Rohre (Referenz)
ORANGE = (0.80, 0.42, 0.12)      # Sicherheits-Akzente (Referenz)
MARKIERUNG = (0.88, 0.75, 0.15)  # Sicherheits-Gelb (Markierung, Warnstreifen)
STAHL_HELL = (0.80, 0.83, 0.86)  # weisser Stahlbau der Dacharbeitsbuehnen (ICE-Werk-Foto)
GRUEN = (0.30, 0.55, 0.32)       # Signal-/Rettungszeichen-Gruen
GRUBE = (0.15, 0.16, 0.18)       # Untersuchungsgrube
ROT_ZUG = (0.70, 0.12, 0.16)     # Verkehrsrot-Streifen am Triebzug
WEISS_ZUG = (0.88, 0.89, 0.90)
KONTUR = (0.05, 0.05, 0.07)

m_boden = material("Boden", GRAU_BODEN)
m_gleiszone = material("Gleiszone", GRAU_GLEISZONE)
m_wand = material("Wand", GRAU_WAND)
m_objekt = material("Objekt", GRAU_OBJEKT)
m_dunkel = material("Dunkel", GRAU_DUNKEL)
m_stahl = material("Stahl", STAHL)
m_fenster = material("Fenster", FENSTER, rauheit=0.3)
m_blau = material("Blau", BLAU)
m_orange = material("Orange", ORANGE)
m_markierung = material("Markierung", MARKIERUNG)
m_zug = material("Zug", ROT_ZUG)
m_zugweiss = material("ZugWeiss", WEISS_ZUG, rauheit=0.5)
m_stahlhell = material("StahlHell", STAHL_HELL, rauheit=0.6)
m_gruen = material("Gruen", GRUEN)
m_grube = material("Grube", GRUBE)
m_kontur = material("Kontur", KONTUR, rauheit=1.0)
m_kontur.use_backface_culling = True  # exportiert single-sided — Pflicht fuer Inverted Hull

# ---- Halle: Boden, Gleiszone, Markierungen ----------------------------------
kasten("Halle_Boden", 34, 20, 0.2, 0, -0.1, 0, m_boden)
kasten("Halle_Gleiszone", 34, 3.6, 0.04, 0, 0.02, 0, m_gleiszone)
kasten("Halle_Markierung_Nord", 30, 0.12, 0.02, 0, 0.045, -1.9, m_markierung)
kasten("Halle_Markierung_Sued", 30, 0.12, 0.02, 0, 0.045, 1.9, m_markierung)
kasten("Halle_Weg_Nord", 34, 1.6, 0.03, 0, 0.02, -8.9, m_wand)

# ---- Nordwand mit Fensterband -----------------------------------------------
kasten("Wand_Nord_Unten", 34, 0.3, 3.5, 0, 1.75, -10, m_wand)
kasten("Wand_Nord_Fenster", 34, 0.1, 1.8, 0, 4.4, -10.08, m_fenster)
kasten("Wand_Nord_Oben", 34, 0.3, 0.7, 0, 5.65, -10, m_wand)
for i, fx in enumerate(range(-16, 17, 4)):
    kasten(f"Wand_Nord_Sprosse_{i}", 0.15, 0.3, 1.8, fx, 4.4, -10, m_stahl)
kasten("Wand_Nord_Quersprosse", 34, 0.24, 0.08, 0, 4.4, -10, m_stahl)

# ---- Westwand mit Fensterband -----------------------------------------------
kasten("Wand_West_Unten", 0.3, 20, 3.5, -17, 1.75, 0, m_wand)
kasten("Wand_West_Fenster", 0.1, 20, 1.8, -17.08, 4.4, 0, m_fenster)
kasten("Wand_West_Oben", 0.3, 20, 0.7, -17, 5.65, 0, m_wand)
for i, fz in enumerate(range(-8, 9, 4)):
    kasten(f"Wand_West_Sprosse_{i}", 0.3, 0.15, 1.8, -17, 4.4, fz, m_stahl)
kasten("Wand_West_Quersprosse", 0.24, 20, 0.08, -17, 4.4, 0, m_stahl)

# ---- Suedwand: niedriger Sockel (Cutaway fuer die Totale) -------------------
kasten("Wand_Sued_Sockel", 34, 0.3, 1.0, 0, 0.5, 10, m_wand)

# ---- Ostwand mit Tor, Gleis fuehrt hinaus -----------------------------------
kasten("Wand_Ost_Nord", 0.3, 8.2, 6, 17, 3, -5.9, m_wand)
kasten("Wand_Ost_Sued", 0.3, 8.2, 6, 17, 3, 5.9, m_wand)
kasten("Wand_Ost_Sturz", 0.3, 3.6, 1.8, 17, 5.1, 0, m_wand)
kasten("Tor_Pfosten_Nord", 0.25, 0.25, 4.4, 16.8, 2.2, -1.9, m_orange, kontur=True)
kasten("Tor_Pfosten_Sued", 0.25, 0.25, 4.4, 16.8, 2.2, 1.9, m_orange, kontur=True)
kasten("Tor_Balken", 0.25, 4.3, 0.25, 16.8, 4.35, 0, m_orange, kontur=True)

# ---- Stahlbau: Stuetzen, Binder, Teildach, Rohre, Leuchten ------------------
for i, sx in enumerate((-13.6, -6.8, 0, 6.8, 13.6)):
    kasten(f"Stuetze_Nord_{i}", 0.3, 0.3, 6, sx, 3, -9.7, m_stahl)
for i, sz in enumerate((-6.7, 0, 6.7)):
    kasten(f"Stuetze_West_{i}", 0.3, 0.3, 6, -16.7, 3, sz, m_stahl)
for i, tx in enumerate((-12, -6, 0, 6, 12)):
    kasten(f"Dachbinder_{i}", 0.22, 19.4, 0.28, tx, 5.7, 0, m_stahl)
    kasten(f"Stuetze_Sued_{i}", 0.25, 0.25, 5.7, tx, 2.85, 9.55, m_stahl)
# Teildach ueber der Nordhaelfte: Cutaway wie in der Referenz
kasten("Dach_Nord", 34, 3.5, 0.12, 0, 5.95, -8.2, m_stahl)
for i, px in enumerate((-15, -9, -3, 3, 9, 15)):
    kasten(f"Dach_Pfette_{i}", 0.14, 3.5, 0.18, px, 5.82, -8.2, m_dunkel)
kasten("Rohr_Blau", 33, 0.18, 0.18, 0, 5.1, -9.3, m_blau)
kasten("Rohr_Grau", 33, 0.16, 0.16, 0, 4.8, -9.0, m_stahl)
kasten("Rohr_Orange", 33, 0.12, 0.12, 0, 4.55, -9.15, m_orange)
for i, lx in enumerate((-10, -4.5, 1, 6.5, 12)):
    kasten(f"Leuchte_{i}_schirm", 0.95, 0.4, 0.1, lx, 4.62, 0, m_dunkel)
    kasten(f"Leuchte_{i}", 0.85, 0.32, 0.06, lx, 4.56, 0, m_fenster)
    kasten(f"Leuchte_{i}_seil", 0.03, 0.03, 1.0, lx, 5.2, 0, m_dunkel)

# ---- Empore an der Westwand mit Treppe (Referenz: Galerie links oben) -------
kasten("Empore_Plattform", 3.0, 10, 0.15, -15.5, 3.05, -5, m_objekt, kontur=True)
for i, ez in enumerate((-9.5, -6.5, -3.5, -0.6)):
    kasten(f"Empore_Stuetze_{i}", 0.2, 0.2, 3.0, -14.2, 1.5, ez, m_stahl)
for i, gz in enumerate((-9.5, -7.2, -4.9, -2.6, -0.4)):
    kasten(f"Empore_Gelaenderpfosten_{i}", 0.06, 0.06, 1.0, -14.1, 3.6, gz, m_dunkel)
kasten("Empore_Handlauf", 0.06, 9.6, 0.07, -14.1, 4.1, -5, m_dunkel)
kasten("Empore_Treppe", 1.0, 4.4, 0.12, -15.5, 1.55, 1.6, m_stahl, drehung=(0.68, 0, 0), kontur=True)
kasten("Empore_Treppe_Wange", 0.08, 0.08, 1.0, -15.0, 3.6, 0.1, m_dunkel)
kasten("Empore_Kiste_1", 0.6, 0.55, 0.5, -15.9, 3.4, -8.4, m_blau, kontur=True)
kasten("Empore_Kiste_2", 0.45, 0.4, 0.4, -15.3, 3.33, -7.9, m_orange, kontur=True)

# ---- Gleis (fuehrt durch das Tor nach draussen) -----------------------------
kasten("Gleis_Schiene_Nord", 38, 0.15, 0.15, 2, 0.08, -0.7, m_dunkel)
kasten("Gleis_Schiene_Sued", 38, 0.15, 0.15, 2, 0.08, 0.7, m_dunkel)
for i in range(16):
    sx = -14.5 + i * 2.4
    if -15.5 < sx < -8.5:
        continue  # im Grubenbereich liegen die Schienen auf den Grubenwaenden, keine Schwellen
    kasten(f"Gleis_Schwelle_{i}", 0.22, 1.8, 0.06, sx, 0.03, 0, m_dunkel)

# ---- Untersuchungsgrube unter dem Gleis (ICE-Werk-Foto: offene Arbeitsgrube) ----
kasten("Grube_Boden", 7, 2.0, 0.03, -12, 0.045, 0, m_grube)
kasten("Grube_Leuchte_Nord", 5.5, 0.06, 0.06, -12, 0.05, -0.9, m_fenster)
kasten("Grube_Leuchte_Sued", 5.5, 0.06, 0.06, -12, 0.05, 0.9, m_fenster)


def warnstreifen(name, laenge, x, z, entlang_x=True):
    """Gelb-schwarz gestreifte Sicherheitskante (0.5er-Segmente) auf dem Boden."""
    n = int(laenge / 0.5)
    for i in range(n):
        m = m_markierung if i % 2 == 0 else m_dunkel
        if entlang_x:
            kasten(f"{name}_{i}", 0.5, 0.14, 0.04, x - laenge / 2 + 0.25 + i * 0.5, 0.05, z, m)
        else:
            kasten(f"{name}_{i}", 0.14, 0.5, 0.04, x, 0.05, z - laenge / 2 + 0.25 + i * 0.5, m)


warnstreifen("Grube_Kante_Nord", 7, -12, -1.12)
warnstreifen("Grube_Kante_Sued", 7, -12, 1.12)
warnstreifen("Grube_Kante_West", 2, -15.55, 0, entlang_x=False)
warnstreifen("Grube_Kante_Ost", 2, -8.45, 0, entlang_x=False)
kasten("Grube_Leiter", 0.4, 0.08, 0.9, -8.7, 0.45, 0.7, m_orange)

# ---- Dacharbeitsbuehne ueber dem Zug (ICE-Werk-Foto: weisse Stahlbuehnen) ---
# Stuetzen enden bei x=4, damit sie der Station-4-Kamera (Anzeigetafel) nicht im Bild stehen
for i, bx in enumerate((-6.5, -3, 0.5, 4)):
    for j, bz in enumerate((-2.7, 2.7)):
        kasten(f"Buehne_Stuetze_{i}_{j}", 0.18, 0.18, 3.2, bx, 1.6, bz, m_stahlhell)
        kasten(f"Buehne_Stuetze_{i}_{j}_fuss", 0.26, 0.26, 0.18, bx, 0.09, bz, m_markierung)
kasten("Buehne_Plattform_Nord", 11.5, 0.85, 0.1, -1.25, 3.25, -2.7, m_stahlhell, kontur=True)
kasten("Buehne_Plattform_Sued", 11.5, 0.85, 0.1, -1.25, 3.25, 2.7, m_stahlhell, kontur=True)
for j, bz in enumerate((-3.08, 3.08)):
    kasten(f"Buehne_Handlauf_{j}", 11.5, 0.05, 0.06, -1.25, 4.25, bz, m_stahlhell)
    for i, px in enumerate((-6.5, -3.75, -1, 1.75, 4)):
        kasten(f"Buehne_Gelaenderpfosten_{j}_{i}", 0.05, 0.05, 0.95, px, 3.78, bz, m_stahlhell)
for i, tx in enumerate((-6.5, 4)):  # Querverbindungen ueber dem Zugdach
    kasten(f"Buehne_Quertraeger_{i}", 0.16, 5.4, 0.2, tx, 3.9, 0, m_stahlhell)
kasten("Buehne_Treppe", 0.9, 2.6, 0.1, -7.3, 1.7, 2.0, m_stahlhell, drehung=(0.9, 0, 0), kontur=True)

# ---- Kranbahn mit Laufkatzen (Foto: gelbe Hebezeuge unter der Decke) --------
kasten("Kran_Traeger", 15, 0.3, 0.25, 0.5, 5.35, 0, m_stahlhell)
for i, kx in enumerate((-2.5, 4)):
    kasten(f"Kran_Laufkatze_{i}", 0.55, 0.6, 0.4, kx, 5.0, 0, m_markierung, kontur=True)
    kasten(f"Kran_Haken_{i}", 0.06, 0.06, 0.5, kx, 4.55, 0, m_dunkel)

# ---- Rollgeruste (Foto: fahrbare Alu-Geruste an den Zugtueren) --------------
def rollgeruest(name, x, z):
    for i, (gx, gz) in enumerate(((-0.55, -0.35), (0.55, -0.35), (-0.55, 0.35), (0.55, 0.35))):
        kasten(f"{name}_holm_{i}", 0.07, 0.07, 2.6, x + gx, 1.3, z + gz, m_stahlhell)
        kasten(f"{name}_rolle_{i}", 0.12, 0.12, 0.12, x + gx, 0.06, z + gz, m_dunkel)
    kasten(f"{name}_buehne_1", 1.25, 0.8, 0.06, x, 1.25, z, m_stahlhell)
    kasten(f"{name}_buehne_2", 1.25, 0.8, 0.06, x, 2.35, z, m_stahlhell, kontur=True)
    kasten(f"{name}_handlauf", 1.25, 0.06, 0.06, x, 2.95, z + 0.38, m_markierung)
    kasten(f"{name}_diagonale", 0.06, 0.06, 1.5, x, 1.8, z - 0.38, m_stahlhell, drehung=(0, 0.6, 0))


rollgeruest("Rollgeruest_1", 4.2, -2.2)
rollgeruest("Rollgeruest_2", -4.2, 2.2)

# ---- Absaug-/Servicewagen (Foto: weisse Maschine mit blauen Tanks) ----------
kasten("Servicewagen_Korpus", 1.3, 0.85, 1.0, 10.5, 0.62, 2.9, m_zugweiss, kontur=True)
kasten("Servicewagen_Tank_1", 0.36, 0.36, 0.5, 10.2, 1.35, 2.75, m_blau)
kasten("Servicewagen_Tank_2", 0.36, 0.36, 0.5, 10.8, 1.35, 2.75, m_blau)
kasten("Servicewagen_Schlauch_1", 1.6, 0.09, 0.09, 9.4, 0.35, 2.4, m_dunkel, drehung=(0, 0, 0.5))
kasten("Servicewagen_Schlauch_2", 1.2, 0.09, 0.09, 8.6, 0.3, 1.7, m_dunkel, drehung=(0, 0, -0.4))
for i, (rx, rz) in enumerate(((-0.5, -0.3), (0.5, -0.3), (-0.5, 0.3), (0.5, 0.3))):
    kasten(f"Servicewagen_rad_{i}", 0.16, 0.16, 0.16, 10.5 + rx, 0.08, 2.9 + rz, m_dunkel)

# ---- Roter Werkstattwagen (Foto: roter Transportwagen) ----------------------
kasten("Werkstattwagen_Korpus", 1.0, 0.65, 0.9, 12.5, 0.55, -3.5, m_zug, kontur=True)
kasten("Werkstattwagen_Griff", 0.06, 0.55, 0.6, 13.05, 0.9, -3.5, m_dunkel)
for i, (rx, rz) in enumerate(((-0.38, -0.24), (0.38, -0.24), (-0.38, 0.24), (0.38, 0.24))):
    kasten(f"Werkstattwagen_rad_{i}", 0.14, 0.14, 0.14, 12.5 + rx, 0.07, -3.5 + rz, m_dunkel)

# ---- Zweite Werkbank mit Schraubstock und Werkzeugkasten --------------------
kasten("Werkbank2", 2.0, 0.7, 0.85, 2.5, 0.43, -9.4, m_stahl, kontur=True)
kasten("Werkbank2_Platte", 2.0, 0.75, 0.08, 2.5, 0.9, -9.4, m_dunkel)
kasten("Werkbank2_Schraubstock", 0.25, 0.3, 0.25, 3.2, 1.06, -9.35, m_dunkel)
kasten("Werkbank2_Werkzeugkasten", 0.5, 0.3, 0.3, 2.0, 1.09, -9.4, m_zug, kontur=True)

# ---- Oelfaesser auf Auffangwanne (Foto/Referenz: Fassgruppe) ----------------
kasten("Oel_Wanne", 1.7, 1.3, 0.15, 11.5, 0.08, -8.7, m_markierung, kontur=True)
kasten("Oel_Fass_1", 0.45, 0.45, 0.62, 11.2, 0.46, -8.9, m_dunkel, kontur=True)
kasten("Oel_Fass_2", 0.45, 0.45, 0.62, 11.8, 0.46, -8.9, m_blau, kontur=True)
kasten("Oel_Fass_3", 0.45, 0.45, 0.62, 11.2, 0.46, -8.4, m_orange, kontur=True)
kasten("Oel_Fass_4", 0.45, 0.45, 0.62, 11.8, 0.46, -8.4, m_dunkel, kontur=True)

# ---- Orange Schraffur-Zone (Foto: markierter Rangierweg) --------------------
for i in range(8):
    kasten(f"Schraffur_{i}", 0.35, 2.4, 0.02, 2.6 + i * 0.62, 0.045, 3.4, m_orange, drehung=(0, 0, 0.785))
kasten("Schraffur_Rahmen_Nord", 5.4, 0.08, 0.02, 4.8, 0.05, 2.3, m_orange)
kasten("Schraffur_Rahmen_Sued", 5.4, 0.08, 0.02, 4.8, 0.05, 4.5, m_orange)

# ---- Signalsaeulen (Foto: kleine Ampeln an der Gleiskante) ------------------
for i, (sx, sz) in enumerate(((-8, 1.6), (1, -1.6), (9, 1.6))):
    kasten(f"Signal_{i}_mast", 0.08, 0.08, 1.0, sx, 0.5, sz, m_dunkel)
    kasten(f"Signal_{i}_rot", 0.13, 0.13, 0.13, sx, 1.1, sz, m_zug)
    kasten(f"Signal_{i}_gelb", 0.13, 0.13, 0.13, sx, 1.25, sz, m_markierung)
    kasten(f"Signal_{i}_gruen", 0.13, 0.13, 0.13, sx, 1.4, sz, m_gruen)

# ---- Kabeltrassen-Details (Foto: Leitungen und Abgaenge) --------------------
kasten("Kabel_Abgang_1", 0.1, 0.1, 2.2, 2.5, 3.6, -9.15, m_dunkel)
kasten("Kabel_Abgang_2", 0.1, 0.1, 2.2, 7, 3.6, -9.15, m_dunkel)
kasten("Kabel_Trommel", 0.5, 0.5, 0.5, 0.2, 0.25, -8.3, m_blau, kontur=True)
kasten("Kabel_Trommel_Kern", 0.2, 0.56, 0.2, 0.2, 0.25, -8.3, m_dunkel)
for i, lx in enumerate((-7, -1, 5, 11)):  # zweite Leuchtenreihe (Foto: dichte Decke)
    kasten(f"Leuchte_Sued_{i}", 0.7, 0.28, 0.06, lx, 4.5, 3.2, m_fenster)
    kasten(f"Leuchte_Sued_{i}_seil", 0.03, 0.03, 1.1, lx, 5.1, 3.2, m_dunkel)
# Rettungszeichen am Tor und an der Westwand
kasten("Rettungszeichen_Tor", 0.5, 0.05, 0.3, 15.8, 3.0, -1.6, m_gruen)
kasten("Rettungszeichen_West", 0.05, 0.5, 0.3, -16.8, 3.0, -4, m_gruen)

# ---- Absperrpfosten und Muelleimer (Referenz: orange Akzente) ---------------
for i, (ax, az) in enumerate(((-10, 2.4), (-3, 2.4), (4, 2.4), (11, 2.4))):
    kasten(f"Absperrpfosten_{i}", 0.12, 0.12, 0.9, ax, 0.45, az, m_orange)
kasten("Muelleimer_1", 0.4, 0.4, 0.7, -7.5, 0.35, -4.6, m_orange, kontur=True)
kasten("Muelleimer_2", 0.4, 0.4, 0.7, 5.2, 0.35, 4.4, m_orange, kontur=True)
for i, wx in enumerate((-8, 0, 8)):
    kasten(f"Warntafel_{i}", 0.5, 0.05, 0.6, wx, 2.5, -9.82, m_orange)

# ---- Triebzug: heller Korpus, Verkehrsrot-Streifen, Drehgestelle ------------
kasten("Triebzug_Unterbau", 14, 2.2, 0.5, 0.5, 0.45, 0, m_dunkel, kontur=True)
kasten("Triebzug_Drehgestell_1", 2.0, 2.0, 0.45, -4.5, 0.25, 0, m_dunkel)
kasten("Triebzug_Drehgestell_2", 2.0, 2.0, 0.45, 5.5, 0.25, 0, m_dunkel)
kasten("Triebzug_Korpus", 14, 2.4, 1.5, 0.5, 1.45, 0, m_zugweiss, kontur=True)
kasten("Triebzug_Streifen_Nord", 14, 0.06, 0.35, 0.5, 1.05, -1.23, m_zug)
kasten("Triebzug_Streifen_Sued", 14, 0.06, 0.35, 0.5, 1.05, 1.23, m_zug)
kasten("Triebzug_Fensterband_Nord", 11.5, 0.06, 0.55, 0, 1.8, -1.23, m_dunkel)
kasten("Triebzug_Fensterband_Sued", 11.5, 0.06, 0.55, 0, 1.8, 1.23, m_dunkel)
kasten("Triebzug_Dach", 13.6, 2.2, 0.3, 0.5, 2.35, 0, m_stahl, kontur=True)
for i, kx in enumerate((-4, 0.5, 5)):
    kasten(f"Triebzug_Klima_{i}", 1.4, 1.4, 0.25, kx, 2.6, 0, m_dunkel)
kasten("Triebzug_Panto_Basis", 0.8, 1.0, 0.1, -2, 2.78, 0, m_dunkel)
kasten("Triebzug_Panto_Arm", 0.08, 0.08, 0.9, -2, 3.2, 0, m_dunkel, drehung=(0.5, 0, 0))
kasten("Triebzug_Panto_Buegel", 0.06, 1.3, 0.05, -2, 3.6, 0.2, m_dunkel)
kasten("Triebzug_Front", 1.2, 2.2, 1.4, 8.1, 1.4, 0, m_zugweiss, kontur=True)
kasten("Triebzug_Front_Streifen", 1.26, 2.1, 0.3, 8.1, 0.95, 0, m_zug)
kasten("Triebzug_Windschutz", 0.15, 1.6, 0.6, 8.65, 1.9, 0, m_dunkel)
kasten("Triebzug_Kupplung", 0.5, 0.25, 0.25, 8.85, 0.55, 0, m_dunkel)
for i, tx in enumerate((-3, 4)):
    kasten(f"Triebzug_Tuer_Nord_{i}", 0.9, 0.05, 1.3, tx, 1.35, -1.24, m_stahl)
    kasten(f"Triebzug_Tuer_Sued_{i}", 0.9, 0.05, 1.3, tx, 1.35, 1.24, m_stahl)

# ---- Station 1: Meisterbuero mit Pinnwand -----------------------------------
kasten("Station_1_meisterbuero", 4, 3, 2.6, -10.5, 1.3, -7.5, m_wand, kontur=True)
kasten("Station_1_buerodach", 4.3, 3.3, 0.1, -10.5, 2.65, -7.5, m_dunkel)
kasten("Station_1_buerofenster", 2.6, 0.06, 0.9, -10.5, 1.9, -5.95, m_fenster)
kasten("Station_1_buerotuer", 0.8, 0.06, 1.9, -8.9, 0.95, -5.95, m_dunkel)
kasten("Station_1_pinnwand", 2.4, 0.08, 1.3, -10, 1.8, -5.2, m_objekt, kontur=True)
kasten("Station_1_pinnwand_pfosten_west", 0.1, 0.1, 2.3, -11.0, 1.15, -5.2, m_dunkel)
kasten("Station_1_pinnwand_pfosten_ost", 0.1, 0.1, 2.3, -9.0, 1.15, -5.2, m_dunkel)
for i in range(6):
    zx = -10.9 + (i % 3) * 0.9
    zy = 2.1 - (i // 3) * 0.55
    kasten(f"Station_1_zettel_{i}", 0.32, 0.03, 0.42, zx, zy, -5.14, m_fenster)
    kasten(f"Station_1_zettel_{i}_zeile", 0.24, 0.035, 0.05, zx, zy + 0.1, -5.14, m_objekt)
kasten("Station_1_schreibtisch", 1.6, 0.7, 0.12, -8.2, 0.72, -5.4, m_objekt, kontur=True)
kasten("Station_1_schreibtisch_fuss", 0.25, 0.6, 0.66, -8.2, 0.33, -5.4, m_dunkel)
kasten("Station_1_ordnerstapel", 0.4, 0.3, 0.25, -8.5, 0.9, -5.5, m_blau)

# ---- Station 2: Datenraum-Regal, Chaos davor / Ordnung darin ----------------
kasten("Station_2_datenraum", 0.08, 1.0, 2.2, -4.2, 1.1, -6, m_blau, kontur=True)
kasten("Station_2_regalwange", 0.08, 1.0, 2.2, -1.8, 1.1, -6, m_blau, kontur=True)
for i, by in enumerate((0.35, 0.95, 1.55, 2.15)):
    kasten(f"Station_2_regalbrett_{i}", 2.5, 1.0, 0.06, -3, by, -6, m_dunkel)
ordner_farben = (m_blau, m_orange, m_objekt, m_blau, m_orange, m_objekt)
for i in range(6):  # geordnete Ordnerreihe im Regal (oberes Fach)
    kasten(f"Station_2_ordner_{i}", 0.2, 0.4, 0.5, -3.9 + i * 0.36, 1.85, -6, ordner_farben[i])
for i in range(5):  # geordnete Kisten im mittleren Fach
    kasten(f"Station_2_kiste_{i}", 0.34, 0.5, 0.4, -3.8 + i * 0.42, 1.2, -6, m_wand)
chaos = [(-4.1, -4.9, 0.5, 0.35, m_objekt), (-3.4, -5.2, 0.45, -0.5, m_wand),
         (-2.7, -4.7, 0.55, 0.9, m_objekt), (-2.1, -5.1, 0.4, -0.2, m_blau),
         (-3.0, -4.5, 0.35, 1.3, m_wand)]
for i, (cx, cz, cg, cr, cm) in enumerate(chaos):
    kasten(f"Station_2_chaos_{i}", cg, cg, cg, cx, cg / 2, cz, cm, drehung=(0, 0, cr), kontur=True)
kasten("Station_2_fass_1", 0.42, 0.42, 0.6, -1.4, 0.3, -5.0, m_dunkel, kontur=True)
kasten("Station_2_fass_2", 0.42, 0.42, 0.6, -1.0, 0.3, -5.5, m_blau, kontur=True)
kasten("Station_2_zettel_am_regal", 0.28, 0.03, 0.38, -4.24, 1.5, -5.45, m_fenster)

# ---- Station 3: Bedienterminal (blauer Leitstand) ---------------------------
kasten("Station_3_terminal_saeule", 0.5, 0.5, 1.2, 7, 0.6, -5, m_dunkel, kontur=True)
kasten("Station_3_terminal_gehaeuse", 1.8, 0.35, 1.05, 7, 1.5, -4.15, m_blau, kontur=True)
kasten("Station_3_terminal_pult", 1.4, 0.5, 0.1, 7, 0.95, -4.45, m_stahl, kontur=True)
kasten("Station_3_tastatur", 0.7, 0.28, 0.05, 7, 1.02, -4.45, m_dunkel)
kasten("Station_3_bodenplatte", 2.2, 1.6, 0.03, 7, 0.02, -4.4, m_gleiszone)
bpy.ops.mesh.primitive_plane_add(size=1, location=pos(7, 1.5, -3.95))
monitor = bpy.context.active_object
monitor.name = "Monitor_Bildschirm"
monitor.scale = (1.6, 0.9, 1)
monitor.rotation_euler = (1.5708, 0, 0)  # senkrecht, Front Richtung Sueden
monitor.data.materials.append(m_dunkel)

# ---- Station 4: Anzeigetafel mit gegreekten Zeilen --------------------------
kasten("Station_4_anzeigetafel", 3.2, 0.15, 1.8, 9, 2, 5.8, m_dunkel, kontur=True)
for i in range(4):  # unleserliche Inhaltszeilen (keine erfundenen Zahlen, Briefing §7)
    breite = 2.6 - (i % 2) * 0.5
    kasten(f"Station_4_zeile_{i}", breite, 0.04, 0.14, 8.8, 2.55 - i * 0.38, 5.71, m_stahl)
kasten("Station_4_titelzeile", 1.8, 0.04, 0.2, 8.5, 2.62, 5.71, m_markierung)
kasten("Station_4_pfosten_west", 0.15, 0.15, 2.9, 7.6, 1.45, 5.8, m_stahl)
kasten("Station_4_pfosten_ost", 0.15, 0.15, 2.9, 10.4, 1.45, 5.8, m_stahl)

# ---- Station 5: Pruefstand mit oranger Maschine -----------------------------
kasten("Station_5_pruefstand", 2.8, 1.2, 0.5, 2, 0.25, 6, m_stahl, kontur=True)
kasten("Station_5_aufbau", 1.4, 0.9, 0.9, 1.6, 1.15, 6, m_blau, kontur=True)
kasten("Station_5_rolle_1", 0.35, 1.0, 0.35, 2.6, 0.7, 6, m_dunkel)
kasten("Station_5_rolle_2", 0.35, 1.0, 0.35, 3.1, 0.7, 6, m_dunkel)
kasten("Station_5_panel", 0.4, 0.05, 0.3, 1.3, 1.5, 5.5, m_fenster)
kasten("Station_5_maschine", 0.9, 0.7, 0.8, 3.9, 0.4, 4.9, m_orange, kontur=True)
kasten("Station_5_maschine_arm", 0.15, 0.6, 0.15, 3.9, 0.95, 5.15, m_dunkel)
kasten("Station_5_kabelkanal", 2.6, 0.18, 0.08, 2, 0.06, 5.3, m_dunkel)

# ---- Station 6: Besprechung (Planungsrunde) ---------------------------------
kasten("Station_6_besprechung_tisch", 2.4, 1.2, 0.1, -9, 0.72, 6, m_objekt, kontur=True)
kasten("Station_6_tischfuss", 0.3, 0.3, 0.67, -9, 0.34, 6, m_dunkel)
stuehle = [(-10.1, 5.2), (-7.9, 5.2), (-10.1, 6.8), (-7.9, 6.8)]
for i, (sx, sz) in enumerate(stuehle):
    kasten(f"Station_6_stuhl_{i}_sitz", 0.45, 0.45, 0.08, sx, 0.45, sz, m_blau, kontur=True)
    lehne_z = sz + (0.24 if sz > 6 else -0.24)
    kasten(f"Station_6_stuhl_{i}_lehne", 0.45, 0.06, 0.5, sx, 0.75, lehne_z, m_blau)
kasten("Station_6_sideboard", 1.6, 0.5, 0.8, -11.5, 0.4, 7, m_objekt, kontur=True)
kasten("Station_6_whiteboard", 1.6, 0.06, 1.0, -11.2, 1.7, 8.2, m_fenster, kontur=True)
kasten("Station_6_whiteboard_fuss_1", 0.08, 0.08, 1.2, -11.9, 0.6, 8.2, m_dunkel)
kasten("Station_6_whiteboard_fuss_2", 0.08, 0.08, 1.2, -10.5, 0.6, 8.2, m_dunkel)

# ---- Requisiten an den Waenden ----------------------------------------------
kasten("Requisite_Fass_1", 0.45, 0.45, 0.62, -15.6, 0.31, -8.2, m_blau, kontur=True)
kasten("Requisite_Fass_2", 0.45, 0.45, 0.62, -15.0, 0.31, -8.5, m_dunkel, kontur=True)
kasten("Requisite_Fass_3", 0.45, 0.45, 0.62, -15.3, 0.31, -7.6, m_orange, kontur=True)
kasten("Requisite_Palette", 1.2, 1.0, 0.12, -6.5, 0.06, -8.6, m_objekt)
kasten("Requisite_Palette_Kiste_1", 0.55, 0.5, 0.5, -6.7, 0.37, -8.7, m_wand, kontur=True)
kasten("Requisite_Palette_Kiste_2", 0.4, 0.45, 0.35, -6.2, 0.3, -8.4, m_blau, kontur=True)
kasten("Requisite_Werkbank", 2.2, 0.7, 0.85, -16.2, 0.43, 3, m_stahl, kontur=True)
kasten("Requisite_Werkbank_Platte", 2.2, 0.75, 0.08, -16.2, 0.9, 3, m_dunkel)
kasten("Requisite_Werkzeugtafel", 0.06, 1.8, 1.0, -16.85, 1.7, 3, m_dunkel)
werkzeuge = ((-16.8, 2.0, 2.5, m_orange), (-16.8, 1.9, 2.8, m_stahl), (-16.8, 2.05, 3.1, m_orange),
             (-16.8, 1.85, 3.4, m_objekt), (-16.8, 1.5, 2.6, m_stahl), (-16.8, 1.45, 3.3, m_orange))
for i, (wx, wy, wz, wm) in enumerate(werkzeuge):
    kasten(f"Requisite_Werkzeug_{i}", 0.05, 0.1, 0.3, wx, wy, wz, wm)
kasten("Requisite_Wagen", 0.9, 0.5, 0.55, -13, 0.28, -2, m_blau, kontur=True)
kasten("Requisite_Wagen_Griff", 0.06, 0.4, 0.5, -13.45, 0.75, -2, m_dunkel)
kasten("Requisite_Schrank_1", 0.8, 0.4, 1.8, 13.5, 0.9, -9.6, m_objekt, kontur=True)
kasten("Requisite_Schrank_2", 0.8, 0.4, 1.8, 14.4, 0.9, -9.6, m_blau, kontur=True)
kasten("Requisite_Leiter", 0.5, 0.08, 2.4, 15.5, 1.2, -9.7, m_orange)

# ---- Stationsschilder: dunkler Wuerfel + helle Ziffer (Spec §4 Startbild) ---
# Die Ziffer haengt auf der kamerazugewandten Seite: Nord-Stationen (z<0) werden von
# Sueden betrachtet (Ziffer bei z+0.28, Front nach Sueden), Sued-Stationen (z>0) von
# Norden (Ziffer bei z-0.28, um 180 Grad gedreht) — sonst verdeckt der eigene Wuerfel
# die Ziffer in den Stationsansichten 4-6.
for nr, (x, z) in {1: (-10, -5), 2: (-3, -6), 3: (7, -5), 4: (9, 5), 5: (2, 6), 6: (-9, 6)}.items():
    schild = kasten(f"Schild_{nr}", 0.5, 0.5, 0.5, x, 3.4, z, m_blau, kontur=True)
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
