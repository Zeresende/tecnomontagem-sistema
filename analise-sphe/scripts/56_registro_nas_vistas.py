# -*- coding: utf-8 -*-
"""ONDE O REGISTRO CORTA A DESCIDA — teste da resposta 16.1 (17/08/2026).

Hederson, item 16.1: "A descida esta no ramal, do registro gaveta para frente segue
no kit."

O corte topologico na PLANTA nao roda: a rede so fecha em 3,6% da metragem porque a
planta nao desenha as descidas (medido em 10/08, script 30, e reconfirmado pelo 55).
Mas a descida ESTA desenhada nas vistas da prancha DET (item 12.1) — e o registro
tambem. Nas vistas o corte e LOCAL: nao precisa de rede conexa, precisa da altura do
registro sobre a coluna de tubo.

Por trecho vertical remontado nas vistas de parede:
    acima do registro -> RAMAL      abaixo do registro -> KIT

O que o resultado tem de bater (Living, por pavimento, numeros de 11/08):
    AF: receita 398,0 · medido no teto 403,4 -> sobra 5,4; o acima tem de ser ~0
    AQ: receita 281,8 · medido no teto 238,1 -> falta 43,7; o acima tem de cobrir isso

Uso: python 56_registro_nas_vistas.py [obra] [tol] [celula]
"""
import sys, re, math, logging
from collections import defaultdict, Counter
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
m55 = __import__("55_fronteira_registro")

RX_SHAFT = re.compile(r"SHAFT|HIDR[OÔ]METRO|RECALQUE|PRUMAD|BARRILETE", re.I)
DX_MAX = 0.35      # m: quanto o simbolo do registro pode estar lateralmente fora do tubo
FOLGA_Y = 0.15     # m: o registro pode cair um pouco fora das pontas do trecho
MIN_TRECHO = 0.20

# Living, por pavimento (NOTA-COMPLEMENTO-VERTICAL-2026-08-11.md)
ALVO = {"20241385": {"nome": "Living", "AF": (398.0, 403.4), "AQ": (281.8, 238.1)}}


def andar(layout, doc, prof=0, base=Vec3(0, 0, 0)):
    """Como o `percorrer` do 45, mas devolve TAMBEM o INSERT (o registro e bloco)."""
    for e in layout:
        if e.dxftype() == "INSERT":
            try:
                desl = base + Vec3(e.dxf.insert)
            except Exception:
                desl = base
            yield e, str(getattr(e.dxf, "name", "")), desl, True
            for att in getattr(e, "attribs", []):
                yield att, str(att.dxf.layer), desl, False
            if prof < m45.MAX_DEPTH:
                try:
                    yield from andar(doc.blocks[e.dxf.name], doc, prof + 1, desl)
                except Exception:
                    pass
        else:
            yield e, str(getattr(e.dxf, "layer", "?")), base, False


def ler(caminho):
    doc = ezdxf.readfile(str(caminho))
    segs, regs, titulos = [], [], []
    for e, cam, base, is_insert in andar(doc.modelspace(), doc):
        t = e.dxftype()
        if is_insert:
            if m55.RX_REG.search(cam):
                regs.append({"nome": cam[:60], "origem": "bloco",
                             "xy": (base.x, base.y)})
            continue
        if t in ("TEXT", "MTEXT", "ATTRIB"):
            s = m45.texto_de(e).strip()
            if not s:
                continue
            try:
                p = base + Vec3(e.dxf.insert)
            except Exception:
                p = base
            if m45.RX_TITULO.match(s) and len(s) < 60:
                titulos.append((s.replace("\n", " "), p))
            if m55.RX_REG.search(s):
                regs.append({"nome": s[:60], "origem": "texto", "xy": (p.x, p.y)})
            continue
        mm = m45.RX_TUBO.search(cam)
        if not mm or m45.RX_EXCL.search(cam):
            continue
        sis = mm.group(1).upper()
        for a, b in m45.segmentos(e, base):
            n = (b - a).magnitude
            if n >= 1e-4:
                segs.append({"a": (a.x, a.y), "b": (b.x, b.y), "m": n, "tipo": sis})
    return segs, regs, titulos


def classificar(segs, titulos, celula):
    """Regioes da prancha -> elevacoes de parede (o resto sai da conta)."""
    meios = [((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2) for s in segs]
    parede, shaft, planta = [], [], []
    for g in m45.agrupar(meios, celula):
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
        alt = max(ys) - min(ys)
        reg = {"idx": g, "m": sum(segs[i]["m"] for i in g),
               "x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys),
               "cx": sum(xs) / len(xs), "cy": sum(ys) / len(ys)}
        tit, d = "-", 1e18
        for s, p in titulos:
            dd = math.dist((p.x, p.y), (reg["cx"], reg["cy"]))
            if dd < d:
                tit, d = s, dd
        reg["titulo"] = tit
        if alt > m46.ALT_MAX_ELEV or vert / (horiz + 1e-9) < m46.VH_MIN_ELEV:
            planta.append(reg)
        elif RX_SHAFT.search(tit):
            shaft.append(reg)
        else:
            parede.append(reg)
    return parede, shaft, planta


def cortar(trechos, regs):
    """Divide cada trecho vertical na altura do registro que estiver sobre ele."""
    acima, abaixo, inteiros = defaultdict(float), defaultdict(float), defaultdict(float)
    com_reg = 0
    for t in trechos:
        v, tot = m46.vertical_de(t["pts"])
        if tot < MIN_TRECHO or v / max(tot, 1e-9) < m46.FRAC_VERT:
            continue
        ys = [p[1] for p in t["pts"]]
        xs = [p[0] for p in t["pts"]]
        y0, y1 = min(ys), max(ys)
        cx = sum(xs) / len(xs)
        alvo = [r for r in regs
                if abs(r["xy"][0] - cx) <= DX_MAX
                and y0 - FOLGA_Y <= r["xy"][1] <= y1 + FOLGA_Y]
        if not alvo:
            inteiros[t["tipo"]] += v
            continue
        com_reg += 1
        yr = max(min(r["xy"][1] for r in alvo), y0)
        yr = min(yr, y1)
        acima[t["tipo"]] += (y1 - yr) * v / max(y1 - y0, 1e-9)
        abaixo[t["tipo"]] += (yr - y0) * v / max(y1 - y0, 1e-9)
    return acima, abaixo, inteiros, com_reg


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01
    celula = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8

    caminho = m45.achar_dxf(obra)
    print(f"== {caminho.name} · obra {obra} · tol {tol} · celula {celula}\n", flush=True)
    segs, regs, titulos = ler(caminho)
    print(f"-- entrada: {len(segs)} segmentos ({sum(s['m'] for s in segs):.1f} m) · "
          f"{len(regs)} marcas de registro")
    for nome, n in Counter(r["nome"] for r in regs).most_common(8):
        print(f"     {n:>4}x  {nome[:70]}")

    parede, shaft, planta = classificar(segs, titulos, celula)
    print(f"\n-- regioes: parede {len(parede)} ({sum(r['m'] for r in parede):.1f} m) · "
          f"shaft {len(shaft)} ({sum(r['m'] for r in shaft):.1f} m) · "
          f"planta {len(planta)} ({sum(r['m'] for r in planta):.1f} m)")

    for rotulo, grupo in (("PAREDE (ramal do apto)", parede), ("SHAFT (prumada)", shaft)):
        idx = [i for r in grupo for i in r["idx"]]
        if not idx:
            continue
        sub = [segs[i] for i in idx]
        adj, arestas = m29.construir(sub, tol)
        trechos = m29.fundir(adj, arestas)
        dentro = [r for r in regs
                  if any(g["x0"] - 1 <= r["xy"][0] <= g["x1"] + 1
                         and g["y0"] - 1 <= r["xy"][1] <= g["y1"] + 1 for g in grupo)]
        acima, abaixo, inteiros, com_reg = cortar(trechos, dentro)
        print(f"\n== {rotulo}: {len(sub)} cacos -> {len(trechos)} trechos · "
              f"{len(dentro)} registros na regiao · {com_reg} descidas cortadas")
        print(f"   {'':<4}{'acima (ramal)':>16}{'abaixo (kit)':>15}{'sem registro':>15}")
        for tipo in ("AF", "AQ"):
            print(f"   {tipo:<4}{acima[tipo]:>16.1f}{abaixo[tipo]:>15.1f}"
                  f"{inteiros[tipo]:>15.1f}")
        if rotulo.startswith("PAREDE") and obra in ALVO:
            a = ALVO[obra]
            print(f"\n   teste contra a receita de ramal ({a['nome']}, por pavimento)")
            for tipo in ("AF", "AQ"):
                rec, teto = a[tipo]
                falta = rec - teto
                soma = teto + acima[tipo]
                print(f"   {tipo}: receita {rec:6.1f} · teto {teto:6.1f} "
                      f"(falta {falta:+6.1f}) · vertical acima do registro "
                      f"{acima[tipo]:6.1f} -> total {soma:6.1f} = {soma/rec:4.2f}x")


if __name__ == "__main__":
    main()
