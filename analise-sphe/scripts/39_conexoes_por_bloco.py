# -*- coding: utf-8 -*-
"""INVENTARIO DE CONEXOES POR NOME DE BLOCO — Brooklyn (10/08/2026).

Subproduto do script 38: a leitura por bloco falhou para TUBO (os trechos estao
soltos no modelspace), mas mostrou que as CONEXOES viraram objeto e carregam nome
proprio — `Joelho 45_90 - Pex - Agua Fria_Quente - MEP - Tigre`.

Isso pode servir a outro pedaco do orcamento. A regra das conexoes esta decodificada
desde 03/07: G = soma EXATA de receita x contagem, sem margem. Se o desenho entrega
a contagem de pecas, esse lado sai direto do CAD.

Obstaculo conhecido antes de comecar: **o vocabulario nao e o mesmo**. A planilha diz
"COTOVELO C/ BASE FIXA", o bloco diz "Joelho com Base Fixa". Mesma peca, palavra
diferente — o mesmo tipo de armadilha do lavatorio x lavabo (item 4.4). Por isso este
script so INVENTARIA; o de-para vem depois, com os nomes reais na mao.

Coleta TODOS os INSERTs, sem filtro de camada — o 38 filtrava por camada de tubo e
por isso nem via a camada `Pipe Fittings`.

Uso: python 39_conexoes_por_bloco.py [obra] [--recarregar]
"""
import sys, re, json, logging
from collections import Counter, defaultdict
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent

RX_HIDRO = re.compile(r"pex|pe-?rt|joelho|cotovelo|\bte\b|tee|adaptad|conexao|conexão|"
                      r"luva|bucha|reduc|redução|tampao|tampão|registro|valvula|válvula|"
                      r"distribuid|coifa|vedante|flexiv|flexív|canopla|misturad|curva", re.I)
RX_DN = re.compile(r"\b(16|20|25|32)\s*mm\b", re.I)


def coletar(entidades, achados, depth=0):
    """Todo INSERT, em qualquer profundidade. Guarda nome, camada e profundidade."""
    for e in entidades:
        if e.dxftype() != "INSERT":
            continue
        try:
            nome = str(e.dxf.name)
        except Exception:
            nome = "?"
        try:
            ins = e.dxf.insert
            xy = (round(float(ins[0]), 3), round(float(ins[1]), 3))
        except Exception:
            xy = (0.0, 0.0)
        achados.append({"nome": nome.split("$0$")[-1],
                        "layer": (e.dxf.layer or "").split("$0$")[-1],
                        "depth": depth, "xy": xy})
        if depth < 4:
            try:
                coletar(e.virtual_entities(), achados, depth + 1)
            except Exception:
                pass


def carregar(obra, recarregar=False):
    cache = BASE / "_analise" / "saida" / f"cache_inserts_{obra}.json"
    if cache.exists() and not recarregar:
        d = json.loads(cache.read_text(encoding="utf-8"))
        print(f"cache: {cache.name} ({len(d['inserts'])} inserts)")
        return d["inserts"], d["arquivo"]
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    print(f"leitura do DXF (pode demorar): {tipos[0].name}", flush=True)
    doc = ezdxf.readfile(str(tipos[0]))
    achados = []
    coletar(doc.modelspace(), achados)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"arquivo": tipos[0].name, "inserts": achados}),
                     encoding="utf-8")
    print(f"cache gravado: {cache.name}")
    return achados, tipos[0].name


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "20251430"
    ins, arquivo = carregar(obra, "--recarregar" in sys.argv)
    print(f"OBRA {obra} | {arquivo}")
    print(f"INSERTs no total: {len(ins)}\n")

    print("--- profundidade ---")
    for d, n in sorted(Counter(x["depth"] for x in ins).items()):
        print(f"  depth {d}: {n:>7}")

    print("\n--- camadas com mais INSERTs (top 12) ---")
    for ly, n in Counter(x["layer"] for x in ins).most_common(12):
        print(f"  {ly[:50]:50} {n:>7}")

    hidro = [x for x in ins if RX_HIDRO.search(x["nome"])]
    print(f"\n--- INSERTs com nome de peca hidraulica: {len(hidro)} ---")

    # posicao unica evita contar a mesma peca em profundidades diferentes
    print("\n--- INVENTARIO por nome (posicao unica, depth minima) ---")
    porpos = {}
    for x in hidro:
        ch = (x["nome"], x["xy"])
        if ch not in porpos or x["depth"] < porpos[ch]["depth"]:
            porpos[ch] = x
    cont = Counter(x["nome"] for x in porpos.values())
    print(f"  pecas distintas: {len(cont)}   instancias: {sum(cont.values())}")
    print(f"  {'qtd':>6}  {'DN':>4}  nome do bloco")
    for nome, n in cont.most_common(40):
        m = RX_DN.search(nome)
        print(f"  {n:>6}  {m.group(1) if m else '-':>4}  {nome[:88]}")

    if len(cont) > 40:
        print(f"  ... e mais {len(cont)-40} nomes distintos")

    print("\n--- quantos nomes trazem o DN embutido? ---")
    com = sum(n for nome, n in cont.items() if RX_DN.search(nome))
    tot = sum(cont.values())
    print(f"  {com} de {tot} instancias ({100*com/max(tot,1):.1f}%)")


if __name__ == "__main__":
    main()
