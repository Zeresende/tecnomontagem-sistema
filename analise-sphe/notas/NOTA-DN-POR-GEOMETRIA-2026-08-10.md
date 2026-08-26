# Rota 3 — o DN sai da geometria no Brooklyn (10/08/2026)

Scripts `36_probe_linha_dupla.py` (teste) e `37_dn_por_geometria.py` (extrator).

## A hipótese e por que valia testá-la

O probe 35 mostrou que o Brooklyn é exportação de Revit. Exportação de Revit em nível de
detalhe Fino desenha o tubo em **linha dupla na escala real** — se fosse o caso aqui, a
distância entre as duas linhas seria o diâmetro, e o DN sairia da geometria.

Isso importa porque as duas rotas anteriores morrem no mesmo ponto: **contagem de rótulo
não acompanha metragem**. Um rótulo de DN32 carrega 5,7 a 9,3 vezes mais tubo que um de
DN16, e qualquer método por proximidade trata os dois com o mesmo peso. Uma rota que lê o
diâmetro direto da geometria não herda esse problema.

## VEREDITO: NÃO CONFIRMADA — o sinal existe, mas não é atribuível

> **Correção registrada.** A primeira versão desta nota dizia "CONFIRMADA" com base só no
> histograma, antes de o teste decisivo terminar. Estava errado, e a correção está abaixo.
> O erro de método é a lição principal: **pico em histograma agregado não prova atribuição
> por elemento.** Ver a seção "o que derrubou".

Histograma dos espaçamentos entre linhas paralelas no Brooklyn, por metragem:

| espaçamento | metros | % | leitura |
|---|---|---|---|
| **0,0200** | 292,2 | 18,9% | **DN20** |
| **0,0250** | 296,1 | 19,2% | **DN25** |
| **0,0300** | 235,3 | 15,3% | **DN32** (bucket de 5 mm cobre 0,032) |
| 0,0650 | 163,4 | 10,6% | provável esgoto ou camisa |
| 0,0400 | 103,2 | 6,7% | a classificar |

**Os três picos dominantes caem exatamente sobre os três DNs que a obra usa.** A receita do
Brooklyn tem DN20, DN25 e DN32 e nenhum DN16 — e o histograma não tem pico em 0,016.

Dados da leitura: 9.251 segmentos nas camadas `Pipes` (8.419) e `Pex - TIGRE` (812), com
85,8% deles com vizinho paralelo. Desenho em metros, extensão 80,0 × 69,8.

## O QUE DERRUBOU

O histograma é sugestivo, mas o extrator (script 37) reprovou nos dois testes que importam.

**Contra o gabarito da planilha:**

| | DN16 | DN20 | DN25 | DN32 | erro |
|---|---|---|---|---|---|
| medido pela geometria | 6,8% | 32,4% | 35,1% | 25,7% | **52,4 p.p.** |
| receita | 0,0% | 58,6% | 23,4% | 18,0% | — |

Pior que as rotas por rótulo (14,2 na Living, 30,0 na Edition). E o método **inventa
DN16 onde a obra não tem nenhum** — 60,7 m atribuídos a uma bitola inexistente, que é a
prova mais direta de falso positivo. Além disso, 42,2% da metragem pareada não cai perto
de diâmetro nenhum.

**Contra o rótulo — o teste que eu mesmo defini como prova:** concorda em 1 de 3 bitolas.
Espaçamentos brutos do par mais próximo de cada tag:

- tag **DN20** (30 tags): 0,040 aparece 12×, 0,020 aparece 9×, 0,100 3×
- tag **DN25** (4 tags): 0,025 2×, 0,032 1×
- tag **DN32** (2 tags): 0,032 1×, 0,025 1×

O diâmetro verdadeiro **está lá** — 0,020 perto de tags DN20, 0,025 perto de DN25, 0,032
perto de DN32. Mas convive com outros espaçamentos que aparecem mais. Perto de tag DN20 o
valor mais frequente é 0,040, não 0,020. Hipótese plausível para o 0,040: o tubo-guia que a
própria nota da obra cita (`AF - PEX. Ø20mm - TUBO GUIA: Ø32mm`), ou dois tubos lado a lado.

**Filtrar por camada não resolve:** só `Pex - TIGRE` dá 63,2 p.p.; só `Pipes` dá 52,0.

## LIÇÃO DE MÉTODO

Declarei confirmado ao ver três picos caírem sobre os três DNs da obra, antes de o teste de
atribuição terminar. **Estrutura agregada não é o mesmo que atribuição por elemento.** Um
histograma pode ter picos nos valores certos e ainda assim não permitir dizer qual DN é cada
trecho — que é exatamente o que o extrator precisa. É o terceiro erro do mesmo dia na mesma
família: afirmar antes de a evidência fechar.

## O CONTROLE QUE DÁ VALOR AO RESULTADO

O mesmo teste rodou na Living, que é AutoCAD no padrão SPHE:

| DN do rótulo | espaçamento mediano | razão | esperado |
|---|---|---|---|
| 16 | 0,0750 | 1,00 | 0,80 |
| 20 | 0,0750 | 1,00 | 1,00 |
| 25 | 0,1000 | 1,33 | 1,25 |
| 32 | 0,1000 | 1,33 | 1,60 |

Há um degrau — bitola maior, traço mais largo —, mas **os valores são 3 a 4 vezes o
diâmetro real** e só existem dois níveis para quatro bitolas. É convenção de traço do
desenhista, não escala. O histograma da Living também não bate com esses valores, o que
reforça a leitura de artefato.

**Conclusão do controle: em desenho AutoCAD da SPHE a geometria não carrega DN. No Revit,
carrega.** É a diferença entre desenhar um símbolo e modelar um objeto.

## ONDE ISSO DEIXA O BROOKLYN

| Obra | Como o DN é lido | Estado |
|---|---|---|
| Living / Edition / Pamaris | rótulo `<DN>-PEX` por trecho | 14,2 p.p. na Living, limitado pela descida não desenhada |
| Peak | nota geral `Ø<DN>mm` | travado: pavimento desenhado duas vezes |
| Brooklyn | rótulo (36 tags) + nota + geometria | **rota por geometria reprovada; sobra o rótulo, ainda não pontuado** |

O Brooklyn segue como a obra menos resolvida. A rota por geometria era a aposta de contorno
e não passou.

Sobre o item 14.2 da rodada 3 — se o BIM está virando padrão: **não há base para dizer que
seria boa notícia.** O modelo até carrega o diâmetro, mas neste arquivo, exportado para
DXF, o diâmetro não chegou de forma utilizável. A pergunta continua válida; a leitura dela
é que muda: BIM não é atalho automático.

## TENTATIVA 2 — LEITURA POR BLOCO (script 38): TAMBÉM REPROVADA

Hipótese: no Revit cada tubo é um objeto, então as duas linhas de um mesmo tubo estariam
dentro do mesmo `INSERT` — o par seria **dado**, não procurado por proximidade.

**A premissa não se sustenta neste arquivo, e o motivo é claro:**

| | metragem | % |
|---|---|---|
| solta no modelspace | 1.045,4 m | **65,7%** |
| dentro de bloco | 544,6 m | 34,3% |

E os 153 blocos que existem **não são tubos, são conexões.** Os nomes entregam:

```
Conexao Fixa Femea - Pex - Agua Fria_Quente - MEP
Joelho com Base Fixa - Pex - Agua Fria_Quente - MEP
Joelho 45_90 - Pex - Agua Fria_Quente - MEP - Tigre
```

Ou seja: **a exportação preservou as peças como objeto e desenhou os trechos de tubo como
linhas soltas.** O tubo — que é o que precisamos medir — é exatamente o que não virou bloco.

Resultado contra o gabarito: **57,0 p.p.**, pior que os 52,4 da leitura por segmento.
51,9% da metragem pareada não cai perto de diâmetro nenhum.

**O único sinal positivo, e é pequeno:** das 30 tags de DN20, apenas 6 tinham bloco por
perto — e nessas o espaçamento mediano deu **0,0208**, lido corretamente como DN20. As tags
de DN25 e DN32 não tinham bloco nenhum por perto. Confirma que **onde há bloco, o
espaçamento é mesmo o diâmetro** — mas a cobertura é pequena demais para virar método.

## O QUE AINDA PODE SALVAR A ROTA

1. **Separar o tubo-guia do PEX.** O 0,040 perto de tags DN20 e o pico de 0,065 são
   candidatos a camisa. Se houver como distinguir os dois pares (um dentro do outro, mesmo
   eixo), o interno é o PEX e o problema vira geometria concêntrica, não proximidade.
2. ~~Ler por bloco~~ — **testado em 10/08 e reprovado** (ver acima).
3. **Pedir o arquivo nativo** (RVT ou IFC) em vez do DXF. Em IFC o diâmetro é propriedade
   explícita. Depende da resposta do item 14.1 sobre qual arquivo eles usam. Com duas
   tentativas de inferência reprovadas, **este passou a ser o caminho mais provável.**

## SUBPRODUTO TESTADO — inventário de conexões: existe, mas não cruza

Scripts `39_conexoes_por_bloco.py` (inventário) e `40_probe_atributos.py` (atributos).

### O inventário funciona, depois de normalizado

Primeira leitura assustou: **2.780 nomes distintos para 2.930 instâncias**, quase um nome
por peça. O Revit carimba um identificador único em cada objeto:

```
Cotovelo - PEX - Padrão-V655-772_925 N_O__2º PAV_ TIPO - HIDRÁULICA
Cotovelo - PEX - Padrão-V656-772_925 N_O__2º PAV_ TIPO - HIDRÁULICA
```

Removido o identificador, sobram **14 famílias limpas** e 305 peças PEX na camada
`Pipe Fittings`, num pavimento:

| qtd | família |
|---|---|
| 103 | Cotovelo - PEX - reduzido-4Ø |
| 97 | Conexao Fixa Femea - Pex — Tigre |
| 47 | Cotovelo - PEX - Padrão |
| 39 | Cotovelo - PEX - reduzido-teto |
| 6 | Joelho 45_90 - Pex — Tigre |
| 6 | Luva Reducao - Pex — Tigre |

### O que impede o cruzamento

**1. O DN não está em lugar nenhum.** Zero dos 2.930 nomes traz a bitola. E o probe de
atributos fechou a última porta: **0 de 2.876 INSERTs de conexão têm atributo**. Não está
no nome nem em parâmetro de bloco.

Isso mata o cruzamento, porque a planilha organiza conexão **por bitola**:
`COTOVELO C/ BASE FIXA 16MM` = 904 peças, `20MM` = 236, `25MM` = 472 — três linhas
distintas. Sem o DN, o inventário diz **que peça é** mas não **a qual linha do orçamento
ela pertence**.

**2. O vocabulário não bate.** A planilha diz `COTOVELO C/ BASE FIXA CORPO EXTRA LONGO`;
o bloco diz `Joelho com Base Fixa` e também `Cotovelo - PEX - reduzido-4Ø`, que não tem
correspondente óbvio em nenhuma linha. Mesma família de armadilha do lavatório × lavabo:
duas casas nomeiam a mesma peça de formas diferentes.

**3. A ordem de grandeza não fecha.** 305 peças por pavimento contra cerca de **14.000
conexões** somadas na planilha (880 no RAMAL + 4.992 nos KITS + 8.138 nos CHICOTES). Mesmo
com vinte pavimentos daria 6.100 — menos da metade. Ou o desenho não traz todas as peças,
ou o pavimento não é representativo.

### Conclusão

O desenho do Brooklyn identifica **que peça é**, mas não **de que bitola**. Sem bitola não
há cruzamento com a planilha, e o inventário fica como mapa de tipos, não como quantitativo.

**Com isto, as três tentativas de extrair algo do DXF do Brooklyn se esgotaram:** tubo por
segmento (52,4 p.p.), tubo por bloco (57,0 p.p.) e conexão por nome de bloco (sem DN).
O que sobra é pedir o **arquivo nativo, RVT ou IFC**, onde diâmetro é propriedade explícita
do objeto — exatamente o que o item 14.1 da rodada 3 pergunta.

**Recomendação para a rodada 3:** o item 14.1 hoje pergunta se o arquivo que temos é o de
trabalho. Vale considerar acrescentar o pedido direto do RVT ou IFC, já que agora se sabe
que nenhuma inferência sobre o DXF funciona. Decisão do José — a página está no ar.

## RESSALVAS TÉCNICAS

1. **Metragem em dobro.** Cada par é contado dos dois lados. O mix percentual não sofre, o
   valor absoluto sim — dividir por 2 antes de usar como metro.
2. **A camada `Pipes` mistura sistemas.** O pico de 0,065 (10,6% da metragem) não é PEX de
   água. Filtrar por camada, porém, piora o erro em vez de melhorar.
3. **Um pavimento só.** Vale o mesmo alerta do Peak: conferir se o arquivo traz o pavimento
   uma vez antes de extrapolar metro absoluto.

## CACHE

O DXF tem 430 MB e a leitura leva cerca de 10 minutos. O script 37 grava os segmentos em
`_analise/saida/cache_segs_<obra>.json` na primeira passada; as seguintes usam o cache.
Use `--recarregar` para forçar releitura.
