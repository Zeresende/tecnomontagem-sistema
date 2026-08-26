# Teste do item 5.2 — o rolo não explica o resíduo (10/08/2026)

Script: `32_teste_rolo.py`. Rodado em Living, Edition e Pamaris.

## A pergunta e a resposta dele

Perguntamos por que o desenho da Living dá DN16 18% / DN20 41% / DN25 13% / DN32 28%
enquanto a compra real foi 12/46/20/22. O Hederson respondeu, nas duas tandas:

> "Por conta do tamanho do rolo que o fornecedor já tem definido, ele tem rolos
> pré-definidos de 50 metros, 100 metros e 200 metros."

## O veredito: ele descreve um efeito real, mas pequeno demais

O arredondamento por rolo existe e está no modelo desde 19/06. Medido agora, isolado:

| Obra | Distorção que o rolo causa no mix | Erro do extrator |
|---|---|---|
| Living | **1,8 p.p.** | 14,1 p.p. |
| Edition | **0,6 p.p.** | 30,0 p.p. |
| Pamaris | 0,0 p.p. (ramal 100% DN25) | — |

E o teste direto, que é o que encerra o assunto: peguei a proporção do desenho, passei
pela cadeia de compra dele (×1,07 → dividir pelo rolo → ROUNDUP, linha a linha) e o mix
mudou **0,1 p.p.** na Living. O erro ficou nos mesmos 14,1.

**O rolo explica 1,8 de um buraco de 14. O resíduo é da nossa extração, não da compra.**
Não vale reperguntar — vale contar a ele o que encontramos.

## Efeito colateral útil: o alvo certo é a receita, não a compra

Até hoje pontuamos o extrator contra a COMPRA (rolos × tamanho ÷ 1,07). A compra carrega
o ROUNDUP embutido, e o ROUNDUP não é neutro entre DNs — PEX16 vem em rolo de 200 m e
PEX32 em rolo de 50 m, então cada DN é quantizado num passo diferente.

O alvo limpo é a RECEITA (Σ receita × contagem), o metro líquido antes de qualquer margem.
Na prática os dois quase coincidem (1,8 p.p. na Living, 0,6 na Edition), então nada do que
foi medido antes precisa ser refeito. Mas daqui pra frente vale usar a receita.

## O RESÍDUO AGORA TEM CAUSA CONHECIDA

Cruzando a fatia de rótulos de cada DN com a fatia de metro que aquele DN realmente tem.
Comparação em percentual de propósito — ver a armadilha de escala logo abaixo.

| DN | Living: % rótulos | % do metro | peso | Edition: % rótulos | % do metro | peso |
|---|---|---|---|---|---|---|
| 16 | 33,6% | 11,2% | 1,0× | 35,4% | 6,9% | 1,0× |
| 20 | 35,2% | 46,9% | 4,0× | 44,1% | 56,2% | 6,5× |
| 25 | 19,4% | 19,6% | 3,0× | 9,4% | 16,7% | 9,0× |
| 32 | 11,9% | 22,4% | **5,7×** | 11,0% | 20,1% | **9,3×** |

**Um rótulo de DN32 carrega 5,7 a 9,3 vezes mais tubo que um de DN16.** Faz sentido
físico: o DN16 rotula o ramalzinho curto que atende um ponto, o DN32 rotula o tronco que
percorre o pavimento.

> **Armadilha de escala — corrigida em auditoria de 10/08.** A primeira versão desta nota
> trazia "metros por rótulo" em números absolutos (DN16 18,3 m, DN32 103,9 m). Estava
> errado: o numerador é a receita do **prédio inteiro** (13.935 m na Living) e o
> denominador são os rótulos de **um pavimento**. Por pavimento os valores reais são
> DN16 0,94 m e DN32 5,33 m — e 18 m para o ramal de um ponto seria absurdo físico.
> **A razão entre DNs sobrevive** (é o mesmo fator nos dois lados), o valor absoluto não.
> Esses números chegaram a ir para o Hederson no item 15.2 e foram corrigidos antes do
> reenvio. Regra: antes de dividir duas grandezas, conferir se estão na mesma escala.

Nosso método atribui metragem por proximidade, e proximidade trata todo rótulo como se
tivesse o mesmo peso. Por isso o DN16 — numeroso e colado no tubo — infla, e o DN25/DN32
esvazia. É exatamente o padrão observado nas duas obras desde 06/08.

**Isso fecha o diagnóstico:** o erro que sobra não é ruído nem falta de calibragem. É a
consequência direta de atribuir por distância um dado cuja lógica é de percurso.

E é precisamente o que a regra topológica do item 5.1 corrigiria — o tronco propagado a
partir do manifold ficaria com seus metros em vez de perdê-los para os rótulos de DN16
vizinhos. O que impede não é a regra, é o desenho: as descidas verticais não existem em
planta, então a rede não fecha (ver `NOTA-DN-TOPOLOGICO-2026-08-10.md`).

## LIÇÃO DE MÉTODO — um bug meu que quase virou conclusão errada

A primeira versão do script agregou as linhas de tubo por DN e guardou um único tamanho de
rolo por DN. Resultado: a cadeia "não batia" (DN16 da Living dava 17 rolos calculados
contra 9 reais, −42%), e a leitura natural seria "descobrimos uma inconsistência na
planilha do cliente".

Era bug meu. O PEX16 da Living vem em rolo de **200 m**, e eu tinha sobrescrito o tamanho
com o da última linha lida. O ROUNDUP é **por linha** — cada linha é um produto distinto
no catálogo do fornecedor, e o mesmo DN aparece em linhas com rolos diferentes (a Edition
tem DN25 em rolo de 50 m e de 100 m na mesma obra).

Só peguei porque o resultado contradizia o erro zero já validado em 19/06. **Registro
como regra: quando um número novo derrubar um resultado antigo já conferido, a primeira
hipótese é bug no código novo, não erro no dado do cliente.**

## O QUE FAZER COM ISSO

1. **Não reperguntar o 5.2.** Contar a ele o que medimos — que a explicação do rolo vale
   1,8 p.p. e o resto é nosso. Assumir erro por escrito funcionou no caso do lavabo.
2. **Trocar o alvo de pontuação** para a receita nos próximos testes.
3. **O caminho para reduzir o erro continua sendo a topologia**, e ela está bloqueada pelo
   desenho. Alternativa a considerar: ponderar o rótulo pelo DN (um rótulo de DN32 "puxa"
   mais longe). Ressalva séria — isso é ajuste a gabarito, não extração, e não há garantia
   de que generalize para obra nova. Só faria sentido com validação leave-one-out.
