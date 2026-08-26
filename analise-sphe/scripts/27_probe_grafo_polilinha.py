# -*- coding: utf-8 -*-
"""PROBE 2 — grafo no nivel da POLILINHA, nao do segmento.

O probe 26 mostrou que snapar vertice a vertice nao fecha: 26 mil segmentos,
mediana de 6 mm, 4138 componentes. Isso e artefato de tesselacao (ARC virando
dezenas de retas), nao a topologia real da rede.

Modelo testado aqui, que e o que o desenhista de fato desenha:
  - cada POLILINHA de tubo e uma ARESTA (um "trecho" do percurso);
  - duas polilinhas se conectam quando a PONTA de uma encosta em QUALQUER ponto
    da outra (ponta-a-ponta = emenda; ponta-no-meio = TEE);
  - o MANIFOLD (bloco "MANIFOLD - N - ROSCA") e a raiz.

Mede: quantas polilinhas encostam no manifold, qual a profundidade da arvore,
quantos tees aparecem, e quanto da metragem fica alcancavel a partir da raiz.

Uso: python 27_probe_grafo_polilinha.py <obra>
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

TUBO_LAYER = re.compile(r"H(AF|AQ)-TUB", re.I)
EXCL_LAYER = re.compile(r"LEG|REF|TAB|DET|PREVIS", re.I)
RX_MANIF = re.compile(r"MANIFOLD", re.I)
MAX_DEPTH = 6


def coletar(entidades, polis, manifs, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT":
            nome = ""
            try:
                nome = str(e.dxf.name)
            except Exception:
                pass
            if RX_MANIF.search(nome):
                try:
                    ins = e.dxf.insert
                    manifs.append({"nome": nome, "xy": (float(ins[0]), float(ins[1]))})
                except Exception:
                    pass
            if depth < MAX_DEPTH:
                try:
                    coletar(e.virtual_entities(), polis, manifs, depth + 1)
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
        m = m22.compr(pts)
        if m > 0:
            polis.append({"pts": pts, "m": m, "layer": ly,
                          "tipo": TUBO_LAYER.search(ly).group(1).upper()})


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    print(f"OBRA {obra} | {tipos[0].name}\n")
    doc = ezdxf.readfile(str(tipos[0]))
    polis, manifs = [], []
    coletar(doc.modelspace(), polis, manifs)

    total = sum(p["m"] for p in polis)
    comp = sorted(p["m"] for p in polis)
    print(f"polilinhas de tubo: {len(polis)}   manifolds: {len(manifs)}   metragem total: {total:.1f}")
    print(f"comprimento por polilinha: mediana {comp[len(comp)//2]:.3f}  "
          f"p90 {comp[int(len(comp)*0.9)]:.2f}  max {comp[-1]:.2f}")
    print(f"vertices por polilinha: mediana {sorted(len(p['pts']) for p in polis)[len(polis)//2]}")

    # indice espacial simples por celula
    print("\n--- CONEXAO ponta -> qualquer ponto de outra polilinha ---")
    print(f"{'tol':>7} {'arestas':>8} {'nos-tee':>8} {'compon':>7} {'maior':>7} "
          f"{'m alcancavel do manifold':>26}")
    for tol in (0.01, 0.05, 0.1, 0.2, 0.4):
        cel = defaultdict(list)
        for i, p in enumerate(polis):
            for (x, y) in p["pts"]:
                cel[(int(x / tol), int(y / tol))].append(i)

        def vizinhos(xy):
            cx, cy = int(xy[0] / tol), int(xy[1] / tol)
            out = set()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    out.update(cel.get((cx + dx, cy + dy), ()))
            return out

        adj = defaultdict(set)
        n_tee = 0
        for i, p in enumerate(polis):
            for ponta in (p["pts"][0], p["pts"][-1]):
                for j in vizinhos(ponta):
                    if j == i:
                        continue
                    q = polis[j]
                    if m22.dist_ponto_poly(ponta, q["pts"]) <= tol:
                        adj[i].add(j)
                        adj[j].add(i)
        n_tee = sum(1 for i in adj if len(adj[i]) >= 3)

        vistos, comps = set(), []
        for i in range(len(polis)):
            if i in vistos:
                continue
            pilha, tam = [i], 0.0
            vistos.add(i)
            while pilha:
                x = pilha.pop()
                tam += polis[x]["m"]
                for y in adj[x]:
                    if y not in vistos:
                        vistos.add(y)
                        pilha.append(y)
            comps.append(tam)

        # alcance a partir dos manifolds
        raiz = set()
        for mf in manifs:
            for j in vizinhos(mf["xy"]):
                if m22.dist_ponto_poly(mf["xy"], polis[j]["pts"]) <= tol * 4:
                    raiz.add(j)
        vistos2, alc = set(raiz), 0.0
        pilha = list(raiz)
        while pilha:
            x = pilha.pop()
            alc += polis[x]["m"]
            for y in adj[x]:
                if y not in vistos2:
                    vistos2.add(y)
                    pilha.append(y)
        pct = 100 * alc / total if total else 0
        print(f"{tol:>7} {sum(len(v) for v in adj.values())//2:>8} {n_tee:>8} "
              f"{len(comps):>7} {max(comps) if comps else 0:>7.1f} "
              f"{alc:>14.1f} m ({pct:>5.1f}%)  raizes={len(raiz)}")


if __name__ == "__main__":
    main()
