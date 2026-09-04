"""Soma a receita de tubo por kit (m/kit) por obra, kit e bitola.

CORRIGIDO EM 04/09/2026. A versao de 26/08 dizia que a coluna `receita` do
`receita_kits_4_sphe.csv` estava em ROLOS e multiplicava por tamanho_do_rolo/contagem.
Estava errado: a celula [peca, coluna de kit] da planilha SPHE e METROS POR KIT. A prova
e a formula da coluna G ("Qtde. Total Levantada") nas 5 obras:
    G = ROUNDUP( soma(celula x contagem) / tamanho_rolo x 1,07 )
Ex.: Pamaris O16 = (1x780 + 10x660 + 1x120) / 200 x 1,07 = 40,1 -> 41 rolos (bate com a planilha).
Com a leitura antiga, o chuveiro da Pamaris dava 0,26 m de tubo (1 rolo x 200 m / 780 kits);
a leitura certa da 1,0 m. O PADRAO_SPHE.yaml (secao unidades, RL) ja dizia isso desde 12/08.

    m/kit = celula (direto)
    compra em rolos = ROUNDUP( soma(m/kit x contagem) x 1,07 / tamanho_rolo )

Uso:  python 60_mkit_por_kit.py
Saida: tabela por bitola + total por kit + o "tronco" (bitola maior / 2) + compra em rolos.
"""
import csv
import io
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "saida" / "receita_kits_4_sphe.csv"

OBRAS = {"20241385": "Living", "20241390": "Edition", "20251430": "Brooklyn",
         "20251533": "Peak", "20251670": "Pamaris"}

# tamanho do rolo fica no nome da peca ("X 200M", "ROLO 100M") e serve so para
# informar a compra, nao para converter a receita (que ja esta em metros).
# "DN16MM" e "12,4MM" nao casam: o M e seguido de outra letra.
RX_ROLO = re.compile(r"([0-9]+)[ ]*M(?:[^A-Z]|$)", re.I)
RX_DN = re.compile(r"(?:PERT|PEX)[ ]*(16|20|25|32)", re.I)
FOLGA = 1.07


def tamanho_do_rolo(peca):
    m = RX_ROLO.findall(peca.upper())
    return int(m[-1]) if m else None


def bitola(peca):
    m = RX_DN.search(peca.upper())
    return m.group(1) if m else None


def carregar():
    with io.open(CSV, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def main():
    try:
        rows = carregar()
    except FileNotFoundError:
        print(f"nao achei {CSV} - rode o 51_receita_kits_4.py antes")
        return 1

    por_variante = defaultdict(dict)   # (obra, kit, coluna, qtd) -> {DN: m/kit}
    compra = defaultdict(lambda: defaultdict(float))   # (obra, DN) -> metros totais
    rolo_de = {}

    for r in rows:
        if "TUBO" not in r["peca"].upper():
            continue
        dn = bitola(r["peca"]) or "?"
        qtd = int(r["contagem"])
        mkit = float(r["receita"])          # a celula JA e m/kit (ver docstring)
        chave = (OBRAS.get(r["obra"], r["obra"]), r["kit_alvo"],
                 r["coluna_planilha"], qtd)
        por_variante[chave][dn] = por_variante[chave].get(dn, 0.0) + mkit
        compra[(chave[0], dn)]["m"] += mkit * qtd
        rolo = tamanho_do_rolo(r["peca"])
        if rolo:
            rolo_de[(chave[0], dn)] = rolo

    print(f"{'obra':9} {'kit':9} {'coluna':34} {'qtd':>4} "
          f"{'m/kit':>7} {'tronco':>7}  por bitola (m/kit)")
    for (obra, kit, coluna, qtd), dns in por_variante.items():
        total = sum(dns.values())
        maior = max(dns, key=lambda d: int(d) if d.isdigit() else 0)
        tronco = dns[maior] / 2          # AF e AQ percorrem o mesmo caminho
        detalhe = " ".join(f"O{d}={v:.2f}" for d, v in sorted(dns.items()))
        print(f"{obra:9} {kit:9} {coluna[:34]:34} {qtd:>4} "
              f"{total:>7.2f} {tronco:>7.2f}  {detalhe}")

    print(f"\ncompra de tubo dos KITS por obra e bitola (metros -> rolos, folga {FOLGA}):")
    for (obra, dn), d in sorted(compra.items()):
        rolo = rolo_de.get((obra, dn))
        rolos = math.ceil(d["m"] * FOLGA / rolo) if rolo else None
        print(f"  {obra:9} O{dn}: {d['m']:8.0f} m -> "
              + (f"{rolos} rolos de {rolo} m" if rolo else "tamanho do rolo nao esta no nome"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
