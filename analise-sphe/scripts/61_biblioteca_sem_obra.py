# -*- coding: utf-8 -*-
"""Biblioteca-mae de receitas SEM uma obra — rodada de validacao "deixar uma de fora".

Pergunta que responde (decisao B1, aberta desde junho): a receita de kit das outras
obras SPHE generaliza para uma obra nova, ou cada obra precisa de captura propria?

Le `saida/receita_kits_4_sphe.csv` (ja com as correcoes auditadas do 51), tira a obra
escolhida e consolida as demais por (kit, PAPEL):
  - PAPEL do tubo = bitola ("TUBO O16"), somando variantes de cor/linha na mesma coluna.
    Valor em METROS POR KIT — a celula da planilha SPHE e m/kit; a compra em rolos e
    ROUNDUP(soma(m/kit x contagem) x 1,07 / tamanho_rolo). Conferido na formula da
    coluna G das 5 obras em 04/09/2026 (o 60 lia como rolos e estava errado).
  - PAPEL da conexao = descricao normalizada (sem acento, caixa alta). Valor em UN/kit.
Obra com 2+ colunas do mesmo kit (Edition lavabo 1/2 x 3/4, Pamaris banho 1/2) entra
com a media ponderada pela contagem. Entre obras: mediana, minimo, maximo, n_obras.

Saidas em saida/holdout_<apelido>/ :
  receita_kits_<n>_obras.csv     linhas cruas das obras que ficaram (mesmo schema do 51)
  biblioteca_mae_sem_<apelido>.csv  kit;papel;unidade;n_obras;mediana;min;max;<uma col por obra>
  predicao_<apelido>.csv         mediana x contagem VERDADEIRA da obra de fora, por kit e papel
                                 (usa a contagem real de proposito: isola a pergunta da receita)

Uso: python 61_biblioteca_sem_obra.py --sem 20251670 [--min-obras 2]
"""
import argparse
import csv
import io
import re
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
CSV = AQUI / "saida" / "receita_kits_4_sphe.csv"
OBRAS = {"20241385": "Living", "20241390": "Edition", "20251430": "Brooklyn",
         "20251533": "Peak", "20251670": "Pamaris"}
RX_DN = re.compile(r"(?:PERT|PEX)[ ]*(16|20|25|32)", re.I)


def sem_acento(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def papel(peca):
    up = re.sub("[ ]+", " ", sem_acento(peca).upper()).strip()
    if up.startswith("TUBO"):
        m = RX_DN.search(up)
        return (f"TUBO O{m.group(1)}" if m else "TUBO ?"), "M/KIT"
    return up, "UN/KIT"


def carregar():
    with io.open(CSV, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def por_obra_kit(rows):
    """{(obra, kit): {papel: (valor_medio_ponderado, unidade)}} e {(obra,kit): contagem_total}."""
    col = defaultdict(lambda: defaultdict(float))      # (obra,kit,coluna) -> papel -> valor
    cont = {}                                           # (obra,kit,coluna) -> contagem
    unid = {}
    for r in rows:
        p, u = papel(r["peca"])
        k = (r["obra"], r["kit_alvo"], r["coluna_planilha"])
        col[k][p] += float(r["receita"])
        cont[k] = float(r["contagem"])
        unid[p] = u
    agreg = defaultdict(lambda: defaultdict(float))
    peso = defaultdict(float)
    for (obra, kit, coluna), papeis in col.items():
        c = cont[(obra, kit, coluna)]
        peso[(obra, kit)] += c
        for p, v in papeis.items():
            agreg[(obra, kit)][p] += v * c
    out = {}
    for ok, papeis in agreg.items():
        out[ok] = {p: v / peso[ok] for p, v in papeis.items()}
    return out, unid, cont


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem", required=True, help="obra que fica de fora, ex.: 20251670")
    ap.add_argument("--min-obras", type=int, default=2,
                    help="papel entra na predicao se aparece em pelo menos N obras")
    a = ap.parse_args()
    if a.sem not in OBRAS:
        print(f"obra {a.sem} desconhecida; opcoes: {', '.join(OBRAS)}")
        return 1
    fora = OBRAS[a.sem]
    saida = AQUI / "saida" / f"holdout_{fora.lower()}"
    saida.mkdir(parents=True, exist_ok=True)

    rows = carregar()
    ficam = [r for r in rows if r["obra"] != a.sem]
    holdout = [r for r in rows if r["obra"] == a.sem]
    obras_ficam = [o for o in OBRAS if o != a.sem]

    # 1) linhas cruas das obras que ficaram
    with io.open(saida / f"receita_kits_{len(obras_ficam)}_obras.csv", "w",
                 encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys(), delimiter=";")
        w.writeheader()
        w.writerows(ficam)

    # 2) biblioteca-mae
    pok, unid, _ = por_obra_kit(ficam)
    kits = sorted({k for _, k in pok})
    papeis_por_kit = defaultdict(set)
    for (_, kit), papeis in pok.items():
        papeis_por_kit[kit] |= set(papeis)
    apelidos = [OBRAS[o] for o in obras_ficam]
    bib = []
    for kit in kits:
        for p in sorted(papeis_por_kit[kit]):
            vals = {OBRAS[o]: pok[(o, kit)][p] for o in obras_ficam
                    if (o, kit) in pok and p in pok[(o, kit)]}
            v = list(vals.values())
            bib.append({"kit": kit, "papel": p, "unidade": unid[p], "n_obras": len(v),
                        "mediana": round(statistics.median(v), 3), "minimo": round(min(v), 3),
                        "maximo": round(max(v), 3),
                        **{ap_: (round(vals[ap_], 3) if ap_ in vals else "") for ap_ in apelidos}})
    with io.open(saida / f"biblioteca_mae_sem_{fora.lower()}.csv", "w",
                 encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(bib[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(bib)

    # 3) predicao para a obra de fora: mediana x contagem verdadeira, por coluna de kit
    _, _, cont_hold = por_obra_kit(holdout)
    colunas = {}
    for (obra, kit, coluna), c in cont_hold.items():
        colunas.setdefault(kit, []).append((coluna, c))
    pred = []
    for kit, cols in sorted(colunas.items()):
        for b in bib:
            if b["kit"] != kit or b["n_obras"] < a.min_obras:
                continue
            for coluna, c in cols:
                pred.append({"obra": a.sem, "kit": kit, "coluna_planilha": coluna, "contagem": int(c),
                             "papel": b["papel"], "unidade": b["unidade"],
                             "receita_mediana": b["mediana"], "n_obras": b["n_obras"],
                             "total": round(b["mediana"] * c, 1)})
    with io.open(saida / f"predicao_{fora.lower()}.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(pred[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(pred)

    # resumo no console
    print(f"obra de fora: {fora} ({a.sem}) · biblioteca com {len(obras_ficam)} obras: {', '.join(apelidos)}")
    print(f"{'kit':9} {'papel':46} {'un':6} {'n':>2} {'mediana':>8} {'min':>7} {'max':>7}")
    for b in bib:
        marca = "" if b["n_obras"] >= a.min_obras else "  (fora da predicao)"
        print(f"{b['kit']:9} {b['papel'][:46]:46} {b['unidade']:6} {b['n_obras']:>2} "
              f"{b['mediana']:>8.2f} {b['minimo']:>7.2f} {b['maximo']:>7.2f}{marca}")
    kits_hold = sorted({(k, c) for (_, k, c) in cont_hold})
    print(f"\ncolunas de kit da {fora} (contagem verdadeira, usada na predicao): "
          + "; ".join(f"{c} x{int(cont_hold[(a.sem, k, c)])}" for k, c in kits_hold))
    print(f"\nsaidas em {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
