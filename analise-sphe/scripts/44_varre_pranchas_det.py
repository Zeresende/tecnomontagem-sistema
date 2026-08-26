# -*- coding: utf-8 -*-
"""VARREDURA DAS PRANCHAS DE DETALHE DAS 5 OBRAS (11/08/2026).

Motivo: o anexo do item 12.1 (uma prancha DET do Peak, torre B) trouxe o que faltava —
vistas/cortes com a DESCIDA VERTICAL desenhada e 109 rotulos `<DN>-PEX` numa obra onde
tinhamos afirmado ao Hederson que so existia a nota geral.

Descoberta imediata: as pranchas DET das 5 obras JA ESTAVAM na pasta, ja convertidas.
Os extratores (scripts 22/25/30) filtram o nome por `PVTIPO|TIPO|TIP`, entao nunca
leram nenhuma delas. Este script mede o que ha em cada uma antes de decidir o que
reprocessar.

Nao mede metragem de ramal (isso e trabalho do extrator): conta sinal.

Uso: python 44_varre_pranchas_det.py [padrao_de_nome]
"""
import sys, re, logging
from collections import Counter
from pathlib import Path
import ezdxf
from ezdxf.math import Vec3

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

BASE = Path(__file__).resolve().parent / "dxf"
MAX_DEPTH = 6
RX_PEX = re.compile(r"(\d{2})\s*-\s*PEX", re.I)
RX_DIAM = re.compile(r"(?:%%C|\\U\+00D8|Ø)\s*(\d{2,3})", re.I)
RX_VISTA = re.compile(r"^(VISTA|DETALHE DO SHAFT|ISOM|AMPLIA|CORTE)", re.I)
RX_TUBO = re.compile(r"HAF-TUB|HAQ-TUB|PRU-F|PRU-rsb|PEX", re.I)
RX_DET = re.compile(r"DET|DTIP|AMPL|ISOM", re.I)


def texto_de(e):
    t = e.dxftype()
    if t == "MTEXT":
        return e.plain_text()
    if t in ("TEXT", "ATTRIB"):
        return str(e.dxf.text)
    return ""


def percorrer(layout, doc, prof=0):
    for e in layout:
        if e.dxftype() == "INSERT":
            for att in getattr(e, "attribs", []):
                yield att, str(att.dxf.layer)
            if prof < MAX_DEPTH:
                try:
                    yield from percorrer(doc.blocks[e.dxf.name], doc, prof + 1)
                except Exception:
                    pass
        else:
            yield e, str(getattr(e.dxf, "layer", "?"))


def vertical(e):
    """Metragem vertical (>=20 cm) da entidade linear."""
    t = e.dxftype()
    try:
        if t == "LINE":
            pares = [(Vec3(e.dxf.start), Vec3(e.dxf.end))]
        elif t == "LWPOLYLINE":
            p = [Vec3(x[0], x[1], 0) for x in e.get_points("xy")]
            pares = [(p[i], p[i + 1]) for i in range(len(p) - 1)]
        elif t == "POLYLINE":
            p = [Vec3(v.dxf.location) for v in e.vertices]
            pares = [(p[i], p[i + 1]) for i in range(len(p) - 1)]
        else:
            return 0.0
    except Exception:
        return 0.0
    total = 0.0
    for a, b in pares:
        d = b - a
        n = d.magnitude
        if n >= 0.20 and abs(d.y) / n > 0.985:
            total += n
    return total


def varrer(caminho):
    doc = ezdxf.readfile(str(caminho))
    pex, diam, vistas = Counter(), Counter(), Counter()
    vert = 0.0
    for e, cam in percorrer(doc.modelspace(), doc):
        t = e.dxftype()
        if t in ("TEXT", "MTEXT", "ATTRIB"):
            s = texto_de(e).strip()
            if not s:
                continue
            m = RX_PEX.search(s)
            if m:
                pex[m.group(1)] += 1
            m = RX_DIAM.search(s)
            if m:
                diam[m.group(1)] += 1
            if RX_VISTA.match(s) and len(s) < 60:
                vistas[s] += 1
        elif RX_TUBO.search(cam):
            vert += vertical(e)
    return pex, diam, vistas, vert


def main():
    padrao = sys.argv[1] if len(sys.argv) > 1 else None
    alvos = []
    for pasta in sorted(BASE.iterdir()):
        if not pasta.is_dir():
            continue
        for f in sorted(pasta.glob("*.dxf")):
            if padrao and padrao.lower() not in f.name.lower():
                continue
            if not padrao and not RX_DET.search(f.name):
                continue
            alvos.append(f)

    for f in alvos:
        mb = f.stat().st_size / 1e6
        print(f"\n== {f.parent.name} / {f.name}  ({mb:.0f} MB)", flush=True)
        try:
            pex, diam, vistas, vert = varrer(f)
        except Exception as erro:
            print(f"   FALHOU: {erro}")
            continue
        print(f"   rotulos <DN>-PEX : {sum(pex.values()):>5}  {dict(pex)}")
        print(f"   notas %%C<DN>    : {sum(diam.values()):>5}  {dict(diam)}")
        print(f"   vistas/cortes    : {sum(vistas.values()):>5}  "
              f"{list(vistas)[:8]}")
        print(f"   tubo VERTICAL >=0,20 m: {vert:>8.1f} m")


if __name__ == "__main__":
    main()
