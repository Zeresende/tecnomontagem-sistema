# -*- coding: utf-8 -*-
"""RECORTE DA PRANCHA DE DETALHE EM REGIOES (11/08/2026).

Passo obrigatorio antes de medir qualquer coisa numa prancha DET: ela contem a
PLANTA do pavimento e as VISTAS lado a lado. Somar tudo, ou somar DET junto com o
TIPO, conta o mesmo tubo duas vezes (registrado na nota de 11/08).

Este script separa a prancha em regioes por aglomeracao espacial do tubo, diz o que
cada regiao e (planta ou vista, pelo titulo mais proximo e pela razao vertical/
horizontal) e confere a ESCALA de cada uma comparando o comprimento desenhado com a
medida das cotas DIMENSION que caem dentro dela — vista fora de escala invalidaria
qualquer metragem.

Uso: python 45_regioes_prancha_det.py <obra|caminho.dxf> [celula]
"""
import sys, re, math, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf
from ezdxf.math import Vec3

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

BASE = Path(__file__).resolve().parent
MAX_DEPTH = 6
RX_TUBO = re.compile(r"H(AF|AQ)-TUB", re.I)
RX_EXCL = re.compile(r"LEG|REF|PREVIS", re.I)
RX_PEX = re.compile(r"(\d{2})\s*-\s*PEX", re.I)
RX_TITULO = re.compile(r"^(VISTA|CORTE|DETALHE|AMPLIA|ISOM|PLANTA|ESQUEMA)", re.I)
MIN_SEG = 0.02


def texto_de(e):
    t = e.dxftype()
    if t == "MTEXT":
        return e.plain_text()
    if t in ("TEXT", "ATTRIB"):
        return str(e.dxf.text)
    return ""


def achar_dxf(alvo):
    p = Path(alvo)
    if p.suffix.lower() == ".dxf" and p.exists():
        return p
    d = BASE / "dxf" / alvo
    cand = [f for f in sorted(d.glob("*.dxf"))
            if re.search(r"DET|DTIP|AMPL|ISOM", f.name, re.I)]
    if not cand:
        raise SystemExit(f"nenhuma prancha DET em {d}")
    return cand[0]


def percorrer(layout, doc, prof=0, base=Vec3(0, 0, 0)):
    """(entidade, camada, deslocamento) — so translacao dos INSERTs."""
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


def segmentos(e, base):
    t = e.dxftype()
    try:
        if t == "LINE":
            return [(base + Vec3(e.dxf.start), base + Vec3(e.dxf.end))]
        if t == "LWPOLYLINE":
            p = [base + Vec3(x[0], x[1], 0) for x in e.get_points("xy")]
        elif t == "POLYLINE":
            p = [base + Vec3(v.dxf.location) for v in e.vertices]
        elif t == "ARC":
            c = base + Vec3(e.dxf.center)
            r = e.dxf.radius
            a0 = math.radians(e.dxf.start_angle)
            a1 = math.radians(e.dxf.end_angle)
            if a1 <= a0:
                a1 += 2 * math.pi
            n = max(2, int((a1 - a0) / 0.35) + 1)
            p = [c + Vec3(r * math.cos(a0 + (a1 - a0) * i / n),
                          r * math.sin(a0 + (a1 - a0) * i / n), 0) for i in range(n + 1)]
        else:
            return []
        return [(p[i], p[i + 1]) for i in range(len(p) - 1)]
    except Exception:
        return []


def agrupar(pontos, celula):
    """Componentes conexas numa grade de lado `celula` (8-vizinhanca)."""
    ocup = defaultdict(list)
    for i, (x, y) in enumerate(pontos):
        ocup[(int(x // celula), int(y // celula))].append(i)
    pai = {c: c for c in ocup}

    def raiz(c):
        while pai[c] != c:
            pai[c] = pai[pai[c]]
            c = pai[c]
        return c

    for (cx, cy) in list(ocup):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                v = (cx + dx, cy + dy)
                if v in ocup:
                    a, b = raiz((cx, cy)), raiz(v)
                    if a != b:
                        pai[a] = b
    grupo = {}
    for c in ocup:
        grupo.setdefault(raiz(c), []).extend(ocup[c])
    return list(grupo.values())


def main():
    alvo = sys.argv[1] if len(sys.argv) > 1 else "20241385"
    celula = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    caminho = achar_dxf(alvo)
    print(f"== {caminho.parent.name} / {caminho.name}  (celula {celula} m)\n", flush=True)

    doc = ezdxf.readfile(str(caminho))
    segs = []           # (a, b, comp, sistema)
    titulos = []        # (texto, ponto)
    rotulos = []        # (dn, ponto)
    cotas = []          # (medida, comprimento_desenhado, ponto)

    for e, cam, base in percorrer(doc.modelspace(), doc):
        t = e.dxftype()
        if t in ("TEXT", "MTEXT", "ATTRIB"):
            s = texto_de(e).strip()
            if not s:
                continue
            try:
                p = base + Vec3(e.dxf.insert)
            except Exception:
                p = base
            if RX_TITULO.match(s) and len(s) < 60:
                titulos.append((s, p))
            m = RX_PEX.search(s)
            if m:
                rotulos.append((m.group(1), p))
        elif t == "DIMENSION":
            try:
                med = float(e.get_measurement())
                d1 = base + Vec3(e.dxf.defpoint2)
                d2 = base + Vec3(e.dxf.defpoint3)
                cotas.append((med, (d2 - d1).magnitude, base + Vec3(e.dxf.defpoint)))
            except Exception:
                pass
        else:
            m = RX_TUBO.search(cam)
            if not m or RX_EXCL.search(cam):
                continue
            sis = m.group(1).upper()
            for a, b in segmentos(e, base):
                n = (b - a).magnitude
                if n >= MIN_SEG:
                    segs.append((a, b, n, sis))

    print(f"   {len(segs)} segmentos de tubo · {len(titulos)} titulos · "
          f"{len(rotulos)} rotulos · {len(cotas)} cotas")

    meios = [((a + b) * 0.5) for a, b, _, _ in segs]
    grupos = agrupar([(p.x, p.y) for p in meios], celula)
    grupos.sort(key=lambda g: -sum(segs[i][2] for i in g))
    print(f"   {len(grupos)} regioes\n")

    print(f"{'#':>3} {'metro':>9} {'AF':>8} {'AQ':>8} {'vert':>8} {'V/H':>6} "
          f"{'X':>7} {'Y':>7}  titulo mais proximo")
    print("-" * 108)
    resumo = []
    for k, g in enumerate(grupos[:25], 1):
        tot = af = aq = vert = horiz = 0.0
        xs, ys = [], []
        for i in g:
            a, b, n, sis = segs[i]
            tot += n
            if sis == "AF":
                af += n
            else:
                aq += n
            d = b - a
            r = abs(d.y) / n
            if r > 0.985:
                vert += n
            elif r < 0.174:
                horiz += n
            xs += [a.x, b.x]
            ys += [a.y, b.y]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        larg, alt = max(xs) - min(xs), max(ys) - min(ys)
        tit, dist = "-", 1e18
        for s, p in titulos:
            dd = math.dist((p.x, p.y), (cx, cy))
            if dd < dist:
                tit, dist = s, dd
        dns = Counter(dn for dn, p in rotulos
                      if min(xs) - 1 <= p.x <= max(xs) + 1 and min(ys) - 1 <= p.y <= max(ys) + 1)
        # escala: cotas dentro da regiao, medida declarada x comprimento desenhado
        fat = [med / dez for med, dez, p in cotas
               if dez > 0.01 and min(xs) - 1 <= p.x <= max(xs) + 1 and min(ys) - 1 <= p.y <= max(ys) + 1]
        esc = f"{sum(fat)/len(fat):.3f}" if fat else "-"
        print(f"{k:>3} {tot:>9.1f} {af:>8.1f} {aq:>8.1f} {vert:>8.1f} "
              f"{vert/(horiz+1e-9):>6.2f} {larg:>7.1f} {alt:>7.1f}  {tit[:34]:<34} "
              f"d={dist:5.1f} esc={esc} dn={dict(dns) if dns else ''}")
        resumo.append((k, tot, vert, tit, dist))

    resto = sum(segs[i][2] for g in grupos[25:] for i in g)
    if resto:
        print(f"    ... mais {len(grupos)-25} regioes somando {resto:.1f} m")

    print(f"\n-- TOTAL DA PRANCHA: {sum(s[2] for s in segs):.1f} m de tubo "
          f"(AF {sum(s[2] for s in segs if s[3]=='AF'):.1f} · "
          f"AQ {sum(s[2] for s in segs if s[3]=='AQ'):.1f})")


if __name__ == "__main__":
    main()
