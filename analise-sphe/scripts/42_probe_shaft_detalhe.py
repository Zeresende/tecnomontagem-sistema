# -*- coding: utf-8 -*-
"""PROBE 2 da prancha de detalhe — a DESCIDA VERTICAL esta cotada? (12.1, 11/08/2026)

O probe 41 achou o que interessa dentro do anexo do Hederson:
  · 109 rotulos `<DN>-PEX` numa obra (Peak/QUA) onde tinhamos afirmado que so havia nota;
  · os titulos 'DETALHE DO SHAFT 1' e 'DETALHE DO SHAFT 2';
  · 193 entidades DIMENSION, a mais comum medindo 0,15.

Falta saber se o detalhe do shaft e o que precisamos: um corte VERTICAL com a altura
da descida cotada. Se for, o complemento vertical deixa de ser tacito e passa a ser
medido — e a topologia do script 31 fecha.

Este probe isola cada titulo de detalhe, pega tudo num raio em volta e mostra:
  a geometria de tubo (camadas HAF/HAQ), os rotulos de DN, as cotas e a extensao
  vertical do desenho (se for corte, Y varia muito mais que numa planta de shaft).

Uso: python 42_probe_shaft_detalhe.py [raio]
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

RX_PEX = re.compile(r"(\d{2})\s*-\s*PEX", re.I)
RX_TITULO = re.compile(r"DETALHE|AMPLIA|ISOM[EÉ]TRIC|CORTE|ESQUEMA|VISTA", re.I)
RX_TUBO = re.compile(r"HAF-TUB|HAQ-TUB|PRU-F", re.I)


def texto_de(e):
    t = e.dxftype()
    if t == "MTEXT":
        return e.plain_text()
    if t in ("TEXT", "ATTRIB"):
        return str(e.dxf.text)
    return ""


def ponto(e):
    for attr in ("insert", "start", "center", "location"):
        if hasattr(e.dxf, attr):
            try:
                return Vec3(getattr(e.dxf, attr))
            except Exception:
                pass
    try:
        pts = list(e.get_points("xy"))
        return Vec3(pts[0][0], pts[0][1], 0)
    except Exception:
        return None


def percorrer(layout, doc, prof=0, base=Vec3(0, 0, 0)):
    """(entidade, camada, ponto_global). Aplica so translacao do INSERT — basta
    para localizar; escala/rotacao nao mudam a vizinhanca de um titulo."""
    for e in layout:
        t = e.dxftype()
        if t == "INSERT":
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
            p = ponto(e)
            yield e, str(getattr(e.dxf, "layer", "?")), (base + p) if p else base


def caixa(e, base):
    """(xmin,ymin,xmax,ymax) aproximada da entidade, ja transladada."""
    t = e.dxftype()
    pts = []
    try:
        if t == "LINE":
            pts = [Vec3(e.dxf.start), Vec3(e.dxf.end)]
        elif t == "LWPOLYLINE":
            pts = [Vec3(p[0], p[1], 0) for p in e.get_points("xy")]
        elif t == "POLYLINE":
            pts = [Vec3(v.dxf.location) for v in e.vertices]
        elif t in ("CIRCLE", "ARC"):
            c, r = Vec3(e.dxf.center), e.dxf.radius
            pts = [c + Vec3(-r, -r, 0), c + Vec3(r, r, 0)]
    except Exception:
        return None
    if not pts:
        return None
    xs = [p.x + base.x for p in pts]
    ys = [p.y + base.y for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def main():
    raio = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    caminho = sorted(PASTA.glob("*.dxf"))[0]
    doc = ezdxf.readfile(str(caminho))
    msp = doc.modelspace()

    itens = list(percorrer(msp, doc))
    print(f"== {caminho.name} — {len(itens)} entidades varridas\n")

    titulos = []
    for e, cam, p in itens:
        if e.dxftype() in ("TEXT", "MTEXT", "ATTRIB"):
            s = texto_de(e).strip()
            if s and RX_TITULO.search(s) and len(s) < 60:
                titulos.append((s, cam, p))

    unicos = Counter(t[0] for t in titulos)
    print(f"-- TITULOS DE DETALHE ({len(titulos)} ocorrencias, {len(unicos)} textos)")
    for s, n in unicos.most_common(30):
        print(f"   {n:>3}x  {s!r}")

    alvos = [t for t in titulos if re.search(r"SHAFT", t[0], re.I)]
    if not alvos:
        alvos = titulos[:4]
    print(f"\n== VIZINHANCA DOS {len(alvos)} DETALHES DE SHAFT (raio {raio})")

    for s, cam, p in alvos:
        print(f"\n-- {s!r} @ ({p.x:.2f}, {p.y:.2f})  [{cam}]")
        metro_tubo = defaultdict(float)
        rotulos = Counter()
        cotas = []
        ymin, ymax, xmin, xmax = 1e18, -1e18, 1e18, -1e18
        n_perto = 0
        for e, c, q in itens:
            if q is None or (q - p).magnitude > raio:
                continue
            n_perto += 1
            b = caixa(e, Vec3(0, 0, 0)) if e.dxftype() not in ("TEXT", "MTEXT", "ATTRIB", "INSERT") else None
            if b:
                xmin, ymin = min(xmin, q.x), min(ymin, q.y)
                xmax, ymax = max(xmax, q.x), max(ymax, q.y)
            if RX_TUBO.search(c):
                t = e.dxftype()
                try:
                    if t == "LINE":
                        metro_tubo[c.split("$")[-1]] += (Vec3(e.dxf.end) - Vec3(e.dxf.start)).magnitude
                    elif t == "LWPOLYLINE":
                        pts = [Vec3(x[0], x[1], 0) for x in e.get_points("xy")]
                        metro_tubo[c.split("$")[-1]] += sum(
                            (pts[i + 1] - pts[i]).magnitude for i in range(len(pts) - 1))
                except Exception:
                    pass
            if e.dxftype() in ("TEXT", "MTEXT", "ATTRIB"):
                m = RX_PEX.search(texto_de(e))
                if m:
                    rotulos[m.group(1)] += 1
            if e.dxftype() == "DIMENSION":
                try:
                    cotas.append(round(float(e.get_measurement()), 3))
                except Exception:
                    pass
        print(f"   entidades no raio: {n_perto}")
        if xmin < 1e17:
            print(f"   extensao: X {xmax-xmin:.2f} × Y {ymax-ymin:.2f}"
                  f"   (razao Y/X {(ymax-ymin)/(xmax-xmin+1e-9):.2f})")
        print(f"   rotulos <DN>-PEX: {dict(rotulos)}")
        if metro_tubo:
            for c, m in sorted(metro_tubo.items(), key=lambda x: -x[1])[:8]:
                print(f"   tubo {c:<28} {m:>8.2f}")
        else:
            print("   tubo: nenhuma camada HAF/HAQ/PRU no raio")
        print(f"   cotas ({len(cotas)}): {dict(Counter(cotas).most_common(12))}")


if __name__ == "__main__":
    main()
