# Extrator de DN do ramal — o que a resposta 5.1 destravou (10/08/2026)

Continuação da `NOTA-EXTRATOR-DN-2026-08-06.md`, que fechou com a engenharia no teto:
20,1 p.p. de erro na Living e o diagnóstico de que o mecanismo era **topológico**, não
geométrico — nenhum ajuste de raio ou ângulo resolveria.

Em 10/08 o Hederson respondeu o item 5.1:

> "O ponto sai do manifold reduzido e dependendo da ligação, após uma conexão ele é
> reduzido para atender os pontos, normalmente após o Têe"

A resposta tem duas metades. **A primeira foi implementada e funciona. A segunda esbarra
num limite do desenho, não do código.**

---

## RESULTADO

| Obra | Método 06/08 (segmento + proximidade) | Método novo (trecho remontado) |
|---|---|---|
| Living (20241385) | 20,1 p.p. · cobertura 93,0% | **14,2 p.p. · cobertura 93,2%** |
| Edition (20241390) | 33,3 p.p. · cobertura 32,6% | **30,0 p.p. · cobertura 54,2%** |

Ganho nas duas obras, em erro e em cobertura. **A inflação sistemática do DN16, que era o
sintoma central do diagnóstico de 06/08, praticamente sumiu na Edition** (23,6% medido
contra 7,0% real virou 8,1% contra 7,0%). Na Living ela caiu pouco (19,7 → 18,6 contra
11,9 real).

Não é erro zero. É a diferença entre um método que erra por um motivo conhecido e um que
errava por motivo desconhecido.

## PRIMEIRA METADE — o rótulo vale pelo trecho inteiro (FUNCIONA)

O método antigo tratava cada pedacinho de tubo como independente: um rótulo de DN16
capturava só os centímetros ao lado dele. Como os rótulos de DN16 são muitos e ficam
perto do tubo, o DN16 roubava metragem do tronco.

Agora a unidade de atribuição é o **trecho** — a cadeia de tubo entre duas conexões.

Remontar o trecho deu trabalho porque o DXF não entrega tubo, entrega caco (probes 26-28):

- 26.013 segmentos, mediana de **6 mm**, 11.722 entidades;
- 52% da metragem vive em só 304 peças ≥ 1 m; os cacos de milímetro são tracejado e arco
  explodidos e carregam 1,1% do total;
- 96,1% dos fragmentos curtos têm vizinho colinear — logo dá para remontar.

Remontagem: snap das pontas em nós, fusão de todo nó de grau 2, sobrando as cadeias
maximais entre bifurcações. Como **o desenho corta o tubo em cada conexão**, há uma ponte
que religa pontas a até 15-25 cm. Melhor combinação na Living: snap 0,05 · ponte 0,25 ·
raio de rótulo 30.

## SEGUNDA METADE — a monotonia a partir do manifold (NÃO DÁ PARA IMPLEMENTAR)

A regra "sai do manifold e reduz depois do tê" implica que o DN nunca engrossa rio abaixo.
Isso é uma restrição forte e atacaria justamente o DN16 que ainda sobra na Living.

O manifold **existe como bloco** no desenho (`MANIFOLD - 2/3/4 - ROSCA`, 36 no pavimento
tipo da Living) e fica em cima do tubo (distância mediana de 3,7 cm). A raiz é
identificável. O problema é o que vem depois dela:

| ponte | grupos | grupos com manifold | metragem alcançável |
|---|---|---|---|
| 0,15 m | 257 | 4 | 45,6 m (3,6%) |
| 0,25 m | 187 | 4 | 45,6 m (3,6%) |
| 0,40 m | 128 | 4 | 46,0 m (3,6%) |
| 0,60 m | 93 | 4 | 46,0 m (3,6%) |

**Só 3,6% da metragem está num percurso ligado a um manifold, e o número não se move
por mais que se afrouxe a tolerância.** Aplicar a monotonia nesses 3,6% piorou o resultado
(18,8 → 20,1 p.p.), o que é esperado: propagar regra sobre amostra minúscula só adiciona
ruído.

### Por que a rede não fecha — e por que isso já era conhecido com outro nome

A planta baixa **não desenha as descidas verticais**. O tubo corre no teto (camada
`EXO-TET`), some, e reaparece no piso (`EXO-PIS`) ou no ponto. O trecho vertical não tem
geometria em planta.

É exatamente por isso que existe o **complemento vertical** que o Hederson soma de cabeça
(itens 2.2, 4.2 e 6.3). O que sempre tratamos como "conhecimento tácito dele" e o que
agora aparece como "rede desconectada" **são o mesmo buraco visto de dois lados**: a
informação vertical não está no desenho, ponto.

Consequência prática: a topologia completa só existe se as descidas forem reconstruídas
— unir ponta de trecho no teto com ponta de trecho no piso quando estiverem alinhadas em
planta. É um passo a mais, com risco de casar tubo errado, e não vale investir antes de
esgotar o que sobrou de erro conhecido.

## O QUE AINDA ERRA, E O QUE ATACA CADA COISA

Living, mix medido × real: DN16 18,6 × 11,9 (+6,7) · DN20 43,1 × 46,2 (−3,1) ·
DN25 15,9 × 19,8 (−3,9) · DN32 22,5 × 22,1 (+0,4). **O DN32 fecha.**

1. **A resposta 5.2 pode explicar parte do resíduo — ou não.** Ele atribuiu a diferença ao
   tamanho de rolo do fornecedor (50/100/200 m). O arredondamento por rolo já está no
   modelo e explica poucos pontos, não 6,7. **Testar antes de reperguntar:** aplicar
   ROUNDUP por rolo sobre a proporção desenhada e medir quanto do gap fecha.
2. **A granularidade do grupo é grosseira.** No melhor resultado, um rótulo nomeia o
   percurso religado inteiro — em média 7,5 m, mas o maior grupo tem 104 m. Atribuir 104 m
   a um rótulo é uma aposta. O trecho isolado (unidade conceitualmente correta) pontua
   pior (18,8) que o grupo (14,2), e isso é um sinal de alerta: parte do ganho pode ser
   sorte. **Vale medir por apartamento, não só no total do pavimento.**
3. **Edition perdeu o DN25** (1,8% contra 16,8% real) enquanto a Living o subestima menos.
   Duas obras erram em direções diferentes no DN25 — ainda sem explicação.

## RESSALVA DE ESCALA ENCONTRADA NA AUDITORIA (10/08)

O DXF do pavimento tipo da Living mede **1.393,6 m** de tubo. A receita do prédio é
13.934,8 m para 164 apartamentos, ou 85,0 m por apartamento — logo 8 finais deveriam dar
**679,7 m**. O medido é **2,05×** o esperado.

O que **não** é: testado e descartado. Não há espelhamento (0,2% dos trechos têm gêmeo em
−x) nem duplicação de planta como a do Peak (os deslocamentos em escala de planta somam
poucas centenas de segmentos em 23 mil). A metragem também está concentrada em x ≥ 0
(1.303 de 1.394 m), então a extensão simétrica do desenho não é plano espelhado.

O que **pode** ser, sem teste ainda: camadas de tubo que entram na medição mas não na aba
RAMAL (prumada além da embutida, ramais de outro sistema), ou o desenho cobrir mais que os
8 finais.

**Por que não invalida o resultado:** a pontuação é de MIX (percentual por DN), e fator de
escala uniforme não muda percentual. **Mas se os 105% excedentes tiverem composição de DN
diferente do restante, o mix é afetado** — e isso não foi testado. Fica registrado como
incerteza conhecida, ao lado da outra já anotada (o trecho isolado pontua pior que o grupo
religado, então parte do ganho pode ser sorte).

## SCRIPTS

| Script | O que faz |
|---|---|
| `26_probe_topologia.py` | conectividade por vértice; acha os blocos MANIFOLD |
| `27_probe_grafo_polilinha.py` | testa grafo no nível da polilinha (reprovado) |
| `28_probe_fragmentacao.py` | mede a fragmentação e prova que é remontável (96,1% colinear) |
| `29_grafo_ramal.py` | remonta trechos: snap + fusão de nós de grau 2 |
| `30_dn_topologico.py` | atribuição por trecho religado + grade de avaliação ← **método vigente** |
| `31_dn_propagado.py` | propagação monotônica a partir do manifold (fica pronto para quando as descidas forem reconstruídas) |

Gabarito e função de pontuação continuam no `25_avaliar_dn.py`.

## PRÓXIMO PASSO RECOMENDADO

Antes de mexer em mais código: rodar o teste do item 5.2 (ROUNDUP por rolo sobre a
proporção desenhada). É barato e decide se o resíduo é do extrator ou da compra.
