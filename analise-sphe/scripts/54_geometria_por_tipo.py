# -*- coding: utf-8 -*-
"""54 — Geometria de tubo por TIPO DE ENTIDADE + teste de proximidade do rotulo de DN.

Nasceu em 13/08/2026, na rodada 2 do piloto HM89. A Ka reportava 4,3 m de agua quente
onde o 53 media 11,2. A diferenca nao era rotulagem: 61,5% da quente e ARC, e o leitor
dela percorre so LINE/LWPOLYLINE. Na fria o mesmo buraco vale 135,0 m (17,2%).

Uso:
    python 54_geometria_por_tipo.py <arquivo.dxf>

Saida:
    1. metros por (sistema, tipo de entidade) — alvo de validacao de qualquer leitor novo
    2. inventario de rotulo <DN>-MATERIAL por camada
    3. o que a atribuicao por proximidade faria com cada sistema (e de que camada vem o
       rotulo vencedor) — expoe contaminacao entre sistemas
"""
import sys, math, re, logging
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding="utf-8")
logging.disable(logging.CRITICAL)
import ezdxf

SISTEMAS = ("HAF", "HAQ", "HAP", "HDR", "HES", "HGC", "HIN")
ROTULO = re.compile(r"\b(\d{2,3})\s*[-–]\s*(PEX|PPR|CPVC|PVC)\b", re.I)

limpa = lambda n: re.split(r"\$0\$|\|", n)[-1]
prefixo = lambda lay: re.split(r"[-_]", limpa(lay))[0].upper()


def comprimento(e):
    """Comprimento em unidade de desenho. Cobre ARC e CIRCLE de proposito."""
    t = e.dxftype()
    try:
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            return math.dist((a.x, a.y), (b.x, b.y))
        if t == "LWPOLYLINE":
            # NAO somar o segmento de fechamento: polilinha fechada em camada de tubo e
            # simbolo, nao cano (cano nao faz laco). Corrigido em 13/08 com a Ka.
            p = [(x[0], x[1]) for x in e.get_points()]
            return sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1))
        if t == "POLYLINE":
            p = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            return sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1))
        if t == "ARC":
            # O arco do DXF e SEMPRE anti-horario de start_angle para end_angle. Com
            # abs(a1-a0) o arco que cruza o zero (a1 < a0) sai pelo complemento: 350 -> 10
            # daria 340 graus em vez de 20. Na HM89 isso inflava a fria em 80,7 m.
            return math.radians((e.dxf.end_angle - e.dxf.start_angle) % 360.0) * e.dxf.radius
        if t == "CIRCLE":
            return 2 * math.pi * e.dxf.radius
    except Exception:
        return 0.0
    return 0.0


def segmentos(e):
    """Pontos medios + comprimento, para o teste de proximidade."""
    t = e.dxftype()
    try:
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            pts = [(a.x, a.y), (b.x, b.y)]
        elif t == "LWPOLYLINE":
            pts = [(x[0], x[1]) for x in e.get_points()]
        elif t == "POLYLINE":
            pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        elif t == "ARC":
            c, r = e.dxf.center, e.dxf.radius
            a0, a1 = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
            am = (a0 + a1) / 2
            return [(c.x + r * math.cos(am), c.y + r * math.sin(am), comprimento(e))]
        else:
            return []
    except Exception:
        return []
    saida = []
    for i in range(len(pts) - 1):
        d = math.dist(pts[i], pts[i + 1])
        if d > 0:
            saida.append(((pts[i][0] + pts[i + 1][0]) / 2,
                          (pts[i][1] + pts[i + 1][1]) / 2, d))
    return saida


def main(caminho):
    doc = ezdxf.readfile(caminho)
    por_tipo = defaultdict(float)
    n_tipo = defaultdict(int)
    rotulos = []
    geo = defaultdict(list)

    def varre(cont, prof=0):
        for e in cont:
            if e.dxftype() == "INSERT" and prof < 6:
                try:
                    varre(e.virtual_entities(), prof + 1)
                except Exception:
                    pass
                continue
            lay = limpa(e.dxf.layer)
            if e.dxftype() in ("TEXT", "MTEXT"):
                txt = str(e.dxf.text if e.dxftype() == "TEXT" else e.text)
                m = ROTULO.search(txt)
                if m:
                    try:
                        p = e.dxf.insert
                        rotulos.append((p.x, p.y, m.group(1), m.group(2).upper(), lay))
                    except Exception:
                        pass
                continue
            p = prefixo(lay)
            if p in SISTEMAS and "TUB" in lay.upper():
                por_tipo[(p, e.dxftype())] += comprimento(e)
                n_tipo[(p, e.dxftype())] += 1
                geo[p].extend(segmentos(e))

    varre(doc.modelspace())

    print("=" * 78)
    print("1. METROS POR SISTEMA E TIPO DE ENTIDADE  (so camadas *TUB*)")
    print("=" * 78)
    tot = defaultdict(float)
    for (p, t), v in por_tipo.items():
        tot[p] += v
    print(f"{'sist':6} {'tipo':13} {'metros':>10} {'ent':>7} {'% sist':>9}")
    for (p, t), v in sorted(por_tipo.items(), key=lambda x: (x[0][0], -x[1])):
        if v <= 0:
            continue
        print(f"{p:6} {t:13} {v:10.2f} {n_tipo[(p, t)]:7d} {100 * v / tot[p]:8.1f}%")
    print()
    for p in sorted(tot):
        print(f"  {p} TOTAL: {tot[p]:.1f} m")

    print()
    print("=" * 78)
    print(f"2. ROTULOS <DN>-MATERIAL: {len(rotulos)}")
    print("=" * 78)
    for lay, q in Counter(r[4] for r in rotulos).most_common():
        print(f"  {lay[:44]:44} {q:5d}")
    for p in ("HAQ", "HAF"):
        q = sum(1 for r in rotulos if r[4].upper().startswith(p))
        print(f"  -> em camada {p}: {q}")

    print()
    print("=" * 78)
    print("3. O QUE A PROXIMIDADE FARIA (rotulo mais proximo de cada segmento)")
    print("=" * 78)
    if not rotulos:
        print("  sem rotulo — nada a testar")
        return
    for p in sorted(geo):
        segs = geo[p]
        if not segs:
            continue
        por_dn = defaultdict(float)
        origem = Counter()
        dists = []
        for x, y, d in segs:
            melhor, dmin = None, float("inf")
            for rx, ry, dn, mat, lay in rotulos:
                dd = math.dist((x, y), (rx, ry))
                if dd < dmin:
                    dmin, melhor = dd, (dn, mat, lay)
            dists.append(dmin)
            por_dn[f"{melhor[0]}-{melhor[1]}"] += d
            origem[prefixo(melhor[2]) if prefixo(melhor[2]) in SISTEMAS else "TXT"] += 1
        dists.sort()
        print(f"\n  {p}: {len(segs)} segmentos, {sum(s[2] for s in segs):.1f} m")
        print(f"     distancia ao rotulo: mediana {dists[len(dists) // 2]:.2f} m"
              f" | min {dists[0]:.2f} | max {dists[-1]:.2f}")
        print(f"     atribuiria: "
              f"{ {k: round(v, 1) for k, v in sorted(por_dn.items(), key=lambda x: -x[1])[:6]} }")
        print(f"     camada de origem do rotulo vencedor: {dict(origem)}")


if __name__ == "__main__":
    main(sys.argv[1])
