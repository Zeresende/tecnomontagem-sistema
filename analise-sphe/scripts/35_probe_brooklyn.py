# -*- coding: utf-8 -*-
"""PROBE do Brooklyn — checa a premissa que usamos na pergunta 5.3.

O probe 33 achou no Brooklyn textos `20 - PEX` (30x), `25 - PEX` (4x) e
`32 - PEX` (2x), alem da nota geral. Isso contradiz o que AFIRMAMOS ao Hederson
no item 5.3 ("nas obras Brooklyn e Peak nao existe nenhum rotulo -PEX").

Este script confere duas coisas antes de qualquer conclusao:
  1. o regex de rotulo da rota 1 (`<DN>-PEX`, que aceita espacos) casa mesmo
     nesses textos? quantos rotulos existem, e de que DN?
  2. quais sao as camadas de tubo do Brooklyn? o probe 33 so achou 10,3 m em
     HAF-TUB, o que indica nomenclatura de camada diferente das outras obras.

Uso: python 35_probe_brooklyn.py [obra]
"""
import sys, re, logging
from collections import Counter, defaultdict
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")

MAX_DEPTH = 6
RX_DN = m22.RX_DN          # exatamente o regex da rota 1, sem adaptacao
RX_PEX = re.compile(r"PE-?X|PE-?RT", re.I)


def coletar(entidades, rotulos, outros_pex, camadas, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT":
            if depth < MAX_DEPTH:
                try:
                    coletar(e.virtual_entities(), rotulos, outros_pex, camadas, depth + 1)
                except Exception:
                    pass
            continue
        ly = e.dxf.layer or ""
        if t in ("TEXT", "MTEXT"):
            s = " ".join(m22.texto_de(e).split())
            m = RX_DN.search(s)
            if m:
                try:
                    ins = e.dxf.insert
                    xy = (float(ins[0]), float(ins[1]))
                except Exception:
                    xy = (0.0, 0.0)
                rotulos.append({"dn": int(m.group(1)), "layer": ly, "txt": s, "xy": xy})
            elif RX_PEX.search(s):
                outros_pex.append(s)
            continue
        if t not in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            continue
        pts = m22.pontos_de(e)
        if len(pts) < 2:
            continue
        d = m22.compr(pts)
        if d > 0:
            camadas[ly.split("$0$")[-1]] += d


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20251430"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    print(f"OBRA {obra} | {tipos[0].name}")
    doc = ezdxf.readfile(str(tipos[0]))
    rotulos, outros, camadas = [], [], defaultdict(float)
    coletar(doc.modelspace(), rotulos, outros, camadas)

    print(f"\n--- 1. ROTULOS <DN>-PEX pelo regex da rota 1 ---")
    print(f"  total: {len(rotulos)}")
    for dn, n in sorted(Counter(r["dn"] for r in rotulos).items()):
        print(f"    DN{dn:<3} {n:>5}")
    print("  textos distintos que casaram:")
    for txt, n in Counter(r["txt"] for r in rotulos).most_common(12):
        print(f"    [{n:>3}x] {txt[:80]}")
    print("  camadas dos rotulos:")
    for ly, n in Counter(r["layer"].split("$0$")[-1] for r in rotulos).most_common(8):
        print(f"    {ly:44} {n:>5}")

    print(f"\n--- 2. CAMADAS COM GEOMETRIA (top 30 por metragem) ---")
    tot = sum(camadas.values())
    print(f"  camadas com geometria: {len(camadas)}   metragem total {tot:.1f}")
    for ly, v in sorted(camadas.items(), key=lambda x: -x[1])[:30]:
        print(f"    {ly:48} {v:11.1f}  {100*v/tot if tot else 0:5.1f}%")

    print(f"\n--- 3. camadas que PARECEM tubo de agua ---")
    alvo = re.compile(r"TUB|PEX|PERT|HAF|HAQ|\bAF\b|\bAQ\b", re.I)
    sel = {k: v for k, v in camadas.items() if alvo.search(k)}
    for ly, v in sorted(sel.items(), key=lambda x: -x[1])[:20]:
        print(f"    {ly:48} {v:11.1f}")
    print(f"    soma {sum(sel.values()):.1f}")


if __name__ == "__main__":
    main()
