# -*- coding: utf-8 -*-
"""DESCIDA DE VISTA POR BITOLA — pedido da Ka de 14/08, no HM89 (17/08/2026).

Ela integrou horizontal (planta 103-TIPA) + vertical (vistas do 202-TIPO-DET) numa
tabela por bitola e pediu a reconciliacao do lado de ca, como no arco e no handshake.
O que fica aberto do lado dela e a DISTRIBUICAO POR DN do vertical: a vista do shaft
desce num prumo so, sem rotulo por segmento, e a proximidade nao alcanca.

Este script faz os quatro passos, cada um conferivel isolado:
  1. mede a prancha DET inteira pela regra do PREFIXO da camada (HAF/HAQ), com arco
     CCW, sem segmento de fechamento e sem CIRCLE;
  2. recorta em regioes e separa PLANTA EMBUTIDA de VISTA (a armadilha do xref);
  3. remonta os cacos dentro das vistas e isola os trechos verticais;
  4. atribui DN de duas formas — proximidade pura e a rota do script 30 (o rotulo vale
     pelo GRUPO religado inteiro) — e mostra as duas lado a lado.

O ponto do exercicio e o passo 4: se o topologico enxuga o balde "sem DN", a coluna
fecha; se nao enxuga, o honesto e dizer que a distribuicao e heuristica.

Uso: python 57_vertical_vista_por_dn.py <caminho.dxf> [celula] [tol] [raio]
"""
import sys, re, math, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.disable(logging.CRITICAL)
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
m22 = __import__("22_ramal_por_dn")
m29 = __import__("29_grafo_ramal")
m30 = __import__("30_dn_topologico")
m45 = __import__("45_regioes_prancha_det")
m46 = __import__("46_complemento_vertical_living")

# 18/08: o marcador de diametro do AutoCAD (%%C, ou o Ø ja resolvido) cola no digito
# e MATA o  — `F- %%C25-PEX` nao casava. Eram justamente os rotulos da prumada.
RX_ROT = re.compile(r"(?:%%[cC]|Ø|\b)(\d{2})\s*[-x]\s*([A-Za-zÇç]{2,6})\b")
MAT_OK = {"PEX", "PERT"}
SISTEMAS = ("HAF", "HAQ")
PONTE = 0.25
MAX_DEPTH = 6

# Numeros da Ka (14/08), agua fria do HM89, 1 pavimento tipo.
KA_VERTICAL = {"16": 3.9, "20": 28.7, "25": 1.9, "sem": 28.1, "total": 62.6}
KA_REGIOES = {"planta": 606.0, "vista": 226.0, "vertical_prancha": 173.3}


def ult(nome):
    """Ultimo campo do nome de camada federada: `xref$0$HAF-TUB-___-EXO-PEX`."""
    return re.sub(r"[-_]+", "-", re.split(r"\$0\$|\|", str(nome))[-1]).upper()


def pontos(e):
    """Vertices da entidade, SEM o segmento de fechamento da polilinha (regra 13/08)."""
    pts = m22.pontos_de(e)
    if e.dxftype() == "LWPOLYLINE" and getattr(e, "closed", False) and len(pts) > 2:
        pts = pts[:-1]
    return pts


TODOS = defaultdict(float)      # metragem por prefixo de sistema, para reconciliar total
TODOS_V = defaultdict(float)    # so a parte vertical, idem
EXTRAS = defaultdict(float)     # o que uma leitura ingenua somaria a mais
CONTA = Counter()               # tipos de entidade que servem de conferencia (DIMENSION)


def coletar(cont, segs, rotulos, prof=0):
    for e in cont:
        t = e.dxftype()
        if t == "INSERT":
            if prof < MAX_DEPTH:
                try:
                    coletar(e.virtual_entities(), segs, rotulos, prof + 1)
                except Exception:
                    pass
            continue
        cam = ult(e.dxf.layer)
        if t in ("TEXT", "MTEXT"):
            try:
                txt = str(e.dxf.text) if t == "TEXT" else e.plain_text()
            except Exception:
                continue
            m = RX_ROT.search(txt or "")
            if not m or m.group(2).upper() not in MAT_OK:
                continue
            try:
                ins = e.dxf.insert
            except Exception:
                continue
            rotulos.append({"dn": m.group(1), "xy": (float(ins[0]), float(ins[1])),
                            "no_tubo": cam.startswith(SISTEMAS)})
            continue
        if t == "CIRCLE":            # ralo e simbolo, nunca cano
            try:
                EXTRAS["CIRCLE (fora)"] += 2 * math.pi * float(e.dxf.radius)
            except Exception:
                pass
            continue
        if t == "DIMENSION":
            CONTA["DIMENSION"] += 1
            continue
        if "-TUB" in cam:
            p0 = pontos(e)
            TODOS[cam.split("-")[0]] += m22.compr(p0)
            for i in range(len(p0) - 1):
                d = math.dist(p0[i], p0[i + 1])
                if d > 1e-4 and abs(p0[i + 1][1] - p0[i][1]) / d > 0.985:
                    TODOS_V[cam.split("-")[0]] += d
            if t == "LWPOLYLINE" and getattr(e, "closed", False):
                p2 = m22.pontos_de(e)
                if len(p2) > 2:
                    EXTRAS["fechamento de polilinha (fora)"] += math.dist(p2[-2], p2[-1])
        sis = next((s for s in SISTEMAS if cam.startswith(s + "-TUB")), None)
        if sis is None:
            continue
        p = pontos(e)
        for i in range(len(p) - 1):
            d = math.dist(p[i], p[i + 1])
            if d > 1e-4:
                segs.append({"a": p[i], "b": p[i + 1], "m": d, "tipo": sis})


def regioes(segs, celula):
    meios = [((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2) for s in segs]
    saida = []
    for g in m45.agrupar(meios, celula):
        ys, vert, horiz, tot = [], 0.0, 0.0, 0.0
        for i in g:
            s = segs[i]
            ys += [s["a"][1], s["b"][1]]
            r = abs(s["b"][1] - s["a"][1]) / s["m"]
            tot += s["m"]
            if r > 0.985:
                vert += s["m"]
            elif r < 0.174:
                horiz += s["m"]
        saida.append({"idx": g, "m": tot, "alt": max(ys) - min(ys),
                      "vh": vert / (horiz + 1e-9), "vert": vert})
    return sorted(saida, key=lambda r: -r["m"])


def dn_por_proximidade(x, y, rotulos, raio):
    """Rotulo mais proximo; empate resolvido a favor do que mora em camada de tubo."""
    melhor, dmin = None, raio
    for r in rotulos:
        d = math.dist((x, y), r["xy"])
        if r["no_tubo"]:
            d *= 0.7          # escada de confianca: rotulo na camada do tubo vale mais
        if d < dmin:
            melhor, dmin = r["dn"], d
    return melhor


def main():
    caminho = Path(sys.argv[1])
    celula = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01
    raio = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0

    print(f"== {caminho.name} · celula {celula} · tol {tol} · raio de rotulo {raio}\n",
          flush=True)
    doc = ezdxf.readfile(str(caminho))
    segs, rotulos = [], []
    coletar(doc.modelspace(), segs, rotulos)
    por_sis = defaultdict(float)
    for s in segs:
        por_sis[s["tipo"]] += s["m"]
    print("-- 1. PRANCHA INTEIRA, pela regra do prefixo")
    for sis in SISTEMAS:
        print(f"     {sis}: {por_sis[sis]:8.1f} m")
    print(f"     rotulos <DN>-PEX/PERT: {len(rotulos)} "
          f"({sum(1 for r in rotulos if r['no_tubo'])} em camada de tubo)")
    cont = Counter(r["dn"] for r in rotulos)
    print(f"     por DN: {dict(sorted(cont.items()))}")
    print("     todos os sistemas com camada *-TUB nesta prancha:")
    print(f"        {'sistema':<8} {'total':>9} {'vertical':>10}")
    for k, v in sorted(TODOS.items(), key=lambda x: -x[1]):
        print(f"        {k:<8} {v:>9.1f} {TODOS_V.get(k, 0.0):>10.1f}")
    print(f"        {'SOMA':<8} {sum(TODOS.values()):>9.1f} "
          f"{sum(TODOS_V.values()):>10.1f}")
    for k, v in EXTRAS.items():
        print(f"     [{k}] {v:.1f} m")
    print(f"     entidades DIMENSION (a cota que confere escala): {CONTA['DIMENSION']}")

    # so agua fria daqui pra frente — e o recorte que a Ka mandou
    fria = [s for s in segs if s["tipo"] == "HAF"]
    regs = regioes(fria, celula)
    planta = [r for r in regs if r["vh"] < 1.0]
    vista = [r for r in regs if r["vh"] >= 1.0]
    print(f"\n-- 2. RECORTE (agua fria): {len(regs)} regioes")
    print(f"     {'metros':>9} {'V/H':>7} {'alt':>6}  classe")
    for r in regs[:10]:
        print(f"     {r['m']:>9.1f} {r['vh']:>7.2f} {r['alt']:>6.2f}  "
              f"{'PLANTA EMBUTIDA' if r['vh'] < 1.0 else 'VISTA'}")
    m_pl, m_vi = sum(r["m"] for r in planta), sum(r["m"] for r in vista)
    print(f"     planta embutida {m_pl:8.1f} m  (Ka: {KA_REGIOES['planta']})")
    print(f"     vistas          {m_vi:8.1f} m  (Ka: {KA_REGIOES['vista']})")
    vert_tudo = sum(s["m"] for s in fria
                    if abs(s["b"][1] - s["a"][1]) / s["m"] > 0.985)
    print(f"     vertical da prancha INTEIRA {vert_tudo:8.1f} m  "
          f"(Ka: {KA_REGIOES['vertical_prancha']}) — e o numero que NAO se usa")

    if not vista:
        print("\nsem regiao de vista — nada a distribuir")
        return

    # ---- 3. remontagem dentro das vistas
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
    total_v = sum(d["m"] for d in verticais)
    print(f"\n-- 3. VISTAS: {len(sub)} cacos -> {len(trechos)} trechos · "
          f"{len(verticais)} verticais · {total_v:.1f} m  (Ka: {KA_VERTICAL['total']})")

    # ---- 4a. DN por proximidade pura
    prox = defaultdict(float)
    for d in verticais:
        prox[dn_por_proximidade(d["cx"], d["cy"], rotulos, raio) or "sem"] += d["m"]

    # ---- 4b. DN pela rota do 30: o rotulo vale pelo GRUPO religado inteiro
    ad = m30.pontes(trechos, PONTE)
    porno = defaultdict(list)           # o no compartilhado tambem liga
    for i, t in enumerate(trechos):
        porno[t["nos"][0]].append(i)
        porno[t["nos"][1]].append(i)
    for lst in porno.values():
        for i in lst:
            for j in lst:
                if i != j:
                    ad[i].add(j)
    grupos = m30.agrupar(trechos, ad)
    grupo_de = {}
    for gi, g in enumerate(grupos):
        for i in g:
            grupo_de[i] = gi
    idx_de = {id(t): i for i, t in enumerate(trechos)}
    dn_do_grupo = {}
    for gi, g in enumerate(grupos):
        pts = [p for i in g for p in trechos[i]["pts"]]
        if not pts:
            continue
        votos = Counter()
        for p in pts[::7]:              # amostra: o grupo pode ter milhares de pontos
            dn = dn_por_proximidade(p[0], p[1], rotulos, raio)
            if dn:
                votos[dn] += 1
        if votos:
            dn_do_grupo[gi] = votos.most_common(1)[0][0]
    topo = defaultdict(float)
    for d in verticais:
        gi = grupo_de.get(idx_de.get(id(d["t"])), None)
        topo[dn_do_grupo.get(gi) or "sem"] += d["m"]

    print(f"\n-- 4. DESCIDA DE VISTA POR BITOLA (agua fria)")
    print(f"     {'DN':>5} {'Ka':>9} {'proximidade':>13} {'topologico':>12}")
    chaves = sorted(set(list(prox) + list(topo) + ["16", "20", "25", "sem"]),
                    key=lambda k: (k == "sem", k))
    for k in chaves:
        ka = KA_VERTICAL.get(k)
        print(f"     {k:>5} {('-' if ka is None else f'{ka:.1f}'):>9} "
              f"{prox.get(k, 0.0):>13.1f} {topo.get(k, 0.0):>12.1f}")
    print(f"     {'total':>5} {KA_VERTICAL['total']:>9.1f} "
          f"{sum(prox.values()):>13.1f} {sum(topo.values()):>12.1f}")
    p_sem = 100 * prox.get("sem", 0.0) / max(total_v, 1e-9)
    t_sem = 100 * topo.get("sem", 0.0) / max(total_v, 1e-9)
    print(f"\n     balde SEM DN: proximidade {p_sem:.1f}% · topologico {t_sem:.1f}%"
          f"  (Ka: {100*KA_VERTICAL['sem']/KA_VERTICAL['total']:.1f}%)")


if __name__ == "__main__":
    main()
