# -*- coding: utf-8 -*-
"""DN POR TRECHO REMONTADO — implementa a regra 5.1 do Hederson (10/08/2026).

  "O ponto sai do manifold reduzido e dependendo da ligacao, apos uma conexao
   ele e reduzido para atender os pontos, normalmente apos o Tee."

O que isso derruba: a atribuicao por proximidade em nivel de SEGMENTO (melhor
metodo ate 06/08, erro 20,1 p.p.) trata cada pedacinho de tubo como independente,
entao um rotulo de DN16 rouba so os centimetros ao lado dele e o DN16 infla.

O que isso propoe: a unidade de atribuicao e o TRECHO — a cadeia de tubo entre
duas conexoes. Um rotulo nomeia o trecho inteiro, nao o pedaco vizinho.

Como o trecho e remontado (probes 26-29): o DXF entrega 26 mil cacos (tracejado e
arcos explodidos, mediana 6 mm). Snapando as pontas em nos e fundindo todo no de
grau 2, sobram cadeias maximais entre bifurcacoes = os trechos. Como o desenho
quebra o tubo em cada conexao, ha uma PONTE opcional que religa pontas proximas.

Grade avaliada contra a compra real do Hederson (mesmo gabarito do script 25).

Uso: python 30_dn_topologico.py <obra>
"""
import sys, re, math, logging
from collections import defaultdict
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")
m25 = __import__("25_avaliar_dn")
m29 = __import__("29_grafo_ramal")

RX_PRU = re.compile(r"PRU", re.I)
MIN_TRECHO = 0.02


def pontes(trechos, R):
    """Une trechos cujas PONTAS se encostam dentro de R. Devolve adjacencia."""
    if R <= 0:
        return defaultdict(set)
    cel = defaultdict(list)
    for i, t in enumerate(trechos):
        for q in (t["pts"][0], t["pts"][-1]):
            cel[(int(q[0] / R), int(q[1] / R))].append(i)
    ad = defaultdict(set)
    for i, t in enumerate(trechos):
        for q in (t["pts"][0], t["pts"][-1]):
            cx, cy = int(q[0] / R), int(q[1] / R)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for j in cel.get((cx + dx, cy + dy), ()):
                        if j == i:
                            continue
                        u = trechos[j]
                        if min(math.dist(q, u["pts"][0]), math.dist(q, u["pts"][-1])) <= R:
                            ad[i].add(j)
                            ad[j].add(i)
    return ad


def agrupar(trechos, ad):
    """Componentes conexos = percursos. Devolve lista de listas de indices."""
    vis, grupos = set(), []
    for i in range(len(trechos)):
        if i in vis:
            continue
        pil, g = [i], []
        vis.add(i)
        while pil:
            x = pil.pop()
            g.append(x)
            for j in ad[x]:
                if j not in vis:
                    vis.add(j)
                    pil.append(j)
        grupos.append(g)
    return grupos


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    print(f"OBRA {obra} | {tipos[0].name}")
    doc = ezdxf.readfile(str(tipos[0]))
    segs, rotulos, manifs = [], [], []
    m29.coletar(doc.modelspace(), segs, rotulos, manifs)

    alvo = m25.mix(m25.gabarito(obra))
    print(f"segmentos {len(segs)}  rotulos {len(rotulos)}  manifolds {len(manifs)}")
    print("GABARITO (compra real): " + "  ".join(f"DN{k}={alvo[k]:.1f}%" for k in sorted(alvo)))
    print()
    print(f"{'unidade':16} {'snap':>6} {'ponte':>6} {'prum':>5} {'raio':>5} "
          f"{'n':>6} {'cobert':>7} {'erro p.p.':>10}   mix 16/20/25/32")
    print("-" * 106)

    melhor = None
    for snap in (0.02, 0.05):
        adj, arestas = m29.construir(segs, snap)
        base = [t for t in m29.fundir(adj, arestas) if t["m"] >= MIN_TRECHO]
        # marca prumada pelo layer dominante do trecho
        for t in base:
            t["prum"] = False
        for t, orig in zip(base, base):
            pass
        for R in (0.0, 0.1, 0.15, 0.25, 0.4):
            ad = pontes(base, R)
            grupos = agrupar(base, ad) if R > 0 else [[i] for i in range(len(base))]
            # unidade de atribuicao = grupo (percurso religado)
            unidades = []
            for g in grupos:
                pts = []
                mm = 0.0
                for i in g:
                    pts.extend(base[i]["pts"])
                    mm += base[i]["m"]
                unidades.append({"pts": pts, "m": mm})
            for sem_prum in (True, False):
                usar = unidades
                total = sum(u["m"] for u in usar)
                for raio in (2, 5, 10, 30):
                    res = defaultdict(float)
                    cl = 0.0
                    for u in usar:
                        best, dmin = None, float("inf")
                        for r in rotulos:
                            dd = m22.dist_ponto_poly(r["xy"], u["pts"]) if len(u["pts"]) > 1 else 9e9
                            if dd < dmin:
                                best, dmin = r, dd
                        if best and dmin <= raio:
                            res[best["dn"]] += u["m"]
                            cl += u["m"]
                    mx = m25.mix(res)
                    er = m25.erro(mx, alvo)
                    cob = 100 * cl / total if total else 0
                    print(f"{'trecho religado':16} {snap:>6} {R:>6} "
                          f"{'-':>5} {raio:>5} {len(usar):>6} {cob:>6.1f}% {er:>9.1f}   "
                          + " ".join(f"{mx.get(dn,0):.0f}" for dn in (16, 20, 25, 32)))
                    if melhor is None or er < melhor[0]:
                        melhor = (er, snap, R, raio, cob, mx, len(usar))
                break   # sem_prum nao se aplica na versao religada

    er, snap, R, raio, cob, mx, n = melhor
    print("\n" + "=" * 70)
    print(f"MELHOR TOPOLOGICO: snap={snap} ponte={R} raio={raio} unidades={n}")
    print(f"  cobertura {cob:.1f}%   erro somado {er:.1f} p.p.")
    print("  mix   " + "  ".join(f"DN{dn}={mx.get(dn,0):.1f}%" for dn in (16, 20, 25, 32)))
    print("  alvo  " + "  ".join(f"DN{dn}={alvo.get(dn,0):.1f}%" for dn in (16, 20, 25, 32)))
    print("\n  referencia 06/08 (segmento, raio 30, sem prumada): 20,1 p.p. / 93,0% cobertura")


if __name__ == "__main__":
    main()
