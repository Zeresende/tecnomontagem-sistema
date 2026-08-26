# -*- coding: utf-8 -*-
"""PROBE 3 — as VISTAS trazem a descida vertical medivel? (anexo 12.1, 11/08/2026)

O probe 42 mostrou que a prancha nao tem so os 2 detalhes de shaft: tem 'Vista A'
a 'Vista G' e duas 'VISTA DO SHAFT CENTRAL'. Vista, em prancha de hidraulica, e
corte/elevacao — exatamente onde o trecho vertical aparece com comprimento real.

Se a hipotese valer, perto de cada titulo de vista o tubo (camadas HAF/HAQ) tem
segmentos VERTICAIS, e o comprimento deles deve conversar com a tabela que o
Hederson deu no item 2.2/4.2: chuveiro 1,00 · lavatorio 1,00 · vaso 0,40 ·
entrada do apto 1,50 · descida de prumada 1,50 (pe-direito 2,80).

Se bater, o complemento vertical deixa de ser regra de cabeca e vira medicao.

Uso: python 43_vistas_descida_vertical.py [raio]
"""
import sys, re, logging
from collections import Counter, defaultdict
from pathlib import Path
import ezdxf
from ezdxf.math import Vec3

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

BASE = Path(__file__).resolve().parent
PASTA = BASE / "dxf" / "DET121"
MAX_DEPTH = 6
TOL_ANG = 10.0          # graus para considerar o segmento vertical/horizontal
MIN_SEG = 0.05          # ignora caco menor que 5 cm

RX_PEX = re.compile(r"(\d{2})\s*-\s*PEX", re.I)
RX_TITULO = re.compile(r"^(VISTA|DETALHE DO SHAFT)", re.I)
RX_TUBO = re.compile(r"HAF-TUB|HAQ-TUB|PRU-F|PRU-rsb", re.I)


def texto_de(e):
    t = e.dxftype()
    if t == "MTEXT":
        return e.plain_text()
    if t in ("TEXT", "ATTRIB"):
        return str(e.dxf.text)
    return ""


def segmentos(e, base):
    """Lista de (p0, p1) globais da entidade linear."""
    t = e.dxftype()
    try:
        if t == "LINE":
            return [(base + Vec3(e.dxf.start), base + Vec3(e.dxf.end))]
        if t == "LWPOLYLINE":
            pts = [base + Vec3(p[0], p[1], 0) for p in e.get_points("xy")]
        elif t == "POLYLINE":
            pts = [base + Vec3(v.dxf.location) for v in e.vertices]
        else:
            return []
        return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    except Exception:
        return []


def percorrer(layout, doc, prof=0, base=Vec3(0, 0, 0)):
    for e in layout:
        if e.dxftype() == "INSERT":
            try:
                desl = base + Vec3(e.dxf.insert)
            except Exception:
                desl = base
            for att in getattr(e, "attribs", []):
                yield att, str(att.dxf.layer), desl
            if prof < MAX_DEPTH:
                try:
                    yield from percorrer(doc.blocks[e.dxf.name], doc, prof + 1, desl)
                except Exception:
                    pass
        else:
            yield e, str(getattr(e.dxf, "layer", "?")), base


def ponto_texto(e, base):
    try:
        return base + Vec3(e.dxf.insert)
    except Exception:
        return base


def main():
    raio = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    caminho = sorted(PASTA.glob("*.dxf"))[0]
    doc = ezdxf.readfile(str(caminho))
    itens = list(percorrer(doc.modelspace(), doc))

    titulos, tubos, rotulos = [], [], []
    for e, cam, base in itens:
        t = e.dxftype()
        if t in ("TEXT", "MTEXT", "ATTRIB"):
            s = texto_de(e).strip()
            if not s:
                continue
            p = ponto_texto(e, base)
            if RX_TITULO.match(s) and len(s) < 60:
                titulos.append((s, p))
            m = RX_PEX.search(s)
            if m:
                rotulos.append((m.group(1), p))
        elif RX_TUBO.search(cam):
            for a, b in segmentos(e, base):
                d = b - a
                if d.magnitude >= MIN_SEG:
                    tubos.append((a, b, d.magnitude, cam))

    print(f"== {caminho.name}")
    print(f"   {len(titulos)} titulos de vista/detalhe · {len(tubos)} segmentos de tubo"
          f" · {len(rotulos)} rotulos <DN>-PEX\n")

    # onde estao os rotulos: dentro das vistas ou na planta?
    print("-- DISTRIBUICAO DOS ROTULOS <DN>-PEX")
    dentro = Counter()
    for dn, p in rotulos:
        casa = None
        for s, q in titulos:
            if (p - q).magnitude <= raio:
                casa = s
                break
        dentro[casa or "(fora de vista — planta)"] += 1
    for k, n in dentro.most_common():
        print(f"   {n:>4}x  {k}")

    print(f"\n-- POR VISTA (raio {raio})")
    for s, q in sorted(titulos, key=lambda x: x[0]):
        vert = []
        horiz = []
        outro = 0.0
        dns = Counter()
        for a, b, ln, cam in tubos:
            if (a - q).magnitude > raio:
                continue
            d = b - a
            ang = abs(d.y) / (d.magnitude + 1e-12)
            if ang > 0.985:          # ~ >80 graus = vertical
                vert.append(round(ln, 3))
            elif ang < 0.174:        # ~ <10 graus = horizontal
                horiz.append(round(ln, 3))
            else:
                outro += ln
        for dn, p in rotulos:
            if (p - q).magnitude <= raio:
                dns[dn] += 1
        if not vert and not horiz:
            continue
        print(f"\n   {s!r} @ ({q.x:.1f}, {q.y:.1f})")
        print(f"      vertical  : {len(vert):>4} seg · {sum(vert):>8.2f} m")
        print(f"      horizontal: {len(horiz):>4} seg · {sum(horiz):>8.2f} m")
        print(f"      inclinado : {outro:>8.2f} m")
        if dns:
            print(f"      rotulos DN: {dict(dns)}")
        comuns = Counter(v for v in vert if v >= 0.20)
        if comuns:
            print("      alturas verticais >=0,20 m mais comuns:",
                  dict(comuns.most_common(10)))

    # visao global: existe altura vertical recorrente na prancha inteira?
    todos_v = [round(ln, 2) for a, b, ln, cam in tubos
               if abs((b - a).y) / (ln + 1e-12) > 0.985 and ln >= 0.20]
    print(f"\n-- TODAS AS VERTICAIS DE TUBO >=0,20 m NA PRANCHA: {len(todos_v)} seg,"
          f" {sum(todos_v):.1f} m")
    print("   comprimentos mais comuns:",
          dict(Counter(todos_v).most_common(20)))
    tabela = {1.00: "chuveiro/lavatorio", 0.40: "vaso", 1.50: "entrada apto/descida prumada",
              2.80: "pe-direito"}
    print("\n-- CONFRONTO COM A TABELA DO HEDERSON (tolerancia 5 cm)")
    for alvo, nome in tabela.items():
        n = sum(1 for v in todos_v if abs(v - alvo) <= 0.05)
        print(f"   {alvo:.2f} m ({nome}): {n} segmentos")


if __name__ == "__main__":
    main()
