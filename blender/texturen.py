"""Prozedurale PBR-Texturen (Albedo, Rauheit, Normal) als 8-Bit-RGB-PNG ohne Abhaengigkeiten.

Alles ist deterministisch (Seed), damit ein Bau die versionierten gen_*.png byteweise
reproduziert. Keine Schrift, keine Logos (Greek-Regel der Spec)."""
import random
import struct
import zlib


def png_speichern(pfad, breite, hoehe, zeilen):
    def chunk(typ, daten):
        return struct.pack(">I", len(daten)) + typ + daten + struct.pack(">I", zlib.crc32(typ + daten) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(zeilen, 6))
    png += chunk(b"IEND", b"")
    with open(pfad, "wb") as f:
        f.write(png)


def _gitter(g, rnd):
    # (g+1)^2 Knoten: Zeile/Spalte g werden seit der periodischen Fassung nicht gelesen,
    # bleiben aber Teil des Zufallsstroms — verkleinern wuerde jede gen_*.png aendern.
    return [[rnd.random() for _ in range(g + 1)] for _ in range(g + 1)]


def _wert(knoten, g, u, v):
    """Bilinear interpoliertes Value-Noise, periodisch in u und v (Kachel ohne Naht)."""
    x = (u % 1.0) * g
    y = (v % 1.0) * g
    x0, y0 = int(x) % g, int(y) % g
    fx, fy = x - int(x), y - int(y)
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    x1, y1 = (x0 + 1) % g, (y0 + 1) % g
    a = knoten[y0][x0] * (1 - fx) + knoten[y0][x1] * fx
    b = knoten[y1][x0] * (1 - fx) + knoten[y1][x1] * fx
    return a * (1 - fy) + b * fy


def fbm_feld(groesse, gitter=6, oktaven=4, seed=1):
    """Liefert eine groesse x groesse Liste von Werten 0..1 (fraktales Value-Noise)."""
    rnd = random.Random(seed)
    schichten = []
    g, amp, summe = gitter, 1.0, 0.0
    for _ in range(oktaven):
        schichten.append((_gitter(g, rnd), g, amp))
        summe += amp
        g *= 2
        amp *= 0.5
    feld = []
    for j in range(groesse):
        zeile = []
        v = j / groesse
        for i in range(groesse):
            u = i / groesse
            n = sum(_wert(k, gg, u, v) * a for k, gg, a in schichten) / summe
            zeile.append(n)
        feld.append(zeile)
    return feld


def schreibe_pbr_set(basispfad, groesse=512, basis_rgb=(120, 122, 125), spann=18, seed=1,
                     platten=None, koernung=0, normal_staerke=1.0,
                     rauheit_basis=0.85, rauheit_spann=0.12):
    """Schreibt <basispfad>_albedo.png (groesse), _rauheit.png und _normal.png (groesse//2)."""
    rnd = random.Random(seed + 101)
    feld = fbm_feld(groesse, gitter=6, oktaven=4, seed=seed)
    fein = fbm_feld(groesse, gitter=48, oktaven=2, seed=seed + 7)
    n_platten, tint = platten if platten else (1, 0)
    platten_tint = [[rnd.uniform(-tint, tint) for _ in range(n_platten)] for _ in range(n_platten)]
    fuge = max(2, groesse // 256)

    def plattenwert(i, j):
        pi, pj = i * n_platten // groesse, j * n_platten // groesse
        am_rand = n_platten > 1 and (i % (groesse // n_platten) < fuge or j % (groesse // n_platten) < fuge)
        return platten_tint[pj][pi], am_rand

    albedo = b""
    for j in range(groesse):
        zeile = b"\x00"
        for i in range(groesse):
            n = 0.7 * feld[j][i] + 0.3 * fein[j][i]
            t, rand = plattenwert(i, j)
            f = (n - 0.5) * 2 * spann + t * 255
            if rand:
                f -= 22  # Dehnfuge dunkler
            if koernung:
                f += rnd.randint(-koernung, koernung)
            zeile += bytes(max(0, min(255, int(c + f))) for c in basis_rgb)
        albedo += zeile
    png_speichern(f"{basispfad}_albedo.png", groesse, groesse, albedo)

    h = groesse // 2
    rauheit = b""
    normal = b""
    for j in range(h):
        zr = b"\x00"
        zn = b"\x00"
        for i in range(h):
            n = feld[j * 2][i * 2]
            r = rauheit_basis + (n - 0.5) * 2 * rauheit_spann + (fein[j * 2][i * 2] - 0.5) * 0.06
            g = max(0, min(255, int(r * 255)))
            # B = 255: glTF nimmt den Blaukanal als Metallic-Maske; so bleibt metallicFactor unveraendert
            zr += bytes((g, g, 255))
            # Normal aus dem Hoehenfeld (zentrale Differenz), periodisch
            hx = feld[j * 2][(i * 2 + 2) % groesse] - feld[j * 2][(i * 2 - 2) % groesse]
            hy = feld[(j * 2 + 2) % groesse][i * 2] - feld[(j * 2 - 2) % groesse][i * 2]
            nx = max(-1.0, min(1.0, -hx * 4.0 * normal_staerke))
            ny = max(-1.0, min(1.0, -hy * 4.0 * normal_staerke))
            zn += bytes((int((nx * 0.5 + 0.5) * 255), int((ny * 0.5 + 0.5) * 255), 255))
        rauheit += zr
        normal += zn
    png_speichern(f"{basispfad}_rauheit.png", h, h, rauheit)
    png_speichern(f"{basispfad}_normal.png", h, h, normal)


def schreibe_rillen_normal_png(pfad, groesse=256, periode=32, tiefe=0.6):
    """Trapezblech: Rillen entlang u als Normal-Map (fuer die Hallendecke)."""
    zeilen = b""
    for j in range(groesse):
        zeile = b"\x00"
        for i in range(groesse):
            phase = (i % periode) / periode
            steig = tiefe if 0.1 < phase < 0.25 else (-tiefe if 0.6 < phase < 0.75 else 0.0)
            zeile += bytes((int((steig * 0.5 + 0.5) * 255), 128, 255))
        zeilen += zeile
    png_speichern(pfad, groesse, groesse, zeilen)


def schreibe_rauheit_png(pfad, groesse=256, basis=0.5, spann=0.25, seed=3, kratzer=0):
    """Reine Rauheitskarte (Lack mit Wolken und optional feinen Kratzern)."""
    rnd = random.Random(seed)
    feld = fbm_feld(groesse, gitter=5, oktaven=3, seed=seed)
    zeilen = b""
    for j in range(groesse):
        zeile = b"\x00"
        for i in range(groesse):
            r = basis + (feld[j][i] - 0.5) * 2 * spann
            if kratzer and rnd.random() < kratzer:
                r += 0.35
            g = max(0, min(255, int(r * 255)))
            # B = 255: glTF nimmt den Blaukanal als Metallic-Maske; so bleibt metallicFactor unveraendert
            zeile += bytes((g, g, 255))
        zeilen += zeile
    png_speichern(pfad, groesse, groesse, zeilen)
