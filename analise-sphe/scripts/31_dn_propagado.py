# -*- coding: utf-8 -*-
"""DN PROPAGADO A PARTIR DO MANIFOLD — regra 5.1 completa.

O script 30 implementou a primeira metade da resposta do Hederson (o rotulo vale
pelo TRECHO inteiro, nao pelo pedaco vizinho) e levou o erro de 20,1 para 14,2 p.p.
Falta a segunda metade:

  "O ponto sai do manifold reduzido e ... apos uma conexao ele e reduzido para
   atender os pontos, normalmente apos o Tee."

Ou seja o DN e MONOTONO NAO-CRESCENTE ao se afastar do manifold. Um trecho nunca
engrossa rio abaixo. Isso ataca exatamente o residuo que sobrou no 30: o DN16
inflado (18,6% contra 11,9% reais), porque rotulo de DN16 perto de um tronco
rouba metragem que e de DN20/25.

Algoritmo:
  1. remonta trechos (probe 29: snap + fusao de nos de grau 2);
  2. religa pontas proximas (o desenho corta o tubo em cada conexao);
  3. raiz = trecho com ponta encostada num bloco MANIFOLD - N - ROSCA;
  4. BFS a partir da raiz dentro de cada percurso;
  5. DN do trecho = min(rotulo mais proximo, DN do trecho pai);
     trecho sem rotulo HERDA o DN do pai (aumenta cobertura sem chutar);
  6. percurso sem raiz cai no metodo do 30 (rotulo mais proximo, sem monotonia).

Uso: python 31_dn_propagado.py <obra> [--detalhe]
"""
import sys, re, math, logging
from collections import defaultdict, deque
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")
m25 = __import__("25_avaliar_dn")
m29 = __import__("29_grafo_ramal")
m30 = __import__("30_dn_topologico")

MIN_TRECHO = 0.02
RAIO_MANIF = 0.10


def preparar(obra):
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    doc = ezdxf.readfile(str(tipos[0]))
    segs, rotulos, manifs = [], [], []
    m29.coletar(doc.modelspace(), segs, rotulos, manifs)
    return tipos[0].name, segs, rotulos, manifs


def montar(segs, rotulos, manifs, snap):
    """Parte cara e independente da grade: trechos + rotulo mais proximo de cada um.

    Guarda (dn, distancia) por trecho para que varios raios reaproveitem a conta.
    """
    adj, arestas = m29.construir(segs, snap)
    trechos = [t for t in m29.fundir(adj, arestas) if t["m"] >= MIN_TRECHO]

    # indice de rotulos por celula, para nao varrer os 253 por trecho
    cel = defaultdict(list)
    passo = 4.0
    for k, r in enumerate(rotulos):
        cel[(int(r["xy"][0] / passo), int(r["xy"][1] / passo))].append(k)

    prox = []
    for t in trechos:
        if len(t["pts"]) < 2:
            prox.append((None, float("inf")))
            continue
        xs = [p[0] for p in t["pts"]]
        ys = [p[1] for p in t["pts"]]
        c0x, c0y = int(min(xs) / passo), int(min(ys) / passo)
        c1x, c1y = int(max(xs) / passo), int(max(ys) / passo)
        cands = set()
        anel = 1
        while not cands and anel <= 10:
            for cx in range(c0x - anel, c1x + anel + 1):
                for cy in range(c0y - anel, c1y + anel + 1):
                    cands.update(cel.get((cx, cy), ()))
            anel += 2
        best, dmin = None, float("inf")
        for k in cands:
            dd = m22.dist_ponto_poly(rotulos[k]["xy"], t["pts"])
            if dd < dmin:
                best, dmin = rotulos[k], dd
        prox.append((best["dn"] if best else None, dmin))

    raiz = _raizes(trechos, manifs)
    return trechos, prox, raiz


def _raizes(trechos, manifs):
    raiz = set()
    cel = defaultdict(list)
    for i, t in enumerate(trechos):
        for q in (t["pts"][0], t["pts"][-1]):
            cel[(int(q[0] / RAIO_MANIF), int(q[1] / RAIO_MANIF))].append(i)
    for mf in manifs:
        cx, cy = int(mf["xy"][0] / RAIO_MANIF), int(mf["xy"][1] / RAIO_MANIF)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in cel.get((cx + dx, cy + dy), ()):
                    t = trechos[i]
                    if min(math.dist(mf["xy"], t["pts"][0]),
                           math.dist(mf["xy"], t["pts"][-1])) <= RAIO_MANIF:
                        raiz.add(i)
    return raiz


def rodar(trechos, prox, raiz, R, raio, herdar=True, monotono=True):
    ad = m30.pontes(trechos, R)
    grupos = m30.agrupar(trechos, ad)
    cand = [(d if dist <= raio else None) for (d, dist) in prox]

    dn = [None] * len(trechos)
    m_raiz = 0.0
    for g in grupos:
        rs = [i for i in g if i in raiz]
        if not rs:
            for i in g:
                dn[i] = cand[i]
            continue
        m_raiz += sum(trechos[i]["m"] for i in g)
        vis = set(rs)
        fila = deque()
        for i in rs:
            dn[i] = cand[i]
            fila.append(i)
        while fila:
            x = fila.popleft()
            for y in ad[x]:
                if y in vis:
                    continue
                vis.add(y)
                pai = dn[x]
                c = cand[y]
                if c is None:
                    dn[y] = pai if herdar else None
                elif pai is None:
                    dn[y] = c
                else:
                    dn[y] = min(c, pai) if monotono else c
                fila.append(y)
        for i in g:
            if i not in vis:
                dn[i] = cand[i]

    res = defaultdict(float)
    cl = 0.0
    total = sum(t["m"] for t in trechos)
    for i, t in enumerate(trechos):
        if dn[i]:
            res[dn[i]] += t["m"]
            cl += t["m"]
    return res, cl, total, len(trechos), len(grupos), m_raiz


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    nome, segs, rotulos, manifs = preparar(obra)
    alvo = m25.mix(m25.gabarito(obra))
    print(f"OBRA {obra} | {nome}")
    print(f"segmentos {len(segs)}  rotulos {len(rotulos)}  manifolds {len(manifs)}")
    print("GABARITO (compra real): " + "  ".join(f"DN{k}={alvo[k]:.1f}%" for k in sorted(alvo)))
    print()
    print(f"{'modo':22} {'snap':>5} {'ponte':>6} {'raio':>5} {'trechos':>8} "
          f"{'%c/raiz':>8} {'cobert':>7} {'erro':>7}   mix 16/20/25/32")
    print("-" * 108)

    melhor = None
    for snap in (0.02, 0.05):
        trechos, prox, raiz = montar(segs, rotulos, manifs, snap)
        for R in (0.15, 0.25, 0.4):
            for raio in (5, 10, 30):
                for modo, her, mon in (("so rotulo (=30)", False, False),
                                       ("herda", True, False),
                                       ("herda+monotono", True, True)):
                    res, cl, total, nt, ng, mr = rodar(trechos, prox, raiz,
                                                       R, raio, her, mon)
                    mx = m25.mix(res)
                    er = m25.erro(mx, alvo)
                    print(f"{modo:22} {snap:>5} {R:>6} {raio:>5} {nt:>8} "
                          f"{100*mr/total:>7.1f}% {100*cl/total:>6.1f}% {er:>7.1f}   "
                          + " ".join(f"{mx.get(dn,0):.0f}" for dn in (16, 20, 25, 32)))
                    if melhor is None or er < melhor[0]:
                        melhor = (er, modo, snap, R, raio, 100 * cl / total, mx)

    er, modo, snap, R, raio, cob, mx = melhor
    print("\n" + "=" * 72)
    print(f"MELHOR: {modo} | snap={snap} ponte={R} raio={raio}")
    print(f"  cobertura {cob:.1f}%   erro somado {er:.1f} p.p.")
    print("  mix   " + "  ".join(f"DN{dn}={mx.get(dn,0):.1f}%" for dn in (16, 20, 25, 32)))
    print("  alvo  " + "  ".join(f"DN{dn}={alvo.get(dn,0):.1f}%" for dn in (16, 20, 25, 32)))
    print("\n  06/08 segmento+proximidade : 20,1 p.p.")
    print("  30  trecho religado        : 14,2 p.p.")


if __name__ == "__main__":
    main()
