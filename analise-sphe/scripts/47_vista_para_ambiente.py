# -*- coding: utf-8 -*-
"""VISTA -> AMBIENTE -> METRO POR PONTO (Living, 11/08/2026).

O teste do script 46 parou por falta de base comum: media-se o vertical da prancha
inteira contra a receita de um pavimento, sem saber quantos apartamentos ou ambientes
as vistas representam. Metro de prancha e metro de pavimento sao escopos diferentes.

A unidade que resolve e METRO POR PONTO — a mesma da tabela que o Hederson deu no
2.2/4.2 (chuveiro 1,00 · lavatorio 1,00 · vaso 0,40 · entrada 1,50 · prumada 1,50) e a
unica que pode ser multiplicada pela contagem do pavimento (item 6.2: chuveiro 2 ·
lavatorio 3 · vaso 3 · pia cozinha 2 · tanque 1, por apartamento tipo).

Duas correcoes que este script faz sobre o 46:
  1. **a vista e identificada pelo CONTEUDO, nao pelo titulo.** As duas regioes maiores
     que o 46 classificou como parede de apartamento se chamam "VISTA A" mas falam de
     HIDROMETROS, ELEVADOR e SALA DE — e sala de hidrometro/barrilete, nao ramal. Sao
     85,4 dos 87,1 m de vertical AF que o 46 contou. O titulo engana; o texto nao;
  2. **regioes com o mesmo titulo sao remontadas juntas** quando apontam para a mesma
     instancia de titulo — antes uma vista partida pela grade virava 3 vistas.

Uso: python 47_vista_para_ambiente.py [obra] [tol] [celula]
"""
import sys, re, math, logging
from collections import Counter, defaultdict
from pathlib import Path
import ezdxf
from ezdxf.math import Vec3

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
m29 = __import__("29_grafo_ramal")
m45 = __import__("45_regioes_prancha_det")
m46 = __import__("46_complemento_vertical_living")

ALT_MAX_ELEV = 4.5
VH_MIN_ELEV = 0.80
FRAC_VERT = 0.80
MIN_TRECHO = 0.20

# --- classificacao. O TITULO decide primeiro quando fala de shaft ou hidrometro
# (a 1a versao deste script deixou o conteudo decidir e "VISTA DO SHAFT 02" virou BANHO,
# porque a caixa de texto pegava rotulo da vista vizinha).
RX_TIT_SHAFT = re.compile(r"SHAFT|HIDR[OÔ]METRO|RECALQUE|RESERVAT[OÓ]RIO|BARRILETE", re.I)

# "VEM DO HIDROMETRO" aparece em vista de cozinha e nao faz dela sala de hidrometro:
# o marcador de barrilete tem que ser forte.
AMBIENTES = [
    ("BARRILETE/HIDROMETRO", re.compile(
        r"ELEVADOR|BARRILETE|TROCADOR|BY-PASS|SALA DE|RESERVAT[OÓ]RIO|"
        r"HIDR[OÔ]METROS (SER[AÃ]O|INCLINADOS)", re.I)),
    ("COZINHA/A.SERVICO", re.compile(
        r"COZINHA|[AÁ]REA (DE )?SERVI[CÇ]O|AQUECEDOR|FOG[AÃ]O|TANQUE|M[AÁ]QUINA", re.I)),
    ("BANHO", re.compile(r"LAVAT[OÓ]RIO|BACIA|CHUVEIRO|MONOCOMANDO|MISTURADOR|"
                         r"\bBANHO\b|CARENAGEM", re.I)),
    ("LAVABO", re.compile(r"LAVABO", re.I)),
]

# --- pontos hidraulicos, contados pelo rotulo dentro da vista
PONTOS = [
    ("chuveiro", re.compile(r"CHUVEIRO|\bCH\b", re.I)),
    ("lavatorio", re.compile(r"LAVAT[OÓ]RIO", re.I)),
    ("vaso", re.compile(r"BACIA|VASO|\bVS\b", re.I)),
    ("pia cozinha", re.compile(r"\bPIA\b|COZINHA \(SOMENTE FOG", re.I)),
    ("tanque", re.compile(r"TANQUE", re.I)),
]

# item 6.2 — pontos do apartamento tipo da Living, respondido pelo Hederson em 10/08
PONTOS_POR_APTO = {"chuveiro": 2, "lavatorio": 3, "vaso": 3, "pia cozinha": 2, "tanque": 1}
# quais pontos tem agua quente. O item 6.1 disse que "existem pontos que nao possuem
# agua quente" sem listar; esta e a leitura padrao, e esta marcada como SUPOSICAO.
TEM_AQ = {"chuveiro": True, "lavatorio": True, "vaso": False,
          "pia cozinha": True, "tanque": False}
RX_TIT = m45.RX_TITULO


def classificar(titulo, textos):
    if RX_TIT_SHAFT.search(titulo):
        return "SHAFT/BARRILETE"
    juntos = " | ".join(textos)
    for nome, rx in AMBIENTES:
        if rx.search(juntos):
            return nome
    return "(indefinido)"


def pontas_livres(adj, arestas, segs_por_aresta=None):
    """Conta nos de grau 1 por sistema — cada ponta livre de tubo numa elevacao e um
    ponto de utilizacao ou uma emenda com o trecho que a planta desenha. Contagem
    geometrica, independente de rotulo de texto (que se mostrou nao confiavel)."""
    c = Counter()
    for no, viz in adj.items():
        if len(viz) != 1:
            continue
        i = viz[0][0]
        c[arestas[i]["tipo"]] += 1
    return c


def contar_pontos(textos):
    c = Counter()
    for s in textos:
        for nome, rx in PONTOS:
            if rx.search(s):
                c[nome] += 1
    return c


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02
    celula = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8

    caminho = m45.achar_dxf(obra)
    print(f"== {caminho.name} · tol {tol} m · celula {celula} m\n", flush=True)
    doc = ezdxf.readfile(str(caminho))

    segs, txts, titulos = [], [], []
    for e, cam, base in m45.percorrer(doc.modelspace(), doc):
        t = e.dxftype()
        if t in ("TEXT", "MTEXT", "ATTRIB"):
            s = m45.texto_de(e).strip().replace("\n", " ")
            if not s:
                continue
            try:
                p = base + Vec3(e.dxf.insert)
            except Exception:
                p = base
            txts.append((s, p))
            if RX_TIT.match(s) and len(s) < 60:
                titulos.append((s, p))
        else:
            mm = m45.RX_TUBO.search(cam)
            if not mm or m45.RX_EXCL.search(cam):
                continue
            for a, b in m45.segmentos(e, base):
                n = (b - a).magnitude
                if n >= 1e-4:
                    segs.append({"a": (a.x, a.y), "b": (b.x, b.y), "m": n,
                                 "tipo": mm.group(1).upper()})

    meios = [((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2) for s in segs]
    grupos = m45.agrupar(meios, celula)

    # regiao -> instancia de titulo mais proxima (indice, nao texto)
    vistas = defaultdict(lambda: {"idx": [], "xs": [], "ys": []})
    for g in grupos:
        xs, ys, vert, horiz = [], [], 0.0, 0.0
        for i in g:
            s = segs[i]
            xs += [s["a"][0], s["b"][0]]
            ys += [s["a"][1], s["b"][1]]
            r = abs(s["b"][1] - s["a"][1]) / s["m"]
            if r > 0.985:
                vert += s["m"]
            elif r < 0.174:
                horiz += s["m"]
        if not (max(ys) - min(ys) <= ALT_MAX_ELEV and vert / (horiz + 1e-9) >= VH_MIN_ELEV):
            continue
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        melhor, d = None, 1e18
        for k, (s, p) in enumerate(titulos):
            dd = math.dist((p.x, p.y), (cx, cy))
            if dd < d:
                melhor, d = k, dd
        v = vistas[melhor]
        v["idx"] += g
        v["xs"] += xs
        v["ys"] += ys

    print(f"-- {len(vistas)} vistas (elevacao) apos juntar regioes da mesma instancia\n")

    # cada texto pertence a UMA vista: a de centroide mais proximo, dentro de um raio.
    # Antes era caixa envolvente, e vistas vizinhas partilhavam rotulo — foi o que fez
    # "VISTA DO SHAFT 02" aparecer como BANHO com 140 m.
    centro = {k: (sum(v["xs"]) / len(v["xs"]), sum(v["ys"]) / len(v["ys"]))
              for k, v in vistas.items()}
    raio = {k: max(max(v["xs"]) - min(v["xs"]), max(v["ys"]) - min(v["ys"])) / 2 + 0.6
            for k, v in vistas.items()}
    texto_da_vista = defaultdict(list)
    for s, p in txts:
        if RX_TIT.match(s):
            continue
        melhor, d = None, 1e18
        for k, (cx, cy) in centro.items():
            dd = math.dist((p.x, p.y), (cx, cy))
            if dd < d and dd <= raio[k]:
                melhor, d = k, dd
        if melhor is not None:
            texto_da_vista[melhor].append(s)

    linhas = []
    for k, v in vistas.items():
        dentro = texto_da_vista.get(k, [])
        titulo = titulos[k][0] if k is not None else "-"
        amb = classificar(titulo, dentro)
        pts = contar_pontos(dentro)
        sub = [segs[i] for i in v["idx"]]
        adj, ar = m29.construir(sub, tol)
        trechos = m29.fundir(adj, ar)
        livres = pontas_livres(adj, ar)
        vaf = vaq = 0.0
        for t in trechos:
            vv, tt = m46.vertical_de(t["pts"])
            if tt >= MIN_TRECHO and vv / max(tt, 1e-9) >= FRAC_VERT:
                if t["tipo"] == "AF":
                    vaf += vv
                else:
                    vaq += vv
        linhas.append({"tit": titulo, "amb": amb, "pts": pts, "vaf": vaf, "vaq": vaq,
                       "m": sum(s["m"] for s in sub), "livres": livres})

    ordem = {n: i for i, (n, _) in enumerate(AMBIENTES)}
    linhas.sort(key=lambda l: (ordem.get(l["amb"], 9), -l["vaf"] - l["vaq"]))
    print(f"   {'titulo':<26} {'ambiente':<19} {'tubo':>7} {'vAF':>6} {'vAQ':>6} "
          f"{'pontasAF':>9} {'pontasAQ':>9}  rotulos")
    print("   " + "-" * 104)
    for l in linhas:
        if l["vaf"] + l["vaq"] < 0.05:
            continue
        p = " ".join(f"{k[:4]}:{v}" for k, v in sorted(l["pts"].items())) or "-"
        print(f"   {l['tit'][:26]:<26} {l['amb']:<19} {l['m']:>7.1f} {l['vaf']:>6.1f} "
              f"{l['vaq']:>6.1f} {l['livres'].get('AF',0):>9} "
              f"{l['livres'].get('AQ',0):>9}  {p}")

    rotulo = re.sub(r"[^A-Za-z0-9]+", "_", Path(obra).stem)[:40] or "obra"
    saida = AQUI / "saida" / f"vista_ambiente_{rotulo}.csv"
    saida.parent.mkdir(exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write("titulo;ambiente;tubo_m;vertical_AF_m;vertical_AQ_m;"
                "pontas_livres_AF;pontas_livres_AQ;rotulos_de_ponto\n")
        for l in linhas:
            p = " ".join(f"{k}:{v}" for k, v in sorted(l["pts"].items()))
            f.write(f"{l['tit']};{l['amb']};{l['m']:.2f};{l['vaf']:.2f};{l['vaq']:.2f};"
                    f"{l['livres'].get('AF',0)};{l['livres'].get('AQ',0)};{p}\n")
    print(f"\n-- mapa gravado em {saida.relative_to(AQUI)}")

    print("\n-- POR AMBIENTE")
    agr = defaultdict(lambda: {"vaf": 0.0, "vaq": 0.0, "n": 0, "pts": Counter(),
                               "livres": Counter()})
    for l in linhas:
        a = agr[l["amb"]]
        a["vaf"] += l["vaf"]
        a["vaq"] += l["vaq"]
        a["n"] += 1
        a["pts"] += l["pts"]
        a["livres"] += l["livres"]
    for amb, a in sorted(agr.items(), key=lambda kv: -kv[1]["vaf"] - kv[1]["vaq"]):
        tp = sum(a["pts"].values())
        print(f"   {amb:<21} {a['n']:>2} vistas · vertical AF {a['vaf']:>6.1f} m · "
              f"AQ {a['vaq']:>6.1f} m · pontas livres AF {a['livres'].get('AF',0)} /"
              f" AQ {a['livres'].get('AQ',0)} · {tp} rotulos "
              f"{dict(a['pts']) if a['pts'] else ''}")

    # ---- metro por ponto, so no que e ramal de apartamento
    RAMAL = ("BANHO", "COZINHA/A.SERVICO", "LAVABO")
    print(f"\n-- METRO POR PONTO (so ambientes de apartamento: {', '.join(RAMAL)})")
    vaf = sum(agr[a]["vaf"] for a in RAMAL if a in agr)
    vaq = sum(agr[a]["vaq"] for a in RAMAL if a in agr)
    pts, livres = Counter(), Counter()
    for a in RAMAL:
        if a in agr:
            pts += agr[a]["pts"]
            livres += agr[a]["livres"]
    n_pts = sum(pts.values())
    n_aq = sum(v for k, v in pts.items() if TEM_AQ.get(k, False))
    print(f"   vertical AF {vaf:.1f} m · AQ {vaq:.1f} m")
    print(f"   contagem A, por ROTULO de texto : {n_pts} pontos "
          f"({n_aq} com agua quente pela suposicao TEM_AQ)")
    print(f"   contagem B, por PONTA LIVRE     : AF {livres.get('AF',0)} · "
          f"AQ {livres.get('AQ',0)}")
    if n_pts:
        print(f"   A -> AF {vaf/n_pts:.2f} m/ponto"
              + (f" · AQ {vaq/n_aq:.2f} m/ponto quente" if n_aq else ""))
    if livres.get("AF"):
        print(f"   B -> AF {vaf/livres['AF']:.2f} m/ponta"
              + (f" · AQ {vaq/livres['AQ']:.2f} m/ponta" if livres.get("AQ") else ""))
    # a extrapolacao usa a contagem A; a B entra so como ordem de grandeza de controle
    n_af_ref, n_aq_ref = n_pts, n_aq

    # ---- extrapolacao para o pavimento
    print("\n-- EXTRAPOLACAO PARA O PAVIMENTO (8 aptos, contagem do item 6.2)")
    m18 = __import__("18_dxf_vs_ramal")
    n_apto = m18.aptos_pav(obra)
    tot_pt = {k: v * n_apto for k, v in PONTOS_POR_APTO.items()}
    tot_aq = sum(v for k, v in tot_pt.items() if TEM_AQ[k])
    tot_af = sum(tot_pt.values())
    print(f"   pontos no pavimento: {tot_pt} = {tot_af} no total, {tot_aq} com AQ")
    dxf, nome = m18.medir_dxf(obra)
    plan = m18.planilha_ramal(obra)
    for sis, vpp, npt in (("AF", vaf / n_af_ref if n_af_ref else 0, tot_af),
                          ("AQ", vaq / n_aq_ref if n_aq_ref else 0, tot_aq)):
        rec = plan[sis][0] * n_apto
        tet = sum(v for (t, suf), v in dxf.items() if t == sis and suf == "EXO-TET")
        falta = rec - tet
        prev = vpp * npt
        print(f"   {sis}: falta {falta:>7.1f} m · previsto pelo desenho "
              f"{vpp:.2f} m/ponto x {npt} = {prev:>7.1f} m"
              f"  -> {prev/falta:5.2f}x" if falta > 0.5 else
              f"   {sis}: nao falta metro ({falta:+.1f} m) · previsto pelo desenho "
              f"{prev:.1f} m")


if __name__ == "__main__":
    main()
