# Peak — medição refeita somando as duas torres (11/08/2026)

Script `48_peak_duas_torres.py`. Corrige a seção "achado que trava o Peak" da
`NOTA-ROTA2-NOTA-GERAL-2026-08-10.md`, que já ficou marcada como corrigida.

## Duas coisas estavam erradas em 10/08, não uma

**A primeira, ele corrigiu.** Item 13.1: as duas cópias deslocadas 50 m em Y não são
duplicação, são duas torres do mesmo empreendimento. Ambas contam. Não há divisão por
dois a fazer, e a metragem absoluta medida no modelspace inteiro nunca esteve dobrada.

**A segunda, achei agora, e é nossa.** Os números daquele dia — 1.034,8 m embaixo e
799,6 m em cima — saíram de um corte pela metade do Y. **Esse corte não separa as duas
torres.** A prancha tem oito aglomerados de tubo:

| x | y | metro | o que é |
|---|---|---|---|
| 100 | 125 | 627,0 | planta de torre |
| 100 | 75 | 605,7 | planta de torre |
| 200 | 75 | 263,0 | bloco estrutural |
| −150 | 75 | 157,5 | planta de furo |
| −150 | 125 | 157,5 | planta de furo |
| 100 | 175 | 6,8 | terceira planta de tipologia, sem tubo |
| 100 | 50 / 150 | 8,3 cada | resíduo |

As plantas de furo também vêm em par deslocado 50 — uma por torre — e o corte pela
metade jogava uma de cada lado. **A planilha tem aba própria para elas (`PASSANTE DE
LAJE`), então não são ramal.** Ao todo, 594,6 m que não deviam estar na conta.

**Medição correta das duas torres: 605,7 + 627,0 = 1.232,7 m.**

## A leitura "duas torres" se confirma pela geometria

Comparando as duas plantas de torre entre si, e não mais metade contra metade:

- **716 dos 722 segmentos da torre de cima têm gêmeo exato na de baixo — 99,2%**;
- a metragem difere em **3,4%** (605,7 × 627,0).

Parecidas e não iguais, que é exatamente o que ele descreveu. Casa também com o resto:
mesmo pavimento tipo, número de andares diferente — Torre A tem 224 apartamentos em 22
pavimentos, Torre B tem 242 em 23.

**Atenção à terceira planta.** As tipologias (TIPO D1, D3, B1, B2, C1, D5) aparecem em
**três** cópias, não duas — mas a terceira tem 6,8 m de tubo contra 627. É planta de
referência. Sem descartá-la, o denominador vira 30 apartamentos em vez de 20 e o
resultado muda 50%. O corte está no script, com o motivo escrito.

## Contra a receita: não fecha, e o desvio é o mesmo de ontem

Receita real, das duas abas de ramal: Torre A 5.467,3 m (24,41 m/apto) · Torre B 4.906,5 m
(20,27 m/apto) · soma 10.373,8 m para 466 apartamentos = **22,26 m/apto**, sendo 17,85 de
água fria e 4,41 de quente.

Desenho, as duas torres somadas sobre 20 apartamentos do tipo:

| sistema | camada | m/apto | × receita do sistema |
|---|---|---|---|
| AF | EXO-TET | 33,97 | **1,90** |
| AF | EXO-TET-CAM | 19,65 | 1,10 |
| AF | EXO-PIS | 3,19 | 0,18 |
| AQ | EXO-TET-CAM | 2,18 | 0,49 |
| AQ | EXO-TET | 1,92 | **0,44** |
| | todas as camadas | 61,64 | 2,77 |

Na camada que fechou a Living (`EXO-TET`), a água fria dá quase o dobro e a quente menos
da metade. Somando todas as camadas dá 2,77× — a Living, medida do mesmo jeito, dá 2,45×.
**O Peak se comporta como a Living: o total de camadas é ~2,5× a receita e uma camada
específica é o ramal. Só que no Peak nenhuma combinação fecha nos dois sistemas.**

**Não vou escolher a combinação que chega perto de 1,0.** Existem seis camadas e dois
sistemas: alguma soma sempre vai cair perto do alvo por acaso. A `EXO-TET-CAM` da água
fria dá 1,10 e a soma `EXO-TET + CAM` da água quente dá 0,93 — números bonitos, obtidos
escolhendo camada diferente para cada sistema depois de ver o gabarito. Isso é ajuste ao
gabarito, não extração, e só valeria com validação em obra que não entrou no ajuste.

## O que isso quer dizer

O Peak não tem um problema próprio: tem o **mesmo problema do denominador** que apareceu
ontem na Living e que já virou o item 16.1 no portal — o que exatamente entra na linha de
ramal quando ele levanta pela planta. Aqui aparece em forma mais crua, porque a obra usa
PERT dentro de tubo guia e há uma camada de camisa concorrendo com a de tubo.

A resposta do 16.1 vale para as duas obras. Não vale abrir item novo para o Peak.

**Observação de menor peso, para registrar:** o arquivo se chama
`QUA-HID-LO-1108-TOA-TIP-R01`, e pela gramática que ele mesmo deu no 12.1 o `TOA` quer
dizer pavimento tipo da **Torre A** — mas a prancha traz as duas torres. Pode ser
convenção de arquivamento, e não muda nenhuma medição. Só não vale usar o nome do arquivo
para decidir a que torre uma planta pertence.
