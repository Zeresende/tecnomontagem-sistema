# Rota 2 do extrator — DN pela nota geral (item 5.3) — 10/08/2026

> **CORRIGIDA EM 11/08/2026 — leia antes.** A seção "ACHADO QUE TRAVA O PEAK"
> está errada em duas coisas. (1) O Hederson respondeu no item 13.1 que **não é
> duplicação: são duas torres do mesmo empreendimento**, e ambas contam — não há
> divisão por 2 a fazer, e a metragem absoluta medida no modelspace inteiro não
> estava dobrada. (2) Os números 1.034,8 e 799,6 m saíram de um corte pela metade
> do Y, que **mistura as plantas de furo** com as plantas de torre. Medição refeita
> por região em `NOTA-PEAK-DUAS-TORRES-2026-08-11.md` (script 48): as duas torres
> são 605,7 e 627,0 m.


Scripts: `33_probe_nota_dn.py` (localiza e lê as notas) e `34_dn_por_nota.py` (extrator
+ grade de avaliação). Obra trabalhada: Peak (20251533). Brooklyn (20251430) pendente —
o DXF tem 430 MB.

## A resposta dele confere no arquivo

Perguntamos por que Brooklyn e Peak não têm nenhum rótulo `<DN>-PEX`. Ele respondeu que
"em ambas as obras existe uma anotação informando o diâmetro" e anexou print do Peak.

Está lá, e o texto é exatamente o do anexo:

```
AF - PEX. %%C20mm - TUBO GUIA: %%C32mm     32 ocorrências
AQ - PEX. %%C20mm - TUBO GUIA: %%C32mm     32 ocorrências
AF - PEX. %%C25mm - TUBO GUIA: %%C40mm      4 ocorrências
```

`%%C` é como o AutoCAD grava o símbolo Ø. **Confirma que a busca por `%%C` do script 18
(03/07) nunca esteve errada — estava aplicada nas obras da outra rota.** A SPHE usa dois
padrões de codificação, e agora os dois estão mapeados.

Dois cuidados que o parser já trata:
- a nota traz **dois** diâmetros, o do PEX e o do tubo guia. Só o primeiro entra;
- há textos de outros sistemas com diâmetro (`DRENO DO AR CONDICIONADO %%C25 - PVC`,
  45 ocorrências) que precisam ser descartados. O regex exige PEX/PERT no texto.

## O que a rota 2 tem de diferente, e melhor

A nota declara o **sistema** junto com o diâmetro — `AF` ou `AQ`. O rótulo `<DN>-PEX` da
rota 1 não fazia isso. Como o sistema também está na camada (`HAF-TUB` / `HAQ-TUB`), dá
para restringir: geometria de água fria só aceita nota AF.

**Essa restrição já se validou.** No Peak todas as 32 notas de AQ são DN20, nenhuma de
DN25 — e a planilha confirma pelo lado independente: o PERT **vermelho** (água quente) só
tem linha de DN20; o DN25 existe apenas no **azul** (água fria). Duas fontes que não se
conversam dizendo a mesma coisa.

Descoberta lateral: o Peak não usa PEX, usa **PERT azul e vermelho**. A cor é o sistema.

## Onde a rota 2 empaca — e é a mesma doença da rota 1

Para o lado AF, a atribuição por proximidade dá 80% DN20 / 20% DN25 contra um alvo de
44/56. Melhor ponto da grade: 13,9 p.p. com apenas 36% de cobertura (raio 2).

O motivo é o mesmo já diagnosticado hoje na outra nota: **contagem de nota não acompanha
metragem.** São 32 notas de Ø20 contra 4 de Ø25, mas pela receita o DN25 é 72% do metro de
água fria. Quem atribui por distância dá peso igual a cada nota e o Ø20 atropela.

Testei se a camada discriminava (as notas de Ø25 estariam sobre uma camada própria).
**Não discrimina** — Ø25 e Ø20 têm as mesmas camadas em volta (`EXO-TET`, `EXO-TET-CAM`).
O que separa é a posição: as 4 notas de Ø25 ficam em x≈113 e x≈128, as de Ø20 em x≈139-141.

## ACHADO QUE TRAVA O PEAK — o pavimento está desenhado duas vezes

Ao olhar as coordenadas das notas apareceu um padrão: elas vêm em pares deslocados
**exatamente 50 em Y** (86,27 e 136,27 · 90,21 e 140,21 · 82,37 e 132,37 …).

Testado na geometria: **94,5% dos trechos da metade de cima têm gêmeo idêntico 50 abaixo**
(467 de 494). Mas as duas metades não têm a mesma metragem — 1.034,8 m embaixo contra
799,6 m em cima.

Consequência: **qualquer metragem absoluta do Peak medida no modelspace inteiro está
contando o mesmo tubo duas vezes**, e como as duas cópias diferem, o mix também distorce.
Não dá para pontuar a rota 2 no Peak antes de resolver isso.

Não é cópia limpa (senão as metragens bateriam) nem plantas independentes (94,5% é
idêntico). As leituras possíveis são duas alas espelhadas, dois pavimentos-tipo, ou uma
cópia de referência que não deveria ser contada. **O desenho não decide — é pergunta para
o Hederson**, e é uma pergunta boa: específica, com número, e ele responde sim/não.

### Isso NÃO contamina Living e Edition

Conferi as duas antes de seguir. Os deslocamentos repetidos são de outra natureza:

- **Living**: dy = −5,68 (1.721×) e −11,36 (= 2 × 5,68). Distância de apartamento —
  é a repetição legítima dos finais dentro da mesma planta.
- **Edition**: dx ≈ 97,5 / 198,6 / −101,1, escala de planta inteira, sugerindo 3 cópias.
  Bate com a receita, que tem **3 linhas de DN20 e 3 de DN32** — três torres. A planta
  traz as três e a receita cobre as três. Consistente, não é duplicação.

Os números de 20,1 → 14,2 p.p. do extrator seguem válidos.

## BROOKLYN — dois achados que mudam o quadro

O DXF tem 430 MB e nunca tinha sido aberto (está registrado como não medido desde 03/07).
Aberto agora, com os scripts 33 e 35.

### 1. Nossa premissa no 5.3 estava errada

Afirmamos ao Hederson: *"nas obras Brooklyn e Peak não existe nenhum rótulo -PEX no
desenho"*. **No Brooklyn existem 36**, achados pelo regex da rota 1 sem nenhuma adaptação:

```
20 - PEX   30      25 - PEX    4      32 - PEX    2      (camada: Pipe Tags)
```

O padrão é o mesmo da Living, escrito com espaço em volta do hífen — que o regex já
aceitava. Não achamos antes porque **nunca rodamos o extrator neste arquivo**. Afirmamos
ausência sem ter procurado. Para o Peak a premissa continua correta (lá só há a nota).

**Segunda vez que erramos do mesmo jeito:** em 06/08 dissemos que "a SPHE não marca DN no
traço do ramal" e ele corrigiu com print. Agora dissemos que Brooklyn não tem rótulo.
Os dois erros são declarações de ausência baseadas em busca que não achou.
**Regra a adotar: não afirmar que um dado não existe sem dizer onde foi procurado.**

### 2. O Brooklyn não é um desenho AutoCAD da SPHE — é exportação de Revit

As 87 camadas com geometria são categorias do Revit em inglês:

```
Structural Connections 33.423   Walls 17.464   Structural Framing 2.740
Windows 2.342   Doors 1.968   Pipes 1.800   Ceilings 1.485
Pipe Accessories 1.476   Mechanical Equipment 997   Plumbing Fixtures 812
Pipe Insulations 549   Ducts 529   Pipe Fittings 433   Pipe Tags 271
Pex - TIGRE 128   Esgoto Série Normal - TIGRE 1.050
```

Consequências:
- **a convenção `PADRÃO_SPHE` não se aplica a este arquivo.** As camadas `HAF-TUB-___-___`
  somam **10,3 m** — resíduo de um DWG importado (existe a camada `LAYOUT-TIPO PADRÃO_dwg`
  com 1.588 m). O extrator atual mediria praticamente nada aqui;
- a geometria real de tubo está em `Pipes` (1.799,9 m) e `Pex - TIGRE` (127,8 m), misturada
  com esgoto e ar-condicionado — precisa de outro filtro;
- os rótulos estão em `Pipe Tags`, que no Revit é anotação **vinculada a um tubo
  específico**. O vínculo se perde no DXF, mas a posição da tag fica junto do tubo dela;
- pista a testar: exportação de Revit costuma desenhar tubo em linha dupla na escala real.
  Se for o caso aqui, **o DN sai da distância entre as duas linhas**, sem depender de
  rótulo nenhum. Seria a rota mais confiável das três — vale um probe.

E o de sempre: 30 tags de DN20 contra 4 de DN25 e 2 de DN32, enquanto a receita diz
DN20 58,6% / DN25 23,4% / DN32 18,0%. Contagem de rótulo não acompanha metragem, pela
terceira vez no mesmo dia.

## SITUAÇÃO

| | Living / Edition / Pamaris | Peak | Brooklyn |
|---|---|---|---|
| Origem do arquivo | AutoCAD, padrão SPHE | AutoCAD, padrão SPHE | **exportação Revit** |
| Rótulo `<DN>-PEX` | sim | não | **sim, 36** |
| Nota geral `Ø<DN>mm` | não | sim | sim |
| Camadas conhecidas | sim | sim | **não — categorias Revit** |
| Medição do metro | 14,2 p.p. (Living) | travada: planta duplicada | travada: camadas |

O quadro que tínhamos — "duas rotas, cada obra numa delas" — não se sustentou. São **três
situações**, e o Brooklyn nem é o mesmo tipo de arquivo.

## PRÓXIMOS PASSOS

1. **Perguntar ao Hederson sobre a duplicação do Peak** — destrava a pontuação da rota 2.
   Pergunta pronta: *"o arquivo TIP do Peak traz o pavimento desenhado duas vezes,
   deslocado 50 m em Y, com 94,5% de geometria idêntica. São duas alas, dois
   pavimentos-tipo diferentes, ou é cópia de referência que não deve entrar na conta?"*
2. **Corrigir o 5.3 com ele** — dizer que o Brooklyn tem sim os rótulos e que o erro foi
   nosso. Assumir erro por escrito já funcionou no caso do lavabo.
3. **Probe do tubo em linha dupla no Brooklyn** — se a exportação do Revit preservou a
   escala real, o DN sai da geometria e dispensa rótulo. É a hipótese mais promissora
   aberta hoje, e vale mais que insistir em proximidade.
4. O lado **AQ do Peak já pode ser extraído** sem ressalva: nota e planilha concordam que é
   DN20 puro. É a primeira parcela de metro que a rota 2 entrega.
