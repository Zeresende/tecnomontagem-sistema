# -*- coding: utf-8 -*-
"""EXTRATOR ROTA 2 — DN pela NOTA GERAL (item 5.3 do Hederson, 10/08/2026).

Brooklyn e Peak nao tem rotulo `<DN>-PEX`. O DN vem de nota do tipo

    AF - PEX. %%C20mm - TUBO GUIA: %%C32mm
    AQ - PEX. %%C20mm - TUBO GUIA: %%C32mm
    AF - PEX. %%C25mm - TUBO GUIA: %%C40mm

A diferenca em relacao a rota 1 nao e so a notacao: **a nota declara o SISTEMA**
(AF ou AQ) junto com o diametro. Isso e uma restricao forte que o rotulo
`<DN>-PEX` nao tinha — geometria de agua fria so pode receber DN de nota AF.

Ou seja a rota 2 nao e "a mesma proximidade com outro regex". E proximidade
DENTRO DO SISTEMA, e o sistema ja esta na camada (HAF-TUB / HAQ-TUB). Restam
poucas notas cobrindo regioes grandes, que e o regime em que proximidade funciona.

Cuidados embutidos:
  - a nota traz DOIS diametros (o do PEX e o do TUBO GUIA). So o primeiro vale;
    o `TUBO GUIA: %%C32mm` e a camisa, nao entra no quantitativo de PEX.
  - textos de outros sistemas com diametro (`DRENO DO AR CONDICIONADO %%C25 - PVC`)
    sao descartados por exigir PEX/PERT no texto.
  - camadas com sufixo `-CAM` (camisa) entram na grade como opcao, para o
    gabarito decidir se sao percurso de PEX ou geometria duplicada.

Uso: python 34_dn_por_nota.py <obra>
"""
import sys, re, logging
from collections import defaultdict
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")
m25 = __import__("25_avaliar_dn")
m32 = __import__("32_teste_rolo")

MAX_DEPTH = 6
DNS = (16, 20, 25, 32)
# "AF - PEX. %%C20mm - TUBO GUIA: %%C32mm" -> sistema AF, DN 20 (o 1o diametro)
RX_NOTA = re.compile(r"\b(AF|AQ)\b[^%\\Ø]{0,24}(?:PE-?X|PE-?RT)[^%\\Ø]{0,12}"
                     r"(?:%%C|\\U\+00D8|Ø)\s*(\d{2,3})", re.I)
RX_TUBO = re.compile(r"H(AF|AQ)-TUB", re.I)
EXCL_LAYER = re.compile(r"LEG|REF|TAB|DET|PREVIS", re.I)
RX_CAM = re.compile(r"-CAM\b", re.I)


def coletar(entidades, notas, geo, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT":
            if depth < MAX_DEPTH:
                try:
                    coletar(e.virtual_entities(), notas, geo, depth + 1)
                except Exception:
                    pass
            continue
        ly = e.dxf.layer or ""
        if t in ("TEXT", "MTEXT"):
            s = " ".join(m22.texto_de(e).split())
            m = RX_NOTA.search(s)
            if not m:
                continue
            try:
                ins = e.dxf.insert
                notas.append({"sis": m.group(1).upper(), "dn": int(m.group(2)),
                              "xy": (float(ins[0]), float(ins[1])), "txt": s})
            except Exception:
                pass
            continue
        if t not in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            continue
        m = RX_TUBO.search(ly)
        if not m or EXCL_LAYER.search(ly):
            continue
        pts = m22.pontos_de(e)
        if len(pts) < 2:
            continue
        d = m22.compr(pts)
        if d > 0:
            geo.append({"sis": m.group(1).upper(), "pts": pts, "m": d,
                        "cam": bool(RX_CAM.search(ly)), "layer": ly})


def alvo_da_obra(obra, torre=None):
    """Mix da receita. Se `torre` vier, usa so a aba RAMAL daquela torre."""
    d = m32.coletar(obra)
    if not d:
        return {}, {}
    liq = defaultdict(float)
    for L in d["linhas"]:
        if torre and torre.upper() not in L["aba"].upper():
            continue
        liq[L["dn"]] += L["liq"]
    return m32.mix(liq), liq


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20251533"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    nome = tipos[0].name
    # o DXF pode ser de uma torre so (ex.: "TOA" = torre A)
    torre = None
    if re.search(r"\bTOA\b|TORRE\s*A|-A-", nome, re.I):
        torre = "TORRE A"
    elif re.search(r"\bTOB\b|TORRE\s*B|-B-", nome, re.I):
        torre = "TORRE B"

    print(f"OBRA {obra} | {nome}")
    doc = ezdxf.readfile(str(tipos[0]))
    notas, geo = [], []
    coletar(doc.modelspace(), notas, geo)

    alvo, liq = alvo_da_obra(obra, torre)
    alvo_tot, _ = alvo_da_obra(obra)
    print(f"notas de sistema: {len(notas)}   trechos de tubo: {len(geo)}")
    if torre:
        print(f"DXF e de {torre} -> alvo da aba RAMAL - {torre}")
    print("ALVO (receita): " + "  ".join(f"DN{k}={alvo.get(k,0):.1f}%" for k in DNS if alvo.get(k)))
    if torre:
        print("  (obra inteira: " + "  ".join(f"DN{k}={alvo_tot.get(k,0):.1f}%"
                                              for k in DNS if alvo_tot.get(k)) + ")")

    print("\n--- notas encontradas ---")
    agr = defaultdict(int)
    for n in notas:
        agr[(n["sis"], n["dn"])] += 1
    for (s, dn), q in sorted(agr.items()):
        print(f"  {s}  DN{dn:<3} x{q}")

    print("\n--- metragem por sistema ---")
    for cam in (False, True):
        for s in ("AF", "AQ"):
            v = sum(g["m"] for g in geo if g["sis"] == s and g["cam"] == cam)
            if v:
                print(f"  {s} {'camisa (-CAM)' if cam else 'tubo':16} {v:9.1f}")

    print("\n--- grade: proximidade DENTRO do sistema ---")
    print(f"{'camisa':>8} {'raio':>6} {'cobert':>8} {'erro':>7}   mix "
          + "/".join(str(x) for x in DNS))
    print("-" * 68)
    melhor = None
    for usar_cam in ("exclui", "inclui"):
        usar = [g for g in geo if usar_cam == "inclui" or not g["cam"]]
        total = sum(g["m"] for g in usar)
        if not total:
            continue
        for raio in (2, 5, 10, 25, 60, 1e9):
            res = defaultdict(float)
            cl = 0.0
            for g in usar:
                cands = [n for n in notas if n["sis"] == g["sis"]]
                if not cands:
                    continue
                best, dmin = None, float("inf")
                for n in cands:
                    dd = m22.dist_ponto_poly(n["xy"], g["pts"])
                    if dd < dmin:
                        best, dmin = n, dd
                if best and dmin <= raio:
                    res[best["dn"]] += g["m"]
                    cl += g["m"]
            mx = m25.mix(res)
            er = m25.erro(mx, alvo)
            rot = "sem limite" if raio > 1e8 else f"{raio:g}"
            print(f"{usar_cam:>8} {rot:>6} {100*cl/total:>7.1f}% {er:>7.1f}   "
                  + " ".join(f"{mx.get(dn,0):.0f}" for dn in DNS))
            if melhor is None or er < melhor[0]:
                melhor = (er, usar_cam, rot, 100 * cl / total, mx)

    if melhor:
        er, uc, rot, cob, mx = melhor
        print("\n" + "=" * 62)
        print(f"MELHOR: camisa={uc}  raio={rot}")
        print(f"  cobertura {cob:.1f}%   erro somado {er:.1f} p.p.")
        print("  mix   " + "  ".join(f"DN{dn}={mx.get(dn,0):5.1f}%" for dn in DNS))
        print("  alvo  " + "  ".join(f"DN{dn}={alvo.get(dn,0):5.1f}%" for dn in DNS))


if __name__ == "__main__":
    main()
