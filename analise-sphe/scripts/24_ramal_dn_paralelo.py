# -*- coding: utf-8 -*-
"""EXTRATOR DE RAMAL POR DN v2 — casamento por PARALELISMO, em nivel de segmento.

Por que mudou (registrar para nao regredir):
  - v1 (script 22) casava por distancia. Travou em 69% de cobertura na Living e,
    ao afrouxar o raio, a precisao contra o gabarito PIOROU (23,6 -> 26,1 p.p.).
    Conclusao: distancia nao e o mecanismo.
  - O probe 23 mostrou que NAO existe LEADER no desenho (chamada nao e entidade),
    mas que os rotulos TEM angulo e ele discrimina: 166 a 90 graus, 54 a 0.
  - Hipotese adotada: a SPHE escreve o rotulo ALINHADO ao tubo que ele descreve.
    Entao o tubo certo nao e o mais proximo — e o mais proximo ENTRE OS PARALELOS
    a direcao do texto. Isso explica o erro do v1: ele pegava tubo vizinho
    perpendicular, que costuma estar mais perto.

Trabalha por SEGMENTO, nao por entidade: uma polyline de ramal muda de direcao
varias vezes e pode legitimamente ter DN diferente em trechos diferentes.

Uso: python 24_ramal_dn_paralelo.py <arquivo.dxf> [--tol 25] [--raio 30]
"""
import sys, re, math, logging
from collections import defaultdict
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")

RX_DN = re.compile(r"\b(16|20|25|32)\s*-\s*PEX\b", re.I)
TUBO_LAYER = re.compile(r"H(AF|AQ)-TUB", re.I)
EXCL_LAYER = re.compile(r"LEG|REF|TAB|DET|PREVIS", re.I)
RX_PRU = re.compile(r"PRU", re.I)
MAX_DEPTH = 6


def coletar(entidades, segs, rotulos, depth=0):
    """segs: (tipo AF/AQ, layer, a, b, comprimento, angulo). rotulos: dn/xy/ang/layer."""
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
            rotulos.append({"dn": int(m.group(1)), "xy": xy, "ang": ang, "layer": ly})
            continue

        if t not in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            continue
        m = TUBO_LAYER.search(ly)
        if not m or EXCL_LAYER.search(ly) or RX_PRU.search(ly):
            continue          # prumada sai daqui: e outra conta (item 2.1)
        pts = m22.pontos_de(e)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            d = math.dist(a, b)
            if d <= 0:
                continue
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
            segs.append((m.group(1).upper(), ly, a, b, d, ang))


def dif_ang(a, b):
    """Diferenca angular tratando 0 e 180 como a mesma direcao."""
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def classificar(segs, rotulos, tol, raio, exigir_paralelo=True):
    res = defaultdict(float)
    classificado = naoclass = 0.0
    for tipo, ly, a, b, d, ang in segs:
        melhor, dmin = None, float("inf")
        for r in rotulos:
            if exigir_paralelo and dif_ang(ang, r["ang"]) > tol:
                continue
            dist = m22.dist_ponto_seg(r["xy"], a, b)
            if dist < dmin:
                melhor, dmin = r, dist
        if melhor and dmin <= raio:
            res[(tipo, melhor["dn"])] += d
            classificado += d
        else:
            naoclass += d
    return res, classificado, naoclass


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tol = 25.0
    raio = 30.0
    for i, a in enumerate(sys.argv):
        if a == "--tol":
            tol = float(sys.argv[i + 1])
        if a == "--raio":
            raio = float(sys.argv[i + 1])

    path = args[0]
    doc = ezdxf.readfile(path)
    segs, rotulos = [], []
    coletar(doc.modelspace(), segs, rotulos)
    total = sum(s[4] for s in segs)

    print(f"ARQUIVO: {path}")
    print(f"segmentos de ramal: {len(segs)} | rotulos: {len(rotulos)} | total {total:.1f} m")
    print(f"tolerancia angular: {tol:g} graus | raio maximo: {raio:g}\n")

    for nome, exigir in (("PARALELO (v2)", True), ("distancia pura (v1)", False)):
        res, cl, nc = classificar(segs, rotulos, tol, raio, exigir)
        print(f"-- {nome} --")
        soma = sum(res.values())
        for (tipo, dn) in sorted(res, key=lambda k: (k[0], k[1])):
            print(f"     {tipo} DN{dn:<3} {res[(tipo, dn)]:9.1f} m")
        print(f"     classificado {cl:9.1f} m ({100*cl/total:.1f}%) | sem casar {nc:9.1f} m")
        porc = defaultdict(float)
        for (tipo, dn), v in res.items():
            porc[dn] += v
        if soma:
            print("     mix por DN: " + "  ".join(
                f"DN{dn}={100*porc[dn]/soma:.1f}%" for dn in sorted(porc)))
        print()


if __name__ == "__main__":
    main()
