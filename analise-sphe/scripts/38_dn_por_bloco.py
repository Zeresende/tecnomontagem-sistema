# -*- coding: utf-8 -*-
"""DN POR BLOCO — a terceira tentativa no Brooklyn (10/08/2026).

O script 37 reprovou a leitura por segmento solto: 52,4 p.p. contra o gabarito,
1 de 3 bitolas no cruzamento com o rótulo, e DN16 inventado numa obra sem DN16.
O diagnóstico foi que o diâmetro está no desenho, mas o pareamento por
proximidade escolhe o par errado — perto de tag DN20 o espaçamento mais comum é
0,040 (provável tubo-guia) e não 0,020.

Hipótese desta rodada: no Revit **cada tubo é um objeto**. Se a exportação
preservou os INSERTs, as duas linhas de um mesmo tubo estão dentro do MESMO
bloco — e aí não há ambiguidade de pareamento: o par é dado, não procurado.

O que este script mede, em ordem:
  1. a geometria de tubo está mesmo dentro de blocos, ou solta no modelspace?
  2. um bloco parece um tubo (poucas linhas, paralelas duas a duas)?
  3. o espaçamento DENTRO do bloco bate com o DN?

Uso: python 38_dn_por_bloco.py [obra] [--recarregar]
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
m37 = __import__("37_dn_por_geometria")

DNS = (16, 20, 25, 32)
MIN_SEG = 0.02
TOL_ANG = 1.5


class Contador:
    def __init__(self):
        self.n = 0

    def novo(self):
        self.n += 1
        return self.n


def coletar(entidades, segs, tags, cont, bloco=None, nome="", depth=0):
    """Igual ao 36, mas cada segmento carrega o INSERT mais interno que o contém."""
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT":
            if depth < m36.MAX_DEPTH:
                try:
                    nb = str(e.dxf.name)
                except Exception:
                    nb = "?"
                try:
                    coletar(e.virtual_entities(), segs, tags, cont,
                            cont.novo(), nb.split("$0$")[-1], depth + 1)
                except Exception:
                    pass
            continue
        ly = (e.dxf.layer or "").split("$0$")[-1]
        if t in ("TEXT", "MTEXT"):
            m = m36.RX_DN.search(" ".join(m22.texto_de(e).split()))
            if m:
                try:
                    ins = e.dxf.insert
                    tags.append({"dn": int(m.group(1)),
                                 "xy": (float(ins[0]), float(ins[1]))})
                except Exception:
                    pass
            continue
        if t not in ("LINE", "LWPOLYLINE", "POLYLINE"):
            continue
        if not m36.RX_CAMADA.search(ly) or m36.RX_EXCLUI.search(ly):
            continue
        pts = m22.pontos_de(e)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            d = math.dist(a, b)
            if d < MIN_SEG:
                continue
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
            segs.append({"a": a, "b": b, "m": d, "ang": ang, "layer": ly,
                         "bloco": bloco, "nome": nome})


def carregar(obra, recarregar=False):
    cache = BASE / "_analise" / "saida" / f"cache_blocos_{obra}.json"
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
    coletar(doc.modelspace(), segs, tags, Contador())
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"arquivo": tipos[0].name, "segs": segs, "tags": tags}),
                     encoding="utf-8")
    print(f"cache gravado: {cache.name}")
    return segs, tags, tipos[0].name


def pares_no_bloco(sub):
    """Pares paralelos DENTRO de um bloco. Devolve lista de (espacamento, metros)."""
    out = []
    for i, s in enumerate(sub):
        for j in range(i + 1, len(sub)):
            t = sub[j]
            if m36.dif_ang(s["ang"], t["ang"]) > TOL_ANG:
                continue
            if not m36.sobrepoe(s, t):
                continue
            d = m36.dist_perp(s, ((t["a"][0] + t["b"][0]) / 2,
                                  (t["a"][1] + t["b"][1]) / 2))
            if 1e-6 < d < 0.5:
                out.append((d, (s["m"] + t["m"]) / 2))
    return out


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "20251430"
    segs, tags, arquivo = carregar(obra, "--recarregar" in sys.argv)
    print(f"OBRA {obra} | {arquivo}")
    tot = sum(s["m"] for s in segs)
    print(f"segmentos {len(segs)} | metragem {tot:.1f} | tags {len(tags)}\n")

    print("--- 1. A GEOMETRIA ESTA DENTRO DE BLOCO? ---")
    solto = sum(s["m"] for s in segs if s["bloco"] is None)
    print(f"  solta no modelspace: {solto:9.1f} m ({100*solto/tot:5.1f}%)")
    print(f"  dentro de bloco    : {tot-solto:9.1f} m ({100*(tot-solto)/tot:5.1f}%)")

    porbloco = defaultdict(list)
    for s in segs:
        if s["bloco"] is not None:
            porbloco[s["bloco"]].append(s)
    if not porbloco:
        print("\n  Nenhuma geometria de tubo dentro de bloco. A hipotese cai aqui.")
        return
    print(f"  instancias de bloco com tubo: {len(porbloco)}")
    tam = Counter(len(v) for v in porbloco.values())
    print("  segmentos por instancia (top 8):")
    for k, n in sorted(tam.items())[:8]:
        print(f"    {k:>3} segmento(s): {n:>6} instancias")
    print("  nomes de bloco mais frequentes:")
    nomes = Counter(v[0]["nome"] for v in porbloco.values())
    for nome, n in nomes.most_common(8):
        print(f"    {nome[:52]:52} {n:>6}")

    print("\n--- 2. UM BLOCO PARECE UM TUBO? ---")
    com_par, sem_par = 0, 0
    esp_por_bloco = {}
    for bid, sub in porbloco.items():
        ps = pares_no_bloco(sub)
        if ps:
            com_par += 1
            # o par de maior extensao manda: e o corpo do tubo, nao a conexao
            ps.sort(key=lambda x: -x[1])
            esp_por_bloco[bid] = ps[0]
        else:
            sem_par += 1
    print(f"  instancias com par paralelo interno: {com_par}")
    print(f"  instancias sem par                 : {sem_par}")
    if not esp_por_bloco:
        print("  Nenhum bloco tem par interno. A hipotese cai aqui.")
        return

    passo = 0.005
    hist = defaultdict(float)
    for bid, (d, m) in esp_por_bloco.items():
        hist[round(d / passo) * passo] += m
    tm = sum(hist.values())
    print(f"\n  espacamento interno, por metragem (top 10):")
    for val, m in sorted(hist.items(), key=lambda x: -x[1])[:10]:
        dn = m37.dn_do_espacamento(val)
        print(f"    {val:7.4f}  {m:9.1f} m  {100*m/tm:5.1f}%   {'-> DN'+str(dn) if dn else ''}")

    print("\n--- 3. CONTRA O GABARITO ---")
    res = defaultdict(float)
    fora = 0.0
    for bid, (d, m) in esp_por_bloco.items():
        dn = m37.dn_do_espacamento(d)
        if dn:
            res[dn] += m
        else:
            fora += m
    mx = m32.mix(res)
    try:
        alvo = m32.mix(m32.coletar(obra)["liquido"])
    except Exception:
        alvo = {}
    print("  medido  " + "  ".join(f"DN{dn}={mx.get(dn,0):5.1f}%" for dn in DNS))
    if alvo:
        print("  receita " + "  ".join(f"DN{dn}={alvo.get(dn,0):5.1f}%" for dn in DNS))
        print(f"  erro somado: {m32.erro(mx, alvo):.1f} p.p.   "
              f"(segmento solto deu 52,4)")
    print(f"  fora de qualquer DN: {100*fora/(sum(res.values())+fora):.1f}% da metragem pareada")

    print("\n--- 4. CRUZAMENTO COM O ROTULO ---")
    centro = {}
    for bid, sub in porbloco.items():
        if bid in esp_por_bloco:
            xs = [q[0] for s in sub for q in (s["a"], s["b"])]
            ys = [q[1] for s in sub for q in (s["a"], s["b"])]
            centro[bid] = (sum(xs) / len(xs), sum(ys) / len(ys))
    print(f"  {'DN da tag':>10} {'tags':>5} {'com bloco':>10} {'espac. mediano':>16} "
          f"{'DN lido':>8} {'confere':>8}")
    acertos = total = 0
    for dn in DNS:
        alvo_t = [t for t in tags if t["dn"] == dn]
        if not alvo_t:
            continue
        vals = []
        for t in alvo_t:
            melhor, dmin = None, math.inf
            for bid, c in centro.items():
                dd = math.dist(c, t["xy"])
                if dd < dmin:
                    melhor, dmin = bid, dd
            if melhor is not None and dmin <= 1.6:
                vals.append(esp_por_bloco[melhor][0])
        if not vals:
            print(f"  {dn:>10} {len(alvo_t):>5} {0:>10} {'sem bloco por perto':>16}")
            continue
        vals.sort()
        med = vals[len(vals) // 2]
        lido = m37.dn_do_espacamento(med)
        ok = "sim" if lido == dn else "nao"
        acertos += (lido == dn)
        total += 1
        print(f"  {dn:>10} {len(alvo_t):>5} {len(vals):>10} {med:>16.4f} "
              f"{str(lido):>8} {ok:>8}")
    if total:
        print(f"\n  rotulo e bloco concordam em {acertos} de {total} bitolas "
              f"(por segmento solto foi 1 de 3).")


if __name__ == "__main__":
    main()
