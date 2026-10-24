# -*- coding: cp1252 -*-
# Visor DXF R12 -> SVG respetando tipos de linea (tabla LTYPE), colores ACI de capa, anchos y bulges.
# Uso: python dxf_preview_v4.py entrada.dxf salida.svg [--bn]   (--bn = todo en negro, como plot monochrome)
import sys, math, html

src, out = sys.argv[1], sys.argv[2]
BN = "--bn" in sys.argv
with open(src, "r", encoding="cp1252") as f:
    lines = [ln.rstrip("\r\n") for ln in f]
pairs = [(lines[i].strip(), lines[i + 1]) for i in range(0, len(lines) - 1, 2)]

def aci_rgb(i):
    base = {1: (255, 0, 0), 2: (255, 255, 0), 3: (0, 255, 0), 4: (0, 255, 255), 5: (0, 0, 255),
            6: (255, 0, 255), 7: (22, 30, 45), 8: (128, 128, 128), 9: (192, 192, 192)}
    if i in base:
        return base[i]
    if 10 <= i <= 249:
        hue = (i // 10 - 1) * 15.0
        sub = i % 10
        val = [255, 255, 165, 165, 127, 127, 76, 76, 38, 38][sub] / 255.0
        h = hue / 60.0
        c = 1.0
        x = c * (1 - abs(h % 2 - 1))
        r, g, b = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)][int(h) % 6]
        if sub % 2 == 1:   # tonos impares: mezclados con blanco al 50 %
            r, g, b = r + (1 - r) * 0.5, g + (1 - g) * 0.5, b + (1 - b) * 0.5
        return tuple(int(255 * v * val) for v in (r, g, b))
    return (22, 30, 45)

hexc = lambda rgb: "#%02x%02x%02x" % rgb

W, H = 1600.0, 1000.0
for k in range(len(pairs) - 1):
    if pairs[k] == ("9", "$EXTMAX"):
        vals = {}
        j = k + 1
        while j < len(pairs) and pairs[j][0] not in ("9", "0"):
            vals[pairs[j][0]] = pairs[j][1]; j += 1
        W, H = float(vals.get("10", W)), float(vals.get("20", H))
        break
fy = lambda y: H - y

ltypes, layers = {}, {}
i = 0
while i < len(pairs):
    c, v = pairs[i]
    if c == "0" and v in ("LTYPE", "LAYER"):
        d, pat = {}, []
        j = i + 1
        while j < len(pairs) and pairs[j][0] != "0":
            if pairs[j][0] == "49":
                pat.append(float(pairs[j][1]))
            else:
                d.setdefault(pairs[j][0], pairs[j][1])
            j += 1
        if v == "LTYPE":
            ltypes[d.get("2")] = pat
        else:
            layers[d.get("2")] = (int(d.get("62", 7)), d.get("6", "CONTINUOUS"))
        i = j
    else:
        i += 1

def color(lay):
    if BN:
        return "#000000"
    return hexc(aci_rgb(layers.get(lay, (7, ""))[0]))

def style(lay, width):
    col = color(lay)
    lt = layers.get(lay, (7, "CONTINUOUS"))[1]
    pat = ltypes.get(lt, [])
    sw = width if width > 0 else 0.9
    dash = ""
    if pat:
        arr = [max(abs(p), 0.6) for p in pat]
        dash = ' stroke-dasharray="%s"' % " ".join("%.2f" % a for a in arr)
    return 'stroke="%s" stroke-width="%.2f" fill="none" stroke-linejoin="round"%s' % (col, sw, dash)

def bulge_pts(p1, p2, b, n=16):
    # puntos de un arco con bulge (en coordenadas DXF)
    if abs(b) < 1e-9:
        return [p2]
    th = 4 * math.atan(b)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    c = math.hypot(dx, dy)
    r = c / (2 * math.sin(th / 2))
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    hd = r * math.cos(th / 2)
    nx, ny = -dy / c, dx / c
    cx, cy = mx + nx * hd, my + ny * hd
    a1 = math.atan2(p1[1] - cy, p1[0] - cx)
    return [(cx + abs(r) * math.cos(a1 + th * k / n), cy + abs(r) * math.sin(a1 + th * k / n)) for k in range(1, n + 1)]

i = pairs.index(("2", "ENTITIES"))
svg = []
n = len(pairs)
while i < n:
    c, v = pairs[i]
    if c != "0":
        i += 1; continue
    if v in ("ENDSEC", "EOF"):
        break
    j = i + 1
    d = {}
    while j < n and pairs[j][0] != "0":
        d.setdefault(pairs[j][0], pairs[j][1]); j += 1
    lay = d.get("8", "0")
    g = lambda k, default=0.0: float(d.get(k, default))
    if v == "LINE":
        svg.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" %s/>' % (g("10"), fy(g("20")), g("11"), fy(g("21")), style(lay, 0)))
    elif v == "CIRCLE":
        svg.append('<circle cx="%.2f" cy="%.2f" r="%.2f" %s/>' % (g("10"), fy(g("20")), g("40"), style(lay, 0)))
    elif v == "TEXT":
        hgt = g("40"); s = d.get("1", "")
        ha = int(float(d.get("72", "0")))
        x = g("11") if ha in (1, 2) else g("10"); y = g("21") if ha in (1, 2) else g("20")
        anchor = {0: "start", 1: "middle", 2: "end"}[ha]
        svg.append('<text x="%.2f" y="%.2f" font-size="%.2f" text-anchor="%s" fill="%s" font-family="Arial Narrow, Arial" >%s</text>'
                   % (x, fy(y), hgt * 1.38, anchor, "#000000" if BN else "#10161f", html.escape(s).replace("%%d", "&#176;")))
    elif v == "POLYLINE":
        wdt = float(d.get("40", 0) or 0)
        closed = int(float(d.get("70", "0"))) & 1
        verts = []
        k = j
        while k < n:
            if pairs[k] == ("0", "VERTEX"):
                dd = {}
                k += 1
                while k < n and pairs[k][0] != "0":
                    dd.setdefault(pairs[k][0], pairs[k][1]); k += 1
                verts.append((float(dd["10"]), float(dd["20"]), float(dd.get("42", 0) or 0)))
            elif pairs[k] == ("0", "SEQEND"):
                k += 1
                while k < n and pairs[k][0] != "0": k += 1
                break
            else:
                k += 1
        j = k
        pts = [(verts[0][0], verts[0][1])]
        m = len(verts)
        for q in range(m - 1 + (1 if closed else 0)):
            a, b = verts[q], verts[(q + 1) % m]
            pts += bulge_pts((a[0], a[1]), (b[0], b[1]), a[2])
        p = " ".join("%.2f,%.2f" % (x, fy(y)) for (x, y) in pts)
        tag = "polygon" if (closed and not any(vv[2] for vv in verts)) else "polyline"
        svg.append('<%s points="%s" %s/>' % (tag, p, style(lay, wdt)))
    elif v == "SOLID":
        p = "%.2f,%.2f %.2f,%.2f %.2f,%.2f" % (g("10"), fy(g("20")), g("11"), fy(g("21")), g("12"), fy(g("22")))
        svg.append('<polygon points="%s" fill="%s" stroke="none"/>' % (p, color(lay)))
    i = j

PXW = 3400
PXH = int(PXW * H / W)
doc = ('<?xml version="1.0" encoding="UTF-8"?><svg width="%d" height="%d" viewBox="0 0 %.0f %.0f" xmlns="http://www.w3.org/2000/svg">'
       '<rect width="%.0f" height="%.0f" fill="#ffffff"/>%s</svg>') % (PXW, PXH, W, H, W, H, "".join(svg))
with open(out, "w", encoding="utf-8") as f:
    f.write(doc)
print("preview OK: %d elementos, lienzo %dx%d -> %dx%d px" % (len(svg), W, H, PXW, PXH))
