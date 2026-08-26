# O teste que decide o `conexoes.py` — densidade de nós de grau 3

12/08/2026 · script `50_densidade_grau3.py` · pedido da Karina

## A pergunta

A leitura geométrica do desenho consegue contar as bifurcações do ramal?

Não se pergunta "quantos tês" — o script 49 (11/08) já mostrou que contagem ingênua
de nó erra por 40x: 626 vãos num pavimento da Living que prevê 16 tês. A pergunta
certa é de **densidade**, contra gabarito que já temos validado:

| Obra | Tês na aba RAMAL | Aptos do prédio | Alvo |
|---|---|---|---|
| Living | 328 | 164 | **2,00 tês/apto** |
| Peak (A+B) | 164 | 466 | **0,35 tês/apto** |

O DXF desenha o pavimento tipo: 8 aptos na Living, 20 no Peak (2 torres).

## O que o script faz

Dois filtros, nesta ordem.

**1. Grau efetivo com colinearidade.** O DXF entrega o tubo em cacos (mediana 6 mm).
Duas pontas colineares no mesmo nó são o mesmo cano partido, não duas derivações.
Então o grau do nó deixa de ser "quantas arestas chegam" e passa a ser **quantas
direções distintas saem**. A direção é medida a pelo menos 5 cm do nó — na ponta do
caco é ruído puro — e agrupada por tolerância angular. Direções opostas continuam
sendo dois grupos (cano que passa reto = grau 2); direções iguais viram um só.
Opcionalmente religa pontas livres separadas por um vão de 3 a 60 cm, porque o
desenho corta o tubo em cada conexão.

**2. Filtro por comprimento de trecho.** Remonta os cacos em trechos (script 29) e
só aceita como derivação o nó onde chegam 3 ou mais trechos com pelo menos X metros.
Um tê liga cano de verdade; símbolo explodido e tracejado somem.

## Resultado do filtro 1

Living, 25.904 segmentos, 1.393,6 m:

| ponte | ângulo | grau 3 | mesmo sistema | grau3/apto | x alvo |
|---|---|---|---|---|---|
| não | 5° | 1.682 | 1.737 | 210,25 | 105,1x |
| não | 15° | 1.657 | 1.713 | 207,12 | 103,6x |
| sim | 15° | 1.617 | 1.728 | 202,12 | 101,1x |

Peak, 1.434 segmentos, 1.232,7 m:

| ponte | ângulo | grau 3 | mesmo sistema | grau3/apto | x alvo |
|---|---|---|---|---|---|
| não | 5° | 60 | 61 | 3,00 | 8,5x |
| não | 15° | 58 | 59 | 2,90 | 8,2x |
| sim | 15° | 64 | 70 | 3,20 | 9,1x |

O filtro **funciona** como filtro: na Living derrubou o grau≥3 bruto de 3.211
(script 49) para ~1.650. E é **estável** — de 5° a 25° o número anda menos de 7%,
então não é artefato de tolerância.

E não resolve: 101x fora na Living, 8,5x no Peak. Praticamente todos os nós são do
mesmo sistema (1.713 de 1.725 na Living), então não são cruzamentos de AF com AQ em
planta — são bifurcações reais do traço, e existem às centenas por apartamento.

## Resultado do filtro 2 — e a armadilha

3 ou mais trechos com pelo menos X metros no nó:

| X (m) | Living /apto | x alvo | Peak /apto | x alvo |
|---|---|---|---|---|
| 0,10 | 6,88 | 3,4x | 2,95 | 8,4x |
| 0,20 | 3,00 | 1,5x | 2,75 | 7,8x |
| 0,50 | 1,25 | 0,6x | 2,10 | 6,0x |
| 1,00 | 0,62 | 0,3x | 0,40 | **1,1x** |
| 2,00 | 0,25 | 0,1x | 0,10 | 0,3x |

**Cada obra acerta o alvo — em um X diferente.** A Living cruza os 2,00 entre 0,20 e
0,50 m; o Peak encosta nos 0,35 em 1,00 m, onde a Living já caiu para 0,3x do alvo.

**Não existe X que sirva para as duas.** Em nenhuma das cinco linhas as duas obras
ficam juntas: a diferença mínima entre elas é de 5x. E as duas se movem em ritmos
opostos conforme X sobe.

Escolher o X depois de olhar o gabarito seria **ajuste a gabarito, não extração** —
a mesma armadilha registrada em 11/08 para as camadas do Peak ("são 6 camadas x 2
sistemas, alguma soma sempre cai perto do alvo"). Com 5 valores de X e 2 obras,
alguma célula ia cair perto de qualquer jeito. O que essa tabela mostra não é um
método, é a ausência dele.

## Veredito

**Não bate. O `conexoes.py` não ganha papel no ramal.**

A recomendação é arquivar com o motivo escrito, e o motivo é este: a densidade de
bifurcação medida na geometria não converge para o gabarito em nenhuma configuração
comum às duas obras, e a distância não é de calibração — é de uma a duas ordens de
grandeza.

## O que este teste NÃO prova, e é honesto registrar

1. **As duas obras não são comparáveis em fragmentação.** A Living tem 25.904
   segmentos para 1.393 m (5 cm por segmento); o Peak tem 1.434 para 1.232 m (86 cm).
   Parte da distância entre 101x e 8,5x é qualidade de desenho, não topologia. Isso
   piora o quadro para o produto, em vez de melhorar: um extrator que depende de como
   o arquivo foi desenhado não atravessa obra.
2. **A Living tem 2,05x de metragem inexplicada** (1.393,6 m medidos contra 679,7
   esperados para 8 finais, registrado em 10/08). Se o desenho traz o pavimento mais
   de uma vez, a densidade real cairia para ~50x o alvo. Continua fora por 50x.
3. **O caminho geométrico do tê depende do DN.** A planilha nomeia o tê pelas três
   pontas (`TE PEX 20-16-16`). Mesmo que a contagem fechasse, atribuir a peça exigiria
   o DN dos três ramos — e o extrator de DN está em 14,2 p.p. de erro na Living e
   30,0 na Edition. A leitura de conexão fica a jusante do DN, e herda o erro.

## O que fica de pé

A conexão continua a sair da receita, que reproduz a compra do Hederson com erro
zero: 77/77 linhas na Living, Edition e Pamaris, mais 78/78 no Brooklyn e no Peak.

O limite conhecido dessa rota não é a conexão do kit — é a do **ramal**, que não
transfere entre obras (2,0 tês/apto na Living contra 0,35 no Peak, quase 6x). Para
obra nova, a receita de ramal ainda precisa vir do desenho daquela obra ou do
Hederson. Esse buraco continua aberto, e este teste mostra que a geometria não o
fecha por enquanto.
