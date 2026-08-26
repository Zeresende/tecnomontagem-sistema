# -*- coding: utf-8 -*-
"""PROBE 3 — por que a geometria do tubo esta em 11.710 pedacos de 23 mm.

Hipoteses a distinguir:
  H1 linetype tracejado explodido (cada traco vira uma LINE curta e colinear);
  H2 geometria cortada em cada cruzamento (trim);
  H3 estamos explodindo blocos que ja continham a polilinha inteira.

Se for H1 (ou H2), os fragmentos sao COLINEARES e consecutivos — da para
remontar o traco antes de montar o grafo. O teste abaixo mede exatamente isso:
quanto da metragem vive em fragmentos curtos, e quanto desses fragmentos tem um
vizinho colinear na mesma direcao.

Uso: python 28_probe_fragmentacao.py <obra>
"""
import sys, re, math, logging
from collections import Counter, defaultdict
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")

TUBO_LAYER = re.compile(r"H(AF|AQ)-TUB", re.I)
EXCL_LAYER = re.compile(r"LEG|REF|TAB|DET|PREVIS", re.I)
MAX_DEPTH = 6


def coletar(entidades, achados, depth=0, dentro=""):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT":
            nome = ""
            try:
                nome = str(e.dxf.name)
            except Exception:
                pass
            if depth < MAX_DEPTH:
                try:
                    coletar(e.virtual_entities(), achados, depth + 1, dentro or nome)
                except Exception:
                    pass
            continue
        ly = e.dxf.layer or ""
        if t not in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            continue
        if not TUBO_LAYER.search(ly) or EXCL_LAYER.search(ly):
            continue
        pts = m22.pontos_de(e)
        if len(pts) < 2:
            continue
        lt = ""
        try:
            lt = str(e.dxf.linetype)
        except Exception:
            pass
        achados.append({"t": t, "pts": pts, "m": m22.compr(pts), "lt": lt,
                        "nv": len(pts), "depth": depth, "dentro": dentro})


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    print(f"OBRA {obra} | {tipos[0].name}\n")
    doc = ezdxf.readfile(str(tipos[0]))
    ach = []
    coletar(doc.modelspace(), ach)
    total = sum(a["m"] for a in ach)
    print(f"entidades de tubo: {len(ach)}   metragem {total:.1f}\n")

    print("--- tipo de entidade ---")
    c = Counter(a["t"] for a in ach)
    mm = defaultdict(float)
    for a in ach:
        mm[a["t"]] += a["m"]
    for k, n in c.most_common():
        print(f"  {k:14} {n:>7}  {mm[k]:>9.1f} m")

    print("\n--- linetype ---")
    c = Counter(a["lt"] for a in ach)
    for k, n in c.most_common(10):
        print(f"  {str(k):20} {n:>7}")

    print("\n--- profundidade de bloco em que a geometria foi achada ---")
    c = Counter(a["depth"] for a in ach)
    for k in sorted(c):
        print(f"  depth {k}: {c[k]:>7}")

    print("\n--- distribuicao de comprimento ---")
    faixas = [(0, 0.01), (0.01, 0.05), (0.05, 0.2), (0.2, 1.0), (1.0, 1e9)]
    for lo, hi in faixas:
        sel = [a for a in ach if lo <= a["m"] < hi]
        s = sum(a["m"] for a in sel)
        print(f"  [{lo:>5} , {hi if hi < 1e9 else 'inf':>5}) : {len(sel):>7} pecas  "
              f"{s:>9.1f} m  ({100*s/total:>5.1f}% da metragem)")

    print("\n--- COLINEARIDADE: fragmento tem vizinho colinear? ---")
    tol = 0.02
    curtos = [a for a in ach if a["m"] < 0.2 and a["nv"] == 2]
    cel = defaultdict(list)
    for i, a in enumerate(curtos):
        for p in (a["pts"][0], a["pts"][-1]):
            cel[(int(p[0] / 0.5), int(p[1] / 0.5))].append(i)
    com_vz, sem_vz = 0, 0
    for i, a in enumerate(curtos):
        (ax, ay), (bx, by) = a["pts"][0], a["pts"][-1]
        ang_a = math.degrees(math.atan2(by - ay, bx - ax)) % 180.0
        achou = False
        cand = set()
        for p in (a["pts"][0], a["pts"][-1]):
            cx, cy = int(p[0] / 0.5), int(p[1] / 0.5)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    cand.update(cel.get((cx + dx, cy + dy), ()))
        for j in cand:
            if j == i:
                continue
            b = curtos[j]
            (cx0, cy0), (dx0, dy0) = b["pts"][0], b["pts"][-1]
            ang_b = math.degrees(math.atan2(dy0 - cy0, dx0 - cx0)) % 180.0
            dif = abs(ang_a - ang_b)
            dif = min(dif, 180 - dif)
            if dif > 3:
                continue
            # ponta encosta na reta suporte do outro e a distancia e pequena
            if min(math.dist(a["pts"][k], b["pts"][l])
                   for k in (0, -1) for l in (0, -1)) <= tol * 6:
                achou = True
                break
        if achou:
            com_vz += 1
        else:
            sem_vz += 1
    print(f"  fragmentos curtos (<0,2 m, 2 vertices): {len(curtos)}")
    print(f"    com vizinho colinear:  {com_vz:>7}  ({100*com_vz/max(1,len(curtos)):.1f}%)")
    print(f"    sem vizinho colinear:  {sem_vz:>7}")

    print("\n--- amostra de 8 fragmentos curtos ---")
    for a in curtos[:8]:
        (x0, y0), (x1, y1) = a["pts"][0], a["pts"][-1]
        print(f"  m={a['m']:.4f} lt={a['lt']:<12} ({x0:.3f},{y0:.3f})->({x1:.3f},{y1:.3f}) dentro={a['dentro'][:40]}")


if __name__ == "__main__":
    main()
