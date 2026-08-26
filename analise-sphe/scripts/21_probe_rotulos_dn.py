# -*- coding: utf-8 -*-
"""PROBE: como os rotulos <DN>-PEX estao gravados no DXF da SPHE.
Descoberta de 06/08/2026 (item 4.1 do Hederson): o DN do ramal ESTA escrito no
desenho como texto "25-PEX"/"20-PEX"/"16-PEX", nao como %%C. O script 18 procurava
%%C e por isso concluiu, errado, que o DN era tacito.
Este probe so inventaria: tipo de entidade, camada, profundidade de bloco e escala.
Uso: python 21_probe_rotulos_dn.py <caminho.dxf>
"""
import sys, re, logging
from collections import Counter, defaultdict
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

RX_DN = re.compile(r"\b(16|20|25|32)\s*-\s*PEX\b", re.I)
MAX_DEPTH = 6


def texto(e):
    """Texto limpo de TEXT/MTEXT (remove formatacao inline do MTEXT)."""
    try:
        if e.dxftype() == "MTEXT":
            return re.sub(r"\\[A-Za-z][^;]*;|[{}]", "", e.text or "")
        return e.dxf.text or ""
    except Exception:
        return ""


def varrer(entidades, achados, tipos, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT" and depth < MAX_DEPTH:
            try:
                varrer(e.virtual_entities(), achados, tipos, depth + 1)
            except Exception:
                pass
            continue
        if t not in ("TEXT", "MTEXT"):
            continue
        s = texto(e)
        m = RX_DN.search(s)
        if not m:
            continue
        try:
            p = e.dxf.insert
            xy = (float(p[0]), float(p[1]))
        except Exception:
            xy = None
        achados.append({"dn": int(m.group(1)), "layer": e.dxf.layer or "",
                        "tipo": t, "depth": depth, "xy": xy, "txt": s.strip()})
        tipos[(t, depth)] += 1


def main():
    path = sys.argv[1]
    doc = ezdxf.readfile(path)
    achados, tipos = [], Counter()
    varrer(doc.modelspace(), achados, tipos)

    print(f"ARQUIVO: {path}")
    print(f"rotulos <DN>-PEX encontrados: {len(achados)}\n")

    print("-- por DN --")
    for dn, n in sorted(Counter(a["dn"] for a in achados).items()):
        print(f"   DN{dn:<3} {n:5}")

    print("\n-- por camada --")
    for ly, n in Counter(a["layer"] for a in achados).most_common(15):
        print(f"   {ly:40} {n:5}")

    print("\n-- por tipo/profundidade de bloco --")
    for (t, d), n in sorted(tipos.items()):
        print(f"   {t:6} depth={d}  {n:5}")

    com_xy = [a for a in achados if a["xy"]]
    print(f"\ncom coordenada utilizavel: {len(com_xy)}/{len(achados)}")
    if com_xy:
        xs = [a["xy"][0] for a in com_xy]
        ys = [a["xy"][1] for a in com_xy]
        print(f"   extensao X: {min(xs):.1f} .. {max(xs):.1f}")
        print(f"   extensao Y: {min(ys):.1f} .. {max(ys):.1f}")

    print("\n-- amostra de texto bruto --")
    vistos = set()
    for a in achados:
        k = a["txt"][:40]
        if k not in vistos:
            vistos.add(k)
            print(f"   DN{a['dn']:<3} [{a['layer']}] {k!r}")
        if len(vistos) >= 12:
            break

    # camadas de tubo, para saber a quem colar o rotulo
    print("\n-- camadas de geometria de tubo (HAF/HAQ-TUB) --")
    lay = Counter()

    def geo(ents, depth=0):
        for e in ents:
            if e.dxftype() == "INSERT" and depth < MAX_DEPTH:
                try:
                    geo(e.virtual_entities(), depth + 1)
                except Exception:
                    pass
            elif e.dxftype() in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
                ly = e.dxf.layer or ""
                if re.search(r"H(AF|AQ)-TUB", ly, re.I):
                    lay[ly] += 1

    geo(doc.modelspace())
    for ly, n in lay.most_common(20):
        print(f"   {ly:40} {n:5}")


if __name__ == "__main__":
    main()
