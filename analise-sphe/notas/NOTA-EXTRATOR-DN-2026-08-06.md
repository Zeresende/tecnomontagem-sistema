# Extrator de ramal por DN — o que foi construído e até onde está validado

**Data:** 06/08/2026 · origem: resposta 4.1 do Hederson

## O erro que foi corrigido

O script `18_dxf_vs_ramal.py` procurava o DN na notação `%%C` e classificava 21% da
geometria. Concluímos daí que "a SPHE não marca DN no traço" e tratamos o DN como
conhecimento tácito do projetista.

Estava errado. A SPHE escreve o DN como **texto `<DN>-PEX`** na própria planta.

## Scripts novos

- `21_probe_rotulos_dn.py` — inventaria como o rótulo está gravado.
- `22_ramal_por_dn.py` — extrai metros de ramal por DN a partir do rótulo.

## O que o probe mostrou (HM89 TIPA)

120 rótulos resolvidos em modelspace. O achado que sustenta o método: **o rótulo em
geral está na MESMA camada da geometria que descreve** — 84 dos 120 em
`...HAF-TUB-___-EXO-TET`. Isso permite casar por camada, não por chute de proximidade.

Por isso o script 22 atribui em duas etapas, da mais segura para a menos:
1. rótulo e geometria na mesma camada, pelo mais próximo;
2. sobra → rótulo mais próximo de qualquer camada de tubo, dentro de 8 unidades.

O que não casa fica em NÃO-CLASSIFICADO. Nunca é chutado para um DN.

## Cobertura obtida

| Desenho | classificado | mesma camada | por raio | sem rótulo |
|---|---|---|---|---|
| HM89 TIPA | **84,3%** | 75,9% | 8,4% | 15,7% |
| HM89 TIPB | **84,3%** | 75,9% | 8,4% | 15,7% |
| Living PVTIPO | **64,5%** | 54,7% | 9,7% | 35,5% |

Método antigo: 21%. TIPA e TIPB dão idêntico, coerente com duas torres iguais de 12 finais.

A convenção não é exclusiva da HM89 — Living (236 rótulos), Edition (319) e Pamaris (232)
também usam. **Brooklyn e Peak: zero rótulos** — ou usam outra convenção, ou o ramal está
em outro arquivo. Investigar antes de generalizar para toda a SPHE.

## Validação contra o gabarito da Living — NÃO passou ainda

Único teste que vale: comparar com a compra real do Hederson.

| DN | planilha (líquida) | DXF | diferença |
|---|---|---|---|
| 16 | 11,9% | 17,7% | +5,8 p.p. |
| 20 | 46,2% | 40,8% | −5,4 p.p. |
| 25 | 19,8% | 13,4% | −6,4 p.p. |
| 32 | 22,1% | 28,1% | +6,0 p.p. |

Compra real da aba RAMAL: 15.150 m brutos, 14.159 m líquidos (÷1,07).

**Leitura honesta:** a ordem de grandeza está certa e o DN20 domina nos dois, mas erra
±6 p.p. em todos os quatro DN. **Isso não é erro zero** — é um rascunho melhor, não um
levantamento confiável. A causa mais provável é justamente os 35,5% de geometria sem
rótulo na Living: essa sobra não se distribui igual entre os DN, então enviesa o mix.

Também há assimetria de escopo na comparação: a aba RAMAL embute a prumada DN32 (item 2.1),
que corre na vertical, enquanto o DXF medido é um pavimento. Fechar isso exige tratar
prumada separadamente antes de comparar.

## Diagnóstico dos não-classificados e teste de raio — resultado NEGATIVO importante

Onde estava a sobra na Living:

- `HAF-TUB___PRU-F` (77,2 m) e `HAF-TUB___PRU-rsb` (21,0 m) são **prumada, não ramal** —
  98,2 m entravam na conta errada. Separados: o ramal real do pavimento são 1.295,4 m.
- o grosso restante está na camada base `HAF-TUB-___-___` (255,3 m), sem rótulo próprio.
- existem **126 rótulos numa camada de texto dedicada** (`HID-___-___-TXT-25`) que o
  método só aproveitava no fallback.

Sensibilidade ao raio de fallback (ramal, sem prumada): a cobertura fica travada em
**69,4% de raio 2 a 15**, e salta para **99,7% em raio 25**. O degrau é seco — aquela
geometria toda está a 15–25 unidades do rótulo mais próximo.

Cobertura alta é fácil de comprar. A pergunta é se ela acerta. Contra o gabarito:

| DN | planilha | raio 8 | dif | raio 25 | dif |
|---|---|---|---|---|---|
| 16 | 11,9% | 17,7% | +5,8 | 12,3% | +0,4 |
| 20 | 46,2% | 40,8% | −5,4 | 58,8% | **+12,6** |
| 25 | 19,8% | 13,4% | −6,4 | 9,4% | **−10,4** |
| 32 | 22,1% | 28,1% | +6,0 | 19,5% | −2,6 |
| **erro somado** | | **23,6 p.p.** | | **26,1 p.p.** | |

**Subir a cobertura de 69% para 99,7% PIOROU a precisão.** Os 393 m extras são
majoritariamente atribuição errada — inflam DN20 e esvaziam DN25. Mantido o raio 8.

Isso é um resultado útil, ainda que negativo: o buraco restante **não se resolve
afrouxando o raio**. Rótulo a 15–25 unidades do tubo indica chamada com linha de
cota (leader), e casar isso exige seguir o leader, não medir distância. Qualquer
tentativa de "melhorar a cobertura" sem seguir o leader vai produzir número
convincente e errado — que é o pior resultado possível num orçamento.

## Duas hipóteses testadas e reprovadas (scripts 23, 24, 25)

**H1 — linha de chamada como entidade.** Reprovada de imediato: o probe 23 não encontrou
**nenhum** LEADER ou MULTILEADER no desenho da Living. A chamada não é entidade.

**H2 — o rótulo é escrito alinhado ao tubo que descreve.** O probe deu esperança: os 253
rótulos têm ângulo e ele discrimina (166 a 90°, 54 a 0°, o resto em diagonal). Implementado
o casamento por paralelismo em nível de segmento (script 24) e avaliado numa grade de 32
combinações contra o gabarito (script 25).

**Reprovada.** Paralelismo nunca vence. Melhor resultado da grade:

| método | prumada | raio | cobertura | erro somado |
|---|---|---|---|---|
| **distância, por segmento** | não | 30 | 93,0% | **20,1 p.p.** |
| paralelo (tol 15) | não | 15 | 52,0% | 25,5 p.p. |
| distância, por entidade (v1) | não | 8 | 69,4% | 23,6 p.p. |

Ganho real de toda esta rodada: **23,6 → 20,1 p.p.** Marginal. Continua longe de erro zero.

## O achado que importa: o erro é sistemático, não ruído

O desvio tem sempre a mesma direção, e repete em dois gabaritos independentes:

| obra | DN16 medido × real | DN25 medido × real |
|---|---|---|
| Living | 19,7% × 11,9% (**+8**) | 12,0% × 19,8% (**−8**) |
| Edition | 23,6% × 7,0% (**+17**) | 12,5% × 16,8% (**−4**) |

**DN16 sempre infla, DN25/DN20 sempre esvaziam.** Ruído não tem direção preferencial.

Pamaris não serve de teste: o ramal dela é 100% DN25, então qualquer método acerta
(erro 7,5 p.p. é artefato do caso degenerado, não validação).

**Explicação que encaixa em tudo:** um rótulo descreve um TRECHO INTEIRO do percurso —
o tronco que sai do manifold —, não o segmento mais próximo dele. O tronco é longo e leva
o DN maior; os ramos são muitos, curtos e levam DN16, com rótulos espalhados perto. Casar
por distância faz os rótulos de DN16 roubarem os metros do tronco. Daí DN16 inflar e
DN25 esvaziar, sempre nessa direção.

Ou seja: **o mecanismo é topológico — posição ao longo do percurso a partir do manifold —
e não geométrico.** Nenhum ajuste de raio, ângulo ou tolerância resolve isso, porque a
informação que falta não está na geometria.

## Conclusão: a engenharia bateu no teto

O caminho geométrico foi explorado até o fim: distância (entidade e segmento), raio,
paralelismo, leader, com e sem prumada. 32 combinações. O melhor é 20,1 p.p.

**O desbloqueio agora é a resposta do item 5.1 do portal, não mais código.** Foi por isso
que ele ficou marcado como "trava a entrega". E a hipótese acima é boa notícia para a
pergunta: em vez de pedir que o Hederson explique do zero, dá para apresentar a regra que
suspeitamos e pedir que ele confirme ou corrija — muito mais rápido de responder.

## Próximo passo, em ordem

1. **Levar a hipótese topológica para o item 5.1 do portal**, com os números das duas obras.
   Pergunta que ele confirma vale mais que pergunta que ele redige.
2. Assim que a regra chegar: reimplementar o casamento seguindo o percurso a partir do
   manifold, e reavaliar com o script 25 (a grade já está pronta para pontuar).
3. Tratar prumada à parte (já separada: 98,2 m, todos DN20 na Living). Atenção: o item
   2.1 fala de prumada PEX32 via blocos `PRUM-PX-32`; a camada `PRU-F` é geometria de
   linha e deu DN20. São coisas diferentes — não confundir.
4. Só depois regerar o `LEVANTAMENTO_HM89` com ramal por DN.

## Estado do teste do complemento vertical (itens 2.2 e 4.2)

Baseline reproduzido: Living AQ `EXO-TET` = 29,76 m/apto contra receita real de
35,22 m/apto → razão 0,85, faltando **5,46 m/apto**.

A tabela do Hederson, somada nos pontos que recebem água quente
(chuveiro 1,00 + lavatório 1,00 + entrada do apto 1,50 + descida de prumada 1,50), dá
**5,00 m** — cobre 92% do buraco. É indício forte, **não é prova**: falta contar quantos
pontos de cada tipo existem por apartamento na Living, em vez de assumir um de cada.

Contraindicação a resolver antes de cravar: a AF não mostra buraco nenhum
(50,42 medido contra 49,75 de receita, razão 1,01). Se o complemento fosse universal,
a AF também deveria estar 15% abaixo. Ou o complemento só se aplica à água quente, ou a
AF está compensando com dupla contagem em algum lugar. **Não codificar no
`PADRAO_SPHE.yaml` enquanto isso não fechar.**
