# -*- coding: utf-8 -*-
"""PROBE das duas hipoteses para casar rotulo <DN>-PEX distante com o tubo.

Contexto: no script 22, casar por distancia pura travou em 69% de cobertura e,
ao afrouxar o raio, a precisao contra o gabarito PIOROU. Logo o mecanismo nao e
distancia. Duas hipoteses melhores:

  H1 LINHA DE CHAMADA — existe LEADER/MLEADER (ou linha curta em camada de
     anotacao) ligando o texto ao tubo. Se existir, e determinista.
  H2 ORIENTACAO DO TEXTO — o rotulo e escrito ALINHADO ao tubo que descreve.
     Entao o tubo certo nao e o mais proximo, e o mais proximo ENTRE OS PARALELOS
     a direcao do texto. Isso explicaria por que distancia pura erra: pega tubo
     vizinho perpendicular.

Uso: python 23_probe_chamada.py <arquivo.dxf>
"""
import sys, re, math, logging
from collections import Counter, defaultdict
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")

RX_DN = re.compile(r"\b(16|20|25|32)\s*-\s*PEX\b", re.I)
MAX_DEPTH = 6


def coletar_tudo(entidades, saco, depth=0):
    """Inventario cru: tipo de entidade x camada, e os rotulos com angulo."""
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT" and depth < MAX_DEPTH:
            try:
                coletar_tudo(e.virtual_entities(), saco, depth + 1)
            except Exception:
                pass
            continue
        ly = e.dxf.layer or ""
        saco["tipos"][t] += 1
        if t in ("LEADER", "MULTILEADER", "MLEADER"):
            saco["leaders"].append((t, ly))
        if t in ("TEXT", "MTEXT"):
            s = m22.texto_de(e)
            m = RX_DN.search(s)
            if not m:
                continue
            ang = None
            try:
                ang = float(e.dxf.rotation)
            except Exception:
                try:
                    ang = math.degrees(math.atan2(e.dxf.text_direction[1], e.dxf.text_direction[0]))
                except Exception:
                    ang = None
            try:
                ins = e.dxf.insert
                xy = (float(ins[0]), float(ins[1]))
            except Exception:
                xy = None
            saco["rotulos"].append({"dn": int(m.group(1)), "layer": ly, "ang": ang, "xy": xy})


def main():
    path = sys.argv[1]
    doc = ezdxf.readfile(path)
    saco = {"tipos": Counter(), "leaders": [], "rotulos": []}
    coletar_tudo(doc.modelspace(), saco)

    print(f"ARQUIVO: {path}\n")

    print("== H1: existe linha de chamada como entidade? ==")
    print(f"   LEADER/MULTILEADER encontrados: {len(saco['leaders'])}")
    if saco["leaders"]:
        for (t, ly), n in Counter(saco["leaders"]).most_common(10):
            print(f"     {t:14} {ly:40} {n:5}")
    else:
        print("     nenhum — H1 descartada como entidade propria.")

    print("\n== tipos de entidade no desenho (top 14) ==")
    for t, n in saco["tipos"].most_common(14):
        print(f"   {t:16} {n:7}")

    rot = saco["rotulos"]
    print(f"\n== H2: os rotulos tem angulo? ==")
    print(f"   rotulos <DN>-PEX: {len(rot)}")
    com = [r for r in rot if r["ang"] is not None]
    print(f"   com angulo lido: {len(com)}/{len(rot)}")
    if com:
        faixas = Counter()
        for r in com:
            a = r["ang"] % 180
            faixas[round(a / 15) * 15] += 1
        print("   distribuicao do angulo (mod 180, agrupado de 15 em 15):")
        for a, n in sorted(faixas.items()):
            print(f"     {a:5.0f} graus  {n:5}  {'#' * min(n, 50)}")
        horiz = sum(n for a, n in faixas.items() if a in (0, 180))
        print(f"   horizontais (0/180): {horiz}/{len(com)} = {100*horiz/len(com):.0f}%")
        print("   -> se quase tudo for 0, o angulo NAO discrimina e H2 morre.")


if __name__ == "__main__":
    main()
