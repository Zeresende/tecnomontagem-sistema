# -*- coding: utf-8 -*-
"""Diagnostica COMO a SPHE codifica o DN do PEX no DXF.
Hipoteses: (a) cor (ACI) por DN; (b) lineweight por DN; (c) nome de bloco PRUM-PX-<DN>.
Le 1x as camadas *-TUB-*/PRU e agrega comprimento por (layer, cor, lineweight).
Tambem conta blocos com DN no nome e amostra textos %%C.
"""
import math, sys, re, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf
sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

DXF = Path(sys.argv[1])
TUB_RE = re.compile(r"TUB|PRU", re.I)
DNBLK_RE = re.compile(r"(PX|PB|PEX|SATT|PR|PRUM|INS|PV)[-_]?(\d{2,3})", re.I)
MAX_DEPTH = 6

def comp(e):
    t = e.dxftype()
    try:
        if t == "LINE": return e.dxf.start.distance(e.dxf.end)
        if t == "LWPOLYLINE":
            p = list(e.get_points("xy"))
            d = sum(math.dist(p[i], p[i+1]) for i in range(len(p)-1))
            return d + (math.dist(p[-1], p[0]) if e.closed and len(p) > 2 else 0)
        if t == "POLYLINE":
            p = [v.dxf.location for v in e.vertices]
            return sum(p[i].distance(p[i+1]) for i in range(len(p)-1))
        if t == "ARC":
            return e.dxf.radius * math.radians((e.dxf.end_angle - e.dxf.start_angle) % 360)
    except Exception: pass
    return 0.0

por_cor = defaultdict(float)
por_lw = defaultdict(float)
por_layer_cor = defaultdict(float)
blocos_dn = Counter()
todos_blocos = Counter()
ccount = Counter()

def aci(e):
    try: return e.dxf.color
    except Exception: return "?"
def lw(e):
    try: return e.dxf.lineweight
    except Exception: return "?"

def varrer(ents, depth=0):
    for e in ents:
        t = e.dxftype()
        if t == "INSERT" and depth < MAX_DEPTH:
            nm = re.sub(r"-flat-\d+$", "", e.dxf.name)
            todos_blocos[nm] += 1
            m = DNBLK_RE.search(nm)
            if m: blocos_dn[f"{m.group(1).upper()}-{m.group(2)}"] += 1
            try: varrer(e.virtual_entities(), depth+1)
            except Exception: pass
        elif t in ("LINE","LWPOLYLINE","POLYLINE","ARC"):
            lay = e.dxf.layer or ""
            if not TUB_RE.search(lay): continue
            d = comp(e)
            if d <= 0: continue
            por_cor[aci(e)] += d
            por_lw[lw(e)] += d
            por_layer_cor[(lay, aci(e))] += d
        elif t in ("TEXT","MTEXT"):
            try: raw = e.dxf.text if t=="TEXT" else e.text
            except Exception: raw=""
            for m in re.finditer(r"%%[Cc]\s*(\d{1,3})", raw or ""):
                ccount[m.group(1)] += 1

doc = ezdxf.readfile(str(DXF))
varrer(doc.modelspace())

print("ARQUIVO", DXF.name)
print("\n=== comprimento de tubo por COR (ACI) ===")
for c, d in sorted(por_cor.items(), key=lambda kv:-kv[1])[:15]:
    print(f"   cor {str(c):>4} : {d:8.1f} m")
print("\n=== comprimento de tubo por LINEWEIGHT ===")
for c, d in sorted(por_lw.items(), key=lambda kv:-kv[1])[:15]:
    print(f"   lw {str(c):>5} : {d:8.1f} m")
print("\n=== blocos com DN no nome (PRUM/PX/INS/etc) ===")
for b, n in blocos_dn.most_common(20):
    print(f"   {b:14s} x{n}")
print("\n=== top layers x cor (m) ===")
for (lay,c), d in sorted(por_layer_cor.items(), key=lambda kv:-kv[1])[:20]:
    short = lay.split("$0$")[-1]
    print(f"   {short:28s} cor={str(c):>4} : {d:7.1f}")
print("\n=== textos %%C presentes (valor:contagem) ===")
print("  ", dict(ccount.most_common(15)))
