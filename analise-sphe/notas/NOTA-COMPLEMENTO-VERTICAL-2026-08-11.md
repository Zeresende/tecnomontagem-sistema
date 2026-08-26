# Remontagem nas vistas e o teste da água quente da Living (11/08/2026)

Scripts novos: `45_regioes_prancha_det.py` (recorta a prancha em regiões e confere
escala), `46_complemento_vertical_living.py` (remonta o trecho e roda o teste).
Antecedente: `NOTA-PRANCHA-DETALHE-2026-08-11.md`.

## A pergunta

O script 18 mediu, em 03/07, que a camada `HAQ-TUB/EXO-TET` do PVTIPO da Living entrega
0,85× a receita real de ramal de água quente — faltam 15%. O lado frio dá 1,01×. A
hipótese registrada desde então: os 15% são o complemento vertical, que a planta não
desenha. Agora que sabemos que a descida está nas pranchas DET, dá para testar.

## O que foi feito

**Recorte.** A `7409-HID-PE-0011-DETTIP-R00` tem 1.435,0 m de tubo PEX em 80 regiões.
Separadas por aglomeração espacial e classificadas por altura (≤ 4,5 m) e razão
vertical/horizontal (≥ 0,8):

| | regiões | metro |
|---|---|---|
| elevação / vista | 35 | 661,9 m |
| planta / ampliação | 45 | 773,0 m |

O recorte não é cosmético: **em planta, "segmento vertical" é a direção norte-sul, não
altura.** Contar altura na região de planta seria erro grosseiro. A escala foi conferida
contra as cotas DIMENSION que caem dentro de cada região — 18 elevações têm cota, e só 2
saem de 1,00 ± 10%.

**Segunda separação, que muda o resultado:** dentro das elevações, o shaft não é o ramal
do apartamento. O item 2.1 já disse que o metro da prumada está dentro da receita do ramal
aéreo. Vista de shaft, hidrômetro e recalque ficaram fora da conta: são 405,3 m dos 661,9.
Sobram **256,7 m em 19 vistas de parede**.

**Remontagem.** Os 4.110 cacos dessas vistas viram 1.125 trechos pelo `construir`/`fundir`
do script 29. Trechos verticais (≥ 80% da extensão): 228.

## Os números

| | AF (fria) | AQ (quente) |
|---|---|---|
| receita real, por pavimento (8 aptos) | 398,0 m | 281,8 m |
| medido no PVTIPO, camada EXO-TET | 403,4 m | 238,1 m |
| **falta** | **−5,4 m (−1%)** | **+43,7 m (+15%)** |
| vertical remontado nas vistas de parede | **87,1 m** | **57,3 m** |
| vertical remontado nas vistas de shaft | 142,4 m | 41,3 m |

Estável: variando a tolerância de nó em 0,01 / 0,02 / 0,05 m, o vertical de parede fica
em 87,1–92,4 (AF) e 57,3–61,2 (AQ). **O resultado não é artefato do parâmetro de snap.**

## O que se conclui

**1. A remontagem funciona, e o vertical é medível.** Aparecem trechos de 2,81 m —
exatamente o pé-direito de 2,80 que o Hederson declarou. Contra a tabela dele (1,00
chuveiro/lavatório · 0,40 vaso · 1,50 entrada e descida), **41% a 46% dos trechos
verticais caem em cima de um dos valores com 10 cm de tolerância**. É sinal, não ruído:
antes de remontar, comparar não fazia sentido nenhum (o DXF entrega caco de mediana 6 mm).

**2. A hipótese de 03/07 não sobrevive na forma em que foi escrita.** Se o buraco fosse o
complemento vertical ausente da planta, o lado frio precisaria estar ainda mais curto que
o quente — porque **a mesma prancha mostra mais vertical na água fria (87,1 m) do que na
quente (57,3 m)**. E a água fria não tem buraco nenhum: fecha em −1%. Os 15% da água
quente são outra coisa.

Isso conversa com o que o próprio Hederson respondeu no item 6.1, e que já tinha derrubado
metade da hipótese: *"existem pontos que não possuem água quente"*. O buraco é de
contagem de ponto, não de metro faltante — e agora há uma segunda evidência independente,
vinda do desenho, apontando na mesma direção.

**3. O que ainda impede fechar um número:** não sabemos a **cobertura das vistas**. A
prancha tem Vista A a K, mais VISTA A/B/D em caixa alta e duas "Espelhada" — e nada diz
quantos apartamentos ou quantos ambientes por pavimento cada uma representa. Sem esse
mapa, comparar total da prancha com receita por pavimento é comparar coisas de escopo
diferente. Os 57,3 m contra 43,7 m (1,31×) **não são um resultado**, são duas grandezas
que ainda não estão na mesma base. Mesmo tipo de erro que a armadilha de escala de 10/08 —
por isso não estou tratando o 1,31× como resposta.

**4. Ressalva que enfraquece os dois lados:** toda a comparação usa `EXO-TET` como proxy
do ramal, escolha feita em 03/07. O total de AF em todas as camadas é 974 m = 2,45× a
receita. Se o proxy estiver ligeiramente errado, tanto o buraco de 15% quanto a ausência
de buraco no AF mudam de tamanho.

## Próximo passo, concreto

Mapear vista → ambiente e cruzar com as contagens do RESUMO (o item 6.2 deu os pontos do
apto tipo da Living: chuveiro 2 · lavatório 3 · vaso 3 · pia cozinha 2 · tanque 1). Com o
ambiente identificado, o vertical vira **metro por ponto**, que é a unidade da tabela do
Hederson e a única que permite multiplicar pela contagem do pavimento. Aí o teste fecha ou
não fecha de verdade.

Achado lateral a conferir: o `DETALHE TÍPICO DA LIGAÇÃO DE PRUMADAS E RAMAIS NA VERTICAL`
existe na prancha, com cotas de 1,50 · 1,50 · 1,00 m — os mesmos números da tabela dele.
Mas os diâmetros escritos ali são 75/100/150, ou seja, **é o detalhe do esgoto, não do
PEX**. Pode ser coincidência de altura de laje; não usar como confirmação.
