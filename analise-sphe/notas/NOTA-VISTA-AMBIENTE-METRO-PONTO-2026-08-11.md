# Vista → ambiente → metro por ponto (Living, 11/08/2026)

Script `47_vista_para_ambiente.py`. Mapa gravado em
`_analise/saida/vista_ambiente_20241385.csv`. Antecedentes:
`NOTA-PRANCHA-DETALHE-2026-08-11.md` e `NOTA-COMPLEMENTO-VERTICAL-2026-08-11.md`.

## O mapa

As 21 elevações da `7409-HID-PE-0011-DETTIP-R00` classificadas por ambiente:

| ambiente | vistas | vertical AF | vertical AQ |
|---|---|---|---|
| SHAFT / BARRILETE | 7 | 142,4 m | 40,8 m |
| BARRILETE / HIDRÔMETRO | 3 | 48,2 m | 37,1 m |
| BANHO | 5 | 29,7 m | 20,5 m |
| COZINHA / ÁREA DE SERVIÇO | 5 | 11,8 m | 1,1 m |

**Duas correções sobre o script 46, e as duas mudam o número.**

A primeira: o título mente. As duas maiores regiões que o 46 tratou como parede de
apartamento se chamam "VISTA A" e falam de hidrômetros, elevador, trocador de calor e
by-pass — é sala de hidrômetro, não ramal. Sozinhas respondem por 41,6 dos 87,1 m de
vertical AF que o 46 tinha contado como apartamento.

A segunda: a associação de texto por caixa envolvente vazava entre vistas vizinhas, e a
`VISTA DO SHAFT 02` chegou a ser classificada como BANHO com 140 m porque puxava rótulo
da vista do lado. Cada texto passou a pertencer a uma única vista, a de centróide mais
próximo dentro do raio da própria vista.

Resultado: **o vertical de parede de apartamento é 41,5 m (AF) e 21,6 m (AQ)** — não os
87,1 / 57,3 do 46. O número de ontem estava inflado pelo barrilete.

## Metro por ponto

Nos ambientes de apartamento (banho + cozinha/área de serviço), com 26 pontos rotulados,
dos quais 14 com água quente:

| | medido no desenho | tabela do Hederson (2.2/4.2) |
|---|---|---|
| AF | **1,60 m por ponto** | 1,00 chuveiro · 1,00 lavatório · 0,40 vaso |
| AQ | **1,54 m por ponto quente** | 1,00 chuveiro · 1,00 lavatório |

**A ordem de grandeza bate — o desenho dá cerca de 1,5× a tabela dele.** É a primeira vez
que o complemento vertical aparece como número medido, e não como regra de cabeça. A
diferença de 1,5× tem explicação plausível: o trecho medido inclui a curva de saída e o
pé de subida, enquanto a tabela dele parece ser a altura do ponto. Não é conclusão, é
hipótese.

**Precisão: baixa, e assumida.** 26 pontos é amostra pequena, e a contagem por rótulo de
texto não é confiável — a Vista G aparece com `vaso:6`, o que é anotação repetida, não
seis bacias. A contagem geométrica alternativa (pontas livres do grafo remontado) dá 137
pontas AF e 49 AQ, ou seja 0,30 e 0,44 m por ponta: também não serve, porque a
fragmentação cria ponta livre onde não há ponto. **O valor honesto hoje é "entre 1 e 2
metros por ponto", não 1,54.**

## Onde a conta não fecha, e o que isso acusa

Extrapolando pela contagem do item 6.2 (chuveiro 2 · lavatório 3 · vaso 3 · pia cozinha 2
· tanque 1, por apartamento × 8 apartamentos = 88 pontos, 56 com água quente):

| | falta na planta | previsto pelo desenho |
|---|---|---|
| AF | −5,4 m (não falta) | 1,60 × 88 = **140,6 m** |
| AQ | +43,7 m | 1,54 × 56 = **86,3 m** (1,98×) |

Nenhum dos dois fecha, e **os dois erram para o mesmo lado**: o desenho tem mais vertical
do que a planta está deixando faltar. Na água quente, o dobro. Na água fria, 140 m que
deveriam faltar e não faltam.

Quando duas contas independentes erram na mesma direção, o suspeito é a base comum. Aqui
a base comum é uma só: **`EXO-TET` como proxy do ramal, escolhido em 03/07 porque deu
1,01× na água fria.** Se o ramal de água fria realmente precisa de ~1,6 m de vertical por
ponto, a medição só do teto teria que ficar uns 26% curta — e ela deu 1% acima. **O
casamento de 1,01× que nos fez adotar esse proxy tem cara de coincidência, não de
validação.** Isso não invalida o trabalho de 03/07, mas tira dele o status de prova.

## Próximo passo

O gargalo deixou de ser o complemento vertical e passou a ser o **denominador**: o que
exatamente o Hederson conta como "ramal" quando levanta pela planta. É pergunta curta e
confirmável, do tipo que ele responde rápido — e é a única que resolve os dois desvios de
uma vez. Enquanto ela não vier, o número de metro por ponto fica registrado como faixa
(1 a 2 m), utilizável para pré-levantamento com ressalva, não para cravar.
