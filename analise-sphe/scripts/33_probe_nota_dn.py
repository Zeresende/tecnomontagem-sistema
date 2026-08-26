# -*- coding: utf-8 -*-
"""PROBE da SEGUNDA ROTA DE DN — a nota geral (item 5.3 do Hederson, 10/08/2026).

Perguntamos por que Brooklyn e Peak nao tem nenhum rotulo `<DN>-PEX`. Resposta:
"Em ambas as obras existe uma anotacao informando o diametro da tubulacao", com
print da Peak mostrando:

   TUBULACOES DE PEX CAMINHAM POR TUBOS GUIAS EMBUTIDOS NA LAJE
   AF - PEX. O25mm - TUBO GUIA: O40mm

Ou seja a SPHE usa DOIS padroes de codificacao, nao um:
  1. rotulo por trecho `<DN>-PEX`      -> Living, Edition, Pamaris (script 30);
  2. NOTA GERAL por sistema `O<DN>mm`  -> Brooklyn, Peak            (esta rota).

O `O` (diametro) e gravado como `%%C` no DXF — a mesma notacao que o script 18
procurava em 03/07. A busca velha nao estava errada: estava aplicada na obra errada.

Na rota 2 o DN nao e propriedade do trecho, e do SISTEMA (AF / AQ). Entao nao ha
casamento geometrico nenhum a fazer: basta ler a nota e medir metragem por sistema.

Uso: python 33_probe_nota_dn.py <obra>
"""
import sys, re, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")

MAX_DEPTH = 6
# %%C = simbolo de diametro no AutoCAD; \U+00D8 e a forma em MTEXT unicode
RX_DIAM = re.compile(r"(?:%%C|\\U\+00D8|Ø)\s*(\d{2,3})", re.I)
RX_INTERESSE = re.compile(r"PEX|PE-?RT|%%C|Ø|TUBO\s*GUIA|AGUA\s*(FRIA|QUENTE)|"
                          r"\bAF\b|\bAQ\b", re.I)
RX_TUBO_LAYER = re.compile(r"(HAF|HAQ|AF|AQ)[-_]?TUB|TUB.*(AF|AQ)", re.I)
EXCL_LAYER = re.compile(r"LEG|REF|TAB|DET|PREVIS", re.I)


def coletar(entidades, textos, geo, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT":
            if depth < MAX_DEPTH:
                try:
                    coletar(e.virtual_entities(), textos, geo, depth + 1)
                except Exception:
                    pass
            continue
        ly = e.dxf.layer or ""
        if t in ("TEXT", "MTEXT"):
            s = m22.texto_de(e)
            if s and RX_INTERESSE.search(s):
                try:
                    ins = e.dxf.insert
                    xy = (float(ins[0]), float(ins[1]))
                except Exception:
                    xy = (0.0, 0.0)
                textos.append({"txt": " ".join(s.split()), "layer": ly, "xy": xy})
            continue
        if t not in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            continue
        pts = m22.pontos_de(e)
        if len(pts) < 2:
            continue
        d = m22.compr(pts)
        if d > 0:
            geo.append({"layer": ly, "m": d})


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20251533"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    if not tipos:
        print(f"sem DXF de tipo em {d}")
        return
    print(f"OBRA {obra} | {tipos[0].name}\n")
    doc = ezdxf.readfile(str(tipos[0]))
    textos, geo = [], []
    coletar(doc.modelspace(), textos, geo)
    print(f"textos de interesse: {len(textos)}   entidades de geometria: {len(geo)}")

    print("\n--- 1. TEXTOS COM DIAMETRO (a nota que ele citou) ---")
    com_dn = [t for t in textos if RX_DIAM.search(t["txt"])]
    print(f"  {len(com_dn)} textos com marca de diametro")
    vistos = Counter(t["txt"] for t in com_dn)
    for txt, n in vistos.most_common(25):
        dns = RX_DIAM.findall(txt)
        print(f"  [{n:>3}x] DN={','.join(dns):<12} {txt[:96]}")

    print("\n--- 2. TEXTOS COM 'PEX' (contexto da nota) ---")
    pex = Counter(t["txt"] for t in textos if re.search(r"PEX", t["txt"], re.I))
    for txt, n in pex.most_common(15):
        print(f"  [{n:>3}x] {txt[:104]}")

    print("\n--- 3. CAMADAS DE TUBO (metragem por sistema) ---")
    mm = defaultdict(float)
    for g in geo:
        mm[g["layer"]] += g["m"]
    tub = {k: v for k, v in mm.items()
           if RX_TUBO_LAYER.search(k) and not EXCL_LAYER.search(k)}
    if not tub:
        print("  nenhuma camada casou o padrao de tubo; top 25 camadas por metragem:")
        tub = dict(sorted(mm.items(), key=lambda x: -x[1])[:25])
    tot = sum(tub.values())
    for k, v in sorted(tub.items(), key=lambda x: -x[1])[:25]:
        print(f"  {k.split('$0$')[-1]:44} {v:10.1f}  {100*v/tot if tot else 0:5.1f}%")
    print(f"  TOTAL {tot:.1f}")

    print("\n--- 4. AGRUPADO POR SISTEMA (AF x AQ) ---")
    sis = defaultdict(float)
    for k, v in tub.items():
        nome = k.upper()
        if re.search(r"HAQ|AQ", nome):
            sis["AQ"] += v
        elif re.search(r"HAF|AF", nome):
            sis["AF"] += v
        else:
            sis["?"] += v
    s = sum(sis.values())
    for k, v in sorted(sis.items(), key=lambda x: -x[1]):
        print(f"  {k:6} {v:10.1f}  {100*v/s if s else 0:5.1f}%")


if __name__ == "__main__":
    main()
