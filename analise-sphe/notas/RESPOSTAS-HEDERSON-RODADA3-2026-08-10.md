# Rodada 3 — respostas do Hederson (10/08/2026, 16:19 às 16:34)

**Respondeu as 6 sem a mensagem ter sido enviada.** Voltou à página por conta própria —
provavelmente tinha o link salvo da rodada 2. As três travas caíram.

Extraído do Supabase em 10/08. O painel exige login; a chave anon não lê.

---

## 12.1 — TRAVA — A DESCIDA EXISTE, E EM ARQUIVO SEPARADO

**P:** Quando o tubo sai do teto e reaparece no piso, existe algum outro arquivo que mostre
essa descida? Ou ela nunca é desenhada?

**R:** "Sim, existe um arquivo em que você consegue pegar essa informação, na maioria das
vezes ele vem contendo no nome DET/AMPL/ISOM, os projetistas sempre mantem um padrão no
nome dos arquivos.

Exemplo: `QUA-HID-LO-1214-TOB-DET-R00`

- QUA — nome do empreendimento ao qual o projeto responde
- HID — disciplina do projeto
- LO — status de projeto (Liberado Obra)
- 1214 — número da folha do projeto
- TOB — neste caso, este detalhe é do pavimento TIPO da Torre B
- DET — significa detalhe (pode variar de projetista para projetista, podendo ser
  ISOM/AMPL/DET), neste arquivo você consegue pegar o que precisa
- R00 — significa a revisão em que o projeto se encontra; em alguns casos nem sempre todo o
  projeto é revisado, apenas uma folha, e com isso, caso recebamos alguma revisão, podemos
  alterar o levantamento apenas desta folha e não do projeto todo."

**Anexo:** `SPHE/12.1/1786378740570-QUA-HID-LO-1214-TOB-DET-R00.dwg` — ainda não baixado.

**Leitura — é a resposta mais valiosa da rodada.** O maior bloqueio técnico do dia era que
a planta não desenha a descida vertical, o que impedia fechar o percurso e aplicar a regra
5.1. **A informação existe, em prancha separada, com convenção de nome previsível.** E ele
ainda entregou a gramática completa do nome de arquivo, que serve para localizar a prancha
certa em qualquer obra sem perguntar de novo.

Ponto extra que ele deu sem ser perguntado: a revisão é **por folha**, não por projeto —
o que significa que o levantamento pode ser atualizado parcialmente.

## 13.1 — TRAVA — NÃO É DUPLICAÇÃO, SÃO DUAS TORRES

**P:** No Peak o pavimento aparece duas vezes, deslocado 50 m, com 94,5% idêntico. São duas
alas, dois pavimentos-tipo, ou cópia de referência?

**R:** "Na realidade, são duas torres do mesmo empreendimento, por isso existe fator de
diferença."

**Leitura:** as duas cópias são reais e **ambas contam**. A conclusão que eu tinha registrado
— "medir o modelspace inteiro conta o mesmo tubo duas vezes" — estava errada. Não há
divisão por 2 a fazer; há duas torres a somar. E explica a diferença de metragem entre as
metades (1.035 m × 800 m): torres parecidas, não iguais.

Confere com a planilha, que tem abas `RAMAL - TORRE A` e `RAMAL - TORRE B`.

## 14.1 — TRAVA — O ARQUIVO É O DE TRABALHO, E ELE PODE PEDIR O REVIT

**R:** "É esse mesmo. O arquivo que está com você é o que recebemos da construtora e
realizamos o nosso levantamento em cima deste. Existe algumas construtoras que trabalham
com o Revit, podemos vir a solicitar este arquivo para facilitar o nosso trabalho."

**Leitura:** o DXF do Brooklyn é o material real de trabalho — não há outro melhor guardado.
E ele **se dispõe a pedir o nativo à construtora**. Como as três tentativas de inferência
falharam (52,4 · 57,0 · sem DN), esse pedido é o caminho. Vale responder confirmando que
sim, o RVT ou IFC resolveria.

## 14.2 — AutoCAD segue padrão

**R:** "O AutoCAD segue como um padrão, porém podemos ver de realizar a alteração, caso
facilite o nosso trabalho."

**Leitura:** o investimento na trilha AutoCAD continua justificado. E fica registrado que
ele considera mudar se houver ganho — decisão que não deve ser empurrada sem prova.

## 15.1 — rótulo e nota nunca divergem

**R:** "Na prática eles nunca divergem, sempre veem com a informação."

**Leitura:** quando as duas codificações coexistem (caso do Brooklyn), não há conflito a
resolver. Simplifica o extrator: pode usar a que estiver disponível.

## 15.2 — CONFIRMA A CAUSA DO RESÍDUO

**P:** Confere que o rótulo de bitola maior marca o tronco, e o de 16 marca o ramal curto
até o ponto?

**R:** "Sim."

**Leitura:** confirma o diagnóstico de que a contagem de rótulo não acompanha metragem, e
que o peso do rótulo varia com a bitola. É a base para qualquer ponderação futura.

---

## PLACAR

**6 de 6 respondidas, as 3 travas incluídas. Nenhuma pergunta nova nasceu da leitura.**

| Item | Resultado |
|---|---|
| 12.1 | **Destrava a topologia** — a descida está em prancha DET/AMPL/ISOM, com anexo |
| 13.1 | **Derruba minha conclusão** — são duas torres, não duplicação |
| 14.1 | Arquivo é o de trabalho; ele pode pedir o nativo à construtora |
| 14.2 | AutoCAD segue padrão |
| 15.1 | Rótulo e nota nunca divergem |
| 15.2 | Confirma o peso do rótulo por bitola |

## O QUE FAZER COM ISSO

1. **Baixar o anexo do 12.1** (`QUA-HID-LO-1214-TOB-DET-R00.dwg`) — pende autorização.
   Converter e verificar se a descida vertical está mesmo cotada ali.
2. **Refazer a medição do Peak somando as duas torres**, e corrigir a nota que dizia
   duplicação. O alvo passa a ser a obra inteira, não a Torre A.
3. **Responder ao 14.1** confirmando que o RVT ou IFC resolveria o Brooklyn.
4. **Reabrir a rota topológica** (script 31) assim que a prancha de detalhe for lida — ela
   ficou pronta em 10/08 justamente à espera desse dado.
