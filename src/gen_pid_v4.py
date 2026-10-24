# -*- coding: cp1252 -*-
# P&ID UNIFICADO v4 (REV. 4 - feedback visual del profesor, 02-10-2026)
# [Portfolio copy, anonymized] Plant, line and equipment brand names were replaced in the
#   title block and notes (PLANT A, EXISTENTE, RETROFIT*). Drawing logic is unchanged.
#   EXTRUSORA (area 01, redibujada) + HILADORES 1 y 2 (area 02). DXF R12.
#   - Cada servicio con su propia linea: patron (LTYPE) + grosor + color de capa.
#     Senales segun ANSI/ISA-5.1-2009 tabla 5.3.2: No.6 electrica (trazos), No.14 bus de campo (rombos), No.16 enlace mecanico.
#   - Llantas (hilera anular + anillo de aire) dibujadas en 3D (vista a 30 grados) con orificios y cortina de filamentos.
#   - Hoja con proporcion A0 (2400 x 1697 u) para plotear en A0 / pliego ("ajustar a papel"); textos y simbolos mas grandes.
# Uso: python gen_pid_v4.py "<salida>.dxf"
import math, io, sys

W, H = 2400.0, 1697.0
ents = []
flip = lambda y: H - y
TS, TM, TL = 8.6, 9.6, 11.5          # textos: pequeno / mediano / grande
K3D = math.sin(math.radians(30))     # relacion de ejes de las elipses (vista a 30 grados)

# anchos de polilinea por servicio (unidades de dibujo; A0 -> ~0.5 mm por unidad)
WF, WAT, WAQ, WHU, WEN, WAG, WPR = 4.0, 2.0, 2.2, 2.4, 1.7, 1.7, 1.0

# ---- capas: (nombre, color ACI, tipo de linea) ----
LAYERS = [
    ("MARCO", 7, "CONTINUOUS"), ("EQUIPOS", 7, "CONTINUOUS"), ("TEXTOS", 7, "CONTINUOUS"),
    ("FUNDIDO", 1, "CONTINUOUS"), ("PRODUCTO", 7, "CONTINUOUS"),
    ("ACEITE_TERMICO", 32, "ACEITE_TERMICO"), ("AIRE_QUENCH", 150, "AIRE_QUENCH"),
    ("HUMOS", 42, "HUMOS"), ("ENSIMAJE", 30, "ENSIMAJE"), ("AGUA", 94, "AGUA"),
    ("INSTRUMENTOS", 7, "CONTINUOUS"), ("SENAL", 7, "DASHED"), ("COM", 7, "CONTINUOUS"),
    ("MECANICO", 7, "CONTINUOUS"), ("POTENCIA", 7, "CONTINUOUS"), ("PISOS", 8, "PHANTOM"),
    ("EXTRUSORA_A01", 7, "CONTINUOUS"), ("DETALLE", 7, "CONTINUOUS"),
]
# ---- tipos de linea (patron en unidades de dibujo, LTSCALE = 1) ----
LTYPES = [
    ("CONTINUOUS", "Linea continua", []),
    ("DASHED", "Senal electrica ISA __ __ __", [8.0, -4.0]),
    ("ACEITE_TERMICO", "Aceite termico ____ . . ____", [24.0, -4.5, 1.5, -4.5, 1.5, -4.5]),
    ("AIRE_QUENCH", "Aire quench ______ __ ______", [26.0, -5.0, 8.0, -5.0]),
    ("HUMOS", "Humos . . . . . .", [1.5, -5.0]),
    ("ENSIMAJE", "Ensimaje ___ ___ . ___ ___ .", [12.0, -3.5, 12.0, -3.5, 1.5, -3.5]),
    ("AGUA", "Agua ____ . ____ .", [14.0, -4.0, 1.5, -4.0]),
    ("PHANTOM", "Pisos ______ __ __ ______", [40.0, -5.0, 6.0, -5.0, 6.0, -5.0]),
]

# ================= EMISORES =================
def line(x1, y1, x2, y2, layer="EQUIPOS"):
    ents.append(["LINE", ("8", layer), ("10", x1), ("20", flip(y1)), ("30", 0.0), ("11", x2), ("21", flip(y2)), ("31", 0.0)])

def circle(cx, cy, r, layer="EQUIPOS"):
    ents.append(["CIRCLE", ("8", layer), ("10", cx), ("20", flip(cy)), ("30", 0.0), ("40", r)])

def text(x, y, h, s, layer="TEXTOS", align="left"):
    e = ["TEXT", ("8", layer), ("10", x), ("20", flip(y)), ("30", 0.0), ("40", h), ("1", s)]
    if align == "center":
        e += [("72", 1), ("11", x), ("21", flip(y)), ("31", 0.0)]
    elif align == "right":
        e += [("72", 2), ("11", x), ("21", flip(y)), ("31", 0.0)]
    ents.append(e)

def poly(pts, layer="EQUIPOS", width=0.0, closed=False, bulges=None):
    # flag 128 = patron de linea continuo a traves de los vertices (PLINEGEN)
    e = ["POLYLINE", ("8", layer), ("66", 1), ("70", (1 if closed else 0) | 128)]
    if width > 0:
        e += [("40", width), ("41", width)]
    ents.append(e)
    for i, (x, y) in enumerate(pts):
        v = ["VERTEX", ("8", layer), ("10", x), ("20", flip(y)), ("30", 0.0)]
        if bulges and bulges[i]:
            v.append(("42", bulges[i]))
        ents.append(v)
    ents.append(["SEQEND", ("8", layer)])

def rect(x1, y1, x2, y2, layer="EQUIPOS"):
    poly([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], layer=layer, closed=True)

def dot(x, y, r, layer="EQUIPOS"):
    # punto relleno (dona de ancho = radio)
    poly([(x - r / 2, y), (x + r / 2, y)], layer, width=r, closed=True, bulges=[1.0, 1.0])

def solid_tri(p1, p2, p3, layer="EQUIPOS"):
    ents.append(["SOLID", ("8", layer),
                 ("10", p1[0]), ("20", flip(p1[1])), ("30", 0.0),
                 ("11", p2[0]), ("21", flip(p2[1])), ("31", 0.0),
                 ("12", p3[0]), ("22", flip(p3[1])), ("32", 0.0),
                 ("13", p3[0]), ("23", flip(p3[1])), ("33", 0.0)])

def flecha(tipx, tipy, direc, l=16.0, w=11.0, layer="FUNDIDO"):
    u = {"E": (1, 0), "W": (-1, 0), "S": (0, 1), "N": (0, -1)}[direc]
    flecha_v((tipx, tipy), u[0], u[1], l, w, layer)

def flecha_v(tip, ux, uy, l, w, layer):
    L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
    bx, by = tip[0] - ux * l, tip[1] - uy * l
    px, py = -uy * w / 2, ux * w / 2
    solid_tri(tip, (bx + px, by + py), (bx - px, by - py), layer)

def _hw(s, th):
    # media anchura aproximada del texto
    return len(str(s)) * th * 0.375

def bubble(cx, cy, r, top, bot, layer="INSTRUMENTOS", th=None):
    th = th or r * 0.42
    r = max(r, _hw(top, th) * 1.12 + 2, _hw(bot, th) * 1.12 + 2)
    circle(cx, cy, r, layer)
    line(cx - r, cy, cx + r, cy, layer)
    text(cx, cy - 3.0, th, top, layer, "center")
    text(cx, cy + th + 5.0, th, bot, layer, "center")
    return r

def plc(cx, cy, s, top, bot, layer="INSTRUMENTOS", th=None):
    th = th or s * 0.42
    s = max(s, _hw(top, th) + 3 + 2, _hw(bot, th) + th + 5 + 2)
    rect(cx - s, cy - s, cx + s, cy + s, layer)
    poly([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], layer=layer, closed=True)
    text(cx, cy - 3.0, th, top, layer, "center")
    text(cx, cy + th + 5.0, th, bot, layer, "center")
    return s

def motor(cx, cy, r, tag=None, tagpos="S", layer="EQUIPOS"):
    circle(cx, cy, r, layer)
    text(cx, cy + r * 0.38, r * 1.05, "M", layer, "center")
    if tag:
        if tagpos == "S":
            text(cx, cy + r + 13, TM, tag, "TEXTOS", "center")
        elif tagpos == "N":
            text(cx, cy - r - 5, TM, tag, "TEXTOS", "center")
        elif tagpos == "W":
            text(cx - r - 5, cy + 3, TM, tag, "TEXTOS", "right")
        elif tagpos == "E":
            text(cx + r + 5, cy + 3, TM, tag, "TEXTOS", "left")

def vfd(cx, cy, w, h, tag, sub, layer="EQUIPOS"):
    rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, layer)
    text(cx, cy - 1, 9.4, tag, "TEXTOS", "center")
    if sub:
        text(cx, cy + 11, 7.2, sub, "TEXTOS", "center")

def contactor(cx, cy, w=30, h=18, layer="EQUIPOS"):
    rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, layer)
    text(cx, cy + 4, 9, "K", "TEXTOS", "center")

def zigzag(x, y, n=4, step=8.0, amp=11.0, layer="EQUIPOS"):
    pts = [(x, y)]
    for i in range(n):
        pts.append((x + step * (2 * i + 1), y - amp))
        pts.append((x + step * (2 * i + 2), y))
    poly(pts, layer=layer)

def fan(cx, cy, r, layer="EQUIPOS"):
    circle(cx, cy, r, layer)
    for k in range(3):
        a = math.radians(90 + k * 120)
        line(cx, cy, cx + r * 0.8 * math.cos(a), cy - r * 0.8 * math.sin(a), layer)

def gearpump(cx, cy, r, layer="EQUIPOS"):
    circle(cx, cy, r, layer)
    circle(cx - r * 0.38, cy, r * 0.32, layer)
    circle(cx + r * 0.38, cy, r * 0.32, layer)

def cpump(cx, cy, r, layer="EQUIPOS"):
    # bomba centrifuga (voluta + eje + descarga superior + base)
    circle(cx, cy, r, layer)
    circle(cx, cy, r * 0.2, layer)
    poly([(cx - r * 0.62, cy - r * 0.78), (cx - r * 0.62, cy - r * 1.5),
          (cx + r * 0.62, cy - r * 1.5), (cx + r * 0.62, cy - r * 0.78)], layer)
    poly([(cx - r * 0.55, cy + r * 0.83), (cx - r * 1.05, cy + r * 1.5),
          (cx + r * 1.05, cy + r * 1.5), (cx + r * 0.55, cy + r * 0.83)], layer)

def rupture_disc(cx, cy, layer="INSTRUMENTOS"):
    line(cx - 12, cy, cx + 12, cy, layer)
    pts = [(cx + 10 * math.cos(math.radians(a)), cy - 10 * math.sin(math.radians(a))) for a in range(0, 181, 20)]
    poly(pts, layer=layer)

def hop(x, y, layer, r=8, width=0.0):
    # salto (cruce sin conexion) sobre una linea HORIZONTAL que pasa por (x,y)
    pts = [(x + r * math.cos(math.radians(a)), y - r * math.sin(math.radians(a))) for a in range(180, -1, -15)]
    poly(pts, layer=layer, width=width)

def vhop(x, y, layer, r=8, width=0.0):
    # salto sobre una linea VERTICAL que pasa por (x,y): semicirculo hacia la derecha
    pts = [(x + r * math.sin(math.radians(a)), y - r * math.cos(math.radians(a))) for a in range(0, 181, 15)]
    poly(pts, layer=layer, width=width)

def seg(p1, p2, layer, width=0.0, gaps=()):
    # tramo recto p1 -> p2 interrumpido en gaps = [(distancia desde p1, media abertura)]
    L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    ux, uy = (p2[0] - p1[0]) / L, (p2[1] - p1[1]) / L
    P = lambda t: (p1[0] + ux * t, p1[1] + uy * t)
    s = 0.0
    for (t, hl) in sorted(gaps):
        if t - hl > s + 0.01:
            poly([P(s), P(t - hl)], layer, width)
        s = t + hl
    if L > s + 0.01:
        poly([P(s), P(L)], layer, width)
    return P, ux, uy

def mec(p1, p2, mark=0.5, hops=()):
    # ENLACE MECANICO (eje motor -> bomba / rodillo / ventilador): ISA-5.1-2009 T.5.3.2 No.16
    L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    tm = L * mark if mark <= 1 else mark
    P, ux, uy = seg(p1, p2, "MECANICO", 0.0, [(tm, 4.6)] + [(h, 8.0) for h in hops])
    c = P(tm)
    circle(c[0], c[1], 4.6, "MECANICO")
    dot(c[0], c[1], 2.2, "MECANICO")
    for h in hops:
        q = P(h)
        if abs(uy) < 1e-9:
            hop(q[0], q[1], "MECANICO", 8, 0)
        else:
            vhop(q[0], q[1], "MECANICO", 8, 0)

def com(p1, p2, spacing=40.0):
    # BUS DE CAMPO / COMUNICACION con variador: ISA-5.1-2009 T.5.3.2 No.14 (rombos huecos)
    L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    n = max(1, int(L // spacing))
    ts = [(k + 0.5) * L / n for k in range(n)]
    d = 5.0
    P, ux, uy = seg(p1, p2, "COM", 0.0, [(t, d) for t in ts])
    for t in ts:
        c = P(t)
        poly([(c[0] + ux * d, c[1] + uy * d), (c[0] - uy * d * 0.8, c[1] + ux * d * 0.8),
              (c[0] - ux * d, c[1] - uy * d), (c[0] + uy * d * 0.8, c[1] - ux * d * 0.8)], "COM", closed=True)

def arc_pts(C, R, a1, a2, sweep, n=10):
    if sweep == 1:
        da = (a2 - a1) % (2 * math.pi)
    else:
        da = -((a1 - a2) % (2 * math.pi))
    return [(C[0] + R * math.cos(a1 + da * k / n), C[1] + R * math.sin(a1 + da * k / n)) for k in range(n + 1)]

def fillet_path(points, radii):
    out = [points[0]]
    centers = []
    for i in range(1, len(points) - 1):
        P, V, N = points[i - 1], points[i], points[i + 1]
        R = radii[i - 1]
        u1 = (V[0] - P[0], V[1] - P[1]); l1 = math.hypot(*u1); u1 = (u1[0] / l1, u1[1] / l1)
        u2 = (N[0] - V[0], N[1] - V[1]); l2 = math.hypot(*u2); u2 = (u2[0] / l2, u2[1] / l2)
        cosang = max(-1.0, min(1.0, -(u1[0] * u2[0] + u1[1] * u2[1])))
        theta = math.acos(cosang)
        t = R / math.tan(theta / 2)
        Tin = (V[0] - u1[0] * t, V[1] - u1[1] * t)
        Tout = (V[0] + u2[0] * t, V[1] + u2[1] * t)
        b = (u2[0] - u1[0], u2[1] - u1[1]); lb = math.hypot(*b); b = (b[0] / lb, b[1] / lb)
        d = R / math.sin(theta / 2)
        C = (V[0] + b[0] * d, V[1] + b[1] * d)
        cross = u1[0] * u2[1] - u1[1] * u2[0]
        sweep = 1 if cross > 0 else 0
        a1 = math.atan2(Tin[1] - C[1], Tin[0] - C[0])
        a2 = math.atan2(Tout[1] - C[1], Tout[0] - C[0])
        out.append(Tin)
        out.extend(arc_pts(C, R, a1, a2, sweep, 14)[1:])
        centers.append(C)
    out.append(points[-1])
    return out, centers

def offset_path(path, d):
    # desplaza una polilinea suave una distancia d (normal izquierda en coordenadas de trabajo)
    pts = [path[0]]
    for p in path[1:]:
        if math.hypot(p[0] - pts[-1][0], p[1] - pts[-1][1]) > 1e-6:
            pts.append(p)
    out = []
    n = len(pts)
    for i in range(n):
        tans = []
        if i > 0:
            a = (pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); la = math.hypot(*a); tans.append((a[0] / la, a[1] / la))
        if i < n - 1:
            b = (pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); lb = math.hypot(*b); tans.append((b[0] / lb, b[1] / lb))
        tx = sum(t[0] for t in tans); ty = sum(t[1] for t in tans); lt = math.hypot(tx, ty)
        tx, ty = tx / lt, ty / lt
        nx, ny = -ty, tx
        miter = 1.0
        if len(tans) == 2:
            miter = 1.0 / max(0.5, nx * (-tans[0][1]) + ny * tans[0][0])
        out.append((pts[i][0] + nx * d * miter, pts[i][1] + ny * d * miter))
    return out

def cinta(path, half=3.5, width=WPR):
    # FILAMENTOS / MAZO: cinta de doble linea (se lee como banda de fibras)
    poly(offset_path(path, half), "PRODUCTO", width)
    poly(offset_path(path, -half), "PRODUCTO", width)

# codigo de letras de cada servicio: va intercalado en la linea (---AT---AT---) para leer el plano en blanco y negro
CODIGO = {"FUNDIDO": "FU", "ACEITE_TERMICO": "AT", "AIRE_QUENCH": "AQ", "HUMOS": "HU", "ENSIMAJE": "EN", "AGUA": "AG"}
CTH = 7.6

def svc(pts, layer, width, at=()):
    """Linea de servicio con su codigo intercalado. at = distancias a lo largo del trazo donde va el codigo."""
    code = CODIGO[layer]
    segs, acc = [], 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, acc, L)); acc += L
    def punto(d):
        for (a, b, s0, L) in segs:
            if d <= s0 + L + 1e-9:
                u = (d - s0) / L
                return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        return pts[-1]
    gaps = []
    for d in at:
        for (a, b, s0, L) in segs:
            if s0 <= d <= s0 + L:
                horiz = abs(b[1] - a[1]) < 1e-6
                h = (_hw(code, CTH) + 3.5) if horiz else (CTH / 2 + 4)
                gaps.append((d - h, d + h))
                c = punto(d)
                text(c[0], c[1] + CTH / 2, CTH, code, layer, "center")
                break
    gaps.sort()
    cortes = [0.0]
    for (g0, g1) in gaps:
        cortes += [g0, g1]
    cortes.append(acc)
    for k in range(0, len(cortes), 2):
        s, e = cortes[k], cortes[k + 1]
        if e - s < 0.5:
            continue
        piece = [punto(s)] + [b for (a, b, s0, L) in segs if s < s0 + L < e] + [punto(e)]
        poly(piece, layer, width)

def ell(cx, cy, a, b, t0, t1, n):
    return [(cx + a * math.cos(t0 + (t1 - t0) * k / n), cy + b * math.sin(t0 + (t1 - t0) * k / n)) for k in range(n + 1)]

# ================= LLANTA EN 3D (vista a 30 grados) =================
def llanta3d(cx, cy, Ro, Ri, t, G, rows, hole_r=1.6, nfront=11, nback=6, lay="EQUIPOS"):
    """Hilera anular ('llanta') vista desde arriba a 30 grados.
    cara superior (elipse exterior + hueco), banda lateral, pared interior visible, orificios y cortina de filamentos hasta la guia G."""
    k = K3D
    poly(ell(cx, cy, Ro, Ro * k, 0, 2 * math.pi, 96), lay, closed=True)
    poly(ell(cx, cy, Ri, Ri * k, 0, 2 * math.pi, 72), lay, closed=True)
    poly(ell(cx, cy + t, Ro, Ro * k, 0, math.pi, 60), lay)
    line(cx - Ro, cy, cx - Ro, cy + t, lay)
    line(cx + Ro, cy, cx + Ro, cy + t, lay)
    inner = [p for p in ell(cx, cy + t, Ri, Ri * k, math.pi, 2 * math.pi, 60)
             if ((p[0] - cx) / Ri) ** 2 + ((p[1] - cy) / (Ri * k)) ** 2 < 0.985]
    if len(inner) > 1:
        poly(inner, lay)
    # orificios (huequitos) en filas concentricas sobre la cara anular
    for r in rows:
        n = int(2 * math.pi * r / 13.0)
        for j in range(n):
            a = 2 * math.pi * (j + 0.5 * (rows.index(r) % 2)) / n
            dot(cx + r * math.cos(a), cy + r * k * math.sin(a), hole_r, lay)
    # cortina de filamentos: salen de la cara inferior (radio medio) y convergen a la guia; se recortan bajo la banda
    rm = (Ro + Ri) / 2.0
    bottom = lambda x: cy + t + k * math.sqrt(max(0.0, Ro * Ro - (x - cx) ** 2))
    def filamento(th):
        S = (cx + rm * math.cos(th), cy + t + rm * k * math.sin(th))
        L = math.hypot(G[0] - S[0], G[1] - S[1])
        P = lambda u: (S[0] + (G[0] - S[0]) * u, S[1] + (G[1] - S[1]) * u)
        lo, hi = 0.0, 1.0
        for _ in range(40):   # primer punto visible bajo la banda exterior
            mid = (lo + hi) / 2
            q = P(mid)
            if abs(q[0] - cx) < Ro and q[1] < bottom(q[0]) + 1.5:
                lo = mid
            else:
                hi = mid
        u_end = 1.0 - 9.5 / L
        if hi < u_end:
            a, b = P(hi), P(u_end)
            line(a[0], a[1], b[0], b[1], "PRODUCTO")
    for i in range(nfront + 2):
        filamento(math.pi * i / (nfront + 1))
    for i in range(nback):
        filamento(math.pi + math.pi * (i + 0.5) / nback)
    circle(G[0], G[1], 9, "EQUIPOS")

def aire_interno(cx, cy, Ri, n=4, l1=6, l2=30):
    # flechas del anillo de aire hacia el centro (dentro del hueco de la llanta)
    k = K3D
    for j in range(n):
        a = 2 * math.pi * j / n
        p1 = (cx + (Ri - l1) * math.cos(a), cy + (Ri - l1) * k * math.sin(a))
        p2 = (cx + (Ri - l2) * math.cos(a), cy + (Ri - l2) * k * math.sin(a))
        poly([p1, p2], "AIRE_QUENCH", 1.2)
        flecha_v(p2, p2[0] - p1[0], p2[1] - p1[1], 7, 6, "AIRE_QUENCH")

# ================= MARCO, CAJETIN, NOTAS, CONVENCIONES =================
rect(15, 15, W - 15, H - 15, "MARCO")
rect(25, 25, W - 25, H - 25, "MARCO")
BY0, BYB = 1440, H - 25        # franja inferior (convenciones / notas / cajetin)

# ---- cajetin ----
CX1, CX2 = 1720, W - 25
rect(CX1, BY0, CX2, BYB, "MARCO")
for yy in (1482, 1526, 1558):
    line(CX1, yy, CX2, yy, "MARCO")
for xx in (1945, 2165):
    line(xx, 1558, xx, BYB, "MARCO")
cxm = (CX1 + CX2) / 2
text(cxm, 1467, 12, "ECCI - INSTRUMENTACION INDUSTRIAL - MECATRONICA VIII", "TEXTOS", "center")
text(cxm, 1511, 15, "P&ID PLANT A: EXTRUSORA + HILADORES 1 Y 2", "TEXTOS", "center")
text(cxm, 1547, 10, "PLANT A (ANONYMIZED) - FILAMENTOS DE POLIPROPILENO", "TEXTOS", "center")
cj = [
    (CX1 + 10, ["NORMA: ANSI/ISA-5.1-2009", "COLORES: REF. NTC 3458", "ESCALA: S/E", "FORMATO: A0 / PLIEGO"]),
    (1955, ["FECHA: 02-10-2026", "REV. 4: LINEAS POR SERVICIO", "Y LLANTAS EN 3D", "HOJA: 1 DE 1"]),
    (2175, ["DIBUJO:", "REVISO:", "APROBO:", ""]),
]
for (xx, rows_) in cj:
    for i, s in enumerate(rows_):
        text(xx, 1580 + i * 25, 8.4, s, "TEXTOS")

# ---- notas ----
NX1, NX2 = 1085, 1710
rect(NX1, BY0, NX2, BYB, "MARCO")
text(NX1 + 12, 1462, TM, "NOTAS", "TEXTOS")
notas = [
    "AREA 01 = EXTRUSORA (EQUIPO 1, REDIBUJADA PARA UNIR EL PROCESO). AREA 02 = HILADORES 1 Y 2. TAGS SEGUN EL LISTADO OFICIAL DE SENALES.",
    "CABEZAL = UN SOLO BLOQUE CALEFACTADO CON ACEITE TERMICO (LAZO TEB-08 / TY-07) CON DISTRIBUIDOR, 2 BOMBAS DE ENGRANAJES Y 2 PAQUETES.",
    "LLANTA = HILERA ANULAR (~65.000 ORIFICIOS) + ANILLO DE AIRE, EN VISTA A 30 GRADOS: EL AIRE ENTRA POR EL COSTADO HACIA EL CENTRO Y LOS FILAMENTOS CAEN EN CORTINA HASTA LA GUIA (DETALLE A).",
    "ESPIRINETE 120-150 BAR (INSTRUMENTISTA); ALARMA ALTA 180 BAR*. ACEITE TERMICO ~250 C*. PSE-01/02 = DISCO DE RUPTURA ASUMIDO, NO CONFIRMADO EN PLANTA.",
    "VFD-10 EXISTENTE (VISTO EN PLANTA); DEMAS VARIADORES ASUMIDOS (RETROFIT*) CON MODULO DE BUS. BOMBA 1 CABLEADA; BOMBA 2 Y RODILLOS LEIDOS POR BUS.",
    "TEB-09/10 EN EL DUCTO DE AIRE DE 6 PULG. MT-01/02 = PROPUESTA DE MEJORA: HUMEDAD / PUNTO DE ROCIO EN LA TOMA DE AIRE.",
    "EL MAZO (TOW) DE LAS 2 LLANTAS SALE HACIA LA IZQUIERDA AL GODET 1 (FUERA DE ALCANCE).",
    "(*) = DATO ASUMIDO. ZSB = FINAL DE CARRERA DE BANDEJA. ST-04/05 = REFERENCIA DE VELOCIDAD DE LOS VENTILADORES (TAG DEL LISTADO).",
    "CADA SERVICIO TIENE PATRON, GROSOR, CODIGO DE LETRAS (FU, AT, AQ, HU, EN, AG) Y COLOR PROPIOS: SE LEE IGUAL EN B/N (MONOCHROME.CTB). PLOTEAR EN A0 / PLIEGO, 'AJUSTAR A PAPEL'.",
]
NTH, NLS = 7.4, 11.3
maxc = int((NX2 - NX1 - 40) / (NTH * 0.75))
ny = 1482
for i, n in enumerate(notas):
    words, cur, lines_ = n.split(), "", []
    for wd in words:
        if len(cur) + len(wd) + 1 > maxc:
            lines_.append(cur); cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines_.append(cur)
    text(NX1 + 12, ny, NTH, "%d." % (i + 1), "TEXTOS")
    for ln in lines_:
        text(NX1 + 30, ny, NTH, ln, "TEXTOS")
        ny += NLS
NOTAS_FIN = ny

# ---- convenciones ----
LX1, LX2 = 40, 1075
rect(LX1, BY0, LX2, BYB, "MARCO")
line(525, BY0, 525, BYB, "MARCO")
text(LX1 + 12, 1462, TM, "CONVENCIONES - SIMBOLOS", "TEXTOS")
text(537, 1462, TM, "CONVENCIONES - LINEAS (CODIGO + PATRON: SE LEE EN B/N)", "TEXTOS")
LR = [1490, 1520, 1550, 1580, 1610, 1640]
LT = 7.4
# simbolos (2 columnas)
bubble(72, LR[0], 11, "XX", "00", th=5); text(96, LR[0] + 4, LT, "INSTRUMENTO EN CAMPO (ELEM. PRIMARIO)")
plc(72, LR[1], 11, "XX", "00", th=5); text(96, LR[1] + 4, LT, "FUNCION EN PLC / PANTALLA")
motor(72, LR[2], 11); text(96, LR[2] + 4, LT, "MOTOR")
vfd(72, LR[3], 44, 20, "VFD", ""); text(100, LR[3] + 4, LT, "VARIADOR (ACCIONAMIENTO)")
contactor(72, LR[4], 28, 16); text(96, LR[4] + 4, LT, "CONTACTOR / ARRANCADOR")
zigzag(56, LR[5] + 5, n=2, step=7, amp=9); text(96, LR[5] + 4, LT, "RESISTENCIA DE CALEFACCION")
gearpump(316, LR[0], 11); text(338, LR[0] + 4, LT, "BOMBA DOSIFICADORA (ENGRANAJES)")
cpump(316, LR[1], 9); text(338, LR[1] + 4, LT, "BOMBA CENTRIFUGA")
fan(316, LR[2], 11); text(338, LR[2] + 4, LT, "VENTILADOR / EXTRACTOR")
rupture_disc(316, LR[3] + 4); text(338, LR[3] + 4, LT, "DISCO DE RUPTURA (PSE)")
line(296, LR[4], 308, LR[4], "SENAL"); hop(316, LR[4], "SENAL", 8, 0); line(324, LR[4], 336, LR[4], "SENAL")
text(342, LR[4] + 4, LT, "CRUCE SIN CONEXION")
line(304, LR[5] - 9, 316, LR[5] + 9, "MARCO"); line(314, LR[5] - 9, 326, LR[5] + 9, "MARCO"); text(338, LR[5] + 4, LT, "LIMITE DE BATERIA")

def muestra(kind, x, y, L=70):
    if kind in CODIGO:
        wd = {"FUNDIDO": WF, "ACEITE_TERMICO": WAT, "AIRE_QUENCH": WAQ, "HUMOS": WHU, "ENSIMAJE": WEN, "AGUA": WAG}[kind]
        svc([(x, y), (x + 74, y)], kind, wd, at=[61])
    elif kind == "PRODUCTO":
        cinta([(x, y), (x + L - 10, y)]); flecha(x + L, y, "E", 12, 12, "PRODUCTO")
    elif kind == "SENAL":
        poly([(x, y), (x + L, y)], "SENAL")
    elif kind == "COM":
        com((x, y), (x + L, y), 40)
    elif kind == "MECANICO":
        mec((x, y), (x + L, y))
    elif kind == "CONEXION":
        line(x, y, x + L, y, "INSTRUMENTOS")
    elif kind == "PISOS":
        poly([(x, y), (x + L, y)], "PISOS")

lineas_ley = [
    ("FUNDIDO", "FUNDIDO PP - PROCESO PRINCIPAL", "CONTINUA MUY GRUESA + FU (ROJO)"),
    ("PRODUCTO", "FILAMENTOS / MAZO (TOW)", "CINTA DE DOBLE LINEA (NEGRO)"),
    ("ACEITE_TERMICO", "ACEITE TERMICO (CALEFACCION)", "TRAZO + 2 PUNTOS + AT (CAFE)"),
    ("AIRE_QUENCH", "AIRE DE ENFRIAMIENTO (QUENCH)", "TRAZO LARGO + CORTO + AQ (AZUL)"),
    ("HUMOS", "HUMOS A EXTRACCION", "PUNTEADA + HU (OCRE)"),
    ("ENSIMAJE", "ACEITE DE ENSIMAJE (LUBRICANTE)", "2 TRAZOS + PUNTO + EN (NARANJA)"),
    ("AGUA", "AGUA DE ENFRIAMIENTO", "TRAZO + PUNTO + AG (VERDE)"),
    ("SENAL", "SENAL ELECTRICA 4-20mA / DIGITAL", "ISA-5.1 T.5.3.2 No.6 - TRAZOS"),
    ("COM", "BUS DE CAMPO (COM. VARIADOR)", "ISA-5.1 T.5.3.2 No.14"),
    ("MECANICO", "ENLACE MECANICO (EJE DE MOTOR)", "ISA-5.1 T.5.3.2 No.16"),
    ("CONEXION", "CONEXION A PROCESO / POTENCIA", "ISA-5.1 T.5.3.1 No.1 - CONTINUA FINA"),
    ("PISOS", "DIVISION ENTRE PISOS", "TRAZO LARGO + 2 CORTOS (GRIS)"),
]
for i, (kind, t1, t2) in enumerate(lineas_ley):
    col, row = divmod(i, 6)
    x0 = 537 + col * 268
    yy = LR[row] - 3
    muestra(kind, x0, yy)
    text(x0 + 82, yy + 1, LT, t1)
    text(x0 + 82, yy + 12, 6.4, t2)

# ================= PISOS =================
PISO_Y = 900
line(30, PISO_Y, W - 30, PISO_Y, "PISOS")
text(36, PISO_Y - 10, 11, "PISO 2 - PLATAFORMA DE HILATURA", "TEXTOS")
text(36, PISO_Y + 22, 11, "PISO 1 - PISO DE PLANTA", "TEXTOS")

# ================= EXTRUSORA (AREA 01, derecha, piso 1) =================
EL = "EXTRUSORA_A01"
EY = 100
BX1, BX2, BY1, BY2 = 1740, 2270, 1035 + EY, 1100 + EY
MY = (BY1 + BY2) / 2
rect(BX1, BY1, BX2, BY2, EL)
line(BX1 + 6, MY, BX2 - 6, MY, EL)
xx = BX1 + 14
while xx < BX2 - 24:
    line(xx, BY1 + 8, xx + 18, BY2 - 8, EL); xx += 26
poly([(BX1, BY1 + 10), (BX1 - 30, BY1 + 22), (BX1 - 30, BY2 - 22), (BX1, BY2 - 10)], EL, closed=True)
poly([(2185, 1060), (2259, 1060), (2240, 1110), (2204, 1110)], EL, closed=True)
rect(2212, 1110, 2232, BY1, EL)
text(2222, 1052, TS, "TOLVA", "TEXTOS", "center")
rect(BX2, BY1 + 10, BX2 + 28, BY2 - 10, EL)
motor(2335, MY, 18, "-ME0101", "S", EL)
mec((BX2 + 28, MY), (2317, MY))
text(2335, 1118, TS, "MOTOR", "TEXTOS", "center"); text(2335, 1131, TS, "PRINCIPAL", "TEXTOS", "center")
for k in range(7):
    zx = BX1 + 10 + k * 64
    zigzag(zx, BY1, n=3, step=7, amp=9, layer=EL)
    text(zx + 22, BY1 - 17, 7.6, "-TH%d101" % k, "TEXTOS", "center")
    r = bubble(zx + 22, 1062, 18, "TE", "%d101" % k, EL, th=7.6)
    line(zx + 22, 1062 + r, zx + 22, BY1 - 27, EL)
    s = plc(zx + 22, 990, 18, "TIC", "%d101" % k, EL, th=7.6)
    line(zx + 22, 990 + s, zx + 22, 1062 - r, "SENAL")
for k in range(7):
    fx = BX1 + 32 + k * 64
    fan(fx, 1250, 13, EL)
    text(fx, 1282, 7.6, "-F%d101" % k, "TEXTOS", "center")
    line(fx, BY2, fx, 1237, EL)
    s = plc(fx, 1336, 18, "HS", "%d101" % k, EL, th=7.6)
    line(fx, 1263, fx, 1271, "SENAL")
    line(fx, 1288, fx, 1336 - s, "SENAL")
cpump(2300, 1268, 14, EL)
motor(2345, 1268, 12, None, "S", EL)
mec((2314, 1268), (2333, 1268))
svc([(2300, 1247), (2300, BY2)], "AGUA", WAG, at=[22])
flecha(2300, BY2 + 1, "N", 10, 8, "AGUA")
text(2322, 1302, TS, "-B0101", "TEXTOS", "center"); text(2322, 1315, TS, "BOMBA DE AGUA", "TEXTOS", "center")
text(2010, 1388, 10.5, "EXTRUSORA - AREA 01 (INSTRUMENTACION EQUIPO 1)", "TEXTOS", "center")
text(2010, 1404, 7.6, "CAPA 'EXTRUSORA_A01': BORRAR E INSERTAR EL DWG ORIGINAL SI SE PREFIERE", "TEXTOS", "center")

# filtro + PT + fundido que sube (entra al cabezal por la cara derecha)
FX = 1660
rect(FX, MY - 25, FX + 40, MY + 25, EL)
for yy in (MY - 13, MY, MY + 13):
    line(FX + 5, yy, FX + 35, yy, EL)
text(FX + 20, MY + 42, TS, "FILTRO", "TEXTOS", "center")
poly([(BX1 - 30, MY), (FX + 40, MY)], "FUNDIDO", WF)
flecha(BX1 - 34, MY, "W", 16, 12, "FUNDIDO")
r = bubble(FX + 20, 1090, 18, "PT", "0101", EL, th=7.6)
line(FX + 20, 1090 + r, FX + 20, MY - 25, EL)
s = plc(FX + 20, 1022, 18, "PI", "0101", EL, th=7.6)
line(FX + 20, 1022 + s, FX + 20, 1090 - r, "SENAL")
RX = 1640
svc([(FX, MY), (RX, MY), (RX, 520), (1600, 520)], "FUNDIDO", WF, at=[127.5, 547.5])
flecha(RX, 780, "N", 18, 13, "FUNDIDO")
flecha(1614, 520, "W", 16, 12, "FUNDIDO")
line(RX - 8, 915, RX + 8, 945, "MARCO"); line(RX, 915, RX + 16, 945, "MARCO")
text(RX - 14, 934, TS, "LIMITE DE BATERIA AREA 01 / 02", "TEXTOS", "right")
text(RX + 14, 766, TM, "FUNDIDO QUE SUBE", "TEXTOS")
text(RX + 14, 780, TM, "AL CABEZAL (PISO 2)", "TEXTOS")

# ================= CABEZAL DE HILATURA (piso 2, un solo bloque) =================
HX1, HY1, HX2, HY2 = 600, 260, 1600, 560
rect(HX1, HY1, HX2, HY2, "EQUIPOS")
rect(HX1 + 6, HY1 + 6, HX2 - 6, HY2 - 6, "EQUIPOS")
text(1100, 296, 13, "CABEZAL DE HILATURA (SPIN BEAM)", "TEXTOS", "center")
text(1100, 314, TS, "BLOQUE UNICO CALEFACTADO CON ACEITE TERMICO", "TEXTOS", "center")
text(1590, 296, TS, "DENTRO: BOMBAS + PAQUETES", "TEXTOS", "right")
text(1590, 310, TS, "CAMISA DE ACEITE TERMICO", "TEXTOS", "right")
P1, P2 = 870, 1330                      # ejes de las posiciones de hilatura 1 y 2
svc([(1594, 520), (1500, 520), (1500, 350), (P1 + 22, 350)], "FUNDIDO", WF, at=[174, 534])
for px in (P1, P2):
    poly([(px + 22, 350), (px + 22, 372)], "FUNDIDO", WF)
    flecha(px + 22, 372, "S", 12, 10, "FUNDIDO")
flecha(1100, 350, "W", 16, 12, "FUNDIDO")
text(1100, 340, TS, "DISTRIBUIDOR DE FUNDIDO", "TEXTOS", "center")

# llantas: geometria comun
CY_R, RO, RI, TH_R = 650, 112, 70, 24
RM = (RO + RI) / 2.0
G_Y = 960

def posicion(px, n, tags):
    side = -1 if n == 1 else 1           # PTB/PIA: izquierda en la posicion 1, derecha en la 2
    gearpump(px, 395, 30)
    text(px + 36, 398, TS, "BOMBA DOSIF. %d" % n, "TEXTOS")
    for dx in (-14, 14):
        poly([(px + dx, 425), (px + dx, 470)], "FUNDIDO", WF)
        flecha(px + dx, 468, "S", 10, 9, "FUNDIDO")
    rupture_disc(px + 48, 448)
    line(px + 14, 448, px + 36, 448, "INSTRUMENTOS")
    line(px + 48, 438, px + 48, 428, "INSTRUMENTOS"); flecha(px + 48, 424, "N", 8, 6, "INSTRUMENTOS")
    rb = bubble(px + 80, 448, 16, "PSE", "0%d*" % n, th=7.0)
    line(px + 60, 448, px + 80 - rb, 448, "INSTRUMENTOS")
    rect(px - 78, 470, px + 78, 560, "EQUIPOS")
    text(px, 500, TS, "PAQUETE DE HILADO", "TEXTOS", "center")
    text(px, 515, TS, "ESPIRINETE %d" % n, "TEXTOS", "center")
    # fundido del paquete a la llanta (entra por la cara superior, lado posterior)
    for dx in (-60, 60):
        yfar = CY_R - K3D * math.sqrt(RM * RM - dx * dx) + 2
        poly([(px + dx, 560), (px + dx, yfar - 2)], "FUNDIDO", WF)
        flecha(px + dx, yfar, "S", 11, 10, "FUNDIDO")
    # PTB (elemento primario) en el paquete; PIA fuera del equipo, debajo del cabezal
    bx = px + side * 130
    r = bubble(bx, 480, 22, "PTB", tags["ptb"])
    line(px + side * 78, 480, bx - side * r, 480, "INSTRUMENTOS")
    s = plc(bx, 602, 20, "PIA", tags["ptb"])
    line(bx, 480 + r, bx, 602 - s, "SENAL")
    if side < 0:
        text(bx - s - 6, 598, TS, "120-150 BAR", "TEXTOS", "right"); text(bx - s - 6, 611, TS, "PAH 180*", "TEXTOS", "right")
    else:
        text(bx + s + 6, 598, TS, "120-150 BAR", "TEXTOS"); text(bx + s + 6, 611, TS, "PAH 180*", "TEXTOS")
    # accionamiento: motor + eje (enlace mecanico) + VFD + referencia STD + arranque NCD
    MYp = 205
    motor(px, MYp, 22, tags["me"], "N")
    mec((px, MYp + 22), (px, 365), mark=305 - (MYp + 22), hops=[350 - (MYp + 22)] if tags["cruza"] else [])
    vfd(px - 150, MYp, 78, 34, tags["vfd"], tags["vfdsub"])
    line(px - 111, MYp, px - 22, MYp, "POTENCIA")
    s1 = plc(px - 150, 125, 18, "STD", tags["std"])
    s2 = plc(px - 206, 125, 18, "NCD", tags["std"])
    line(px - 150, 125 + s1, px - 150, MYp - 17, "SENAL")
    poly([(px - 206, 125 + s2), (px - 206, 168), (px - 150, 168)], "SENAL")
    text(px - 178, 94, TS, "4-20mA / ARR-PAR", "TEXTOS", "center")
    if tags["com"]:
        rs = bubble(px + 72, MYp, 22, "ST", tags["snm"])
        mec((px + 22, MYp), (px + 72 - rs, MYp))
        com((px - 150, MYp + 17), (px - 150, 240), 40)
        text(px - 150, 253, TS, "BUS: IN-%s, SNM-%s, XSR-%s, XSF-%s" % ((tags["snm"],) * 4), "TEXTOS", "center")
    else:
        rs = bubble(px + 72, MYp, 22, "SNM", tags["snm"])
        mec((px + 22, MYp), (px + 72 - rs, MYp))
        s3 = plc(px + 72, 125, 18, "SNL", tags["snm"])
        line(px + 72, MYp - rs, px + 72, 125 + s3, "SENAL")
        s4 = plc(px + 132, 125, 18, "XSR/XSF", tags["snm"], th=6.6)
        poly([(px - 150, MYp + 17), (px - 150, 243), (px - 9, 243)], "SENAL")
        hop(px, 243, "SENAL", 9, 0)
        poly([(px + 9, 243), (px + 176, 243), (px + 176, 168), (px + 132, 168), (px + 132, 125 + s4)], "SENAL")
        text(px + 132, 94, TS, "ESTADOS (DI)", "TEXTOS", "center")
    # llanta en 3D + cortina de filamentos hasta la guia
    llanta3d(px, CY_R, RO, RI, TH_R, (px, G_Y), rows=[79, 91, 103])
    aire_interno(px, CY_R, RI)

posicion(P1, 1, dict(ptb="03", me="ME-B1", vfd="VFD-10", vfdsub="EXISTENTE", std="02", snm="02", com=False, cruza=False))
posicion(P2, 2, dict(ptb="04", me="ME-B2", vfd="VFD-11", vfdsub="RETROFIT*", std="03", snm="03", com=True, cruza=True))

# rotulos de las llantas
for (px, al, xl, n) in ((P1, "right", P1 - RO - 8, 1), (P2, "left", P2 + RO + 10, 2)):
    text(xl, 700, TL, "LLANTA %d" % n, "TEXTOS", al)
    text(xl, 715, TS, "HILERA ANULAR", "TEXTOS", al)
    text(xl, 728, TS, "+ ANILLO DE AIRE", "TEXTOS", al)
    text(xl, 741, TS, "(VISTA A 30%%d)", "TEXTOS", al)
text(P1 - RO - 8, 756, TS, "VER DETALLE A", "TEXTOS", "right")
text(P1 - 70, 812, TS, "~65.000 FILAMENTOS", "TEXTOS", "right")
text(P1 - 70, 825, TS, "POR LLANTA -> MAZO", "TEXTOS", "right")

# ================= ACEITE TERMICO: CALDERIN DE LOS ESPIRINETES (piso 2, derecha) =================
KX1, KY1, KX2, KY2 = 1930, 380, 2100, 560
KXC = (KX1 + KX2) / 2 + 8
rect(KX1, KY1, KX2, KY2, "EQUIPOS")
text(KXC, 402, 9, "CALDERIN DE LOS", "TEXTOS", "center")
text(KXC, 416, 9, "ESPIRINETES", "TEXTOS", "center")
text(KXC, 432, TS, "ACEITE TERMICO ~250 C*", "TEXTOS", "center")
line(KX1, 450, KX2, 450, "EQUIPOS")
for k in range(3):
    zigzag(KX1 + 25, 545 - k * 18, n=6, step=10, amp=10)
text(KXC, 578, TS, "RESISTENCIAS (TY-07)", "TEXTOS", "center")
r = bubble(2150, 430, 22, "TEB", "08")
line(KX2, 430, 2150 - r, 430, "INSTRUMENTOS")
s = plc(2150, 336, 20, "TI/TN", "08", th=7.4)
line(2150, 430 - r, 2150, 336 + s, "SENAL")
text(2150 + s + 8, 340, TS, "PANTALLA: T Y SET POINT", "TEXTOS")
TYX = 1945
s2 = plc(TYX, 336, 20, "TY", "07")
line(TYX, 336 + s2, TYX, 500, "SENAL")
line(2150 - s, 336, TYX + s2, 336, "SENAL")
r = bubble(2150, 510, 22, "LSL", "02")
line(KX2, 510, 2150 - r, 510, "INSTRUMENTOS")
s = plc(2225, 510, 18, "MF", "02")
line(2150 + r, 510, 2225 - s, 510, "SENAL")
text(2225, 548, TS, "ALARMA GENERAL:", "TEXTOS", "center")
text(2225, 561, TS, "NIVEL MIN. + TERMICO", "TEXTOS", "center")
cpump(1700, 420, 16)
motor(1700, 370, 12, None, "N")
mec((1700, 396), (1700, 382))
contactor(1700, 326)
line(1700, 358, 1700, 335, "POTENCIA")
s = plc(1700, 282, 18, "NS", "03")
line(1700, 282 + s, 1700, 317, "SENAL")
text(1700, 250, TS, "BOMBA DE RECIRCULACION", "TEXTOS", "center")
svc([(KX1, 420), (1716, 420)], "ACEITE_TERMICO", WAT, at=[170])
poly([(1684, 420), (1600, 420)], "ACEITE_TERMICO", WAT)
flecha(1614, 420, "W", 14, 11, "ACEITE_TERMICO")
svc([(1600, 480), (KX1, 480)], "ACEITE_TERMICO", WAT, at=[130])
flecha(KX1 - 2, 480, "E", 14, 11, "ACEITE_TERMICO")
text(1922, 410, TS, "ACEITE TERMICO - IDA", "TEXTOS", "right")
text(1922, 498, TS, "ACEITE TERMICO - RETORNO", "TEXTOS", "right")

# ================= AIRE DE ENFRIAMIENTO (QUENCH): 2 ventiladores + ductos 6" + llantas =================
def ventilador(fx, fy, tags):
    fan(fx, fy, 26)
    motor(fx + 62, fy, 16, tags["me"], "S")
    mec((fx + 26, fy), (fx + 46, fy))
    vfd(fx + 62, fy - 62, 78, 30, tags["vfd"], "RETROFIT*")
    line(fx + 62, fy - 47, fx + 62, fy - 16, "POTENCIA")
    PX = fx + 155
    s1 = plc(PX, fy - 62, 18, "ST", tags["st"])
    line(fx + 101, fy - 62, PX - s1, fy - 62, "SENAL")
    s2 = plc(PX, fy - 112, 18, "NC", tags["st"])
    poly([(fx + 62, fy - 77), (fx + 62, fy - 112), (PX - s2, fy - 112)], "SENAL")
    s3 = plc(PX, fy + 10, 18, "SNM", tags["st"])
    s4 = plc(PX, fy + 62, 18, "XSR/XSF", tags["st"], th=6.6)
    poly([(fx + 101, fy - 52), (fx + 118, fy - 52), (fx + 118, fy + 62), (PX - s4, fy + 62)], "SENAL")
    line(fx + 118, fy + 10, PX - s3, fy + 10, "SENAL")
    lx = PX + max(s1, s2, s3, s4) + 6
    for (yy, s) in ((fy - 58, "REF. VEL."), (fy - 108, "ARR / PAR"), (fy + 14, "VEL. (AI)"), (fy + 66, "EST. (DI)")):
        text(lx, yy, TS, s, "TEXTOS")
    ix = fx - 26 - 96
    svc([(ix, fy), (fx - 28, fy)], "AIRE_QUENCH", WAQ, at=[70])
    flecha(fx - 26, fy, "E", 14, 11, "AIRE_QUENCH")
    text(ix - 6, fy + 4, TS, "AIRE ATMOSFERICO", "TEXTOS", "right")
    r = bubble(ix + 38, fy + 54, 22, "MT", tags["mt"])
    line(ix + 38, fy + 54 - r, ix + 38, fy + 2, "INSTRUMENTOS")
    s = plc(ix + 38, fy + 116, 16, "MI", tags["mt"], th=7)
    line(ix + 38, fy + 54 + r, ix + 38, fy + 116 - s, "SENAL")
    text(ix + 38, fy + 116 + s + 14, TS, "HUMEDAD / PUNTO DE", "TEXTOS", "center")
    text(ix + 38, fy + 116 + s + 27, TS, "ROCIO (PROPUESTA)", "TEXTOS", "center")

AIR_Y = CY_R + TH_R / 2.0
# ventilador 1 (arriba-izquierda): ducto por arriba, baja por fuera del cabezal y entra a la llanta 1 por la izquierda
ventilador(330, 270, dict(me="ME-V1", vfd="VFD-V1*", st="04", mt="01*"))
DX1 = 592
svc([(330, 244), (330, 88), (DX1, 88), (DX1, AIR_Y), (P1 - RO - 2, AIR_Y)], "AIRE_QUENCH", WAQ, at=[54, 356, 520, 940, 1090])
flecha(P1 - RO, AIR_Y, "E", 15, 12, "AIRE_QUENCH")
r = bubble(430, 136, 22, "TEB", "09")
line(430, 88, 430, 136 - r, "INSTRUMENTOS")
s = plc(370, 136, 16, "TI", "09", th=7)
line(430 - r, 136, 370 + s, 136, "SENAL")
text(460, 80, TS, "DUCTO 6 PULG. - AIRE HILADOR 1", "TEXTOS", "center")
# ventilador 2 (arriba-derecha): ducto por arriba, baja entre el cabezal y el tubo de fundido (con saltos)
ventilador(1900, 210, dict(me="ME-V2", vfd="VFD-V2*", st="05", mt="02*"))
DX2 = 1620
svc([(1900, 184), (1900, 48), (DX2, 48), (DX2, 412)], "AIRE_QUENCH", WAQ, at=[64, 206, 688])
vhop(DX2, 420, "AIRE_QUENCH", 8, WAQ)
poly([(DX2, 428), (DX2, 472)], "AIRE_QUENCH", WAQ)
vhop(DX2, 480, "AIRE_QUENCH", 8, WAQ)
poly([(DX2, 488), (DX2, 512)], "AIRE_QUENCH", WAQ)
vhop(DX2, 520, "AIRE_QUENCH", 8, WAQ)
svc([(DX2, 528), (DX2, AIR_Y), (P2 + RO + 2, AIR_Y)], "AIRE_QUENCH", WAQ, at=[72, 224])
flecha(P2 + RO, AIR_Y, "W", 15, 12, "AIRE_QUENCH")
r = bubble(1760, 92, 22, "TEB", "10")
line(1760, 48, 1760, 92 - r, "INSTRUMENTOS")
s = plc(1760, 152, 16, "TI", "10", th=7)
line(1760, 92 + r, 1760, 152 - s, "SENAL")
text(1700, 40, TS, "DUCTO 6 PULG. - AIRE HILADOR 2", "TEXTOS", "center")

# ================= EXTRACTOR DE HUMOS (campanas entre las llantas, extractor al centro) =================
HC = 1100
hx1 = P1 + RO + 8
hx2 = P2 - RO - 8
poly([(hx1, 636), (hx1 + 30, 655), (hx1 + 30, 681), (hx1, 700)], "EQUIPOS", closed=True)
poly([(hx2, 636), (hx2 - 30, 655), (hx2 - 30, 681), (hx2, 700)], "EQUIPOS", closed=True)
text(HC, 640, TS, "CAMPANAS DE HUMOS", "TEXTOS", "center")
svc([(hx1 + 30, 668), (hx2 - 30, 668)], "HUMOS", WHU, at=[38, 122])
svc([(HC, 668), (HC, 750)], "HUMOS", WHU, at=[44])
flecha(HC, 752, "S", 12, 10, "HUMOS")
fan(HC, 778, 24)
motor(HC + 60, 778, 14, "ME-EX", "N")
mec((HC + 24, 778), (HC + 46, 778))
poly([(HC - 24, 778), (HC - 54, 778), (HC - 54, 742)], "HUMOS", WHU)
flecha(HC - 54, 730, "N", 13, 10, "HUMOS")
text(HC - 54, 722, TS, "A ATMOSFERA", "TEXTOS", "center")
text(HC - 30, 816, TS, "EXTRACTOR", "TEXTOS", "right")
text(HC - 30, 829, TS, "DE HUMOS", "TEXTOS", "right")
contactor(HC + 60, 816)
line(HC + 60, 792, HC + 60, 807, "POTENCIA")
s = plc(HC + 60, 852, 18, "NC", "06")
line(HC + 60, 825, HC + 60, 852 - s, "SENAL")
text(HC + 60, 889, TS, "XSR/XSF-06 (DI)", "TEXTOS", "center")

# ================= RODILLOS (piso 1): pulling y finish rolls =================
def rodillos(px, n, tags):
    G = (px, G_Y)
    pts = [G, (px + 40, G_Y + 95), (px - 30, G_Y + 180), (px + 45, G_Y + 265), (px - 40, G_Y + 345), (px - 260, G_Y + 440)]
    radii = [38, 38, 22, 44]
    path, centers = fillet_path(pts, radii)
    draw_r = [33.5, 33.5, 17.5, 39.5]
    for (C, rr) in zip(centers, draw_r):
        circle(C[0], C[1], rr, "EQUIPOS")
        circle(C[0], C[1], 4, "EQUIPOS")
    cA, cB, cL, cP = centers
    # bandejas de ensimaje bajo cada finish roll, del lado opuesto al hilo
    tyA = cA[1] + 42
    rect(cA[0] - 52, tyA, cA[0] + 18, tyA + 10, "EQUIPOS")
    poly([(cA[0] - 48, tyA + 5), (cA[0] + 14, tyA + 5)], "ENSIMAJE", 1.2)
    ty = cB[1] + 42
    rect(cB[0] - 18, ty, cB[0] + 52, ty + 10, "EQUIPOS")
    poly([(cB[0] - 14, ty + 5), (cB[0] + 48, ty + 5)], "ENSIMAJE", 1.2)
    r = bubble(cB[0] + 86, ty + 5, 20, "ZSB", tags["zsb"])
    line(cB[0] + 52, ty + 5, cB[0] + 86 - r, ty + 5, "INSTRUMENTOS")
    line(cB[0] + 86 + r, ty + 5, cB[0] + 86 + r + 12, ty + 5, "SENAL")
    text(cB[0] + 86 + r + 16, ty + 2, TS, "DI -> PLC: BANDEJA", "TEXTOS")
    text(cB[0] + 86 + r + 16, ty + 15, TS, "SUBE / BAJA", "TEXTOS")
    # motores (enlace mecanico con salto sobre el hilo) + accionamientos a la derecha
    mx = px + 130
    for (C, rr, tagm, vf, std, ncd, cm) in ((cA, 38, "ME-F%d" % n, tags["vfdf"], tags["stdf"], tags["ncdf"], tags["comf"]),
                                            (cP, 44, "ME-P%d" % n, tags["vfdp"], tags["stdp"], tags["ncdp"], tags["comp"])):
        motor(mx, C[1], 18, tagm, "N")
        L = (mx - 18) - (C[0] + 4)
        mec((C[0] + 4, C[1]), (mx - 18, C[1]), mark=(rr + 8 + L) / 2, hops=[rr])
        vfd(mx + 95, C[1], 78, 30, vf, "RETROFIT*")
        line(mx + 18, C[1], mx + 56, C[1], "POTENCIA")
        text(mx + 95, C[1] - 24, TS, "STD-%s (REF) / %s" % (std, ncd), "TEXTOS", "center")
        com((mx + 95, C[1] + 15), (mx + 95, C[1] + 38), 40)
        text(mx + 95, C[1] + 50, TS, "BUS: " + cm[0], "TEXTOS", "center")
        text(mx + 95, C[1] + 63, TS, cm[1], "TEXTOS", "center")
    if n == 1:
        text(cA[0] - 44, cA[1] + 3, TS, "FINISH ROLL A", "TEXTOS", "right")
        text(cB[0] - 44, cB[1] + 3, TS, "FINISH ROLL B", "TEXTOS", "right")
        text(cL[0] - 26, cL[1] + 3, TS, "RODILLO LIBRE", "TEXTOS", "right")
        text(cP[0] - 50, cP[1] + 3, TS, "PULLING ROLL", "TEXTOS", "right")
    return path, (cB[0] + 52, ty), px + 19, cA

path1, tray1, hx_1, cA1 = rodillos(P1, 1, dict(zsb="14", vfdf="VFD-F1*", stdf="04", ncdf="NCD-07", comf=("IN-06, SNM-06", "XSR-07, XSF-07"),
                                              vfdp="VFD-P1*", stdp="09", ncdp="NCD-09", comp=("IN-02, SNM-08", "XSR-09, XSF-09")))
path2, tray2, hx_2, cA2 = rodillos(P2, 2, dict(zsb="15", vfdf="VFD-F2*", stdf="05", ncdf="NCD-08", comf=("IN-07, SNM-07", "XSR-08, XSF-08"),
                                              vfdp="VFD-P2*", stdp="10", ncdp="NCD-10", comp=("IN-08, SNM-09", "XSR-10, XSF-10")))

# mazo: los dos hilos salen a la IZQUIERDA y se unen en una guia de convergencia
gx, gy = path1[-1]
def recorta_final(path, d):
    (ax, ay), (bx, by) = path[-2], path[-1]
    L = math.hypot(bx - ax, by - ay)
    return path[:-1] + [(bx - (bx - ax) * d / L, by - (by - ay) * d / L)]
cinta(recorta_final(path1, 9.5))
cinta(path2 + [(gx + 9.5, gy)])
circle(gx, gy, 9, "EQUIPOS")
cinta([(gx - 9.5, gy), (150, gy)], half=5.0, width=1.4)
flecha(124, gy, "W", 26, 22, "PRODUCTO")
text(60, gy - 20, TL, "MAZO DE FILAMENTOS (TOW)", "TEXTOS")
text(60, gy + 26, TM, "A GODET 1 (ESTIRAJE)", "TEXTOS")

# ================= ENSIMAJE: aceite lubricante de fibra (piso 1, izquierda) =================
EN_Y = G_Y + 45
rect(300, 1105, 400, 1185, "EQUIPOS")
text(350, 1135, TS, "ACEITE", "TEXTOS", "center"); text(350, 1148, TS, "LUBRICANTE", "TEXTOS", "center"); text(350, 1161, TS, "DE FIBRA", "TEXTOS", "center")
cpump(440, 1210, 14)
poly([(400, 1172), (414, 1172), (414, 1210), (426, 1210)], "ENSIMAJE", WEN)
flecha(426, 1210, "E", 9, 7, "ENSIMAJE")
mec((454, 1210), (478, 1210))
motor(492, 1210, 14, "ME-AL", "S")
contactor(545, 1210, 28, 16)
line(506, 1210, 531, 1210, "POTENCIA")
s = plc(545, 1262, 18, "NCD", "04")
line(545, 1218, 545, 1262 - s, "SENAL")
d1x, d2x = tray1[0] - 8, tray2[0] - 8
svc([(440, 1189), (440, EN_Y), (hx_1 - 9, EN_Y)], "ENSIMAJE", WEN, at=[89, 544])
hop(hx_1, EN_Y, "ENSIMAJE", 9, WEN)
svc([(hx_1 + 9, EN_Y), (hx_2 - 9, EN_Y)], "ENSIMAJE", WEN, at=[202])
hop(hx_2, EN_Y, "ENSIMAJE", 9, WEN)
poly([(hx_2 + 9, EN_Y), (d2x, EN_Y)], "ENSIMAJE", WEN)
for (dx, tr, cA) in ((d1x, tray1, cA1), (d2x, tray2, cA2)):
    poly([(dx, EN_Y), (dx, cA[1] - 8)], "ENSIMAJE", WEN)
    vhop(dx, cA[1], "ENSIMAJE", 8, WEN)
    poly([(dx, cA[1] + 8), (dx, tr[1] - 1)], "ENSIMAJE", WEN)
    flecha(dx, tr[1] - 1, "S", 10, 8, "ENSIMAJE")
text(452, EN_Y - 8, TS, "ACEITE LUBRICANTE (ENSIMAJE) A LAS BANDEJAS", "TEXTOS")

# ================= DETALLE A: LLANTA AMPLIADA (espacio libre de la izquierda) =================
DXA1, DYA1, DXA2, DYA2 = 40, 462, 568, 868
rect(DXA1, DYA1, DXA2, DYA2, "DETALLE")
text(DXA1 + 12, DYA1 + 20, TM, "DETALLE A - LLANTA (HILERA ANULAR)", "TEXTOS")
text(DXA1 + 12, DYA1 + 34, TS, "VISTA A 30%%d - SIN ESCALA", "TEXTOS")
dcx, dcy, dRo, dRi, dt = 300, 640, 160, 102, 34
dG = (dcx, 838)
for dx in (-82, 82):
    yfar = dcy - K3D * math.sqrt(((dRo + dRi) / 2) ** 2 - dx * dx) + 2
    poly([(dcx + dx, 528), (dcx + dx, yfar - 2)], "FUNDIDO", WF)
    flecha(dcx + dx, yfar, "S", 12, 11, "FUNDIDO")
text(dcx, 522, TS, "FUNDIDO DESDE EL PAQUETE", "TEXTOS", "center")
llanta3d(dcx, dcy, dRo, dRi, dt, dG, rows=[112, 124, 136, 148], hole_r=1.9, nfront=15, nback=8, lay="DETALLE")
aire_interno(dcx, dcy, dRi, n=4, l1=6, l2=40)
svc([(56, dcy + dt / 2), (dcx - dRo - 2, dcy + dt / 2)], "AIRE_QUENCH", WAQ, at=[44])
flecha(dcx - dRo, dcy + dt / 2, "E", 13, 11, "AIRE_QUENCH")
text(56, dcy + dt / 2 - 8, TS, "AIRE", "TEXTOS")
text(56, dcy + dt / 2 + 18, TS, "QUENCH", "TEXTOS")
# leyendas con lineas guia
def guia(p_txt, p_obj, lines_, align="left"):
    line(p_txt[0], p_txt[1], p_obj[0], p_obj[1], "DETALLE")
    dot(p_obj[0], p_obj[1], 2.4, "DETALLE")
    for i, s in enumerate(lines_):
        text(p_txt[0] + (4 if align == "left" else -4), p_txt[1] + 4 + i * 13, TS, s, "TEXTOS", align)
a = math.radians(-35)
guia((478, 572), (dcx + 148 * math.cos(a), dcy + 148 * K3D * math.sin(a)), ["ORIFICIOS", "(~65.000)"])
a = math.radians(205)
guia((134, 560), (dcx + 124 * math.cos(a), dcy + 124 * K3D * math.sin(a)), ["CARA DE LA", "HILERA"], "right")
a = math.radians(55)
guia((478, 716), (dcx + dRo * math.cos(a), dcy + dt * 0.5 + dRo * K3D * math.sin(a)), ["ANILLO DE", "AIRE"])
guia((478, 784), (dcx + 52, 790), ["CORTINA DE", "FILAMENTOS"])
text(dcx + 16, dG[1] + 4, TS, "GUIA -> RODILLOS", "TEXTOS")
text(dcx, dcy + 4, TS - 0.6, "AIRE AL CENTRO", "TEXTOS", "center")

# ================= ESCRITURA DXF =================
def w(f, code, value):
    f.write("%s\r\n%s\r\n" % (code, value))

def fmt(v):
    return ("%.4f" % v) if isinstance(v, float) else str(v)

out = sys.argv[1] if len(sys.argv) > 1 else "pid_spinning_line_rev4.dxf"
f = io.open(out, "w", encoding="cp1252", newline="")
w(f, 0, "SECTION"); w(f, 2, "HEADER")
w(f, 9, "$ACADVER"); w(f, 1, "AC1009")
w(f, 9, "$INSBASE"); w(f, 10, "0.0"); w(f, 20, "0.0"); w(f, 30, "0.0")
w(f, 9, "$EXTMIN"); w(f, 10, "0.0"); w(f, 20, "0.0"); w(f, 30, "0.0")
w(f, 9, "$EXTMAX"); w(f, 10, fmt(W)); w(f, 20, fmt(H)); w(f, 30, "0.0")
w(f, 9, "$LIMMIN"); w(f, 10, "0.0"); w(f, 20, "0.0")
w(f, 9, "$LIMMAX"); w(f, 10, fmt(W)); w(f, 20, fmt(H))
w(f, 9, "$LTSCALE"); w(f, 40, "1.0")
w(f, 9, "$PLINEGEN"); w(f, 70, 1)
w(f, 0, "ENDSEC")
w(f, 0, "SECTION"); w(f, 2, "TABLES")
w(f, 0, "TABLE"); w(f, 2, "VPORT"); w(f, 70, 1)
w(f, 0, "VPORT"); w(f, 2, "*ACTIVE"); w(f, 70, 0)
w(f, 10, "0.0"); w(f, 20, "0.0"); w(f, 11, "1.0"); w(f, 21, "1.0")
w(f, 12, fmt(W / 2)); w(f, 22, fmt(H / 2))
w(f, 13, "0.0"); w(f, 23, "0.0"); w(f, 14, "10.0"); w(f, 24, "10.0"); w(f, 15, "10.0"); w(f, 25, "10.0")
w(f, 16, "0.0"); w(f, 26, "0.0"); w(f, 36, "1.0"); w(f, 17, "0.0"); w(f, 27, "0.0"); w(f, 37, "0.0")
w(f, 40, fmt(H * 1.08)); w(f, 41, fmt(W / H)); w(f, 42, "50.0"); w(f, 43, "0.0"); w(f, 44, "0.0"); w(f, 50, "0.0"); w(f, 51, "0.0")
w(f, 71, 0); w(f, 72, 100); w(f, 73, 1); w(f, 74, 1); w(f, 75, 0); w(f, 76, 0); w(f, 77, 0); w(f, 78, 0)
w(f, 0, "ENDTAB")
w(f, 0, "TABLE"); w(f, 2, "LTYPE"); w(f, 70, len(LTYPES))
for (nm, desc, pat) in LTYPES:
    w(f, 0, "LTYPE"); w(f, 2, nm); w(f, 70, 64); w(f, 3, desc); w(f, 72, 65); w(f, 73, len(pat))
    w(f, 40, fmt(float(sum(abs(p) for p in pat))))
    for p in pat:
        w(f, 49, fmt(float(p)))
w(f, 0, "ENDTAB")
w(f, 0, "TABLE"); w(f, 2, "LAYER"); w(f, 70, len(LAYERS) + 1)
w(f, 0, "LAYER"); w(f, 2, "0"); w(f, 70, 64); w(f, 62, 7); w(f, 6, "CONTINUOUS")
for (nm, col, lt) in LAYERS:
    w(f, 0, "LAYER"); w(f, 2, nm); w(f, 70, 64); w(f, 62, col); w(f, 6, lt)
w(f, 0, "ENDTAB")
w(f, 0, "TABLE"); w(f, 2, "STYLE"); w(f, 70, 1)
w(f, 0, "STYLE"); w(f, 2, "STANDARD"); w(f, 70, 0); w(f, 40, "0.0"); w(f, 41, "1.0"); w(f, 50, "0.0"); w(f, 71, 0); w(f, 42, "2.5"); w(f, 3, "romans"); w(f, 4, "")
w(f, 0, "ENDTAB")
w(f, 0, "ENDSEC")
w(f, 0, "SECTION"); w(f, 2, "ENTITIES")
for e in ents:
    w(f, 0, e[0])
    for (code, val) in e[1:]:
        w(f, code, fmt(val))
w(f, 0, "ENDSEC")
w(f, 0, "EOF")
f.close()
print("OK: %s (%d entidades) | notas hasta y=%.0f (limite %.0f)" % (out, len(ents), NOTAS_FIN, BYB))
