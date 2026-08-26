"""Converte a receita de kit (em ROLOS) para m/kit, por obra, kit e bitola.

Motivo de existir: a coluna `receita` do `receita_kits_4_sphe.csv` esta em ROLOS,
nao em metros, e o tamanho do rolo varia por peca (PEX/PERT 25 = 50 m, PEX 16
Serie 5 da Pamaris = 200 m, o resto 100 m). Somar `receita` direto mistura
unidade e da numero errado — foi o que quase saiu na rodada de 26/08.

    m/kit = rolos * tamanho_do_rolo / contagem

Uso:  python 60_mkit_por_kit.py
Saida: tabela por bitola + total por kit + o "tronco" (bitola maior / 2), que e a
       leitura testada em 26/08 contra o "chicote de ~15 m" que o Marcelo descreveu
       para a cozinha do final 1/2 da Edition.
"""
import csv
import io
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "saida" / "receita_kits_4_sphe.csv"

OBRAS = {"20241385": "Living", "20241390": "Edition", "20251430": "Brooklyn",
         "20251533": "Peak", "20251670": "Pamaris"}

# `\d+\s*M\b` nao casa "DN16MM" (o M colado no M nao tem fronteira), entao pega
# so o tamanho do rolo no fim do nome. Guarda-corpo: se nao achar, devolve None
# e a linha fica de fora em vez de virar metro inventado.
RX_ROLO = re.compile(r"(\d+)\s*M\b", re.I)
RX_DN = re.compile(r"(?:PERT|PEX)\s*(16|20|25|32)", re.I)


def tamanho_do_rolo(peca):
    m = RX_ROLO.search(peca.upper())
    return int(m.group(1)) if m else None


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
        print(f"nao achei {CSV} — rode o 51_receita_kits_4.py antes")
        return 1

    por_variante = defaultdict(dict)   # (obra, kit, coluna, qtd) -> {DN: m/kit}
    sem_rolo = []

    for r in rows:
        if "TUBO" not in r["peca"].upper():
            continue
        rolo = tamanho_do_rolo(r["peca"])
        if rolo is None:
            sem_rolo.append(r["peca"])
            continue
        dn = bitola(r["peca"]) or "?"
        qtd = int(r["contagem"])
        mkit = float(r["receita"]) * rolo / qtd
        chave = (OBRAS.get(r["obra"], r["obra"]), r["kit_alvo"],
                 r["coluna_planilha"], qtd)
        por_variante[chave][dn] = por_variante[chave].get(dn, 0.0) + mkit

    print(f"{'obra':9} {'kit':9} {'coluna':34} {'qtd':>4} "
          f"{'total':>7} {'tronco':>7}  por bitola")
    for (obra, kit, coluna, qtd), dns in por_variante.items():
        total = sum(dns.values())
        maior = max(dns, key=lambda d: int(d) if d.isdigit() else 0)
        tronco = dns[maior] / 2          # AF e AQ percorrem o mesmo caminho
        detalhe = " ".join(f"O{d}={v:.2f}" for d, v in sorted(dns.items()))
        print(f"{obra:9} {kit:9} {coluna[:34]:34} {qtd:>4} "
              f"{total:>7.2f} {tronco:>7.2f}  {detalhe}")

    if sem_rolo:
        print("\nsem tamanho de rolo no nome (ficaram de fora):")
        for p in sorted(set(sem_rolo)):
            print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
