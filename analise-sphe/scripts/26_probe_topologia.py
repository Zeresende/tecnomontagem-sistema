# -*- coding: utf-8 -*-
"""PROBE da topologia do ramal — prepara a regra 5.1 do Hederson (10/08/2026).

Resposta 5.1: "O ponto sai do manifold reduzido e dependendo da ligacao, apos uma
conexao ele e reduzido para atender os pontos, normalmente apos o Tee."

Ou seja o DN NAO e propriedade do segmento mais proximo do rotulo: ele se propaga
pelo percurso a partir do manifold e cai depois do tee. Antes de codificar isso
preciso saber se a geometria sustenta um grafo:
  1. os trechos se encostam (da para snapar vertices em nos)?
  2. quantos nos de grau 3+ existem (candidatos a tee)?
  3. o manifold aparece como bloco? com que nome?
  4. a rede e uma arvore por apartamento ou um emaranhado unico?

Uso: python 26_probe_topologia.py <obra>    ex.: python 26_probe_topologia.py 20241385
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
RX_DN = re.compile(r"\b(16|20|25|32)\s*-\s*PEX\b", re.I)
RX_RAIZ = re.compile(r"MANIF|COLET|QUADR|MLR|DISTRIB|BARRIL", re.I)
MAX_DEPTH = 6


def coletar(entidades, segs, rotulos, blocos, depth=0, nome_pai=""):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT":
            nome = ""
            try:
                nome = str(e.dxf.name)
            except Exception:
                pass
            try:
                ins = e.dxf.insert
                blocos.append({"nome": nome, "xy": (float(ins[0]), float(ins[1]))})
            except Exception:
                pass
            if depth < MAX_DEPTH:
                try:
                    coletar(e.virtual_entities(), segs, rotulos, blocos, depth + 1, nome)
                except Exception:
                    pass
            continue
        ly = e.dxf.layer or ""
        if t in ("TEXT", "MTEXT"):
            m = RX_DN.search(m22.texto_de(e))
            if m:
                try:
                    ins = e.dxf.insert
                    rotulos.append({"dn": int(m.group(1)), "layer": ly,
                                    "xy": (float(ins[0]), float(ins[1]))})
                except Exception:
                    pass
            continue
        if t not in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            continue
        if not TUBO_LAYER.search(ly) or EXCL_LAYER.search(ly):
            continue
        pts = m22.pontos_de(e)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if math.dist(a, b) > 0:
                segs.append({"a": a, "b": b, "m": math.dist(a, b), "layer": ly})


def snap(p, tol):
    return (round(p[0] / tol), round(p[1] / tol))


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    if not tipos:
        print(f"sem DXF de tipo em {d}")
        return
    print(f"OBRA {obra} | {tipos[0].name}\n")
    doc = ezdxf.readfile(str(tipos[0]))
    segs, rotulos, blocos = [], [], []
    coletar(doc.modelspace(), segs, rotulos, blocos)
    print(f"segmentos de tubo: {len(segs)}   rotulos <DN>-PEX: {len(rotulos)}   inserts: {len(blocos)}")
    comp = sorted(s["m"] for s in segs)
    print(f"comprimento de segmento: mediana {comp[len(comp)//2]:.3f}  min {comp[0]:.4f}  max {comp[-1]:.2f}")

    print("\n--- 1/2. CONECTIVIDADE por tolerancia de snap ---")
    print(f"{'tol':>8} {'nos':>7} {'grau1':>7} {'grau2':>7} {'grau3':>7} {'grau4+':>7} {'componentes':>12} {'maior comp':>11}")
    for tol in (0.001, 0.01, 0.05, 0.1, 0.25, 0.5):
        adj = defaultdict(set)
        nos = defaultdict(int)
        arestas = []
        for s in segs:
            na, nb = snap(s["a"], tol), snap(s["b"], tol)
            if na == nb:
                continue
            nos[na] += 1
            nos[nb] += 1
            adj[na].add(nb)
            adj[nb].add(na)
            arestas.append((na, nb))
        graus = Counter(len(v) for v in adj.values())
        vistos, comps = set(), []
        for n in adj:
            if n in vistos:
                continue
            pilha, tam = [n], 0
            vistos.add(n)
            while pilha:
                x = pilha.pop()
                tam += 1
                for y in adj[x]:
                    if y not in vistos:
                        vistos.add(y)
                        pilha.append(y)
            comps.append(tam)
        print(f"{tol:>8} {len(adj):>7} {graus.get(1,0):>7} {graus.get(2,0):>7} {graus.get(3,0):>7} "
              f"{sum(v for k,v in graus.items() if k>=4):>7} {len(comps):>12} {max(comps) if comps else 0:>11}")

    print("\n--- 3. BLOCOS candidatos a raiz (manifold/coletor/quadro) ---")
    c = Counter(b["nome"] for b in blocos if RX_RAIZ.search(b["nome"] or ""))
    if c:
        for nome, n in c.most_common(20):
            print(f"  {nome:40} {n:>5}")
    else:
        print("  nenhum bloco com nome de manifold/coletor/quadro")
    print("\n  20 nomes de bloco mais frequentes (para achar a raiz na mao):")
    for nome, n in Counter(b["nome"] for b in blocos).most_common(20):
        print(f"  {nome:40} {n:>5}")

    print("\n--- 4. ROTULOS por DN ---")
    for dn, n in sorted(Counter(r["dn"] for r in rotulos).items()):
        print(f"  DN{dn:<3} {n:>5} rotulos")
    print("\n  camadas dos rotulos:")
    for ly, n in Counter(r["layer"] for r in rotulos).most_common(10):
        print(f"  {ly:40} {n:>5}")


if __name__ == "__main__":
    main()
