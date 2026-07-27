# -*- coding: utf-8 -*-
"""Extrai quantitativo de um DXF: metros por layer e por DN (proximidade %%C).

Reusa as licoes M07/FPM/Joao Dias:
- geometria mora DENTRO de blocos -> virtual_entities recursivo (depth 6)
- DN nos textos no formato %%C<num> (Ø) -> classifica por proximidade
- detecta unidade pela mediana do comprimento dos LINEs

Uso: python 03_extrair_dxf.py <COD_OBRA> [--tipo|--det|--all]
Procura DXF em _analise/dxf/<COD_OBRA>/. Default: arquivos TIPO/TIP/PVTIPO.
"""
import math, sys, re, argparse, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)  # silencia avisos ACAD_PROXY_OBJECT
BASE = Path(__file__).resolve().parent
DXF_DIR = BASE / "dxf"
SAIDA = BASE / "saida"; SAIDA.mkdir(exist_ok=True)
MAX_DEPTH = 6
DN_RE = re.compile(r"%%[Cc]\s*(\d{1,3})")

def comp_entidade(e):
    t = e.dxftype()
    try:
        if t == "LINE":
            return e.dxf.start.distance(e.dxf.end), e.dxf.start, e.dxf.end
        if t == "LWPOLYLINE":
            pts = list(e.get_points("xy"))
            d = sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))
            if e.closed and len(pts) > 2:
                d += math.dist(pts[-1], pts[0])
            return d, pts[0], pts[-1]
        if t == "POLYLINE":
            pts = [v.dxf.location for v in e.vertices]
            d = sum(pts[i].distance(pts[i+1]) for i in range(len(pts)-1))
            return d, pts[0], pts[-1]
        if t == "ARC":
            ang = (e.dxf.end_angle - e.dxf.start_angle) % 360
            return e.dxf.radius * math.radians(ang), e.dxf.center, e.dxf.center
    except Exception:
        pass
    return 0.0, None, None

def midpoint(p1, p2):
    try:
        return ((p1[0]+p2[0])/2.0, (p1[1]+p2[1])/2.0)
    except Exception:
        return None

def coletar(entidades, segs, textos_dn, blocos, depth=0, ins_point=None):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT" and depth < MAX_DEPTH:
            name = e.dxf.name
            blocos[re.sub(r"-flat-\d+$", "", name)] += 1
            try:
                coletar(e.virtual_entities(), segs, textos_dn, blocos, depth+1)
            except Exception:
                pass
        elif t in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            d, a, b = comp_entidade(e)
            if d > 0:
                mp = midpoint(a, b) if (a is not None and b is not None) else None
                segs.append((e.dxf.layer, d, mp))
        elif t in ("TEXT", "MTEXT"):
            try:
                raw = e.dxf.text if t == "TEXT" else e.text
            except Exception:
                raw = ""
            for m in DN_RE.finditer(raw or ""):
                try:
                    ins = e.dxf.insert
                    textos_dn.append((int(m.group(1)), (ins[0], ins[1])))
                except Exception:
                    pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obra")
    ap.add_argument("--all", action="store_true", help="processa todos os dxf da obra")
    ap.add_argument("--filtro", default="TIPO|TIP|PVTIPO", help="regex no nome do arquivo")
    ap.add_argument("--hid", default=None, help="regex p/ isolar layers hidraulicos (ex: HID|-HD-|PRUM|PEX)")
    ap.add_argument("--dir", default=None, help="diretorio absoluto de DXF (sobrepoe DXF_DIR/obra)")
    args = ap.parse_args()
    hid_rx = re.compile(args.hid, re.I) if args.hid else None

    d = Path(args.dir) if args.dir else DXF_DIR / args.obra
    dxfs = sorted(d.glob("*.dxf")) + sorted(d.glob("*.DXF"))
    if not args.all:
        rx = re.compile(args.filtro, re.I)
        sel = [p for p in dxfs if rx.search(p.name)]
        dxfs = sel or dxfs
    if not dxfs:
        print("Nenhum DXF em", d); return

    for path in dxfs:
        print("=" * 88)
        print("ARQUIVO:", path.name, f"({path.stat().st_size/1e6:.1f} MB)")
        doc = ezdxf.readfile(str(path))
        msp = doc.modelspace()
        segs, textos_dn, blocos = [], [], Counter()
        coletar(msp, segs, textos_dn, blocos)
        if hid_rx:
            antes = len(segs)
            segs = [s for s in segs if hid_rx.search(s[0] or "")]
            print(f"  [filtro hidraulico '{args.hid}': {antes} -> {len(segs)} segs]", flush=True)

        comps = sorted(d for _, d, _ in segs)
        if not comps:
            print("  sem geometria linear"); continue
        n = len(comps); med = comps[n//2]
        unidade = "METROS" if med < 20 else ("CENTIMETROS" if med < 2000 else "MILIMETROS")
        fator = {"METROS": 1.0, "CENTIMETROS": 100.0, "MILIMETROS": 1000.0}[unidade]
        raio = 2.0 * fator  # 2 metros no espaco do desenho

        por_layer = defaultdict(float)
        for layer, dist, _ in segs:
            por_layer[layer] += dist

        # classificacao por DN via proximidade (grade espacial: O(n) em vez de O(n*m))
        por_dn = defaultdict(float); nao_class = 0.0
        cell = raio
        grid = defaultdict(list)
        for dn, (tx, ty) in textos_dn:
            grid[(int(tx//cell), int(ty//cell))].append((dn, tx, ty))
        for layer, dist, mp in segs:
            if mp is None or not textos_dn:
                nao_class += dist; continue
            cx, cy = int(mp[0]//cell), int(mp[1]//cell)
            best, bd = None, raio
            for gx in (cx-1, cx, cx+1):
                for gy in (cy-1, cy, cy+1):
                    for dn, tx, ty in grid.get((gx, gy), ()):
                        dd = math.hypot(mp[0]-tx, mp[1]-ty)
                        if dd < bd:
                            bd, best = dd, dn
            if best is None:
                nao_class += dist
            else:
                por_dn[best] += dist

        total = sum(comps)
        out = []
        def w(s): out.append(s); print(s, flush=True)
        w(f"OBRA {args.obra} | ARQUIVO {path.name} ({path.stat().st_size/1e6:.1f} MB)")
        w(f"  unidade={unidade} (mediana LINE={med:.2f}) | n_segs={n} | textos %%C={len(textos_dn)}")
        w(f"  TOTAL bruto={total/fator:.1f} m  |  classificado por DN={sum(por_dn.values())/fator:.1f} m "
          f"({100*sum(por_dn.values())/total:.0f}%)")
        w("  --- metros por DN (proximidade %%C, raio 2m) ---")
        for dn in sorted(por_dn, key=lambda k: -por_dn[k]):
            w(f"     DN {dn:>4} : {por_dn[dn]/fator:8.1f} m")
        w(f"     (nao classificado: {nao_class/fator:.1f} m)")
        w("  --- top 15 layers (m) ---")
        for layer, dist in sorted(por_layer.items(), key=lambda kv: -kv[1])[:15]:
            w(f"     {layer:34s} {dist/fator:8.1f}")
        w("  --- top 15 blocos ---")
        for b, c in blocos.most_common(15):
            w(f"     {b:34s} {c:5d}")
        (SAIDA / f"{args.obra}_{path.stem}.txt").write_text("\n".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
