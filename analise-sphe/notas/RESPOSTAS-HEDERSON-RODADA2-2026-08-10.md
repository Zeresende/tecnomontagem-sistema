# Rodada 2 — respostas do Hederson (portal SPHE)

Extraído do Supabase em 10/08/2026. Duas tandas: 8 respostas em 08/08 (parciais) e as
13 finais em 10/08 entre 11:34 e 11:49. **Todas as 13 pendências abertas foram respondidas,
inclusive as 3 travas.**

Quando o mesmo item foi respondido duas vezes, vale a de 10/08 (mais detalhada). A de 08/08
está registrada abaixo como "1ª versão" quando acrescenta algo.

---

## BLOCO 5 — DN do ramal

### 5.1 — TRAVA — CRAVA (com ressalva)
**P:** Cada rótulo vale para um trecho inteiro do percurso — o tronco que sai do manifold —
e não só para o pedaço de tubo ao lado dele? Se sim, qual é a regra?

**R (10/08):** "O ponto sai do manifold reduzido e dependendo da ligação, após uma conexão
ele é reduzido para atender os pontos, normalmente após o Têe"

**R (08/08, 1ª versão):** "Depois do próprio manifold acontece a redução do Dn"

**Leitura:** confirma a hipótese topológica levantada em 06/08. O DN não é uma propriedade
do segmento mais próximo do rótulo — ele se propaga ao longo do percurso a partir do
manifold e **reduz depois do tê**. Regra implementável: montar o grafo do ramal, atribuir o
DN do rótulo ao tronco e reduzir a jusante de cada tê.
**Ressalva:** "dependendo da ligação" e "normalmente" — não é determinístico. Precisa ser
pontuado contra gabarito antes de virar regra fixa (script 25 já serve).

### 5.2 — RESPOSTA QUE PODE NÃO FECHAR A CONTA
**P:** Na Living, o desenho dá DN16 18% / DN20 41% / DN25 13% / DN32 28%. A compra real foi
DN16 12% / DN20 46% / DN25 20% / DN32 22%. O que entra na compra que não está no desenho?

**R:** "Por conta do tamanho do rolo que o fornecedor já tem definido, ele tem rolos
pré-definidos de 50 metros, 100 metros e 200 metros."

**Leitura:** ele deu a mesma resposta nas duas tandas, então é a leitura dele. Mas o
arredondamento por rolo **já está** no nosso modelo (ROUNDUP por rolo × 1,07) e explica
desvio de poucos pontos, não os 6 p.p. do DN16. **A conferir por conta própria antes de
voltar a perguntar:** aplicar ROUNDUP por rolo sobre a proporção desenhada e medir quanto
do gap fecha. Se sobrar diferença, a pergunta volta com o número na mão.

### 5.3 — CRAVA — SEGUNDO PADRÃO DE CODIFICAÇÃO DE DN
**P:** Em Brooklyn (7332) e Peak (QUA) não existe nenhum rótulo `-PEX` no desenho. Foi outro
desenhista, outra época, ou o DN está em outro arquivo?

**R:** "Em ambas as obras existe uma anotação informando o diâmetro da tubulação."
**Anexo `00 peak.png`** (lido na tela): nota em azul sobre a planta —
`TUBULAÇÕES DE PEX CAMINHAM POR TUBOS GUIAS EMBUTIDOS NA LAJE / AF - PEX. Ø25mm - TUBO GUIA: Ø40mm`

**Leitura:** a SPHE usa **dois** padrões, não um:
1. rótulo por trecho `<DN>-PEX` — Living, Edition, Pamaris;
2. **nota geral por sistema** `Ø<DN>mm` — Brooklyn, Peak.
O `Ø` é gravado como `%%C` no DXF, ou seja, **a busca antiga por `%%C` não estava errada —
estava aplicada na obra errada.** O extrator precisa das duas rotas.

---

## BLOCO 6 — Complemento vertical

### 6.1 — TRAVA — CRAVA E DERRUBA NOSSA HIPÓTESE
**P:** O complemento vale igual para a água fria? Na Living a AQ fica 15% abaixo da receita
e sua tabela explica quase exatamente essa diferença; a AF bate sem complemento nenhum.

**R:** "Resposta: Não. Existem pontos que não possuem água quente, por este motivo a
diferença de 15% no valor total"

**Leitura importante:** ele não confirmou nossa explicação — **corrigiu**. A razão 0,85 da
água quente não vem de metro vertical faltante, vem de **contagem de pontos**: nem todo
ponto tem água quente. A hipótese de 06/08 ("o complemento vertical explica 92% do buraco da
AQ") cai. O teste do complemento precisa ser refeito com os pontos de AQ descontados antes.

### 6.2 — CRAVA — a tabela virou multiplicador
**P:** Quantos pontos de cada tipo existem no apartamento tipo da Living?

**R:** Chuveiro 2 | Lavatório 3 | Vaso/caixa acoplada 3 | Pia de cozinha 2 | Tanque/máquina 1
"2 pias de cozinha, pois existe também a pia do terraço."

**Leitura:** com o 6.1, dá para separar quais pontos entram na AQ e quais só na AF —
vaso e tanque são os candidatos naturais a não ter água quente. É o teste que substitui
o teste do complemento.

### 6.3 — CRAVA
**P:** A descida de prumada de 1,50 m (item 2.2) e a descida do aéreo de 1,50 m (item 4.2)
são a mesma medida ou somam?

**R:** "Duas coisas que somam."

**Leitura:** fecha o risco de dupla contagem levantado em 06/08 — na direção oposta à que
supúnhamos. São **+3,00 m** nesse eixo, não 1,50.

---

## BLOCO 7 — Prumada

### 7.1 — CRAVA PELA METADE
**P:** Os blocos PRUM-PX-32 (17 prumadas × 20 pav) e os traços da camada PRU-F que os
rótulos marcam como DN20 — a prumada tem DN20 e DN32, ou PRU-F é outra coisa?

**R (10/08):** "Não"
**R (08/08):** "Pru-F se refere a outra coisa"

**Leitura:** resolve o cálculo — **não somar PRU-F como prumada PEX**. Mas ele disse o que
não é, sem dizer o que é. Resíduo aberto, de baixo impacto.

---

## BLOCO 8 — HM89 térreo e subsolo

### 8.1 — CRAVA
**R:** Subsolo Torre A: 7 | Térreo Torre A: 11 | Subsolo Torre B: 6 | Térreo Torre B: 9

**Leitura:** +33 unidades. O total da HM89 vai de 216 (tipo) para **249 unidades**.

### 8.2 — CRAVA
**P:** Térreo e subsolo usam os mesmos kits do tipo ou têm receita própria?
**R (10/08):** "Sim" — **R (08/08):** "Mesmos kits das unidades tipo"

**Leitura:** as 33 entram com a receita do tipo. Cálculo direto, sem levantamento novo.

---

## BLOCO 9 — As duas que voltaram da rodada 1

### 9.1 — CRAVA
**P:** A coluna "20º pav – duplex" com contagem 4 cobre a tubulação dos dois pavimentos do
duplex, ou o de cima entra em outro lugar?
**R:** "O Duplex é alimentado pelo 20º, não existe ramal que o alimenta pelo 21º."

### 9.2 — CRAVA
**P:** Quantos finais da HM89 têm lavabo (banheiro sem kit chuveiro)?
**R:** "Nenhum."

**Leitura:** fecha o item que nasceu do nosso erro de terminologia lavatório × lavabo.

---

## BLOCO 11 — Numeração de pavimento

### 11.1 — TRAVA — CRAVA
**P:** Quando a planilha diz "20º", ela se refere ao pavimento 20 do esquema, ou é o nome
que vocês dão ao último pavimento tipo?
**R (10/08):** "Ao pavimento 20 do esquema"
**R (08/08, 2×):** "Ela se refere ao 20º pavimento"

**Leitura:** convenção fixada. Planilha "20º" = pavimento 20 do esquema vertical (o que tem
os finais 3/4/5/6); o andar dos reservatórios é o 21. Protege as 5 regras da rodada 1 que
dependiam disso para entrar no andar certo.

---

## BLOCO 10 — Conferência e próximo passo

### 10.2 — SEM DATA
**P:** Qual obra da SPHE vem primeiro no teste em paralelo e quando ela chega?
**R:** "Ainda não chegou, mas assim que chegar já onformo"

**Leitura:** o piloto não tem data porque depende de entrar obra nova na casa dele. Não é
recusa — é fila. Consequência comercial: não dá para amarrar prazo de validação a
calendário; amarrar a evento ("primeira obra SPHE que entrar").

---

## PLACAR DA RODADA 2

**13 de 13 respondidas. As 3 travas caíram.**

| Resultado | Itens |
|---|---|
| Cravam como regra | 5.1, 5.3, 6.1, 6.2, 6.3, 8.1, 8.2, 9.1, 9.2, 11.1 |
| Cravam parcialmente | 7.1 (diz o que não é) |
| A conferir do nosso lado antes de reperguntar | 5.2 |
| Fora do nosso controle | 10.2 (depende de entrar obra) |

**Nenhuma pergunta nova foi gerada nesta leitura** — ao contrário da rodada 1, que abriu 13.
O mecanismo convergiu, como argumentado em 06/08.

## O QUE MUDA NO TRABALHO TÉCNICO

1. **5.1 destrava o extrator de DN** — propagação topológica a partir do manifold, redução
   depois do tê. Pontuar com o script 25 contra Living e Edition antes de fixar.
2. **5.3 abre uma segunda rota** — nota geral `Ø<DN>mm` (`%%C`) para Brooklyn e Peak.
3. **6.1 cancela o teste do complemento vertical como estava desenhado** — refazer com os
   pontos sem água quente descontados, usando a contagem do 6.2.
4. **6.3 vira +3,00 m**, não 1,50.
5. **HM89 passa a 249 unidades** com a receita do tipo (8.1 + 8.2), zero lavabo (9.2),
   sem travessa manifold/aquecedor (4.3 da rodada 1).
6. **11.1 libera codificar alocação por pavimento** no PADRAO_SPHE.yaml sem risco de
   deslocar andar.
