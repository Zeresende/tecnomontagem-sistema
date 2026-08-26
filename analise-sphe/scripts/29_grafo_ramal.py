# -*- coding: utf-8 -*-
"""GRAFO DO RAMAL — remonta a rede a partir dos cacos e mede se ela fecha.

Base: probe 28. A geometria do tubo chega em 11.722 pecas, mas 52% da metragem
esta em 304 pecas longas; os cacos de milimetro sao tracejado/simbolo explodido e
96% deles tem vizinho colinear. Logo da para remontar.

Modelo:
  - cada peca vira uma sequencia de SEGMENTOS; as pontas sao snapadas em NOS;
  - um no de grau 2 e passagem: os dois segmentos sao o mesmo percurso -> funde;
  - TRECHO (run) = cadeia maximal entre nos de grau != 2. E o "trecho inteiro do
    percurso" da resposta 5.1 do Hederson;
  - no de grau >= 3 = TEE (onde o DN cai);
  - raiz = bloco MANIFOLD - N - ROSCA.

Este script so DIAGNOSTICA: quantos trechos, quanto da metragem fica ligada a um
manifold, qual a profundidade da arvore. A propagacao de DN vem no 30.

Uso: python 29_grafo_ramal.py <obra> [tol]
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
RX_MANIF = re.compile(r"MANIFOLD", re.I)
MAX_DEPTH = 6
MIN_SEG = 1e-4


def coletar(entidades, segs, rotulos, manifs, depth=0):
    """Segmentos elementares de tubo + rotulos <DN>-PEX + insercoes de manifold."""
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
                    coletar(e.virtual_entities(), segs, rotulos, manifs, depth + 1)
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
        tipo = TUBO_LAYER.search(ly).group(1).upper()
        pts = m22.pontos_de(e)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if math.dist(a, b) > MIN_SEG:
                segs.append({"a": a, "b": b, "m": math.dist(a, b),
                             "tipo": tipo, "layer": ly})


def construir(segs, tol):
    """Devolve (nos, adjacencia no->lista de (aresta, outro_no), arestas)."""
    def no(p):
        return (round(p[0] / tol), round(p[1] / tol))

    adj = defaultdict(list)
    arestas = []
    for s in segs:
        na, nb = no(s["a"]), no(s["b"])
        if na == nb:
            continue
        i = len(arestas)
        arestas.append({"na": na, "nb": nb, "m": s["m"], "tipo": s["tipo"],
                        "pts": [s["a"], s["b"]]})
        adj[na].append((i, nb))
        adj[nb].append((i, na))
    return adj, arestas


def fundir(adj, arestas):
    """Funde cadeias em nos de grau 2. Devolve lista de TRECHOS."""
    usada = [False] * len(arestas)
    trechos = []

    def grau(n):
        return len(adj[n])

    # 1) comeca por arestas que tocam no de grau != 2 (pontas e tees)
    sementes = [i for i, a in enumerate(arestas)
                if grau(a["na"]) != 2 or grau(a["nb"]) != 2]
    for i in sementes:
        if usada[i]:
            continue
        a = arestas[i]
        ini = a["na"] if grau(a["na"]) != 2 else a["nb"]
        usada[i] = True
        pts = list(a["pts"])
        m = a["m"]
        tipos = Counter([a["tipo"]])
        atual = a["nb"] if ini == a["na"] else a["na"]
        nos = [ini]
        while grau(atual) == 2:
            prox = None
            for (j, outro) in adj[atual]:
                if not usada[j]:
                    prox = (j, outro)
                    break
            if prox is None:
                break
            j, outro = prox
            usada[j] = True
            pts.extend(arestas[j]["pts"])
            m += arestas[j]["m"]
            tipos[arestas[j]["tipo"]] += 1
            atual = outro
        nos.append(atual)
        trechos.append({"m": m, "pts": pts, "nos": (ini, atual),
                        "tipo": tipos.most_common(1)[0][0]})

    # 2) sobras = aneis fechados so de grau 2
    for i, a in enumerate(arestas):
        if usada[i]:
            continue
        usada[i] = True
        pts = list(a["pts"])
        m = a["m"]
        tipos = Counter([a["tipo"]])
        ini, atual = a["na"], a["nb"]
        while atual != ini:
            prox = None
            for (j, outro) in adj[atual]:
                if not usada[j]:
                    prox = (j, outro)
                    break
            if prox is None:
                break
            j, outro = prox
            usada[j] = True
            pts.extend(arestas[j]["pts"])
            m += arestas[j]["m"]
            tipos[arestas[j]["tipo"]] += 1
            atual = outro
        trechos.append({"m": m, "pts": pts, "nos": (ini, atual),
                        "tipo": tipos.most_common(1)[0][0]})
    return trechos


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    tols = [float(sys.argv[2])] if len(sys.argv) > 2 else [0.005, 0.01, 0.02, 0.05, 0.1]
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    print(f"OBRA {obra} | {tipos[0].name}\n")
    doc = ezdxf.readfile(str(tipos[0]))
    segs, rotulos, manifs = [], [], []
    coletar(doc.modelspace(), segs, rotulos, manifs)
    total = sum(s["m"] for s in segs)
    print(f"segmentos {len(segs)}  metragem {total:.1f}  rotulos {len(rotulos)}  "
          f"manifolds {len(manifs)}\n")

    print(f"{'tol':>7} {'trechos':>8} {'med m':>7} {'p90 m':>7} {'tees':>6} "
          f"{'compon':>7} {'m ligada a manifold':>22} {'prof max':>9}")
    for tol in tols:
        adj, arestas = construir(segs, tol)
        trechos = fundir(adj, arestas)
        comp = sorted(t["m"] for t in trechos)
        n_tee = sum(1 for n in adj if len(adj[n]) >= 3)

        # grafo de trechos: no -> trechos incidentes
        tno = defaultdict(list)
        for i, t in enumerate(trechos):
            tno[t["nos"][0]].append(i)
            if t["nos"][1] != t["nos"][0]:
                tno[t["nos"][1]].append(i)

        # raizes: trecho cuja ponta esta perto de um manifold
        raio = max(tol * 10, 0.3)
        raiz = set()
        cel = defaultdict(list)
        for i, t in enumerate(trechos):
            for p in (t["pts"][0], t["pts"][-1]):
                cel[(int(p[0] / raio), int(p[1] / raio))].append(i)
        for mf in manifs:
            cx, cy = int(mf["xy"][0] / raio), int(mf["xy"][1] / raio)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for i in cel.get((cx + dx, cy + dy), ()):
                        t = trechos[i]
                        if min(math.dist(mf["xy"], t["pts"][0]),
                               math.dist(mf["xy"], t["pts"][-1])) <= raio:
                            raiz.add(i)

        vistos, alc, prof = set(raiz), 0.0, 0
        fila = [(i, 0) for i in raiz]
        while fila:
            i, p = fila.pop()
            alc += trechos[i]["m"]
            prof = max(prof, p)
            for n in trechos[i]["nos"]:
                for j in tno[n]:
                    if j not in vistos:
                        vistos.add(j)
                        fila.append((j, p + 1))

        vis2, comps = set(), 0
        for i in range(len(trechos)):
            if i in vis2:
                continue
            comps += 1
            pilha = [i]
            vis2.add(i)
            while pilha:
                x = pilha.pop()
                for n in trechos[x]["nos"]:
                    for j in tno[n]:
                        if j not in vis2:
                            vis2.add(j)
                            pilha.append(j)
        pct = 100 * alc / total if total else 0
        print(f"{tol:>7} {len(trechos):>8} {comp[len(comp)//2]:>7.3f} "
              f"{comp[int(len(comp)*0.9)]:>7.2f} {n_tee:>6} {comps:>7} "
              f"{alc:>13.1f} m ({pct:>4.1f}%) {prof:>9}")


if __name__ == "__main__":
    main()
