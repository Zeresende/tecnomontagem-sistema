# -*- coding: utf-8 -*-
"""EXTRATOR DE RAMAL POR DN — a partir do rotulo <DN>-PEX escrito no desenho.

Base: resposta 4.1 do Hederson (06/08/2026). O DN do ramal NAO e tacito: esta
escrito na planta como texto "16-PEX"/"20-PEX"/"25-PEX".

CORRECAO 18/08/2026 — a frase que estava aqui ("o script 18 procurava a notacao
%%C, que a SPHE nao usa aqui") ESTAVA ERRADA, e custou caro. A SPHE usa `%%C`, e
usa justamente onde o rotulo mais importa: na prumada do shaft (`F- %%C25-PEX`,
`A.F. - 12x%%C25-PEX`). O `\b` do regex exigia fronteira de palavra, e entre o `C`
de `%%C` e o digito nao ha fronteira — entao esses rotulos NUNCA casaram. Achado
ao investigar o balde "sem DN" do vertical (script 58).

Casamento: o rotulo quase sempre esta NA MESMA CAMADA da geometria que descreve
(probe 21: 84 de 120 rotulos da TIPA em HAF-TUB-___-EXO-TET). Entao a atribuicao
e feita em duas etapas, da mais segura para a menos:
  1. rotulo e geometria na MESMA camada, pelo mais proximo;
  2. sobra de geometria -> rotulo mais proximo de qualquer camada de tubo,
     dentro de RAIO_MAX.
O que nao casar fica em NAO-CLASSIFICADO — nunca e chutado para um DN.

Uso: python 22_ramal_por_dn.py <arquivo.dxf> [mais.dxf ...]
     python 22_ramal_por_dn.py --dir <pasta_com_dxf>
"""
import sys, re, math, logging, glob, os
from collections import defaultdict
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)

RX_DN = re.compile(r"(?:%%[cC]|Ø|\b)(16|20|25|32)\s*-\s*PEX\b", re.I)
TUBO_LAYER = re.compile(r"H(AF|AQ)-TUB", re.I)
EXCL_LAYER = re.compile(r"LEG|REF|TAB|DET|PREVIS", re.I)
MAX_DEPTH = 6
RAIO_MAX = 8.0          # unidades de desenho; alem disso nao atribui
DN_VALIDOS = (16, 20, 25, 32)


def texto_de(e):
    try:
        if e.dxftype() == "MTEXT":
            return re.sub(r"\\[A-Za-z][^;]*;|[{}]", "", e.text or "")
        return e.dxf.text or ""
    except Exception:
        return ""


def pontos_de(e):
    """Lista de vertices (x, y) da entidade, ou [] se nao for geometria linear."""
    t = e.dxftype()
    try:
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            return [(a[0], a[1]), (b[0], b[1])]
        if t == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            if e.closed and len(pts) > 2:
                pts.append(pts[0])
            return pts
        if t == "POLYLINE":
            return [(v.dxf.location[0], v.dxf.location[1]) for v in e.vertices]
        if t == "ARC":
            c, r = e.dxf.center, e.dxf.radius
            a0 = math.radians(e.dxf.start_angle)
            a1 = math.radians(e.dxf.end_angle)
            if a1 < a0:
                a1 += 2 * math.pi
            n = max(2, int((a1 - a0) / 0.35) + 1)
            return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n),
                     c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    except Exception:
        pass
    return []


def compr(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def dist_ponto_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    den = dx * dx + dy * dy
    if den == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / den))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def dist_ponto_poly(p, pts):
    return min(dist_ponto_seg(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def coletar(entidades, geoms, rotulos, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT" and depth < MAX_DEPTH:
            try:
                coletar(e.virtual_entities(), geoms, rotulos, depth + 1)
            except Exception:
                pass
            continue
        ly = e.dxf.layer or ""
        if t in ("TEXT", "MTEXT"):
            m = RX_DN.search(texto_de(e))
            if not m:
                continue
            try:
                ins = e.dxf.insert
                rotulos.append({"dn": int(m.group(1)), "layer": ly,
                                "xy": (float(ins[0]), float(ins[1]))})
            except Exception:
                pass
            continue
        if t in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            m = TUBO_LAYER.search(ly)
            if not m or EXCL_LAYER.search(ly):
                continue
            pts = pontos_de(e)
            if len(pts) < 2:
                continue
            d = compr(pts)
            if d <= 0:
                continue
            geoms.append({"tipo": m.group(1).upper(), "layer": ly, "pts": pts, "m": d})


def atribuir(geoms, rotulos):
    """Devolve (resultado, stats). Duas etapas: mesma camada, depois raio."""
    por_camada = defaultdict(list)
    for r in rotulos:
        por_camada[r["layer"]].append(r)

    res = defaultdict(float)          # (AF/AQ, dn) -> metros
    stats = {"mesma_camada": 0.0, "por_raio": 0.0, "sem_rotulo": 0.0}
    sobra = []

    for g in geoms:
        cands = por_camada.get(g["layer"])
        if cands:
            r = min(cands, key=lambda r: dist_ponto_poly(r["xy"], g["pts"]))
            res[(g["tipo"], r["dn"])] += g["m"]
            stats["mesma_camada"] += g["m"]
        else:
            sobra.append(g)

    for g in sobra:
        melhor, dmin = None, float("inf")
        for r in rotulos:
            d = dist_ponto_poly(r["xy"], g["pts"])
            if d < dmin:
                melhor, dmin = r, d
        if melhor and dmin <= RAIO_MAX:
            res[(g["tipo"], melhor["dn"])] += g["m"]
            stats["por_raio"] += g["m"]
        else:
            stats["sem_rotulo"] += g["m"]
    return res, stats


def processar(path):
    doc = ezdxf.readfile(path)
    geoms, rotulos = [], []
    coletar(doc.modelspace(), geoms, rotulos)
    if not geoms:
        return None

    # escala: mesma heuristica do script 18 (mediana do comprimento dos trechos)
    todos = sorted(g["m"] for g in geoms)
    med = todos[len(todos) // 2]
    fator = 1.0 if med < 20 else (100.0 if med < 2000 else 1000.0)

    res, stats = atribuir(geoms, rotulos)
    total = sum(g["m"] for g in geoms)
    return {"res": res, "stats": stats, "total": total, "fator": fator,
            "n_rot": len(rotulos), "n_geo": len(geoms)}


def imprimir(nome, d):
    f = d["fator"]
    tot = d["total"] / f
    print("=" * 78)
    print(f"{nome}")
    print(f"  rotulos <DN>-PEX: {d['n_rot']}  |  trechos de tubo: {d['n_geo']}  |  escala /{f:g}")
    print(f"  {'tipo':5} {'DN':>5} {'metros':>12}")
    for (tipo, dn) in sorted(d["res"], key=lambda k: (k[0], k[1])):
        print(f"  {tipo:5} {dn:>5} {d['res'][(tipo, dn)] / f:12.1f}")
    print(f"  {'-'*30}")
    print(f"  {'TOTAL classificado':23} {sum(d['res'].values()) / f:12.1f} m")
    s = d["stats"]
    for k, rot in (("mesma_camada", "casado na mesma camada"),
                   ("por_raio", f"casado por raio (<={RAIO_MAX:g})"),
                   ("sem_rotulo", "NAO-CLASSIFICADO")):
        v = s[k] / f
        pct = 100 * s[k] / d["total"] if d["total"] else 0
        print(f"    {rot:32} {v:9.1f} m  {pct:5.1f}%")
    print(f"  cobertura classificada: {100*(s['mesma_camada']+s['por_raio'])/d['total']:.1f}%  "
          f"(script 18 chegava a 21%)")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == "--dir":
        arquivos = sorted(glob.glob(os.path.join(args[1], "*.dxf")))
    else:
        arquivos = args
    for path in arquivos:
        try:
            d = processar(path)
        except Exception as ex:
            print(f"{os.path.basename(path)}: ERRO {ex}")
            continue
        if d is None:
            print(f"{os.path.basename(path)}: sem geometria de tubo")
            continue
        imprimir(os.path.basename(path), d)


if __name__ == "__main__":
    main()
