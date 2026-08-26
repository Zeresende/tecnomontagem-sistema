# -*- coding: utf-8 -*-
"""Fecha as 2 perguntas da Ka: o bucket PEX e os DN 40/50 da HM89 TIPA."""
import sys, math, re, logging
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
logging.disable(logging.CRITICAL)
import ezdxf

doc = ezdxf.readfile(sys.argv[1])
msp = doc.modelspace()
lp = lambda n: re.split(r"\$0\$|\|", n)[-1]

def comp(e):
    t = e.dxftype()
    try:
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            return math.dist((a.x, a.y), (b.x, b.y))
        if t == "LWPOLYLINE":
            # sem o segmento de fechamento — ver nota no 54
            p = [(x[0], x[1]) for x in e.get_points()]
            return sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1))
        if t == "POLYLINE":
            p = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            return sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1))
        if t == "ARC":
            # arco do DXF e sempre CCW; abs(a1-a0) pega o complemento quando cruza o zero
            return math.radians((e.dxf.end_angle - e.dxf.start_angle) % 360.0) * e.dxf.radius
    except Exception:
        return 0.0
    return 0.0

comp_por = defaultdict(float)
txt_por = defaultdict(list)

def varre(cont, prof=0):
    for e in cont:
        if e.dxftype() == "INSERT" and prof < 6:
            try:
                varre(e.virtual_entities(), prof + 1)
            except Exception:
                pass
            continue
        lay = lp(e.dxf.layer)
        if e.dxftype() in ("TEXT", "MTEXT"):
            t = str(e.dxf.text if e.dxftype() == "TEXT" else e.text).strip()
            if t:
                txt_por[lay].append(t)
        else:
            c = comp(e)
            if c > 0:
                comp_por[lay] += c

varre(msp)

print("=" * 88)
print("1. AGUA — comprimento por camada, agrupado pelo PREFIXO (o campo que classifica)")
print("=" * 88)
grupos = defaultdict(list)
for lay, m in comp_por.items():
    p = re.split(r"[-_]", lay)[0].upper()
    if p in ("HAF", "HAQ", "HAP", "HDR", "HES", "HGC", "HIN"):
        grupos[p].append((lay, m))
nomes = {"HAF": "agua fria", "HAQ": "AGUA QUENTE", "HAP": "agua ? (HAP)",
         "HDR": "dreno", "HES": "esgoto", "HGC": "gas", "HIN": "incendio"}
for p in ["HAF", "HAQ", "HAP", "HDR", "HES", "HGC", "HIN"]:
    if p not in grupos:
        continue
    tot = sum(m for _, m in grupos[p])
    print(f"\n  {p} = {nomes[p]}   TOTAL {tot:.1f} m")
    for lay, m in sorted(grupos[p], key=lambda x: -x[1]):
        marca = "  <<< bucket 'PEX'" if lay.upper().endswith("PEX") else ""
        print(f"      {lay:34} {m:9.1f} m{marca}")

print()
print("=" * 88)
print("2. ROTULOS DE DN no padrao SPHE (<DN>-PEX etc.) — em que camada moram")
print("=" * 88)
rot = re.compile(r"\b(\d{2,3})\s*[-–]\s*(PEX|PPR|CPVC|PVC)\b", re.I)
inv = defaultdict(lambda: defaultdict(int))
for lay, ts in txt_por.items():
    for t in ts:
        for m in rot.finditer(t):
            inv[m.group(1)][lay] += 1
if not inv:
    print("  (nenhum rotulo <DN>-MATERIAL encontrado)")
for dn in sorted(inv, key=lambda x: int(x)):
    tot = sum(inv[dn].values())
    top = sorted(inv[dn].items(), key=lambda x: -x[1])[:3]
    print(f"  {dn:>3}: {tot:4d}   {['%s(%d)' % (k[:30], v) for k, v in top]}")

print()
print("=" * 88)
print("3. ONDE APARECEM 40 e 50 — texto bruto por camada")
print("=" * 88)
vis = set()
for lay, ts in txt_por.items():
    for t in ts:
        if re.search(r"\b(40|50)\b", t) and len(t) < 90:
            vis.add((lay, t.replace("\n", " ")[:74]))
for lay, t in sorted(vis)[:26]:
    print(f"  [{lay[:30]:30}] {t}")

print()
print("=" * 88)
print("4. ARMADILHA DE NOME — camadas com '___' colado por underscore em vez de traco")
print("=" * 88)
for lay in sorted(set(list(comp_por) + list(txt_por))):
    if re.match(r"^H[A-Z]{2}[-_]TUB", lay, re.I) and "-TUB-" not in lay.upper():
        print(f"  {lay:34} {comp_por.get(lay, 0):9.1f} m")
