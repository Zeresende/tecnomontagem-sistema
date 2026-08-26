# -*- coding: utf-8 -*-
"""Receita completa (tubo + conexao) dos kits CHUVEIRO / BANHO / LAVABO / COZINHA
nas obras SPHE, para entregar a Karina (pedido de 12/08/2026).

A `biblioteca_receitas.txt` do script 08 so guarda TUBO por DN. A receita de CONEXAO
existe nas mesmas colunas da planilha, mas nunca foi exportada — o script 14 so
conferiu que ela fecha (77/77), sem despejar os valores. Este script despeja.

Estrutura da planilha, ja decodificada em 19/06:
  col 5 = descricao da peca · col 6 = unidade (RL/BR/UN) · col 7 = G (compra)
  col 8+ = uma coluna por KIT; linha de contagem = quantas vezes o kit ocorre;
  celula [linha da peca, coluna do kit] = RECEITA (quanto da peca em 1 kit)

Uso: python 51_receita_kits_4.py [--csv]
"""
import sys, os, re, glob
from pathlib import Path
import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
p17 = __import__("17_parser_contagens")
BASE = AQUI.parent

OBRAS = {"20241385": "Living", "20241390": "Edition", "20251430": "Brooklyn",
         "20251533": "Peak", "20251670": "Pamaris"}

# Os 4 kits que a Karina pediu. Casamento por palavra-chave no cabecalho da coluna,
# porque cada obra nomeia diferente (CHICOTE BANHO 1, KIT CHUVEIRO H, COZ./A.S...).
ALVOS = {
    "CHUVEIRO": re.compile(r"CHUVEIRO", re.I),
    "BANHO":    re.compile(r"BANHO", re.I),
    "LAVABO":   re.compile(r"LAVABO", re.I),
    "COZINHA":  re.compile(r"COZINHA|COZ\.", re.I),
}


def planilha(obra):
    arqs = [a for a in glob.glob(os.path.join(BASE, obra, "*.xlsx"))
            if "PRE-" not in a.upper() and "LEVANTAMENTO" not in a.upper()
            and not os.path.basename(a).startswith("~$")]
    return arqs[0] if arqs else None


def cabecalho_kit(ws, col, linha_cont):
    """Nome do kit = TODAS as strings acima da linha de contagem, juntas.

    Nao basta pegar a primeira: no Peak a primeira e o codigo da folha ('F.1116') e
    o nome do kit vem na linha seguinte ('CHICOTE BANHO AQ/AF'). Ler so a primeira
    fazia os 4 kits do Peak sumirem — e viraria um 'essa obra nao tem' falso."""
    partes = []
    for r in range(1, linha_cont + 1):
        v = ws.cell(r, col).value
        if isinstance(v, str) and len(v.strip()) >= 3:
            partes.append(" ".join(v.split()))
    return " · ".join(partes)


def coletar(obra):
    caminho = planilha(obra)
    if not caminho:
        return {}
    wb = openpyxl.load_workbook(caminho, data_only=True)
    achados = {}
    for ws in wb.worksheets:
        t = ws.title.upper()
        if not (t.startswith("RAMAL") or t.startswith("KIT")
                or t.startswith("CHICOTE")):
            continue
        cr = p17.linha_contagem(ws)
        for col in range(8, ws.max_column + 1):
            cont = ws.cell(cr, col).value
            if not isinstance(cont, (int, float)) or not cont:
                continue
            nome = cabecalho_kit(ws, col, cr)
            alvo = next((k for k, rx in ALVOS.items() if rx.search(nome)), None)
            if not alvo:
                continue
            itens = []
            for r in range(cr + 1, ws.max_row + 1):
                desc = ws.cell(r, 5).value
                un = ws.cell(r, 6).value
                v = ws.cell(r, col).value
                if not isinstance(desc, str) or not isinstance(v, (int, float)) or not v:
                    continue
                itens.append((desc.strip(), str(un or "").strip().upper(), float(v)))
            if itens:
                achados.setdefault(alvo, []).append(
                    {"aba": ws.title, "coluna": nome, "contagem": cont, "itens": itens})
    wb.close()
    return achados


def main():
    csv = "--csv" in sys.argv
    linhas_csv = [("obra", "kit_alvo", "coluna_planilha", "aba", "contagem",
                   "peca", "unidade", "receita")]
    for obra, apelido in OBRAS.items():
        achados = coletar(obra)
        if not achados:
            continue
        print("=" * 78)
        print(f"OBRA {obra} · {apelido}")
        for alvo in ("CHUVEIRO", "BANHO", "LAVABO", "COZINHA"):
            for bloco in achados.get(alvo, []):
                print(f"\n  [{alvo}] coluna \"{bloco['coluna']}\" "
                      f"(aba {bloco['aba']}, ocorre {bloco['contagem']:.0f}x)")
                tubo = [i for i in bloco["itens"] if i[1] in ("RL", "M", "BR")]
                conex = [i for i in bloco["itens"] if i[1] not in ("RL", "M", "BR")]
                for rotulo, grupo in (("tubo", tubo), ("conexao", conex)):
                    if not grupo:
                        continue
                    print(f"    {rotulo}:")
                    for desc, un, v in grupo:
                        print(f"      {v:>8.3f} {un:<3} {desc[:58]}")
                for desc, un, v in bloco["itens"]:
                    linhas_csv.append((obra, alvo, bloco["coluna"], bloco["aba"],
                                       bloco["contagem"], desc, un, v))
        print()

    if csv:
        import csv as _csv
        saida = AQUI / "saida" / "receita_kits_4_sphe.csv"
        with open(saida, "w", newline="", encoding="utf-8-sig") as f:
            _csv.writer(f, delimiter=";").writerows(linhas_csv)
        print(f"CSV: {saida}  ({len(linhas_csv)-1} linhas)")


if __name__ == "__main__":
    main()
