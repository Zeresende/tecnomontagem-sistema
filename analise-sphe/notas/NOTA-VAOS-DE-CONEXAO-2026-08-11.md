# Os tês estão sendo contados? (pergunta do José, 11/08/2026)

Script `49_conta_os_tes.py`. A pergunta tem duas leituras, e a resposta é diferente
para cada uma.

## Como PEÇA: sim, e sempre estiveram

O tê é uma conexão, e entra pela linha de conexão da planilha, não pela metragem de tubo.
As linhas existem e são explícitas:

| obra | linha | unidades |
|---|---|---|
| Living | `TE PEX 20-20-20` | 328 |
| Peak Torre A | `TE PEX 20-20-20` | 76 |
| Peak Torre B | `TE PEX 20-20-20` | 88 |

O script 14 reproduziu as linhas de conexão com **erro zero em 77 de 77** em 03/07, e a
fórmula delas é diferente da do tubo: conexão é soma exata de receita × contagem, sem o
×1,07 e sem arredondamento por rolo. Então esse lado está fechado desde junho.

Vale notar a densidade: **2 tês por apartamento na Living** (328 para 164) e **0,35 no
Peak** (164 para 466). O ramal tem pouquíssimo tê.

## Como METRO: não, e isso pesa

O desenho **corta o tubo em cada conexão**. Fica um vão entre a ponta que chega e a ponta
que sai, e esse vão não está em camada nenhuma — ninguém o mede. A "ponte de 15 a 25 cm"
que o script 30 usa desde 10/08 existe para *religar* o percurso e poder propagar o DN;
ela nunca somou o vão à metragem. Religava e seguia.

Medindo os vãos — pares de pontas livres entre 3 e 60 cm:

| | Living (1 pavimento) | Peak (2 torres, sem as plantas de furo) |
|---|---|---|
| vãos encontrados | 626 | 224 |
| metro não desenhado | **90,2 m** | **41,6 m** |
| vão médio · mediana | 0,144 · 0,101 m | 0,186 · 0,110 m |
| por sistema | AF 62,6 · AQ 27,6 | AF 38,9 · AQ 2,8 |
| receita do mesmo pavimento | 679,8 m | 445,2 m |
| **peso do vão** | **13,3%** | **9,3%** |

## Três ressalvas, todas importantes

**1. Os vãos não são tês.** A Living tem 626 vãos num pavimento cuja receita prevê 16 tês.
Os vãos são *toda* conexão — joelho, luva, adaptador — mais os pontos onde o desenho
simplesmente interrompe o traço. Chamar o conjunto de "tês" subestima em quarenta vezes.

**2. Não sei se esse metro deve ser somado, e a resposta não está no desenho.** Se o
Hederson mede o percurso de centro a centro, o vão é tubo na conta dele e nos falta. Se
ele mede peça a peça, o vão é ocupado pela conexão e não é tubo. **É a mesma pergunta do
item 16.1 vista de outro ângulo** — o que exatamente entra na linha de ramal.

**3. Somar os vãos não conserta os desvios conhecidos, e piora um.** Na Living a água
quente tem 43,7 m faltando e o vão de água quente vale 27,6 m — cobriria 63%. Mas a água
fria não tem buraco (fecha em 1%) e o vão dela vale 62,6 m, o que jogaria o AF para 1,17×.
Além disso os 90,2 m são de **todas as camadas**, não só da `EXO-TET` — então esse número
é teto, não medida do ramal.

## Onde isso deixa a coisa

O vão de conexão é a terceira quantidade que aparece na mesma faixa de 10 a 15% e que
depende de uma única definição que não temos: o complemento vertical (1 a 2 m por ponto),
a diferença de camada no Peak (1,90× no AF) e agora o vão (13,3% e 9,3%). **As três se
resolvem com a resposta do 16.1.** Nenhuma delas justifica pergunta nova ao Hederson —
justifica, no máximo, acrescentar uma linha à evidência do 16.1 dizendo que o desenho
corta o tubo na conexão e perguntando se a metragem dele é de centro a centro.
