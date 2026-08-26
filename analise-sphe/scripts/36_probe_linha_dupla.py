# -*- coding: utf-8 -*-
"""PROBE DA LINHA DUPLA — o DN do Brooklyn pode sair da geometria (10/08/2026).

O probe 35 mostrou que o Brooklyn e exportacao de Revit: camadas em ingles
(`Pipes`, `Pex - TIGRE`, `Pipe Fittings`, `Pipe Insulations`), e o padrao de
camada da SPHE aparece so como residuo de 10 m.

Hipotese a testar: exportacao de Revit em nivel de detalhe Fino desenha o tubo em
LINHA DUPLA na escala real. Se for o caso aqui, a distancia entre as duas linhas
paralelas E o diametro — e o DN sai da geometria, sem depender de rotulo nenhum.
Seria a rota mais confiavel das tres, porque nao herda o problema que derrubou as
outras duas (contagem de rotulo nao acompanha metragem).

O teste que prova ou derruba, em duas partes:
  1. o histograma dos espacamentos tem PICOS? Se o tubo for linha dupla, os
     espacamentos se concentram em poucos valores, nao se espalham.
  2. o pico casa com o ROTULO? Perto de uma tag "25 - PEX" o espacamento tem que
     ser maior que perto de uma "20 - PEX", na proporcao 25/20. Essa e a prova:
     duas fontes independentes no mesmo desenho dizendo a mesma coisa.

Uso: python 36_probe_linha_dupla.py [obra]
"""
import sys, re, math, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")

MAX_DEPTH = 6
RX_CAMADA = re.compile(r"\bPipes?\b|\bPex\b|Tubula|PE-?X|PE-?RT|HAF-TUB|HAQ-TUB", re.I)
RX_EXCLUI = re.compile(r"Tag|Insulation|Accessor|Esgoto|Ralo|Duct|Fitting", re.I)
RX_DN = m22.RX_DN
TOL_ANG = 1.5           # graus para considerar duas retas paralelas
MIN_SEG = 0.02          # ignora caco


def coletar(entidades, segs, tags, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT":
            if depth < MAX_DEPTH:
                try:
                    coletar(e.virtual_entities(), segs, tags, depth + 1)
                except Exception:
                    pass
            continue
        ly = (e.dxf.layer or "").split("$0$")[-1]
        if t in ("TEXT", "MTEXT"):
            m = RX_DN.search(" ".join(m22.texto_de(e).split()))
            if m:
                try:
                    ins = e.dxf.insert
                    tags.append({"dn": int(m.group(1)),
                                 "xy": (float(ins[0]), float(ins[1]))})
                except Exception:
                    pass
            continue
        if t not in ("LINE", "LWPOLYLINE", "POLYLINE"):
            continue
        if not RX_CAMADA.search(ly) or RX_EXCLUI.search(ly):
            continue
        pts = m22.pontos_de(e)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            d = math.dist(a, b)
            if d < MIN_SEG:
                continue
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
            segs.append({"a": a, "b": b, "m": d, "ang": ang, "layer": ly})


def dif_ang(x, y):
    d = abs(x - y) % 180.0
    return min(d, 180.0 - d)


def dist_perp(s, p):
    """Distancia do ponto p a reta suporte do segmento s."""
    (ax, ay), (bx, by) = s["a"], s["b"]
    dx, dy = bx - ax, by - ay
    n = math.hypot(dx, dy)
    if n == 0:
        return math.inf
    return abs(dy * (p[0] - ax) - dx * (p[1] - ay)) / n


def sobrepoe(s, t):
    """Projecoes de t nos extremos de s se cruzam? Evita casar tubos distantes."""
    (ax, ay), (bx, by) = s["a"], s["b"]
    dx, dy = bx - ax, by - ay
    n2 = dx * dx + dy * dy
    if n2 == 0:
        return False
    ts = []
    for p in (t["a"], t["b"]):
        ts.append(((p[0] - ax) * dx + (p[1] - ay) * dy) / n2)
    return max(ts) > 0.05 and min(ts) < 0.95


def parear(segs, raio):
    """Para cada segmento, o vizinho paralelo mais proximo. Devolve espacamentos."""
    cel = defaultdict(list)
    for i, s in enumerate(segs):
        mx = (s["a"][0] + s["b"][0]) / 2
        my = (s["a"][1] + s["b"][1]) / 2
        cel[(int(mx / raio), int(my / raio))].append(i)

    pares = []
    for i, s in enumerate(segs):
        mx = (s["a"][0] + s["b"][0]) / 2
        my = (s["a"][1] + s["b"][1]) / 2
        cx, cy = int(mx / raio), int(my / raio)
        melhor, dmin = None, math.inf
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                for j in cel.get((cx + ddx, cy + ddy), ()):
                    if j == i:
                        continue
                    t = segs[j]
                    if dif_ang(s["ang"], t["ang"]) > TOL_ANG:
                        continue
                    if not sobrepoe(s, t):
                        continue
                    d = dist_perp(s, ((t["a"][0] + t["b"][0]) / 2,
                                      (t["a"][1] + t["b"][1]) / 2))
                    if 1e-6 < d < dmin:
                        melhor, dmin = j, d
        if melhor is not None and dmin <= raio:
            pares.append({"i": i, "j": melhor, "d": dmin, "m": s["m"],
                          "xy": (mx, my), "layer": s["layer"]})
    return pares


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20251430"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    print(f"OBRA {obra} | {tipos[0].name}", flush=True)
    doc = ezdxf.readfile(str(tipos[0]))
    segs, tags = [], []
    coletar(doc.modelspace(), segs, tags)
    if not segs:
        print("nenhum segmento nas camadas de tubo")
        return

    xs = [q[0] for s in segs for q in (s["a"], s["b"])]
    ys = [q[1] for s in segs for q in (s["a"], s["b"])]
    comp = sorted(s["m"] for s in segs)
    print(f"segmentos de tubo {len(segs)} | tags <DN>-PEX {len(tags)}")
    print(f"extensao X {max(xs)-min(xs):.1f}  Y {max(ys)-min(ys):.1f}  "
          f"-> unidade provavel: {'metros' if max(xs)-min(xs) < 500 else 'cm ou mm'}")
    print(f"comprimento de segmento: mediana {comp[len(comp)//2]:.3f}  max {comp[-1]:.2f}")
    print("camadas:", ", ".join(f"{k}={v}" for k, v in
                                Counter(s["layer"] for s in segs).most_common(6)))

    # raio de busca generoso: 0,2 unidade cobre DN ate 200 mm se a unidade for metro
    raio = 0.2 if max(xs) - min(xs) < 500 else 20.0
    print(f"\n--- 1. HISTOGRAMA DE ESPACAMENTOS (raio {raio:g}) ---", flush=True)
    pares = parear(segs, raio)
    print(f"  segmentos com vizinho paralelo: {len(pares)} de {len(segs)} "
          f"({100*len(pares)/len(segs):.1f}%)")
    if not pares:
        print("  NENHUM par paralelo -> tubo desenhado em linha simples. Hipotese cai.")
        return

    passo = raio / 40.0
    hist = Counter(round(p["d"] / passo) * passo for p in pares)
    total_m = sum(p["m"] for p in pares)
    print(f"  {'espacamento':>12} {'pares':>7} {'metros':>10} {'%':>6}")
    mm = defaultdict(float)
    for p in pares:
        mm[round(p["d"] / passo) * passo] += p["m"]
    for val, n in sorted(hist.items(), key=lambda x: -x[1])[:14]:
        print(f"  {val:12.4f} {n:>7} {mm[val]:>10.1f} {100*mm[val]/total_m:>5.1f}%")

    print("\n--- 2. O ESPACAMENTO CASA COM O ROTULO? ---", flush=True)
    if not tags:
        print("  sem tags para cruzar")
        return
    # Um par POR TAG — o mais proximo dela. Buscar todos dentro de um raio largo
    # dilui o sinal: a mediana converge para a mediana global e todo DN parece igual.
    print(f"  {'DN da tag':>10} {'tags':>5} {'com par':>8} "
          f"{'espacamento mediano':>21} {'razao p/ DN20':>14}")
    base = None
    linhas = []
    for dn in (16, 20, 25, 32):
        alvo = [t for t in tags if t["dn"] == dn]
        if not alvo:
            continue
        perto = []
        for t in alvo:
            melhor, dmin = None, math.inf
            for p in pares:
                dd = math.dist(p["xy"], t["xy"])
                if dd < dmin:
                    melhor, dmin = p, dd
            if melhor is not None and dmin <= raio * 8:
                perto.append(melhor["d"])
        if not perto:
            linhas.append((dn, len(alvo), 0, None))
            continue
        perto.sort()
        med = perto[len(perto) // 2]
        if dn == 20:
            base = med
        linhas.append((dn, len(alvo), len(perto), med))
    for dn, ntag, npar, med in linhas:
        if med is None:
            print(f"  {dn:>10} {ntag:>5} {npar:>12} {'sem par por perto':>21}")
            continue
        raz = f"{med/base:.2f}" if base else "-"
        esp = f"{dn/20:.2f}" if base else "-"
        print(f"  {dn:>10} {ntag:>5} {npar:>12} {med:>21.4f} {raz:>14}"
              f"   (esperado {esp})")
    print("\n  Se a coluna 'razao' seguir o 'esperado', o espacamento E o diametro.")


if __name__ == "__main__":
    main()
