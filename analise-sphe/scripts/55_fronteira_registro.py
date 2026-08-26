# -*- coding: utf-8 -*-
"""FRONTEIRA RAMAL/KIT = O REGISTRO DE GAVETA (resposta 16.1, 17/08/2026).

Hederson, item 16.1: "A descida esta no ramal, do registro gaveta para frente
segue no kit."

A fronteira deixa de ser convencao de planilha e vira peca fisica do desenho.
Este script faz duas coisas:

  --inventario   varre TODOS os dxf por token de registro (varredura de texto
                 cru, rapida). Responde a pergunta que decide o resto: o registro
                 e ~1 por apartamento (shaft) ou ~3-4 (um por ambiente)?

  <obra>         abre a planta do pavimento tipo, remonta o grafo (funcoes do 29),
                 corta a rede no no mais proximo de cada registro e mede montante
                 (ramal) x jusante (kit) por sistema.

Uso: python 55_fronteira_registro.py --inventario
     python 55_fronteira_registro.py 20241385 [tol]
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
m29 = __import__("29_grafo_ramal")
m30 = __import__("30_dn_topologico")

# Ponte de 0,25 m: valor adotado em 10/08 no script 30 para religar o percurso que o
# desenho corta em cada conexao. Raio do registro um pouco maior, porque o simbolo do
# bloco nao e desenhado exatamente sobre a ponta do tubo.
PONTE = 0.25
RAIO_REG = 0.40

# `gaveta` sozinho pega o bloco da Living; `registro` pega texto e legenda.
RX_REG = re.compile(r"registro|gaveta|\bR\.?G\.?\b|REG[\s_-]*GAV", re.I)
RX_MANIF = re.compile(r"MANIFOLD", re.I)
TUBO_LAYER = re.compile(r"H(AF|AQ)-TUB", re.I)
EXCL_LAYER = re.compile(r"LEG|REF|TAB|DET|PREVIS", re.I)
MAX_DEPTH = 6
MIN_SEG = 1e-4

# Receita real por pavimento, medida em 03/07 e reconferida em 11/08.
RECEITA = {"20241385": {"nome": "Living", "AF": 398.0, "AQ": 281.8}}


def inventario():
    """Varredura de texto cru: quais obras escrevem registro, e como."""
    raiz = BASE / "_analise" / "dxf"
    for pasta in sorted(p for p in raiz.iterdir() if p.is_dir()):
        print(f"\n=== {pasta.name}")
        for arq in sorted(pasta.glob("*.dxf")):
            try:
                raw = arq.read_text(encoding="latin-1", errors="replace")
            except Exception as exc:
                print(f"  {arq.name}: falhou ({exc})")
                continue
            achados = Counter(l.strip() for l in raw.splitlines()
                              if l.strip() and RX_REG.search(l))
            if not achados:
                print(f"  {arq.name}: nenhum token de registro")
                continue
            print(f"  {arq.name}:")
            for txt, n in achados.most_common(8):
                print(f"      {n:>4}x  {txt[:100]}")


def coletar(entidades, segs, regs, manifs, depth=0):
    """Segmentos de tubo AF/AQ + insercoes de registro + manifolds, em coord. mundo."""
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT":
            nome = ""
            try:
                nome = str(e.dxf.name)
            except Exception:
                pass
            alvo = None
            if RX_REG.search(nome):
                alvo = regs
            elif RX_MANIF.search(nome):
                alvo = manifs
            if alvo is not None:
                try:
                    ins = e.dxf.insert
                    alvo.append({"nome": nome, "xy": (float(ins[0]), float(ins[1])),
                                 "origem": "bloco"})
                except Exception:
                    pass
            if depth < MAX_DEPTH:
                try:
                    coletar(e.virtual_entities(), segs, regs, manifs, depth + 1)
                except Exception:
                    pass
            continue
        ly = e.dxf.layer or ""
        if t in ("TEXT", "MTEXT"):
            if RX_REG.search(m22.texto_de(e)) and not EXCL_LAYER.search(ly):
                try:
                    ins = e.dxf.insert
                    regs.append({"nome": m22.texto_de(e)[:60], "layer": ly,
                                 "xy": (float(ins[0]), float(ins[1])),
                                 "origem": "texto"})
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


def indice(trechos, celula):
    """Mapa espacial ponta-de-trecho -> indices, para busca por raio."""
    cel = defaultdict(list)
    for i, t in enumerate(trechos):
        for p in (t["pts"][0], t["pts"][-1]):
            cel[(int(p[0] / celula), int(p[1] / celula))].append(i)
    return cel


class Barreira:
    """Grade espacial dos registros. `perto(p)` = ponto cai em cima de um registro."""

    def __init__(self, regs, raio):
        self.raio = raio
        self.cel = defaultdict(list)
        for r in regs:
            x, y = r["xy"]
            self.cel[(int(x / raio), int(y / raio))].append(r["xy"])

    def perto(self, p):
        cx, cy = int(p[0] / self.raio), int(p[1] / self.raio)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for q in self.cel.get((cx + dx, cy + dy), ()):
                    if math.dist(p, q) <= self.raio:
                        return True
        return False


def dist_ao_tubo(regs, trechos, teto):
    """Distancia de cada registro a ponta de trecho mais proxima (para diagnostico)."""
    cel = indice(trechos, teto)
    fora = []
    for r in regs:
        cx, cy = int(r["xy"][0] / teto), int(r["xy"][1] / teto)
        dmin = float("inf")
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in cel.get((cx + dx, cy + dy), ()):
                    t = trechos[i]
                    dmin = min(dmin, math.dist(r["xy"], t["pts"][0]),
                               math.dist(r["xy"], t["pts"][-1]))
        fora.append((dmin, r))
    return fora


def ligar(trechos, tno, no_xy, barreira, ponte):
    """Adjacencia trecho-a-trecho: no compartilhado + ponte, cortada no registro.

    A ponte existe porque o desenho interrompe o tubo em cada conexao (90,2 m num
    pavimento da Living). O registro de gaveta mora justamente numa dessas
    interrupcoes — por isso o corte e a ligacao NAO feita, nao um no removido."""
    ad = defaultdict(set)
    cortadas = 0
    for n, lst in tno.items():
        if len(lst) < 2:
            continue
        if barreira.perto(no_xy[n]):
            cortadas += 1
            continue
        for i in lst:
            for j in lst:
                if i != j:
                    ad[i].add(j)
    for i, js in m30.pontes(trechos, ponte).items():
        for j in js:
            if j in ad[i]:
                continue
            t, u = trechos[i], trechos[j]
            par = min(((math.dist(p, q), p, q)
                       for p in (t["pts"][0], t["pts"][-1])
                       for q in (u["pts"][0], u["pts"][-1])), key=lambda x: x[0])
            meio = ((par[1][0] + par[2][0]) / 2, (par[1][1] + par[2][1]) / 2)
            if barreira.perto(meio):
                cortadas += 1
                continue
            ad[i].add(j)
            ad[j].add(i)
    return ad, cortadas


def corte(obra, tol):
    d = BASE / "_analise" / "dxf" / obra
    plantas = [p for p in sorted(d.glob("*.dxf"))
               if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
               and not re.search(r"DET|DTIP", p.name, re.I)]
    if not plantas:
        print(f"obra {obra}: nenhuma planta de pavimento tipo")
        return
    arq = plantas[0]
    print(f"OBRA {obra} | {arq.name} | tol {tol}\n")
    doc = ezdxf.readfile(str(arq))
    segs, regs, manifs = [], [], []
    coletar(doc.modelspace(), segs, regs, manifs)

    total = defaultdict(float)
    for s in segs:
        total[s["tipo"]] += s["m"]
    print(f"segmentos {len(segs)}  AF {total['AF']:.1f} m  AQ {total['AQ']:.1f} m")
    print(f"registros {len(regs)}  manifolds {len(manifs)}")
    for nome, n in Counter(r["nome"] for r in regs).most_common(6):
        print(f"    {n:>4}x  {nome[:80]}")
    if not regs:
        print("\nSEM REGISTRO NA PLANTA — o corte nao roda por aqui.")
        return

    adj, arestas = m29.construir(segs, tol)
    trechos = m29.fundir(adj, arestas)
    tno = defaultdict(list)
    no_xy = {}
    for i, t in enumerate(trechos):
        for no, p in ((t["nos"][0], t["pts"][0]), (t["nos"][1], t["pts"][-1])):
            tno[no].append(i)
            no_xy.setdefault(no, p)

    print(f"\ntrechos {len(trechos)}")
    print("distancia de cada registro ao tubo mais proximo:")
    fora = sorted(dist_ao_tubo(regs, trechos, 5.0), key=lambda x: x[0])
    faixas = Counter("<=0,10 m" if d <= 0.10 else "<=0,50 m" if d <= 0.5 else
                     "<=2,00 m" if d <= 2 else "> 2 m ou fora" for d, _ in fora)
    for faixa, n in faixas.most_common():
        print(f"    {n:>4}  {faixa}")
    print("  os 12 mais proximos:")
    for d, r in fora[:12]:
        print(f"    {d:>6.3f} m  {r['origem']:<6} {r['nome'][:52]}")

    perto = [r for d, r in fora if d <= RAIO_REG]
    print(f"\nregistros que encostam no tubo (<= {RAIO_REG} m): {len(perto)} de {len(regs)}")
    if not perto:
        print("SEM REGISTRO SOBRE O TUBO — o corte topologico nao roda nesta planta.")
        return

    barreira = Barreira(perto, RAIO_REG)
    for rotulo, br in (("sem corte (controle)", Barreira([], RAIO_REG)),
                       ("com corte no registro", barreira)):
        ad, cortadas = ligar(trechos, tno, no_xy, br, PONTE)
        raizes = raizes_manifold(trechos, manifs, PONTE)
        if not raizes:
            print(f"\n{rotulo}: sem raiz de manifold — pulado")
            continue
        alc, vistos = defaultdict(float), set(raizes)
        fila = list(raizes)
        while fila:
            i = fila.pop()
            alc[trechos[i]["tipo"]] += trechos[i]["m"]
            for j in ad[i]:
                if j not in vistos:
                    vistos.add(j)
                    fila.append(j)
        print(f"\n{rotulo} — raizes {len(raizes)}, ligacoes cortadas {cortadas}")
        print(f"{'':<6}{'total':>10}{'alcancado':>12}{'%':>8}")
        for tipo in ("AF", "AQ"):
            v = alc.get(tipo, 0.0)
            pct = 100 * v / total[tipo] if total[tipo] else 0
            print(f"{tipo:<6}{total[tipo]:>10.1f}{v:>12.1f}{pct:>7.1f}%")
        rec = RECEITA.get(obra)
        if rec:
            for tipo in ("AF", "AQ"):
                v, alvo = alc.get(tipo, 0.0), rec[tipo]
                print(f"    {tipo} vs receita de ramal {alvo:>6.1f} m = {v / alvo:>5.2f}x")


def raizes_manifold(trechos, manifs, raio):
    """Trechos cuja ponta encosta num manifold — a raiz do ramal."""
    raizes = set()
    cel = indice(trechos, raio)
    for mf in manifs:
        cx, cy = int(mf["xy"][0] / raio), int(mf["xy"][1] / raio)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in cel.get((cx + dx, cy + dy), ()):
                    t = trechos[i]
                    if min(math.dist(mf["xy"], t["pts"][0]),
                           math.dist(mf["xy"], t["pts"][-1])) <= raio:
                        raizes.add(i)
    return raizes


def main():
    if "--inventario" in sys.argv:
        inventario()
        return
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02
    corte(obra, tol)


if __name__ == "__main__":
    main()
