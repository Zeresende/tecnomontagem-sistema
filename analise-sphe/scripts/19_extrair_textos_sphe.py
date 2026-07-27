# -*- coding: utf-8 -*-
"""Extrai textos-chave da convencao SPHE: "Final N" (aptos por pavimento)
e "Nº pavimento" (numero de pavimentos), recursivo em blocos.

Uso: python 19_extrair_textos_sphe.py <DIR_DXF> [--filtro REGEX] [--dump-final]
"""
import sys, re, argparse, logging
from collections import Counter, defaultdict
from pathlib import Path
import ezdxf

sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("ezdxf").setLevel(logging.ERROR)
MAX_DEPTH = 8

FINAL_RE = re.compile(r"\bFINAL\s*[:\-]?\s*(\d{1,3})\b", re.I)
PAV_RE = re.compile(r"(\d{1,2})\s*[º°oO]?\s*[\-\.]?\s*PAV(?:IMENTO)?\b", re.I)
PAV_RE2 = re.compile(r"\bPAV(?:IMENTO)?\s*[:\-]?\s*(\d{1,2})\b", re.I)


def norm(s):
    # MTEXT vem com codigos de formatacao {\f...;} \P etc.
    s = re.sub(r"\\[A-Za-z][^;\\]*;", "", s)
    s = s.replace("\\P", " ").replace("{", "").replace("}", "")
    s = re.sub(r"\\[~]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def coletar_textos(entidades, textos, depth=0):
    for e in entidades:
        t = e.dxftype()
        if t == "INSERT" and depth < MAX_DEPTH:
            try:
                coletar_textos(e.virtual_entities(), textos, depth + 1)
            except Exception:
                pass
        elif t in ("TEXT", "MTEXT"):
            try:
                raw = e.dxf.text if t == "TEXT" else e.text
            except Exception:
                raw = ""
            if raw:
                textos.append(norm(raw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir_dxf")
    ap.add_argument("--filtro", default=None, help="regex no nome do arquivo")
    ap.add_argument("--dump-final", action="store_true")
    ap.add_argument("--niveis", action="store_true", help="dump de rotulos de nivel/pavimento")
    ap.add_argument("--grep", default=None, help="regex; dump textos distintos que casam, com contagem")
    args = ap.parse_args()

    NIVEL_RE = re.compile(r"PAVIMENTO|T[EÉ]RREO|TERREO|COBERTURA|BARRILETE|[AÁ]TICO|ATICO|SUBSOLO|"
                          r"CASA DE M|RESERVAT|TETO|CAIXA|MEZANINO|PILOTIS", re.I)

    d = Path(args.dir_dxf)
    dxfs = sorted(d.glob("*.dxf")) + sorted(d.glob("*.DXF"))
    if args.filtro:
        rx = re.compile(args.filtro, re.I)
        dxfs = [p for p in dxfs if rx.search(p.name)]
    if not dxfs:
        print("Nenhum DXF em", d, "com filtro", args.filtro); return

    for path in dxfs:
        print("=" * 90)
        print(f"ARQUIVO: {path.name} ({path.stat().st_size/1e6:.1f} MB)")
        try:
            doc = ezdxf.readfile(str(path))
        except Exception as ex:
            print("  ERRO ao ler:", ex); continue
        textos = []
        coletar_textos(doc.modelspace(), textos)

        finais = Counter()
        finais_txt = Counter()
        pavs = Counter()
        pav_txt = Counter()
        for tx in textos:
            for m in FINAL_RE.finditer(tx):
                finais[int(m.group(1))] += 1
                finais_txt[tx[:40]] += 1
            for m in list(PAV_RE.finditer(tx)) + list(PAV_RE2.finditer(tx)):
                pavs[int(m.group(1))] += 1
                pav_txt[tx[:40]] += 1

        print(f"  total textos: {len(textos)}")
        if finais:
            nums = sorted(finais)
            print(f"  FINAL -> nums distintos: {nums} | MAX={max(nums)} | ocorrencias={sum(finais.values())}")
            if args.dump_final:
                for n in nums:
                    print(f"      Final {n}: {finais[n]}x")
        else:
            print("  FINAL -> nenhum")
        if pavs:
            nums = sorted(pavs)
            print(f"  PAVIMENTO -> nums: {nums} | MAX={max(nums)} | ocorrencias={sum(pavs.values())}")
            for tx, c in pav_txt.most_common(8):
                print(f"      '{tx}' ({c}x)")
        else:
            print("  PAVIMENTO -> nenhum")

        if args.niveis:
            niveis = sorted({tx for tx in textos if NIVEL_RE.search(tx)})
            print(f"  --- rotulos de nivel ({len(niveis)}) ---")
            for tx in niveis:
                print("     ", repr(tx[:60]))

        if args.grep:
            gx = re.compile(args.grep, re.I)
            hits = Counter(tx for tx in textos if gx.search(tx))
            print(f"  --- grep '{args.grep}' ({len(hits)} distintos) ---")
            for tx, c in hits.most_common(80):
                print(f"     {c:4d}x  {tx[:70]!r}")


if __name__ == "__main__":
    main()
