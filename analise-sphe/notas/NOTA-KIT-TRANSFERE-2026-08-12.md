# A receita de CONEXÃO do kit transfere entre obras? Medida peça a peça

12/08/2026 · script `52_kit_transfere.py`

## Por que medir isso agora

A Karina propôs uma Fase 0: provar que a receita de kit independe do projetista,
cruzando a biblioteca SPHE com o que o leitor dela tira da HM89.

**A HM89 não serve para esse teste: é do mesmo projetista SPHE**, confirmado pelo
José em 14/07 (as 5 obras Cyrela e a HM89 são todas SPHE — foi justamente essa
confirmação que fez a biblioteca das 5 obras valer para obra nova). Cruzar as duas
mede repetição do mesmo projetista, não independência dele.

O que dá para medir com o que existe é a variação entre **5 obras diferentes do
mesmo projetista**. E esse é o teste que importa para o produto, porque é assim que
a biblioteca vai ser usada: receita de obra passada aplicada em obra nova.

O leave-one-out de 03/07 (script 16) já tinha respondido isso para **tubo**: kits
transferem com desvio de +5% (banho), -8/-14% (lavabo), -7/+20% (cozinha); ramal não
transfere (-100% a +140%). Para **conexão**, nunca foi medido — o script 14 conferiu
que a cadeia fecha, sem comparar obra com obra.

## Resultado

Núcleo estável = mesma peça, mesma quantidade, em todas as obras onde o kit existe.

| Kit | Obras | Peças distintas | Núcleo estável |
|---|---|---|---|
| Chuveiro | 5 | 16 | 1 (**6%**) |
| Banho | 4 | 10 | 0 (**0%**) |
| Lavabo | 3 | 7 | 3 (**43%**) |
| Cozinha | 5 | 12 | 0 (**0%**) |

A única peça que é idêntica nas 5 obras do chuveiro é o
`COTOVELO C/ BASE FIXA CORPO EXTRA LONGO PEX 16MM X 1/2"`, 1 unidade.

## Isso não é ruído — são quatro causas identificáveis

Antes de concluir que a biblioteca não presta, vale abrir a variação. Ela tem
explicação, e a explicação muda o que fazer.

**1. Cada obra decompõe o kit de um jeito.** Já estava registrado desde 19/06
("receitas não são fixas entre obras — cada obra decompõe diferente"), e aparece
cru aqui: o chicote de cozinha tem 5-6 conexões na Living, Edition, Brooklyn e Peak,
e **2 na Pamaris**. Não é a mesma peça com quantidade diferente; é outra fronteira do
que entra no kit. Comparar os dois é comparar recortes diferentes.

**2. A mesma coisa física escrita em número diferente de linhas.** Living e Brooklyn
lançam `FLEXÍVEL CROMADO` + `CANOPLA CROMADA` em duas linhas; a Edition lança
`FLEXÍVEL + CANOPLA CROMADA` numa só. Conteúdo idêntico, três "peças distintas" na
contagem. Sozinho, isso já explica parte do 43% do lavabo não ser 100%.

**3. O DN do ramal que alimenta o kit muda a peça do kit.** O tê de saída do chuveiro
é `20MM X 1/2"` na Living, Edition e Brooklyn, e `25MM X 1/2"` na Pamaris — porque o
ramal da Pamaris é DN25. **A fronteira kit/ramal vaza:** o kit não é independente do
ramal, ele termina numa peça cujo diâmetro é o do ramal.

**4. Registro é especificação de obra, não do kit.** `RP DOCOLBASE 1/2` na Living e
Edition, `BASE REG PRESSAO MVS 3/4 DN20-B` no Brooklyn, duas bases diferentes na
Pamaris. Isso vem do acabamento contratado, não do desenho hidráulico.

## Leitura

**O esqueleto funcional do kit é estável; a lista de peças não é.** Todo chuveiro tem
um cotovelo de base fixa de 16, um tê misturador, um tê de saída e as bases de
registro. Qual peça exatamente ocupa cada posição depende de três variáveis externas
ao kit: como a obra recorta o kit, qual o DN do ramal que chega, e qual o registro
especificado.

Isso **não derruba** o erro zero: cada obra continua reproduzida a partir da receita
dela mesma, 77/77 e 78/78 linhas de conexão. O que isso corrige é a força da frase
"kit vem de biblioteca". A leitura honesta passa a ser:

> A biblioteca transfere a ESTRUTURA do kit e a ordem de grandeza do material
> (±5 a 20% no tubo, medido em 03/07). Não transfere o `PECA_ID` exato.

Para o produto, a consequência é de projeto: guardar o kit como **esqueleto
parametrizado** — posição funcional + DN de entrada + linha de acabamento — e não como
lista de peças congelada. Uma lista congelada emprestada de outra obra erra a peça
sem errar a conta, que é o pior tipo de erro: passa na conferência por total e chega
errado na compra.

## O que isso faz com a Fase 0 da Karina

O objetivo declarado ("provar que a receita de kit independe do projetista") não se
sustenta como está, por duas razões independentes: a HM89 é do mesmo projetista, e
dentro do mesmo projetista a lista de peças já varia pelos quatro motivos acima.

A pergunta que **dá** para responder, e que vale mais: *o esqueleto funcional do kit
se repete em obra nova, e as três variáveis (recorte, DN de entrada, acabamento) são
capturáveis do desenho e do memorial?* Se sim, a biblioteca vira gerador em vez de
arquivo — e aí sim atravessa projetista.

## Ressalva do método

Uma coluna representativa por obra (a de maior contagem). Living e Edition têm mais
de uma variante do mesmo kit por grupo de finais; a variante escolhida pode não ser
a mais comparável. Refazer com todas as variantes mudaria os percentuais, não a
conclusão — o chuveiro tem 16 peças distintas em 5 obras, e nenhuma escolha de
variante junta isso em uma lista só.

Segundo aviso, custou um resultado errado nesta sessão: a primeira versão do script
51 lia só a **primeira** string acima da linha de contagem para achar o nome do kit.
No Peak a primeira é o código da folha (`F.1116`) e o nome vem depois — os 4 kits do
Peak sumiram da extração. Seria a quarta vez neste projeto que afirmamos que um dado
não existe depois de procurar no lugar errado. **Antes de escrever "essa obra não
tem", conferir como aquela obra nomeia.**
