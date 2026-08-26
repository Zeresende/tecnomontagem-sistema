# -*- coding: utf-8 -*-
"""A receita de kit transfere entre obras? Medido peca a peca (12/08/2026).

A Karina quer provar que a receita de kit independe do projetista, e propos cruzar
com a HM89. A HM89 NAO serve para isso: e do mesmo projetista SPHE (confirmado pelo
Jose em 14/07). O que da para medir com o que existe e a variacao entre 5 OBRAS
DIFERENTES do mesmo projetista — que ja e o teste que importa para o produto, porque
e assim que a biblioteca vai ser usada: receita de obra passada aplicada em obra nova.

O leave-one-out de 03/07 (script 16) respondeu isso para TUBO. Este script responde
para CONEXAO, que nunca foi medida entre obras.

Metodo: para cada kit, uma coluna representativa por obra (a de maior contagem);
peca normalizada; classifica em nucleo (mesma peca e mesma quantidade em todas as
obras onde o kit existe), quantidade variavel, e presenca variavel.

Uso: python 52_kit_transfere.py
"""
import sys, re
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
m51 = __import__("51_receita_kits_4")


def normaliza(desc):
    d = " ".join(desc.upper().split())
    d = d.replace("FLÉXIVEL", "FLEXÍVEL").replace('"', "").replace("'", "")
    return d


def main():
    # kit -> obra -> {peca: qtd}   (so a coluna de maior contagem por obra)
    dados = defaultdict(dict)
    for obra, apelido in m51.OBRAS.items():
        for alvo, blocos in m51.coletar(obra).items():
            melhor = max(blocos, key=lambda b: b["contagem"])
            dados[alvo][apelido] = {
                "coluna": melhor["coluna"].replace("\n", " "),
                "contagem": melhor["contagem"],
                "pecas": {normaliza(d): v for d, u, v in melhor["itens"]
                          if u not in ("RL", "M", "BR")},
                "tubo": {normaliza(d): v for d, u, v in melhor["itens"]
                         if u in ("RL", "M", "BR")},
            }

    for alvo in ("CHUVEIRO", "BANHO", "LAVABO", "COZINHA"):
        obras = dados.get(alvo, {})
        if len(obras) < 2:
            continue
        print("=" * 78)
        print(f"KIT {alvo} — presente em {len(obras)} obras")
        for ap, d in obras.items():
            print(f"   {ap:<9} \"{d['coluna'][:48]}\" ({d['contagem']:.0f}x) · "
                  f"{len(d['pecas'])} conexoes · {len(d['tubo'])} linhas de tubo")

        todas = set()
        for d in obras.values():
            todas |= set(d["pecas"])

        nucleo, qtd_varia, presenca_varia = [], [], []
        for p in sorted(todas):
            vals = {ap: d["pecas"].get(p) for ap, d in obras.items()}
            presentes = {ap: v for ap, v in vals.items() if v is not None}
            if len(presentes) < len(obras):
                presenca_varia.append((p, presentes))
            elif len(set(presentes.values())) == 1:
                nucleo.append((p, next(iter(presentes.values()))))
            else:
                qtd_varia.append((p, presentes))

        print(f"\n   NUCLEO — mesma peca e mesma quantidade nas {len(obras)} obras: "
              f"{len(nucleo)} de {len(todas)}")
        for p, v in nucleo:
            print(f"      {v:>5.1f} un  {p[:60]}")
        if qtd_varia:
            print(f"\n   quantidade varia: {len(qtd_varia)}")
            for p, d in qtd_varia:
                print(f"      {p[:52]}  " +
                      " · ".join(f"{a} {v:.0f}" for a, v in d.items()))
        if presenca_varia:
            print(f"\n   so em algumas obras: {len(presenca_varia)}")
            for p, d in presenca_varia:
                print(f"      {p[:52]}  " +
                      " · ".join(f"{a} {v:.0f}" for a, v in d.items()))

        est = 100 * len(nucleo) / len(todas) if todas else 0
        print(f"\n   >> nucleo estavel: {est:.0f}% das pecas do kit\n")


if __name__ == "__main__":
    main()
