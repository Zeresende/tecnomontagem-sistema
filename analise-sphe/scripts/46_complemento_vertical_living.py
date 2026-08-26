# -*- coding: utf-8 -*-
"""O COMPLEMENTO VERTICAL DEIXA DE SER TACITO? — teste na Living (11/08/2026).

A pergunta que este script responde, e so ela:
  o buraco de 15% que o script 18 mediu na agua quente da Living aparece como tubo
  VERTICAL desenhado nas vistas da prancha de detalhe `7409-HID-PE-0011-DETTIP-R00`?

Como se chegou aqui:
  · 03/07 (script 18) — no PVTIPO, HAQ-TUB/EXO-TET da 0,85x a receita real de ramal
    AQ; o AF da 1,01x. Hipotese registrada: os 15% que faltam sao o complemento
    vertical "de cabeca" do Hederson;
  · 06/08 (itens 2.2/4.2) — ele deu a tabela: chuveiro 1,00 · lavatorio 1,00 ·
    vaso 0,40 · entrada do apto 1,50 · descida de prumada 1,50;
  · 10/08 (item 6.1) — DERRUBOU parte da hipotese: "existem pontos que nao possuem
    agua quente". Ou seja, parte do buraco e CONTAGEM de ponto, nao metro faltante;
  · 11/08 (item 12.1) — a descida vertical existe desenhada, nas vistas das pranchas
    DET, que nunca foram lidas porque os extratores filtram nome por TIPO.

Tres cuidados que o desenho impoe, e que este script trata explicitamente:
  1. a prancha tem PLANTA e VISTA lado a lado. Em planta, segmento "vertical" e
     direcao norte-sul, nao altura — contar altura ali seria erro grosseiro. So
     regiao classificada como ELEVACAO entra na conta;
  2. o DXF entrega caco (mediana 6 mm). Comparar comprimento de segmento com a
     tabela do Hederson nao vale nada: e preciso REMONTAR o trecho antes
     (`construir`/`fundir` do script 29, mesma remontagem que levou o extrator de
     DN de 20,1 para 14,2 p.p.);
  3. escala — cada regiao e conferida contra as cotas DIMENSION que caem dentro dela.

Uso: python 46_complemento_vertical_living.py [obra] [tol_no] [celula]
"""
import sys, re, math, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
m29 = __import__("29_grafo_ramal")
m45 = __import__("45_regioes_prancha_det")

# limites de classificacao — impressos no relatorio para poderem ser contestados
ALT_MAX_ELEV = 4.5      # m: uma elevacao de pavimento nao passa disso (pe-direito 2,80)
VH_MIN_ELEV = 0.80      # vertical/horizontal minimo para chamar de elevacao
FRAC_VERT = 0.80        # fracao do trecho que precisa ser vertical p/ ser "descida"
MIN_TRECHO = 0.20       # m

TABELA_HEDERSON = [
    (1.00, "chuveiro"), (1.00, "lavatorio"), (0.40, "vaso"),
    (1.50, "entrada do apto"), (1.50, "descida de prumada"),
]


def vertical_de(pts):
    """Metragem vertical de um trecho remontado. pts = [a1,b1,a2,b2,...]."""
    v = t = 0.0
    for i in range(0, len(pts) - 1, 2):
        a, b = pts[i], pts[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        if n <= 0:
            continue
        t += n
        if abs(dy) / n > 0.985:
            v += n
    return v, t


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01
    celula = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8

    caminho = m45.achar_dxf(obra)
    print(f"== PRANCHA DE DETALHE: {caminho.name}")
    print(f"   obra {obra} · tolerancia de no {tol} m · celula de regiao {celula} m\n",
          flush=True)

    doc = ezdxf.readfile(str(caminho))
    segs, titulos, rotulos, cotas = [], [], [], []
    for e, cam, base in m45.percorrer(doc.modelspace(), doc):
        t = e.dxftype()
        if t in ("TEXT", "MTEXT", "ATTRIB"):
            s = m45.texto_de(e).strip()
            if not s:
                continue
            try:
                p = base + ezdxf.math.Vec3(e.dxf.insert)
            except Exception:
                p = base
            if m45.RX_TITULO.match(s) and len(s) < 60:
                titulos.append((s.replace("\n", " "), p))
            mm = m45.RX_PEX.search(s)
            if mm:
                rotulos.append((mm.group(1), p))
        elif t == "DIMENSION":
            try:
                med = float(e.get_measurement())
                d1 = base + ezdxf.math.Vec3(e.dxf.defpoint2)
                d2 = base + ezdxf.math.Vec3(e.dxf.defpoint3)
                cotas.append((med, (d2 - d1).magnitude, base + ezdxf.math.Vec3(e.dxf.defpoint)))
            except Exception:
                pass
        else:
            mm = m45.RX_TUBO.search(cam)
            if not mm or m45.RX_EXCL.search(cam):
                continue
            sis = mm.group(1).upper()
            for a, b in m45.segmentos(e, base):
                n = (b - a).magnitude
                if n >= 1e-4:
                    segs.append({"a": (a.x, a.y), "b": (b.x, b.y), "m": n, "tipo": sis})

    print(f"-- ENTRADA: {len(segs)} segmentos de tubo "
          f"({sum(s['m'] for s in segs):.1f} m) · {len(rotulos)} rotulos <DN>-PEX")

    # ---- 1. regioes
    meios = [((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2) for s in segs]
    grupos = m45.agrupar(meios, celula)
    print(f"-- {len(grupos)} regioes na prancha\n")

    elevacoes, plantas = [], []
    for g in grupos:
        xs, ys, vert, horiz, tot = [], [], 0.0, 0.0, 0.0
        for i in g:
            s = segs[i]
            xs += [s["a"][0], s["b"][0]]
            ys += [s["a"][1], s["b"][1]]
            dy = abs(s["b"][1] - s["a"][1])
            tot += s["m"]
            r = dy / s["m"]
            if r > 0.985:
                vert += s["m"]
            elif r < 0.174:
                horiz += s["m"]
        alt = max(ys) - min(ys)
        vh = vert / (horiz + 1e-9)
        reg = {"idx": g, "alt": alt, "larg": max(xs) - min(xs), "vh": vh, "m": tot,
               "cx": sum(xs) / len(xs), "cy": sum(ys) / len(ys),
               "cx0": min(xs), "cx1": max(xs), "cy0": min(ys), "cy1": max(ys)}
        tit, d = "-", 1e18
        for s, p in titulos:
            dd = math.dist((p.x, p.y), (reg["cx"], reg["cy"]))
            if dd < d:
                tit, d = s, dd
        reg["titulo"], reg["dist"] = tit, d
        fat = [med / dez for med, dez, p in cotas if dez > 0.01
               and reg["cx0"] - 1 <= p.x <= reg["cx1"] + 1
               and reg["cy0"] - 1 <= p.y <= reg["cy1"] + 1]
        reg["escala"] = sum(fat) / len(fat) if fat else None
        (elevacoes if (alt <= ALT_MAX_ELEV and vh >= VH_MIN_ELEV) else plantas).append(reg)

    m_elev = sum(r["m"] for r in elevacoes)
    m_plan = sum(r["m"] for r in plantas)
    print(f"-- CLASSIFICACAO (elevacao = altura <= {ALT_MAX_ELEV} m e V/H >= {VH_MIN_ELEV})")
    print(f"   ELEVACAO/VISTA : {len(elevacoes):>3} regioes · {m_elev:8.1f} m")
    print(f"   PLANTA/AMPLIACAO: {len(plantas):>3} regioes · {m_plan:8.1f} m")
    fora = [r["escala"] for r in elevacoes if r["escala"] and abs(r["escala"] - 1) > 0.10]
    print(f"   escala conferida nas elevacoes: "
          f"{sum(1 for r in elevacoes if r['escala'])} com cota, "
          f"{len(fora)} fora de 1,00 +-10%")

    print("\n-- 12 MAIORES ELEVACOES")
    print(f"   {'metro':>8} {'alt':>5} {'V/H':>6} {'esc':>5}  titulo")
    for r in sorted(elevacoes, key=lambda x: -x["m"])[:12]:
        esc = f"{r['escala']:.2f}" if r["escala"] else "  - "
        print(f"   {r['m']:>8.1f} {r['alt']:>5.2f} {r['vh']:>6.2f} {esc:>5}  "
              f"{r['titulo'][:44]}")

    # ---- 2. remontagem DENTRO das elevacoes
    # O shaft e a prumada, nao o ramal do apartamento: item 2.1 ja disse que o metro
    # da prumada esta dentro da receita do ramal aereo. Misturar as duas coisas
    # inflaria o complemento. Entao a conta principal roda so nas vistas de parede.
    RX_SHAFT = re.compile(r"SHAFT|HIDR[OÔ]METRO|RECALQUE|PRUMAD|BARRILETE", re.I)
    parede = [r for r in elevacoes if not RX_SHAFT.search(r["titulo"])]
    shaft = [r for r in elevacoes if RX_SHAFT.search(r["titulo"])]
    print(f"\n-- ELEVACOES SEPARADAS: parede de apartamento {len(parede)} reg / "
          f"{sum(r['m'] for r in parede):.1f} m · "
          f"shaft e prumada {len(shaft)} reg / {sum(r['m'] for r in shaft):.1f} m")

    idx_elev = [i for r in parede for i in r["idx"]]
    sub = [segs[i] for i in idx_elev]
    adj, arestas = m29.construir(sub, tol)
    trechos = m29.fundir(adj, arestas)
    print(f"\n-- REMONTAGEM (so nas elevacoes): {len(sub)} cacos -> {len(trechos)} trechos")

    descidas = []
    for t in trechos:
        v, tot = vertical_de(t["pts"])
        if tot >= MIN_TRECHO and v / max(tot, 1e-9) >= FRAC_VERT:
            descidas.append({"m": v, "tipo": t["tipo"],
                             "x": t["pts"][0][0], "y": t["pts"][0][1]})
    d_af = sum(d["m"] for d in descidas if d["tipo"] == "AF")
    d_aq = sum(d["m"] for d in descidas if d["tipo"] == "AQ")
    print(f"   trechos verticais (>= {FRAC_VERT:.0%} da extensao): {len(descidas)}"
          f" · AF {d_af:.1f} m · AQ {d_aq:.1f} m")

    bruto = sum(s["m"] for s in sub
                if abs(s["b"][1] - s["a"][1]) / s["m"] > 0.985 and s["m"] >= MIN_TRECHO)
    print(f"   (antes de remontar, somando caco solto >= {MIN_TRECHO} m: {bruto:.1f} m)")

    # o mesmo, agora nas vistas de shaft — para saber o tamanho do que foi separado
    sub_s = [segs[i] for r in shaft for i in r["idx"]]
    if sub_s:
        a_s, e_s = m29.construir(sub_s, tol)
        t_s = m29.fundir(a_s, e_s)
        vs = [(vertical_de(t["pts"]), t["tipo"]) for t in t_s]
        s_af = sum(v for (v, tt), tp in vs if tt >= MIN_TRECHO
                   and v / max(tt, 1e-9) >= FRAC_VERT and tp == "AF")
        s_aq = sum(v for (v, tt), tp in vs if tt >= MIN_TRECHO
                   and v / max(tt, 1e-9) >= FRAC_VERT and tp == "AQ")
        print(f"   [shaft, fora da conta] vertical remontado: AF {s_af:.1f} m · AQ {s_aq:.1f} m")

    comp = Counter(round(d["m"], 2) for d in descidas)
    print("\n-- COMPRIMENTO DOS TRECHOS VERTICAIS REMONTADOS (top 15)")
    print("  ", dict(comp.most_common(15)))

    print("\n-- CONFRONTO COM A TABELA DO HEDERSON (2.2/4.2), tolerancia 10 cm")
    vistos = set()
    for alvo, nome in TABELA_HEDERSON:
        if alvo in vistos:
            continue
        vistos.add(alvo)
        casa = [d for d in descidas if abs(d["m"] - alvo) <= 0.10]
        rot = " / ".join(n for a, n in TABELA_HEDERSON if a == alvo)
        print(f"   {alvo:.2f} m ({rot}): {len(casa):>3} trechos · "
              f"{sum(d['m'] for d in casa):.1f} m")
    dentro = sum(1 for d in descidas
                 if any(abs(d["m"] - a) <= 0.10 for a, _ in TABELA_HEDERSON))
    print(f"   cobertura: {dentro} de {len(descidas)} trechos verticais caem na tabela"
          f" ({dentro/max(len(descidas),1):.0%})")

    # ---- 3. o buraco da agua quente
    print("\n-- O BURACO DA AGUA QUENTE (script 18, no PVTIPO)")
    m18 = __import__("18_dxf_vs_ramal")
    dxf, nome = m18.medir_dxf(obra)
    plan = m18.planilha_ramal(obra)
    n = m18.aptos_pav(obra)
    print(f"   {nome} · {n} aptos/pavimento")
    for sis in ("AF", "AQ"):
        rec = plan[sis][0]
        tet = sum(v for (t, suf), v in dxf.items() if t == sis and suf == "EXO-TET")
        falta = rec * n - tet
        print(f"   {sis}: receita {rec:6.2f} m/apto x {n} = {rec*n:7.1f} m · "
              f"medido no teto {tet:7.1f} m · falta {falta:7.1f} m "
              f"({falta/max(rec*n,1e-9):+.0%})")
        vert_det = d_aq if sis == "AQ" else d_af
        print(f"       vertical remontado na prancha DET: {vert_det:7.1f} m"
              f"  -> cobre {vert_det/falta:5.2f}x do que falta" if falta > 0 else
              f"       vertical remontado na prancha DET: {vert_det:7.1f} m (nao falta metro)")


if __name__ == "__main__":
    main()
