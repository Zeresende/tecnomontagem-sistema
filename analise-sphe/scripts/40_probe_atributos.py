# -*- coding: utf-8 -*-
"""PROBE DE ATRIBUTOS — o DN das conexoes pode estar fora do nome (10/08/2026).

O script 39 inventariou as conexoes do Brooklyn. Depois de tirar o ID unico que o
Revit poe em cada instancia, sobram 14 familias limpas (`Cotovelo - PEX - Padrao`,
`Conexao Fixa Femea - Pex ... Tigre`, `Luva Reducao - Pex ...`).

Mas **nenhum nome traz o DN** — 0 de 2.930 instancias. E a planilha separa conexao
por bitola (`TE PEX 20-16-16` e `TE PEX 20-20-20` sao linhas diferentes). Sem o DN,
o inventario diz o tipo de peca e nao a linha do orcamento.

Ultima possibilidade antes de desistir da rota: no Revit os parametros da peca podem
sair como ATRIBUTOS do bloco (entidades ATTRIB dentro do INSERT), nao no nome. Se o
diametro estiver la, o cruzamento com a planilha volta a ser possivel.

Este script so pergunta: os INSERTs de conexao tem atributo? Quais? Algum com DN?

Uso: python 40_probe_atributos.py [obra]
"""
import sys, re, logging
from collections import Counter, defaultdict
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parent.parent

RX_ALVO = re.compile(r"Pipe Fitting|Pipe Accessor|Plumbing", re.I)
RX_PEX = re.compile(r"pex", re.I)
RX_ID = re.compile(r"-V?\d+-")       # corrigido: 39 exigia 3+ digitos e deixava -V4- passar
RX_DN = re.compile(r"\b(16|20|25|32|40|50)\b")


def familia(n):
    m = RX_ID.search(n)
    return (n[:m.start()] if m else n).strip()


def main():
    obra = sys.argv[1] if len(sys.argv) > 1 else "20251430"
    d = BASE / "_analise" / "dxf" / obra
    tipos = [p for p in sorted(d.glob("*.dxf"))
             if re.search(r"PVTIPO|TIPO|TIP\b|-TIP-", p.name, re.I)
             and not re.search(r"DET", p.name, re.I)]
    print(f"OBRA {obra} | {tipos[0].name}", flush=True)
    doc = ezdxf.readfile(str(tipos[0]))

    com_attr = sem_attr = 0
    tags_attr = Counter()
    exemplos = defaultdict(list)
    fam_attr = defaultdict(Counter)

    for e in doc.modelspace():
        if e.dxftype() != "INSERT":
            continue
        ly = (e.dxf.layer or "").split("$0$")[-1]
        try:
            nome = str(e.dxf.name).split("$0$")[-1]
        except Exception:
            nome = "?"
        alvo = RX_ALVO.search(ly) or RX_PEX.search(nome)
        if not alvo:
            continue
        attrs = list(getattr(e, "attribs", []) or [])
        if not attrs:
            sem_attr += 1
            continue
        com_attr += 1
        for a in attrs:
            try:
                tag = str(a.dxf.tag)
                val = str(a.dxf.text)
            except Exception:
                continue
            tags_attr[tag] += 1
            fam_attr[familia(nome)][tag] += 1
            if len(exemplos[tag]) < 6 and val.strip():
                exemplos[tag].append(val.strip()[:60])

    print(f"\nINSERTs de conexao COM atributo: {com_attr}")
    print(f"INSERTs de conexao SEM atributo: {sem_attr}")

    if not tags_attr:
        print("\n  Nenhum atributo. O DN nao esta em atributo de bloco.")
        print("  Resta o arquivo nativo (RVT/IFC) — ver item 14.1 da rodada 3.")
        return

    print(f"\n--- ATRIBUTOS encontrados ({len(tags_attr)} tags distintas) ---")
    print(f"  {'ocorr.':>7}  {'tag':24}  exemplos de valor")
    for tag, n in tags_attr.most_common(25):
        vals = " | ".join(exemplos.get(tag, []))
        marca = "  <-- tem DN?" if any(RX_DN.search(v) for v in exemplos.get(tag, [])) else ""
        print(f"  {n:>7}  {tag[:24]:24}  {vals[:70]}{marca}")

    print("\n--- atributos por familia (top 8 familias) ---")
    for fam, tags in sorted(fam_attr.items(), key=lambda x: -sum(x[1].values()))[:8]:
        print(f"  {fam[:60]:60} {', '.join(t for t,_ in tags.most_common(4))}")


if __name__ == "__main__":
    main()
