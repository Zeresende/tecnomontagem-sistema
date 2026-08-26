# A prancha de detalhe tinha o que faltava — e ela já estava aqui (11/08/2026)

Scripts novos: `41_probe_prancha_detalhe.py`, `42_probe_shaft_detalhe.py`,
`43_vistas_descida_vertical.py`, `44_varre_pranchas_det.py`.

## De onde veio

Item 12.1 da rodada 3. Perguntamos ao Hederson se a descida vertical — o trecho que
some no teto e reaparece no piso, e que em 10/08 deixou 96,4% da metragem fora de
qualquer percurso ligado a manifold — é desenhada em algum lugar. Ele respondeu que sim,
em prancha separada com `DET` / `AMPL` / `ISOM` no nome, deu a gramática completa do nome
de arquivo e anexou `QUA-HID-LO-1214-TOB-DET-R00.dwg` (Peak, torre B, pavimento tipo).

Baixado em 11/08 com autorização do José (2,47 MB, DWG AC1018), convertido pelo ODA
27.1.0 → DXF de 16,8 MB em `_analise/dxf/DET121/`.

## O que tem dentro do anexo

| | |
|---|---|
| entidades | 127.335 (73.452 LINE, 27.476 LWPOLYLINE, 5.196 TEXT, 4.799 INSERT) |
| camadas | 264, no padrão SPHE com prefixo de xref (`1994-HD-16-TOB-TIPB$0$HAF-TUB-___-EXO-TET`) |
| rótulos `<DN>-PEX` | **109** — DN20 55, DN16 34, DN25 20 |
| notas `%%C<DN>` | 143, incluindo `AF - PEX. %%C20mm - TUBO GUIA: %%C32mm` |
| vistas e cortes | Vista A a G, `Vista A - Espelhada`, `DETALHE DO SHAFT 1` e `2`, `VISTA DO SHAFT CENTRAL 01` e `02` |
| cotas (DIMENSION) | 193, a mais comum 0,15 m (69×) |
| tubo vertical ≥20 cm | **208,0 m** em 294 segmentos |

**A prancha é a planta do pavimento MAIS os detalhes.** Dos 109 rótulos, 69 estão na
região da planta e 40 dentro das vistas.

## Os dois achados

### 1. A descida vertical está desenhada, em escala real

As vistas são elevações das paredes molhadas, em metro (a cota mais comum, 0,15 m, e as
de 1,33 / 1,80 / 2,13 m só fazem sentido como medida real). Nelas o tubo aparece com
segmento **vertical**, que é exatamente a geometria que a planta não tem:

| vista | vertical | horizontal | rótulos DN |
|---|---|---|---|
| Vista A | 7,70 m | 0,52 m | 20:3 · 16:3 · 25:1 |
| Vista A - Espelhada | 12,49 m | 0,41 m | 20:4 · 16:4 · 25:1 |
| Vista B | 6,48 m | 0,43 m | 16:5 · 20:3 |
| Vista C | 4,80 m | 0,21 m | 16:5 · 20:3 |
| Vista D | 8,56 m | 0,61 m | 16:8 · 20:2 |
| Vista E | 4,13 m | 0,13 m | 25:2 · 16:3 · 20:1 |
| DETALHE DO SHAFT 1 | 19,98 m | 5,09 m | — |
| VISTA DO SHAFT CENTRAL 02 | 42,27 m | 5,95 m | — |

Note a razão: nas vistas o vertical domina o horizontal em 10 a 20 vezes. É corte, não
planta. E o rótulo de DN vem junto — ou seja, **a descida não só existe, como já vem
classificada por bitola**.

**Ressalva que impede cravar agora:** os comprimentos medidos não batem com a tabela que
o Hederson deu no 2.2/4.2 (1,00 chuveiro · 1,00 lavatório · 0,40 vaso · 1,50 entrada e
descida de prumada). Só 2 segmentos caem perto de 1,00 m e nenhum perto de 1,50. **Isso
era esperado e não refuta nada:** o DXF entrega o tubo em cacos (mediana 6 mm, medido no
probe 28) e os comprimentos mais frequentes aqui — 0,71 (37×), 0,75 (34×), 0,45 (32×) —
têm cara de fragmento, não de trecho. A comparação com a tabela só vale **depois** de
remontar o trecho pelo caminho do script 29. Registrando isto de propósito: em 10/08
declarei uma hipótese confirmada antes do teste de atribuição terminar, e não repito.

### 2. As pranchas de detalhe das 5 obras já estavam na pasta, e nunca foram lidas

Esta é a parte que muda o cronograma. O script 44 varreu todas:

| obra | prancha | rótulos `<DN>-PEX` | vistas | tubo vertical |
|---|---|---|---|---|
| Living | `7409-HID-PE-0011-DETTIP-R00` | **297** (20:104 · 16:90 · 25:60 · 32:43) | 53 | **559,7 m** |
| Edition | `7432-HID-PE-0015-DTIP-R01` | **286** (20:124 · 16:93 · 25:35 · 32:34) | 48 | **988,8 m** |
| Pamaris | `PAMA-0C-HI-PE-0106-DTIP-R00` | **245** (25:196 · 16:33 · 20:15 · 32:1) | 50 | **1.436,9 m** |
| Peak torre A | `QUA-HID-LO-1116-TOA-DET-R01` | **140** (16:61 · 20:58 · 25:21) | 27 | **253,0 m** |
| Peak torre B | anexo do 12.1 | 109 | 19 | 208,0 m |
| Brooklyn | 4× `DETIPO` | 355 somados | 24 | 0,0 m |

Os arquivos estavam convertidos desde junho. **Os extratores nunca os abriram porque
filtram o nome por `PVTIPO|TIPO|TIP`** (scripts 22, 25, 30, linha do `glob`) — o filtro
que separa "planta" de "detalhe" também separou a resposta do problema.

Duas consequências imediatas:

- **O Peak não estava restrito à nota geral.** Dissemos ao Hederson, no item 5.3, que
  Brooklyn e Peak não têm rótulo `<DN>-PEX`. A prancha TOA que já tínhamos tem 140, e a
  TOB que ele mandou tem 109. **É a terceira vez que afirmamos que um dado não existe
  depois de procurar no arquivo errado** (as duas primeiras: "a SPHE não marca DN no traço
  do ramal", corrigida por ele em 06/08; "o Brooklyn não tem rótulo", corrigida por nós em
  10/08). A regra escrita em 10/08 — não afirmar que um dado não existe sem dizer onde foi
  procurado — precisa virar prática: **rodar em TODOS os arquivos da obra antes de concluir**.
- **O Brooklyn confirma a leitura de 10/08 por outro caminho:** 355 rótulos e zero metro
  vertical. É exportação de Revit de vista em planta — não há elevação para medir. O
  pedido do arquivo nativo (item 14.1) continua sendo o caminho de lá.

## O que fazer com isso, em ordem

1. **Tirar o filtro de nome dos extratores** ou passar a prancha DET explicitamente. Cuidado
   obrigatório: a prancha DET **contém a planta inteira também** (69 dos 109 rótulos do
   anexo estão na planta). Medir TIPO + DET sem separar região **conta o mesmo tubo duas
   vezes**. Precisa recortar por região de vista antes de somar.
2. **Remontar trecho dentro das vistas** (script 29) e só então confrontar com a tabela do
   2.2/4.2. É o teste que decide se o complemento vertical vira medição.
3. **Refazer o teste da água quente da Living** — o buraco de 15% do script 18 é o candidato
   natural a ser preenchido pelos 559,7 m verticais da DETTIP. Combinar com a resposta do
   6.1 (existem pontos sem água quente, então parte do buraco é contagem, não metro).
4. **Reabrir a rota topológica** (script 31): a raiz do percurso que faltava é a descida.
5. **Contar ao Hederson** que a prancha resolveu, e **corrigir a nossa afirmação do 5.3**
   sobre o Peak. Ele corrigiu a mesma classe de erro nosso em 06/08 — assumir por escrito
   funcionou como ativo de relação daquela vez.
