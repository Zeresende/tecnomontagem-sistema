# -*- coding: utf-8 -*-
"""O BALDE "SEM DN" TEM ENDERECO? — pergunta da Ka de 18/08 (18/08/2026).

Em 17/08 o script 57 mediu o vertical de vista do HM89 (59,2 m) e mostrou que 49% dele
fica "sem DN" por nenhum dos dois caminhos (proximidade e rota topologica do 30). A
proposta daquele dia foi tirar o DN do ambiente que a descida atende — o mapa vista ->
ambiente do script 47. A Ka perguntou como esse mapa esta.

Este script responde a pergunta ANTES de construir o mapa como regra: ele cruza os dois
eixos que ja existem — DN (do 57) e AMBIENTE (do 47) — no mesmo trecho vertical, e mostra
ONDE o balde "sem DN" mora. Se ele mora nos ambientes de apartamento, o mapa fecha a
coluna. Se ele mora no shaft, o mapa NAO fecha, porque prumada nao e descida de ponto e
nao tem ramal rotulado para herdar bitola.

Uso: python 58_sem_dn_por_ambiente.py <caminho.dxf> [celula] [tol] [raio]
"""
import sys, math, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf
from ezdxf.math import Vec3

sys.stdout.reconfigure(encoding="utf-8")
logging.disable(logging.CRITICAL)
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
m29 = __import__("29_grafo_ramal")
m30 = __import__("30_dn_topologico")
m45 = __import__("45_regioes_prancha_det")
m46 = __import__("46_complemento_vertical_living")
m47 = __import__("47_vista_para_ambiente")
m57 = __import__("57_vertical_vista_por_dn")


def main():
    caminho = Path(sys.argv[1])
    celula = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01
    raio = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0

    print(f"== {caminho.name} · celula {celula} · tol {tol} · raio {raio}\n", flush=True)
    doc = ezdxf.readfile(str(caminho))

    # --- eixo 1: tubo e rotulo de DN, pela regra do prefixo (script 57)
    segs, rotulos = [], []
    m57.coletar(doc.modelspace(), segs, rotulos)
    fria = [s for s in segs if s["tipo"] == "HAF"]

    # --- textos e titulos, para o eixo do ambiente (script 45/47)
    txts, titulos = [], []
    for e, cam, base in m45.percorrer(doc.modelspace(), doc):
        if e.dxftype() not in ("TEXT", "MTEXT", "ATTRIB"):
            continue
        s = m45.texto_de(e).strip().replace("\n", " ")
        if not s:
            continue
        try:
            p = base + Vec3(e.dxf.insert)
        except Exception:
            p = base
        txts.append((s, p))
        if m45.RX_TITULO.match(s) and len(s) < 60:
            titulos.append((s, p))

    # --- regioes de vista (o recorte do 57)
    regs = m57.regioes(fria, celula)
    vista = [r for r in regs if r["vh"] >= 1.0]
    if not vista:
        raise SystemExit("sem regiao de vista")

    # --- cada regiao de vista -> instancia de titulo mais proxima (regra do 47)
    vistas = defaultdict(lambda: {"idx": [], "xs": [], "ys": []})
    for r in vista:
        xs, ys = [], []
        for i in r["idx"]:
            s = fria[i]
            xs += [s["a"][0], s["b"][0]]
            ys += [s["a"][1], s["b"][1]]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        melhor, d = None, 1e18
        for k, (s, p) in enumerate(titulos):
            dd = math.dist((p.x, p.y), (cx, cy))
            if dd < d:
                melhor, d = k, dd
        v = vistas[melhor]
        v["idx"] += r["idx"]
        v["xs"] += xs
        v["ys"] += ys

    centro = {k: (sum(v["xs"]) / len(v["xs"]), sum(v["ys"]) / len(v["ys"]))
              for k, v in vistas.items()}
    raio_v = {k: max(max(v["xs"]) - min(v["xs"]), max(v["ys"]) - min(v["ys"])) / 2 + 0.6
              for k, v in vistas.items()}
    texto_da_vista = defaultdict(list)
    for s, p in txts:
        if m45.RX_TITULO.match(s):
            continue
        melhor, d = None, 1e18
        for k, (cx, cy) in centro.items():
            dd = math.dist((p.x, p.y), (cx, cy))
            if dd < d and dd <= raio_v[k]:
                melhor, d = k, dd
        if melhor is not None:
            texto_da_vista[melhor].append(s)

    ambiente = {k: m47.classificar(titulos[k][0] if k is not None else "-",
                                   texto_da_vista.get(k, [])) for k in vistas}
    titulo = {k: (titulos[k][0] if k is not None else "-") for k in vistas}

    # --- eixo 2: trechos verticais e DN (pipeline do 57)
    sub = [fria[i] for r in vista for i in r["idx"]]
    adj, arestas = m29.construir(sub, tol)
    trechos = m29.fundir(adj, arestas)
    verticais = []
    for t in trechos:
        v, tt = m46.vertical_de(t["pts"])
        if tt >= m46.MIN_TRECHO and v / max(tt, 1e-9) >= m46.FRAC_VERT:
            cx = sum(p[0] for p in t["pts"]) / len(t["pts"])
            cy = sum(p[1] for p in t["pts"]) / len(t["pts"])
            verticais.append({"m": v, "cx": cx, "cy": cy, "t": t})

    ad = m30.pontes(trechos, m57.PONTE)
    porno = defaultdict(list)
    for i, t in enumerate(trechos):
        porno[t["nos"][0]].append(i)
        porno[t["nos"][1]].append(i)
    for lst in porno.values():
        for i in lst:
            for j in lst:
                if i != j:
                    ad[i].add(j)
    grupos = m30.agrupar(trechos, ad)
    grupo_de = {i: gi for gi, g in enumerate(grupos) for i in g}
    idx_de = {id(t): i for i, t in enumerate(trechos)}
    dn_do_grupo = {}
    for gi, g in enumerate(grupos):
        pts = [p for i in g for p in trechos[i]["pts"]]
        votos = Counter()
        for p in pts[::7]:
            dn = m57.dn_por_proximidade(p[0], p[1], rotulos, raio)
            if dn:
                votos[dn] += 1
        if votos:
            dn_do_grupo[gi] = votos.most_common(1)[0][0]

    # --- o cruzamento: cada vertical ganha ambiente (vista mais proxima) e DN
    cruz = defaultdict(float)
    por_amb = defaultdict(float)
    sem_por_vista = defaultdict(float)
    for d in verticais:
        melhor, dd = None, 1e18
        for k, (cx, cy) in centro.items():
            x = math.dist((d["cx"], d["cy"]), (cx, cy))
            if x < dd:
                melhor, dd = k, x
        amb = ambiente.get(melhor, "(fora)")
        gi = grupo_de.get(idx_de.get(id(d["t"])), None)
        dn = dn_do_grupo.get(gi) or "sem"
        cruz[(amb, dn)] += d["m"]
        por_amb[amb] += d["m"]
        if dn == "sem":
            sem_por_vista[(titulo.get(melhor, "-"), amb)] += d["m"]

    total = sum(por_amb.values())
    dns = sorted({dn for _, dn in cruz}, key=lambda k: (k == "sem", k))
    print(f"-- VERTICAL DE VISTA (agua fria): {total:.1f} m em {len(vistas)} vistas\n")
    print(f"   {'ambiente':<22} " + " ".join(f"{('Ø'+d if d!='sem' else 'sem DN'):>8}"
                                             for d in dns) + f" {'total':>8}")
    for amb, tot in sorted(por_amb.items(), key=lambda x: -x[1]):
        linha = " ".join(f"{cruz.get((amb, d), 0.0):>8.1f}" for d in dns)
        print(f"   {amb:<22} {linha} {tot:>8.1f}")
    linha = " ".join(f"{sum(cruz.get((a, d), 0.0) for a in por_amb):>8.1f}" for d in dns)
    print(f"   {'TOTAL':<22} {linha} {total:>8.1f}")

    sem = sum(v for (a, d), v in cruz.items() if d == "sem")
    print(f"\n-- ONDE MORA O BALDE SEM DN ({sem:.1f} m = "
          f"{100*sem/max(total,1e-9):.1f}% do vertical de vista)")
    for (tit, amb), v in sorted(sem_por_vista.items(), key=lambda x: -x[1]):
        print(f"   {tit[:34]:<34} {amb:<22} {v:>7.1f} m  "
              f"({100*v/max(sem,1e-9):.1f}% do sem DN)")


if __name__ == "__main__":
    main()
