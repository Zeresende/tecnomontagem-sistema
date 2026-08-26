# -*- coding: utf-8 -*-
"""EXTRATOR DE DN PELA GEOMETRIA — rota 3, para o Brooklyn (10/08/2026).

O probe 36 confirmou a hipotese: no Brooklyn (exportacao de Revit) o tubo e
desenhado em LINHA DUPLA na escala real, e os espacamentos se concentram em
0,020 / 0,025 / 0,030 m — que sao DN20, DN25 e DN32. Na Living, usada como
controle, o mesmo teste nao acha diametro nenhum (o espacamento e convencao de
traco, 3 a 4x maior que o tubo).

Consequencia: nesta obra o DN NAO precisa de rotulo. Sai da propria geometria,
o que evita de uma vez o problema que derrubou as outras duas rotas — contagem
de rotulo nao acompanha metragem.

Como o DXF tem 430 MB e a leitura leva ~10 min, os segmentos sao gravados num
cache .json na primeira passada. Rodadas seguintes usam o cache.

Uso: python 37_dn_por_geometria.py [obra] [--recarregar]
"""
import sys, re, math, json, logging
from collections import defaultdict, Counter
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
m22 = __import__("22_ramal_por_dn")
m32 = __import__("32_teste_rolo")
m36 = __import__("36_probe_linha_dupla")

DNS = (16, 20, 25, 32)
TOL_DN = 0.0035          # quanto o espacamento pode desviar do DN nominal (m)
RAIO = 0.2


def carregar(obra, recarregar=False):
    cache = BASE / "_analise" / "saida" / f"cache_segs_{obra}.json"
    if cache.exists() and not recarregar:
        d = json.loads(cache.read_text(encoding="utf-8"))
        print(f"cache: {cache.name} ({len(d['segs'])} segmentos)")
        return d["segs"], d["tags"], d["arquivo"]

    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    print(f"leitura do DXF (pode demorar): {tipos[0].name}", flush=True)
    doc = ezdxf.readfile(str(tipos[0]))
    segs, tags = [], []
    m36.coletar(doc.modelspace(), segs, tags)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"arquivo": tipos[0].name, "segs": segs, "tags": tags}),
                     encoding="utf-8")
    print(f"cache gravado: {cache.name}")
    return segs, tags, tipos[0].name


def dn_do_espacamento(d):
    """Espacamento -> DN nominal, ou None se nao cair perto de nenhum."""
    melhor, dmin = None, math.inf
    for dn in DNS:
        dif = abs(d - dn / 1000.0)
        if dif < dmin:
            melhor, dmin = dn, dif
    return melhor if dmin <= TOL_DN else None


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "20251430"
    segs, tags, arquivo = carregar(obra, "--recarregar" in sys.argv)
    print(f"OBRA {obra} | {arquivo}")
    print(f"segmentos {len(segs)} | tags {len(tags)}")

    pares = m36.parear(segs, RAIO)
    print(f"segmentos com par paralelo: {len(pares)} ({100*len(pares)/len(segs):.1f}%)\n")

    print("--- 1. DN ATRIBUIDO PELO ESPACAMENTO ---")
    # Cada par aparece dos dois lados; a metragem dobra, mas o MIX nao muda.
    res = defaultdict(float)
    fora = 0.0
    for p in pares:
        dn = dn_do_espacamento(p["d"])
        if dn:
            res[dn] += p["m"]
        else:
            fora += p["m"]
    tot_cls = sum(res.values())
    tot = sum(p["m"] for p in pares)
    mx = m32.mix(res)
    for dn in DNS:
        if res.get(dn):
            print(f"  DN{dn:<3} {res[dn]:9.1f} m  {mx.get(dn,0):5.1f}%")
    print(f"  fora de qualquer DN: {fora:.1f} m ({100*fora/tot:.1f}%)")
    print(f"  cobertura do metodo: {100*tot_cls/sum(s['m'] for s in segs):.1f}% do tubo")

    alvo, liq = None, None
    try:
        d32 = m32.coletar(obra)
        alvo = m32.mix(d32["liquido"])
    except Exception as ex:
        print(f"  (sem gabarito: {ex})")

    if alvo:
        print("\n--- 2. CONTRA O GABARITO (receita da planilha) ---")
        print("  medido  " + "  ".join(f"DN{dn}={mx.get(dn,0):5.1f}%" for dn in DNS))
        print("  receita " + "  ".join(f"DN{dn}={alvo.get(dn,0):5.1f}%" for dn in DNS))
        print(f"  erro somado: {m32.erro(mx, alvo):.1f} p.p.")

    print("\n--- 3. CRUZAMENTO COM O ROTULO (um par por tag, o mais proximo) ---")
    if not tags:
        print("  sem tags")
        return
    print(f"  {'DN da tag':>10} {'tags':>5} {'com par':>8} {'espac. mediano':>16} "
          f"{'DN lido':>8} {'confere':>8}")
    acertos = total = 0
    for dn in DNS:
        alvo_t = [t for t in tags if t["dn"] == dn]
        if not alvo_t:
            continue
        vals = []
        for t in alvo_t:
            melhor, dmin = None, math.inf
            for p in pares:
                dd = math.dist(p["xy"], t["xy"])
                if dd < dmin:
                    melhor, dmin = p, dd
            if melhor is not None and dmin <= RAIO * 8:
                vals.append(melhor["d"])
        if not vals:
            print(f"  {dn:>10} {len(alvo_t):>5} {0:>8} {'sem par por perto':>16}")
            continue
        vals.sort()
        med = vals[len(vals) // 2]
        lido = dn_do_espacamento(med)
        ok = "sim" if lido == dn else "nao"
        acertos += (lido == dn)
        total += 1
        print(f"  {dn:>10} {len(alvo_t):>5} {len(vals):>8} {med:>16.4f} "
              f"{str(lido):>8} {ok:>8}")
    if total:
        print(f"\n  o rotulo e a geometria concordam em {acertos} de {total} bitolas.")


if __name__ == "__main__":
    main()
