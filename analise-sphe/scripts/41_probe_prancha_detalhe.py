# -*- coding: utf-8 -*-
"""PROBE da PRANCHA DE DETALHE — anexo do item 12.1 (Hederson, 10/08/2026).

Contexto: o bloqueio tecnico de 10/08 era que a planta de pavimento NAO desenha a
descida vertical (o tubo some no teto e reaparece no piso), o que deixava 96,4% da
metragem fora de qualquer percurso ligado a manifold e impedia aplicar a regra 5.1.

O Hederson respondeu que a descida EXISTE, em prancha separada, com nome contendo
DET / AMPL / ISOM, e anexou `QUA-HID-LO-1214-TOB-DET-R00.dwg` (Peak, torre B, tipo).

Este probe responde 3 perguntas, nesta ordem:
  1. o que tem dentro (camadas, entidades, textos) — e do mesmo universo SPHE?
  2. a prancha traz DN? por rotulo `<DN>-PEX`, por nota `%%C`, ou nenhum?
  3. a descida vertical esta COTADA (numero de altura legivel) ou so desenhada?

Nao mede nada ainda: so diz se o dado esta la e em que forma.

Uso: python 41_probe_prancha_detalhe.py [pasta_dxf]
"""
import sys, re, logging
from collections import Counter, defaultdict
from pathlib import Path
import ezdxf
from ezdxf.math import Vec3

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

BASE = Path(__file__).resolve().parent
PADRAO = BASE / "dxf" / "DET121"

MAX_DEPTH = 6
RX_PEX = re.compile(r"(\d{2})\s*-\s*PEX", re.I)
RX_DIAM = re.compile(r"(?:%%C|\\U\+00D8|Ø)\s*(\d{2,3})", re.I)
RX_NUM = re.compile(r"^[\s]*(\d{1,4}(?:[.,]\d{1,2})?)[\s]*$")
RX_INTERESSE = re.compile(r"PEX|PE-?RT|%%C|Ø|TUBO\s*GUIA|PRUMAD|DESCID|SUBID|"
                          r"AGUA\s*(FRIA|QUENTE)|\bAF\b|\bAQ\b|ISOM|AMPL|DETALHE", re.I)


def texto_de(e):
    """Texto plano de TEXT/MTEXT/ATTRIB, sem formatacao de MTEXT."""
    t = e.dxftype()
    if t == "MTEXT":
        return e.plain_text()
    if t in ("TEXT", "ATTRIB"):
        return str(e.dxf.text)
    return ""


def percorrer(layout, doc, prof=0, transform=None):
    """Gera (entidade, camada_efetiva) descendo em INSERTs aninhados."""
    for e in layout:
        t = e.dxftype()
        if t == "INSERT":
            yield e, "INSERT:" + str(e.dxf.name)
            if prof < MAX_DEPTH:
                try:
                    bloco = doc.blocks[e.dxf.name]
                except Exception:
                    continue
                yield from percorrer(bloco, doc, prof + 1)
            for att in getattr(e, "attribs", []):
                yield att, str(att.dxf.layer)
        else:
            yield e, str(getattr(e.dxf, "layer", "?"))


def comprimento(e):
    """Metragem da entidade linear, em unidades do desenho."""
    t = e.dxftype()
    try:
        if t == "LINE":
            return (Vec3(e.dxf.end) - Vec3(e.dxf.start)).magnitude
        if t in ("LWPOLYLINE", "POLYLINE"):
            pts = [Vec3(p[0], p[1], 0) if len(p) >= 2 else Vec3(p)
                   for p in e.get_points("xy")] if t == "LWPOLYLINE" else \
                  [Vec3(v.dxf.location) for v in e.vertices]
            return sum((pts[i + 1] - pts[i]).magnitude for i in range(len(pts) - 1))
    except Exception:
        return 0.0
    return 0.0


def main():
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else PADRAO
    arquivos = sorted(pasta.glob("*.dxf"))
    if not arquivos:
        print(f"nenhum .dxf em {pasta}")
        return
    caminho = arquivos[0]
    print(f"== {caminho.name} ({caminho.stat().st_size/1e6:.1f} MB)\n")

    doc = ezdxf.readfile(str(caminho))
    msp = doc.modelspace()

    ent_por_tipo = Counter()
    metro_por_camada = defaultdict(float)
    ent_por_camada = Counter()
    textos = []
    blocos = Counter()

    for e, camada in percorrer(msp, doc):
        t = e.dxftype()
        ent_por_tipo[t] += 1
        if camada.startswith("INSERT:"):
            blocos[camada[7:]] += 1
            continue
        ent_por_camada[camada] += 1
        c = comprimento(e)
        if c:
            metro_por_camada[camada] += c
        if t in ("TEXT", "MTEXT", "ATTRIB"):
            s = texto_de(e).strip()
            if s:
                textos.append((s, camada, tuple(round(v, 2) for v in
                                                (e.dxf.insert if hasattr(e.dxf, "insert")
                                                 else (0, 0, 0)))[:2]))

    print("-- ENTIDADES")
    for t, n in ent_por_tipo.most_common(12):
        print(f"   {t:<14} {n:>7}")

    print(f"\n-- CAMADAS ({len(ent_por_camada)} distintas) — top 20 por metragem")
    for cam, m in sorted(metro_por_camada.items(), key=lambda x: -x[1])[:20]:
        print(f"   {cam:<38} {m:>12.1f}   ({ent_por_camada[cam]} ent.)")
    sem_metro = [c for c in ent_por_camada if c not in metro_por_camada]
    if sem_metro:
        print(f"   ... e {len(sem_metro)} camadas sem geometria linear")

    print(f"\n-- BLOCOS ({len(blocos)} nomes, {sum(blocos.values())} instancias) — top 15")
    for b, n in blocos.most_common(15):
        print(f"   {b:<48} {n:>5}")

    print(f"\n-- TEXTOS: {len(textos)} no total")
    pex = [t for t in textos if RX_PEX.search(t[0])]
    diam = [t for t in textos if RX_DIAM.search(t[0])]
    print(f"   rotulo '<DN>-PEX' : {len(pex)}")
    if pex:
        print("      DNs:", dict(Counter(RX_PEX.search(t[0]).group(1) for t in pex)))
        for t in pex[:8]:
            print(f"      · {t[0][:70]!r} [{t[1]}] @{t[2]}")
    print(f"   nota '%%C<DN>'    : {len(diam)}")
    if diam:
        print("      DNs:", dict(Counter(RX_DIAM.search(t[0]).group(1) for t in diam)))
        for t in diam[:8]:
            print(f"      · {t[0][:90]!r} [{t[1]}]")

    inter = [t for t in textos if RX_INTERESSE.search(t[0]) and t not in pex and t not in diam]
    print(f"\n-- TEXTOS DE INTERESSE (PEX/prumada/descida/AF/AQ/ISOM): {len(inter)} — 25 primeiros")
    for t in inter[:25]:
        print(f"   · {t[0][:95]!r} [{t[1]}]")

    nums = [t for t in textos if RX_NUM.match(t[0])]
    print(f"\n-- TEXTOS PURAMENTE NUMERICOS (candidatos a cota): {len(nums)}")
    print("   valores mais comuns:",
          dict(Counter(t[0].strip() for t in nums).most_common(15)))

    dims = ent_por_tipo.get("DIMENSION", 0)
    print(f"\n-- COTAS (entidade DIMENSION): {dims}")
    if dims:
        vals = Counter()
        for e, _ in percorrer(msp, doc):
            if e.dxftype() == "DIMENSION":
                try:
                    vals[round(float(e.get_measurement()), 3)] += 1
                except Exception:
                    pass
        print("   medidas mais comuns:", dict(vals.most_common(15)))

    print("\n-- PAPERSPACE (a prancha pode estar no layout, nao no modelspace)")
    for nome in doc.layout_names():
        if nome == "Model":
            continue
        lay = doc.layout(nome)
        n = sum(1 for _ in lay)
        print(f"   layout {nome!r}: {n} entidades")


if __name__ == "__main__":
    main()
