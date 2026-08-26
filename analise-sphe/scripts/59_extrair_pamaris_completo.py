# -*- coding: utf-8 -*-
"""Pre-levantamento PAMARIS (26 arquivos, primeira vez completo) — 19/08/2026.

Reusa as regras ja cravadas com o Hederson, sem redescobrir:
- DN por ROTULO <DN>-PEX (Living/Edition/Pamaris usam esse padrao, nao %%C — o
  extrator antigo, script 03, so reconhece %%C e por isso erraria aqui).
- Sistema = PREFIXO da camada (HAF/HAQ), nao o sufixo (PADRAO_SPHE_ARQUIVOS.yaml).
- Arco: ((a1-a0) % 360) * raio, nunca abs() (bug documentado, inflava HM89 em 80,7 m).
- Classificacao por PROXIMIDADE simples (raio ~2 m no espaco do desenho) — NAO e o
  metodo topologico validado (scripts 26-31), que exige remontagem de trecho por
  obra e nao coube no tempo desta rodada. Erro esperado ~15-30 p.p. no mix por DN,
  documentado no proprio PADRAO_SPHE.yaml. Serve para ORDEM DE GRANDEZA, nao para
  fechar contra a planilha real.

Uso: python 59_extrair_pamaris_completo.py
"""
import glob, math, re, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf

logging.getLogger("ezdxf").setLevel(logging.ERROR)
DXF_DIR = Path(r"C:\Users\resen\Clientes\Tecnomontagem\automatização kits\teste 19.08\dxf")
SAIDA = Path(__file__).resolve().parent / "saida"
SAIDA.mkdir(exist_ok=True)
MAX_DEPTH = 6
# regra do PADRAO_SPHE_ARQUIVOS.yaml: (?:%%[cC]|Ø|\b)(\d{2})\s*-\s*PEX\b
DN_RE = re.compile(r"(?:%%[Cc]|Ø|\b)(\d{2})\s*-\s*PEX\b")


def comp_entidade(e):
    t = e.dxftype()
    try:
        if t == "LINE":
            return e.dxf.start.distance(e.dxf.end), e.dxf.start, e.dxf.end
        if t == "LWPOLYLINE":
            pts = list(e.get_points("xy"))
            if len(pts) < 2:
                return 0.0, None, None
            d = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
            return d, pts[0], pts[-1]
        if t == "POLYLINE":
            pts = [v.dxf.location for v in e.vertices]
            if len(pts) < 2:
                return 0.0, None, None
            d = sum(pts[i].distance(pts[i + 1]) for i in range(len(pts) - 1))
            return d, pts[0], pts[-1]
        if t == "ARC":
            ang = (e.dxf.end_angle - e.dxf.start_angle) % 360  # nunca abs()
            return e.dxf.radius * math.radians(ang), e.dxf.center, e.dxf.center
    except Exception:
        pass
    return 0.0, None, None


def midpoint(p1, p2):
    try:
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
    except Exception:
        return None


def sistema_da_camada(layer):
    up = (layer or "").upper()
    if "HAF" in up:
        return "AF"
    if "HAQ" in up:
        return "AQ"
    return None


def coletar(entidades, segs, textos_dn, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT" and depth < MAX_DEPTH:
            try:
                coletar(e.virtual_entities(), segs, textos_dn, depth + 1)
            except Exception:
                pass
        elif t in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            sis = sistema_da_camada(e.dxf.layer)
            if sis is None:
                continue
            d, a, b = comp_entidade(e)
            if d > 0:
                mp = midpoint(a, b) if (a is not None and b is not None) else None
                segs.append((sis, e.dxf.layer, d, mp))
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


def processa(path):
    print("=" * 90)
    print("ARQUIVO:", path.name, f"({path.stat().st_size / 1e6:.1f} MB)")
    try:
        doc = ezdxf.readfile(str(path))
    except Exception as erro:
        print("  FALHA AO ABRIR:", erro)
        return None
    msp = doc.modelspace()
    segs, textos_dn = [], []
    coletar(msp, segs, textos_dn)

    if not segs:
        print("  sem geometria HAF/HAQ neste arquivo")
        return {"arquivo": path.name, "segs": 0}

    comps = sorted(d for _, _, d, _ in segs)
    n = len(comps)
    med = comps[n // 2]
    unidade = "METROS" if med < 20 else ("CENTIMETROS" if med < 2000 else "MILIMETROS")
    fator = {"METROS": 1.0, "CENTIMETROS": 100.0, "MILIMETROS": 1000.0}[unidade]
    raio = 2.0 * fator

    cell = raio
    grid = defaultdict(list)
    for dn, (tx, ty) in textos_dn:
        grid[(int(tx // cell), int(ty // cell))].append((dn, tx, ty))

    por_sis_dn = defaultdict(float)
    por_layer = defaultdict(float)
    nao_class = 0.0
    for sis, layer, dist, mp in segs:
        por_layer[layer] += dist
        if mp is None or not textos_dn:
            nao_class += dist
            continue
        cx, cy = int(mp[0] // cell), int(mp[1] // cell)
        best, bd = None, raio
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for dn, tx, ty in grid.get((gx, gy), ()):
                    dd = math.hypot(mp[0] - tx, mp[1] - ty)
                    if dd < bd:
                        bd, best = dd, dn
        if best is None:
            nao_class += dist
        else:
            por_sis_dn[(sis, best)] += dist

    total = sum(comps)
    classificado = sum(por_sis_dn.values())
    print(f"  unidade={unidade} (mediana={med:.2f}) | n_segs={n} | rotulos DN={len(textos_dn)}")
    print(f"  TOTAL AF+AQ bruto={total / fator:.1f} m | classificado por DN={classificado / fator:.1f} m "
          f"({100 * classificado / total:.0f}%)")
    for (sis, dn) in sorted(por_sis_dn, key=lambda k: (k[0], k[1])):
        print(f"     {sis} DN{dn:>3}: {por_sis_dn[(sis, dn)] / fator:8.1f} m")
    print(f"     nao classificado: {nao_class / fator:.1f} m")

    return {
        "arquivo": path.name, "unidade": unidade, "fator": fator,
        "total_m": total / fator, "classificado_m": classificado / fator,
        "nao_class_m": nao_class / fator,
        "por_sis_dn": {f"{s}_DN{d}": v / fator for (s, d), v in por_sis_dn.items()},
        "por_layer_m": {k: v / fator for k, v in por_layer.items()},
        "n_segs": n, "n_rotulos": len(textos_dn),
    }


def main():
    arquivos = sorted(DXF_DIR.glob("*.dxf"))
    print(f"{len(arquivos)} arquivos DXF encontrados em {DXF_DIR}")
    resultados = []
    for path in arquivos:
        r = processa(path)
        if r:
            resultados.append(r)

    print("\n" + "=" * 90)
    print("RESUMO GERAL — soma de todos os arquivos (AF+AQ, todas as camadas HAF/HAQ)")
    agregado_sis_dn = defaultdict(float)
    total_geral = total_nao_class = 0.0
    for r in resultados:
        if r.get("segs") == 0:
            continue
        total_geral += r.get("total_m", 0)
        total_nao_class += r.get("nao_class_m", 0)
        for k, v in r.get("por_sis_dn", {}).items():
            agregado_sis_dn[k] += v
    print(f"TOTAL bruto (todos os arquivos, AF+AQ): {total_geral:.1f} m")
    print(f"Classificado por DN: {sum(agregado_sis_dn.values()):.1f} m "
          f"({100 * sum(agregado_sis_dn.values()) / max(total_geral,1):.0f}%)")
    for k in sorted(agregado_sis_dn):
        print(f"  {k}: {agregado_sis_dn[k]:.1f} m")
    print(f"Nao classificado: {total_nao_class:.1f} m")

    import json
    with open(SAIDA / "pamaris_completo_59.json", "w", encoding="utf-8") as f:
        json.dump({"por_arquivo": resultados, "agregado_sis_dn": dict(agregado_sis_dn),
                    "total_geral_m": total_geral, "total_nao_class_m": total_nao_class},
                   f, ensure_ascii=False, indent=2)
    print(f"\nsalvo: {SAIDA / 'pamaris_completo_59.json'}")


if __name__ == "__main__":
    main()
