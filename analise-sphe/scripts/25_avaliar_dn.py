# -*- coding: utf-8 -*-
"""AVALIACAO SISTEMATICA do casamento rotulo->DN contra o gabarito da obra.

Em vez de escolher o metodo por intuicao, roda a grade de combinacoes e pontua
cada uma pelo erro absoluto somado do mix de DN contra a compra real do Hederson.

Confundidor corrigido aqui: a aba RAMAL da planilha EMBUTE a prumada (item 2.1
confirmado pelo Hederson). Medir o DXF sem a prumada e comparar com ela penaliza
o DN32 de graca. Por isso "com prumada" entra na grade.

Uso: python 25_avaliar_dn.py <obra>     ex.: python 25_avaliar_dn.py 20241385
"""
import sys, os, re, glob, math, logging
from collections import defaultdict
from pathlib import Path
import ezdxf, openpyxl

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")
m24 = __import__("24_ramal_dn_paralelo")

RX_DN = re.compile(r"\b(16|20|25|32)\s*-\s*PEX\b", re.I)
TUBO_LAYER = re.compile(r"H(AF|AQ)-TUB", re.I)
EXCL_LAYER = re.compile(r"LEG|REF|TAB|DET|PREVIS", re.I)
RX_PRU = re.compile(r"PRU", re.I)
MAX_DEPTH = 6
TAM_ROLO = re.compile(r"(\d+)\s*M\b")
RX_TUBO = re.compile(r"TUBO\s+(PEX|PERT)\s*(16|20|25|32)")


def coletar(entidades, segs, rotulos, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT" and depth < MAX_DEPTH:
            try:
                coletar(e.virtual_entities(), segs, rotulos, depth + 1)
            except Exception:
                pass
            continue
        ly = e.dxf.layer or ""
        if t in ("TEXT", "MTEXT"):
            m = RX_DN.search(m22.texto_de(e))
            if not m:
                continue
            try:
                ins = e.dxf.insert
                xy = (float(ins[0]), float(ins[1]))
            except Exception:
                continue
            try:
                ang = float(e.dxf.rotation) % 180.0
            except Exception:
                ang = 0.0
            rotulos.append({"dn": int(m.group(1)), "xy": xy, "ang": ang})
            continue
        if t not in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            continue
        m = TUBO_LAYER.search(ly)
        if not m or EXCL_LAYER.search(ly):
            continue
        pts = m22.pontos_de(e)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            d = math.dist(a, b)
            if d <= 0:
                continue
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
            segs.append((a, b, d, ang, bool(RX_PRU.search(ly))))


def gabarito(obra):
    """Mix de DN da compra real (aba RAMAL, coluna G), em metros liquidos."""
    x = [a for a in glob.glob(os.path.join(BASE, obra, "*.xlsx"))
         if "PRE-" not in a.upper() and "LEVANTAMENTO" not in a.upper()
         and not os.path.basename(a).startswith("~$")][0]
    wb = openpyxl.load_workbook(x, data_only=True)
    p17 = __import__("17_parser_contagens")
    tot = defaultdict(float)
    for ws in wb.worksheets:
        if not ws.title.upper().startswith("RAMAL"):
            continue
        cr = p17.linha_contagem(ws)
        for r in range(cr + 1, ws.max_row + 1):
            e, u, g = ws.cell(r, 5).value, ws.cell(r, 6).value, ws.cell(r, 7).value
            if not (isinstance(e, str) and e.upper().startswith("TUBO")):
                continue
            if str(u).strip().upper() != "RL" or not isinstance(g, (int, float)) or not g:
                continue
            m = RX_TUBO.search(e.upper())
            if not m:
                continue
            tams = [int(t) for t in TAM_ROLO.findall(e.upper()) if int(t) in (50, 100, 200)]
            tot[int(m.group(2))] += g * (tams[-1] if tams else 100) / 1.07
    wb.close()
    return tot


def mix(d):
    s = sum(d.values())
    return {k: 100 * v / s for k, v in d.items()} if s else {}


def erro(a, b):
    return sum(abs(a.get(dn, 0) - b.get(dn, 0)) for dn in (16, 20, 25, 32))


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    doc = ezdxf.readfile(str(tipos[0]))
    segs, rotulos = [], []
    coletar(doc.modelspace(), segs, rotulos)

    alvo = mix(gabarito(obra))
    print(f"OBRA {obra} | {tipos[0].name}")
    print(f"segmentos {len(segs)} | rotulos {len(rotulos)}")
    print("GABARITO (compra real): " + "  ".join(f"DN{k}={alvo[k]:.1f}%" for k in sorted(alvo)))
    print()
    print(f"{'metodo':22} {'prum':5} {'tol':>4} {'raio':>5} {'cobert':>7} {'erro p.p.':>10}   mix")
    print("-" * 104)

    melhor = None
    for com_prum in (True, False):
        usar = segs if com_prum else [s for s in segs if not s[4]]
        total = sum(s[2] for s in usar)
        for nome, exigir, tols in (("distancia", False, [None]), ("paralelo", True, [15, 25, 40])):
            for tol in tols:
                for raio in (8, 15, 30, 60):
                    res = defaultdict(float)
                    cl = 0.0
                    for a, b, dd, ang, _p in usar:
                        best, dmin = None, float("inf")
                        for r in rotulos:
                            if exigir and m24.dif_ang(ang, r["ang"]) > tol:
                                continue
                            dist = m22.dist_ponto_seg(r["xy"], a, b)
                            if dist < dmin:
                                best, dmin = r, dist
                        if best and dmin <= raio:
                            res[best["dn"]] += dd
                            cl += dd
                    m = mix(res)
                    er = erro(m, alvo)
                    cob = 100 * cl / total if total else 0
                    linha = (f"{nome:22} {'sim' if com_prum else 'nao':5} "
                             f"{(tol if tol else 0):>4} {raio:>5} {cob:>6.1f}% {er:>9.1f}   "
                             + " ".join(f"{m.get(dn,0):.0f}" for dn in (16, 20, 25, 32)))
                    print(linha)
                    if melhor is None or er < melhor[0]:
                        melhor = (er, nome, com_prum, tol, raio, cob, m)

    er, nome, cp, tol, raio, cob, m = melhor
    print("\n" + "=" * 60)
    print(f"MELHOR: {nome} | prumada={'sim' if cp else 'nao'} | tol={tol} | raio={raio}")
    print(f"  cobertura {cob:.1f}%  erro somado {er:.1f} p.p.")
    print("  mix   " + "  ".join(f"DN{dn}={m.get(dn,0):.1f}%" for dn in (16, 20, 25, 32)))
    print("  alvo  " + "  ".join(f"DN{dn}={alvo.get(dn,0):.1f}%" for dn in (16, 20, 25, 32)))


if __name__ == "__main__":
    main()
