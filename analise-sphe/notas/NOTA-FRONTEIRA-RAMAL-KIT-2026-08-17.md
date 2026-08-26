# A fronteira ramal/kit tem nome — e o desenho quase não a mostra (17/08/2026)

Scripts novos: `55_fronteira_registro.py` (inventário do registro nas 5 obras + tentativa de
corte topológico na planta) e `56_registro_nas_vistas.py` (corte na altura do registro dentro
das vistas da prancha DET).

## A resposta

Rodada 4, item 16.1, respondido em 17/08 às 08:36:

> "A descida está no ramal, do registro gaveta para frente segue no kit."

Perguntamos "ramal ou kit" e oferecemos as duas opções. Ele deu uma terceira, e melhor: **a
fronteira não é um tipo de tubo nem uma camada — é uma peça física do desenho.** Isso troca
uma convenção de planilha por um critério verificável, e explica de uma vez por que a receita
do kit muda com o DN do ramal (nota de 12/08): o kit começa numa peça cujo diâmetro é o do
ramal que chega nela.

Ele não respondeu a segunda frase — se a metragem corre de centro a centro ou peça a peça.
Essa metade continua aberta e vale 90,2 m num pavimento da Living.

## O que a resposta quebra

| Living, por pavimento | AF | AQ |
|---|---|---|
| receita real de ramal | 398,0 m | 281,8 m |
| medido na planta, camada `EXO-TET` | 403,4 m (−1%) | 238,1 m (+15% de buraco) |
| vertical remontado nas vistas de parede | 87,1 m | 57,3 m |

Se a descida inteira entra no ramal, a água fria vai a 490,5 contra 398 de receita — **+23%**,
e o "bate em 1%" que sustenta o proxy `EXO-TET` desde 03/07 cai. A água quente, ao contrário,
fecharia. Os dois lados só se acertam se parte do vertical estiver **depois** do registro.
Daí o teste.

## Teste 1 — corte topológico na planta: REPROVADO, e não por bug

A ideia direta seria cortar o grafo no nó do registro e medir montante × jusante. Não roda:

- 36 manifolds como raiz, ponte de 0,25 m, e o alcance na Living é **24,7 m de 973,5 (2,5%)**,
  antes de aplicar corte nenhum.
- É o mesmo 3,6% que o script 30 mediu em 10/08, e a causa está escrita lá: **a planta não
  desenha as descidas verticais.** A rede não fecha porque falta justamente o trecho que a
  pergunta 16.1 trata.

Fica registrado como limite conhecido no `PADRAO_SPHE_ARQUIVOS.yaml`
(`corte_topologico_na_planta: reprovado`). O corte precisa acontecer onde a descida existe:
nas vistas.

## Teste 2 — corte na altura do registro, dentro das vistas de parede

Para cada trecho vertical remontado nas vistas de parede, procura registro sobre a mesma
coluna (±0,35 m em x) e divide: acima é ramal, abaixo é kit.

| obra | registros na região | descidas cortadas | acima AF/AQ | abaixo AF/AQ | vertical **sem** registro AF/AQ |
|---|---|---|---|---|---|
| Living | 3 | 4 | 1,0 / 1,0 | 0,1 / 0,1 | **86,0 / 56,2** |
| Edition | 6 | 15 | 2,1 / 2,8 | 1,7 / 3,5 | **114,0 / 95,5** |
| Pamaris | 8 | 18 | 1,2 / 3,6 | 1,3 / 7,4 | **16,0 / 37,8** |
| Peak | 1 | 2 | 0,6 / 0,0 | 0,6 / 0,0 | **47,5 / 24,6** |

**O resultado é o mesmo nas quatro obras: o registro não está sobre a descida.** Ele corta
menos de 5% do vertical de parede em qualquer uma delas. Não é ruído de tolerância — são
poucos registros, e eles estão em outro lugar.

Onde eles estão, medido: na Living, das marcas que caem dentro de uma vista, **32 são de
shaft e 3 de parede**. Na Pamaris o shaft tem 44 descidas cortadas (12,7 m acima e 41,6 m
abaixo no AF), o que desenha um registro no alto da coluna, não junto do ponto.

## O que isso significa, com honestidade

O registro de gaveta que o desenho mostra é o **registro geral** — do shaft, da entrada do
apartamento e do manifold. Não há um registro por ponto de utilização: na Living o pavimento
tem **15 registros encostados no tubo para 88 pontos** (11 pontos por apto × 8 aptos, contagem
do item 6.2).

Isso deixa a frase dele com duas leituras, e elas dão resultados opostos:

1. **Registro geral (shaft/entrada).** Então tudo dentro do apartamento é kit — e a aba RAMAL
   AÉREO da Living, com 398 m por pavimento (≈50 m por apartamento), não teria o que conter.
   Não fecha.
2. **Registro do ambiente** — o que a receita do kit chama de `RP DOCOLBASE 1/2` na Living e
   `BASE REG PRESSAO MVS 3/4 DN20-B` no Brooklyn. Fecha conceitualmente: o kit começa no
   registro do ambiente, e a descida até ele é ramal. Mas esse registro **não está desenhado
   sobre as descidas** nas vistas de parede das quatro obras medidas.

A única obra que rotula a fronteira é a **Brooklyn** — e só pelo nome do bloco, porque a
geometria dela não entra: o `56` leu 0 segmento de tubo na prancha DETIPO, o que era esperado
desde 11/08 (a Brooklyn é exportação de Revit, não AutoCAD SPHE, e as camadas de tubo não
seguem `HAF-TUB`/`HAQ-TUB`). O que dá para usar lá é o nome do bloco, que carrega o contexto —
`Registro de gaveta DocolBase - ... - MANIFOLD A_S_ - FINAIS B2_B1_A1_A2`,
`- VISTA DA COZINHA E A_S - FINAL B3`, `- DETALHE DO SHAFT`. Ou seja, registro no manifold,
na cozinha/área de serviço e no shaft. Nenhum em vista de banheiro.

## Onde o registro aparece, por obra (inventário completo)

| obra | como o registro aparece |
|---|---|
| Living | bloco `Registro de gaveta ABNT DocolBásicos ... VISTA SHAFT 001` (11) + `HI-RG-40-1` (9) + textos `RG` |
| Edition | bloco `Registro de gaveta ABNT DocolBásicos ...` (9) + texto `REGISTRO - VISTA LATERAL` |
| Brooklyn | bloco `Registro de gaveta DocolBase`, **com o contexto no nome** (manifold, cozinha/AS, shaft) |
| Pamaris | bloco `REGISTRO DE GAVETA FRONTAL` (17) |
| Peak | só texto (`RG`, `REGISTRO DE PRESSÃO (VISTA E PLANTA)`) — sem bloco próprio |

Vale para o extrator: em 4 das 5 o registro é bloco nomeado e localizável. No Peak é texto,
e ali a fronteira teria de vir de outro lugar.

## O que fica pendente, e por quê

**Rodada 5, item 19.1** — qual registro é a fronteira: o geral do apartamento ou o do
ambiente. A pergunta agora carrega evidência dura (15 registros para 88 pontos) em vez de
teoria, e o resultado dela é binário para o sistema.

**Rodada 5, item 19.2** — a régua: centro a centro ou peça a peça. Ele não respondeu essa
metade, e o vão de conexão continua fora da metragem até ela voltar.

## Ressalvas do método

1. O casamento registro × descida usa ±0,35 m em x e 0,15 m de folga em y. Afrouxar isso não
   muda o quadro: o vertical **sem** registro é uma ordem de grandeza maior que o cortado em
   todas as obras — não é questão de tolerância.
2. `55` e `56` percorrem INSERT só com translação (mesma simplificação do script 45). Bloco
   rotacionado sai de lugar. Como o registro é um símbolo pequeno, o erro é da ordem do
   símbolo, não do trecho.
3. A regex de registro é ampla de propósito (`registro|gaveta|RG|REG GAV`) e pega texto de
   legenda e de nota geral. Por isso o script mede a distância ao tubo e reporta as faixas:
   na Living, 12 das 50 marcas estão a mais de 2 m de qualquer tubo.
