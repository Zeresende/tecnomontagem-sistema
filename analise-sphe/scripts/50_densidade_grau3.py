# -*- coding: utf-8 -*-
"""TESTE QUE DECIDE O conexoes.py (pedido da Karina, 12/08/2026)

Pergunta: a leitura geometrica do desenho consegue contar as bifurcacoes do ramal?

O teste NAO e "quantos tes" — o script 49 ja mostrou que contagem ingenua erra 40x
(626 vaos num pavimento que preve 16 tes). O teste e a DENSIDADE de nos de grau 3
por apartamento, contra gabarito que ja temos validado:

    Living  328 tes / 164 aptos = 2,00 tes/apto
    Peak    164 tes / 466 aptos = 0,35 tes/apto

Refinamento que a Karina pediu, e que e o miolo do script: o DXF entrega o tubo em
cacos (mediana 6 mm). Duas pontas colineares no mesmo no sao O MESMO CANO partido,
nao duas derivacoes. Sem esse filtro o grau infla. Entao:

  grau efetivo do no = numero de DIRECOES DISTINTAS que saem dele

Direcao medida a >= DIST_DIR do no (nao na ponta do caco, que e ruido puro), e
agrupada por tolerancia angular. Duas arestas na mesma direcao = 1 cano.
Direcoes opostas = cano que passa reto = grau 2. Grau 3 = derivacao.

Segundo refinamento, do script 49: o desenho CORTA o tubo em cada conexao. Um te
real pode chegar como 3 pontas livres soltas em volta de um ponto. A opcao --ponte
religa pontas livres proximas antes de medir o grau.

Uso:
    python 50_densidade_grau3.py                 # Living e Peak, grade de parametros
    python 50_densidade_grau3.py 20241385        # so uma obra
"""
import sys, os, re, math, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
m29 = __import__("29_grafo_ramal")

TOL_NO = 0.02        # snap de no, mesmo do script 49
DIST_DIR = 0.05      # distancia minima para medir a direcao de uma aresta
VAO_MIN, VAO_MAX = 0.03, 0.60

# Gabarito: contagem de TE da aba RAMAL da propria planilha do Hederson, dividida
# pelos aptos do PREDIO; e o numero de aptos do pavimento TIPO, que e o que o DXF
# desenha. Denominador explicito de proposito — misturar predio com pavimento ja
# derrubou um resultado em 10/08.
OBRAS = {
    "20241385": {
        "nome": "Living Only Ipiranga",
        "tes_predio": 328, "aptos_predio": 164, "aptos_tipo": 8,
        "regiao": None,
        "alerta": "o DXF do tipo mede 1.393,6 m contra 679,7 esperados (2,05x). "
                  "Se o desenho traz o pavimento mais de uma vez, o grau-3 vem "
                  "inflado pelo mesmo fator.",
    },
    "20251533": {
        "nome": "Peak (2 torres)",
        "tes_predio": 164, "aptos_predio": 466, "aptos_tipo": 20,
        "regiao": (100, 150, 75, 150),
        "alerta": "recorte de regiao aplicado: so as 2 plantas de torre, sem as "
                  "2 plantas de furo e sem o bloco estrutural (script 48).",
    },
}


def coletar(doc):
    segs, rot, man = [], [], []
    m29.coletar(doc.modelspace(), segs, rot, man)
    return segs


def posicao(no):
    return (no[0] * TOL_NO, no[1] * TOL_NO)


def direcao(no, i, adj, arestas):
    """Direcao unitaria com que a aresta i sai do no, medida a >= DIST_DIR.
    Segue a cadeia enquanto os nos forem de passagem, para nao ler o angulo de um
    caco de 6 mm — que e ruido, nao geometria."""
    p0 = posicao(no)
    atual, aresta = no, i
    vistas = set()
    for _ in range(200):
        a = arestas[aresta]
        outro = a["nb"] if a["na"] == atual else a["na"]
        p = posicao(outro)
        d = math.dist(p0, p)
        if d >= DIST_DIR or len(adj[outro]) != 2:
            if d == 0:
                return None
            return ((p[0] - p0[0]) / d, (p[1] - p0[1]) / d)
        vistas.add(aresta)
        prox = [j for j, _ in adj[outro] if j != aresta and j not in vistas]
        if not prox:
            return None if d == 0 else ((p[0] - p0[0]) / d, (p[1] - p0[1]) / d)
        atual, aresta = outro, prox[0]
    return None


def agrupa_direcoes(dirs, ang_tol_graus):
    """Junta direcoes quase iguais. Devolve o numero de direcoes distintas."""
    cos_lim = math.cos(math.radians(ang_tol_graus))
    grupos = []
    for d in dirs:
        for g in grupos:
            if d[0] * g[0] + d[1] * g[1] >= cos_lim:
                break
        else:
            grupos.append(d)
    return len(grupos)


def religar(adj, arestas):
    """Une pontas livres separadas por um vao de conexao. Devolve mapa no->no."""
    livres = [n for n, v in adj.items() if len(v) == 1]
    cel = defaultdict(list)
    for n in livres:
        p = posicao(n)
        cel[(int(p[0] / VAO_MAX), int(p[1] / VAO_MAX))].append(n)
    pai = {}

    def raiz(x):
        while pai.get(x, x) != x:
            x = pai[x]
        return x

    for n in livres:
        p = posicao(n)
        cx, cy = int(p[0] / VAO_MAX), int(p[1] / VAO_MAX)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for o in cel.get((cx + dx, cy + dy), ()):
                    if o == n:
                        continue
                    d = math.dist(p, posicao(o))
                    if VAO_MIN <= d <= VAO_MAX:
                        ra, rb = raiz(n), raiz(o)
                        if ra != rb:
                            pai[rb] = ra
    return {n: raiz(n) for n in livres}


def medir(segs, ang, com_ponte):
    adj, arestas = m29.construir(segs, TOL_NO)

    if com_ponte:
        mapa = religar(adj, arestas)
        if mapa:
            novo = defaultdict(list)
            for a in arestas:
                a["na"] = mapa.get(a["na"], a["na"])
                a["nb"] = mapa.get(a["nb"], a["nb"])
            for i, a in enumerate(arestas):
                if a["na"] == a["nb"]:
                    continue
                novo[a["na"]].append((i, a["nb"]))
                novo[a["nb"]].append((i, a["na"]))
            adj = novo

    graus = Counter()
    por_sistema = Counter()
    for no, viz in adj.items():
        if len(viz) < 3:
            graus[len(viz)] += 1
            continue
        dirs, dirs_sis = [], defaultdict(list)
        for i, _ in viz:
            d = direcao(no, i, adj, arestas)
            if d:
                dirs.append(d)
                dirs_sis[arestas[i]["tipo"]].append(d)
        g = agrupa_direcoes(dirs, ang)
        graus[g] += 1
        if max((agrupa_direcoes(v, ang) for v in dirs_sis.values()), default=0) >= 3:
            por_sistema["ok"] += 1
    return graus, por_sistema["ok"]


def por_trecho(segs, min_m):
    """Filtro mais duro que a colinearidade: remonta os cacos em TRECHOS (script 29)
    e so aceita como derivacao o no onde chegam 3+ trechos com pelo menos min_m de
    comprimento. Um te liga cano de verdade; simbolo explodido e tracejado somem."""
    adj, arestas = m29.construir(segs, TOL_NO)
    trechos = m29.fundir(adj, arestas)
    tno = defaultdict(list)
    for t in trechos:
        if t["m"] < min_m:
            continue
        tno[t["nos"][0]].append(t)
        if t["nos"][1] != t["nos"][0]:
            tno[t["nos"][1]].append(t)
    return sum(1 for n, ts in tno.items() if len(ts) >= 3), len(trechos)


def main():
    alvos = sys.argv[1:] or list(OBRAS)
    for obra in alvos:
        cfg = OBRAS[obra]
        d = AQUI / "dxf" / obra
        cand = [p for p in sorted(d.glob("*.dxf"))
                if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
                and not re.search(r"DET", p.name, re.I)]
        if not cand:
            print(f"OBRA {obra}: DXF do tipo nao encontrado")
            continue

        alvo = cfg["tes_predio"] / cfg["aptos_predio"]
        print("=" * 78)
        print(f"OBRA {obra} · {cfg['nome']} · {cand[0].name}")
        print(f"  gabarito: {cfg['tes_predio']} tes / {cfg['aptos_predio']} aptos "
              f"= {alvo:.2f} tes/apto · pavimento tipo tem {cfg['aptos_tipo']} aptos")
        print(f"  ALERTA: {cfg['alerta']}", flush=True)

        segs = coletar(ezdxf.readfile(str(cand[0])))
        if cfg["regiao"]:
            x0, x1, y0, y1 = cfg["regiao"]
            segs = [s for s in segs
                    if x0 <= (s["a"][0] + s["b"][0]) / 2 <= x1
                    and y0 <= (s["a"][1] + s["b"][1]) / 2 <= y1]
        print(f"  {len(segs)} segmentos · {sum(s['m'] for s in segs):.1f} m\n")

        print(f"  {'ponte':>6} {'ang':>5} {'grau3':>7} {'grau>=3':>8} "
              f"{'mesmo sist':>11} {'grau3/apto':>11} {'x alvo':>8}")
        for com_ponte in (False, True):
            for ang in (5, 10, 15, 25):
                graus, sis = medir(segs, ang, com_ponte)
                g3 = graus[3]
                gm = sum(n for g, n in graus.items() if g >= 3)
                dens = g3 / cfg["aptos_tipo"]
                print(f"  {'sim' if com_ponte else 'nao':>6} {ang:>4}° {g3:>7} "
                      f"{gm:>8} {sis:>11} {dens:>11.2f} {dens / alvo:>7.1f}x")

        print(f"\n  filtro por comprimento de trecho (3+ trechos com >= X m no no):")
        print(f"  {'X (m)':>7} {'nos':>7} {'/apto':>8} {'x alvo':>8}")
        for min_m in (0.10, 0.20, 0.50, 1.00, 2.00):
            n, ntr = por_trecho(segs, min_m)
            dens = n / cfg["aptos_tipo"]
            print(f"  {min_m:>7.2f} {n:>7} {dens:>8.2f} {dens / alvo:>7.1f}x")
        print(f"  (remontagem gerou {ntr} trechos)")
        print()


if __name__ == "__main__":
    main()
