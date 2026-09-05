# PROTOCOLO — Rodada holdout com a Pamaris (2026-09-04)

Pergunta que a rodada responde: **a receita de kit das outras obras SPHE generaliza para uma obra nova, ou cada obra precisa de captura propria?** (decisao B1, aberta desde junho). Junto, prova se o levantamento completo (ramal medido + kits) fecha com o que o Hederson/Marcelo entregaram.

## 0. Correcao de unidade que muda tudo (achado de 04/09, antes de qualquer rodada)

A celula [peca, coluna de kit] da planilha SPHE e **METROS POR KIT** para tubo (e UN/kit para conexao). Nao e rolos. Prova: a formula da coluna G ("Qtde. Total Levantada") nas 5 obras e

    G = ROUNDUP( soma(celula x contagem) / tamanho_rolo x 1,07 )   para tubo
    G = soma(celula x contagem)                                     para conexao (sem folga)

Ex.: Pamaris O16 = (1x780 + 10x660 + 1x120) / 200 x 1,07 = 40,1 -> **41 rolos**, exatamente a planilha.

O que estava errado ate hoje: a leitura de 26/08 ("receita em ROLOS, m/kit = rolos x tamanho / contagem"), o `60_mkit_por_kit.py` (corrigido) e a semantica combinada em 28/08 para o conector ("tubo = total-da-coluna / contagem"). **O conector da Karina precisa trocar para: m/kit = celula, direto.** O `PADRAO_SPHE.yaml` (secao unidades, RL) ja dizia o certo desde 12/08. Efeito pratico: o chuveiro da Pamaris tem 1,0 m de O16 por kit, nao 0,26 m.

## 1. Regras da rodada

- **Obra de fora: PAMARIS (20251670).** Motivos: unica com receita auditada pelo Marcelo (04/09), contagens fechadas (780/660/120), grupo de finais declarado, ramal 100% DN25. Edition (cozinha 10x fora, kit com nome proprio) e Peak (duas torres) nao servem como primeira prova. 2a rodada: Brooklyn de fora.
- **Entradas permitidas:** DWG/DXF da Pamaris (TIPO e DTIP), campos de abertura (secao 3), biblioteca das outras 4 obras (`saida/holdout_pamaris/biblioteca_mae_sem_pamaris.csv`, `receita_kits_4_obras.csv`).
- **Entrada proibida durante a rodada:** `PAMARIS-QUANTITATIVO PEX-R00.xlsx` e qualquer derivado dele (o `receita_kits_4_sphe.csv` completo tem as linhas da Pamaris — usar o `receita_kits_4_obras.csv`, que nao tem).
- **Gabarito cravado antes, sem retrofit:** o `gabarito_pamaris.xlsx` foi gerado em 04/09 pelo `62_gabarito_holdout.py` e fica com o Jose ate o fim. Falha e resultado valido.
- **Saida do conector:** `levantamento.xlsx` no contrato de 12/08 (PECA_ID + QTD_TOTAL, caixa alta). Tubo em METROS (unidade do catalogo, ids 1049/1052/1055). Opcional: `kits.csv` com COLUNA;CONTAGEM para o criterio C1.

## 2. Criterios (fixados em 04/09)

| # | Criterio | Regra |
|---|---|---|
| C1 | contagem de kits | exata, por coluna (KIT CHUVEIRO H 780, CHICOTE BANHO 1 660, CHICOTE BANHO 2 120, CHICOTE COZINHA 780) |
| C2 | conexao por PECA_ID | total da obra dentro de 5% do gabarito, para TODA peca; peca a mais tambem reprova |
| C3 | tubo por bitola | rolos dentro de +-1 do que o Hederson comprou (ROUNDUP(m x 1,07 / rolo)) |
| C4 | pecas fora do catalogo | zero |

Quem avalia e o `63_comparar_holdout.py`, mecanico. Reprovou em um, reprovou.

### 2b. Adendo de 04/09 (18h, antes de qualquer resultado do braco B): as 2 celulas pendentes do Marcelo

O gabarito de tubo e a coluna G do quantitativo (o que o Hederson comprou). A fonte NAO tem tubo O16 no CHICOTE BANHO 2 nem tubo O25 no CHICOTE BANHO 1 - sao exatamente os 2 tubos que o Marcelo ficou de cotar (aba PENDENTES do gabarito). Se a DTIP mostrar esses tubos, o conector vai emitir mais metros que o gabarito e o C3 acusa sem ser erro do conector.

Regra: diferenca de tubo que cai **inteira** numa celula da aba PENDENTES e "explicada, aguarda Marcelo" e nao reprova; o C3 e avaliado **sem** esses metros (C3 ajustado). Qualquer outra diferenca segue a regra normal (+-1 rolo). Quando o numero do Marcelo chegar, entra no gabarito e o C3 fecha sem ajuste.

Para isso a Karina devolve um 3o arquivo, `receita_lida.csv` (`COLUNA;PECA_ID;QTD_POR_KIT`, tubo em m/kit, conexao em UN/kit): o que o conector leu de cada kit na DTIP. O `63` compara celula a celula com a aba POR_KIT do gabarito (conexao exata, tubo 5% por celula), marca EXPLICADA / DIFERENCA / A MAIS / FALTA e recalcula o C3. Colunas de RAMAL nao entram (ramal e medido na TIPO). Sem o arquivo, o 63 so ve o total da obra e nao separa "Marcelo" de erro de leitura.

### 2c. Adendo de 05/09 (antes de qualquer resultado do braco B): os 2 tubos do Marcelo chegaram

Marcelo cotou (via Karina, 05/09, manha): **CHICOTE BANHO 1 - tubo O25 = 2 m/kit** e **CHICOTE BANHO 2 - tubo O16 = 4 m/kit** (bitola 16 confirmada; a estimativa de 1 m/kit que circulou em 04/09 estava errada). Os dois entraram em `correcoes_receita_sphe.csv` como `aplicada` e, com isso, a aba PENDENTES do gabarito ficou vazia: **a regra 2b nao tem mais celula para explicar**, o C3 volta a ser avaliado inteiro (+-1 rolo), e o `63` com `--receita` continua decompondo por celula, agora sem desconto.

O gabarito de tubo mudou em duas bitolas. A coluna G do Hederson foi calculada sem essas celulas, entao o `62` passou a RECALCULAR os rolos da linha de tubo que recebeu correcao (as outras linhas seguem a coluna G; a aba TUBO_POR_BITOLA diz qual foi qual):

| Bitola | Antes (coluna G) | Depois (05/09) | O que entrou |
|---|---|---|---|
| O16 | 7.500 m = 41 rolos | **7.980 m = 43 rolos** | +480 m (4 m/kit x 120 BANHO 2) |
| O20 | 8.658 m = 93 rolos | 8.658 m = 93 rolos | nada |
| O25 | 29.958 m = 321 rolos (KITS 918 + RAMAL 29.040) | **31.278 m = 335 rolos** (KITS 2.238 + RAMAL 29.040) | +1.320 m (2 m/kit x 660 BANHO 1) |

Atencao ao O25: o C3 compara o **total da obra**, e o tubo 25 tem ramal (29.040 m, 311 rolos) e CHICOTE ASV (300 m) alem dos kits de banho. A conta "618 m -> 1.938 m, 7 -> 21 rolos" que circulou em 05/09 olha so KIT CHUVEIRO H + CHICOTE BANHO 1 + CHICOTE BANHO 2; o delta esta certo (+14 rolos), a base nao. O gabarito e 321 -> 335.

Receita e gabarito mudaram juntos, no mesmo commit (`receita_kits_4_sphe.csv` ganhou as 2 linhas; `gabarito_pamaris.xlsx` regerado pelo `62` em 05/09). A biblioteca das 4 obras (`holdout_pamaris/receita_kits_4_obras.csv`) nao muda: Pamaris nao esta nela.

## 3. Campos de abertura da Pamaris (o que o Marcelo declara numa obra nova)

| Campo | Valor |
|---|---|
| torres / pavimentos / finais | 1 torre - 20 pavimentos tipo - 39 finais = 780 aptos |
| linha de produto | PEX Serie 5 (O16 rolo 200 m, O20 100 m, O25 100 m) |
| grupo de finais (banho) | BANHO 1 = finais 1-18 e 25-39 (660) - BANHO 2 = finais 19-24 (120) |
| area de servico | TRAVESSA TANQUE (120) e CHICOTE ASV (120) nos finais 19-24 - QUADRO ASV em todos (780) |
| registro do chuveiro | BASE REG GAVETA 3/4 DN20-B (2/kit) + BASE REG PRESSAO MVS 1/2 DN15-B (2/kit) |
| ramal | 100% DN25 |

## 4. Dois bracos

**Braco A — biblioteca-mae (ja rodado em 04/09, pelo Jose).** Mediana da receita das outras 4 obras por (kit, papel) x contagem verdadeira da Pamaris. Usa a contagem real de proposito, para isolar a pergunta da receita. Resultado: **FALHA em C2 e C3.**

- Conexao: 2 de 17 pecas dentro de 5%. A Pamaris usa registro de base (GAVETA/PRESSAO), adaptador fixo 25 x 3/4" e coifas 16-40/75 e 20-50/75 que nenhuma das outras 4 tem; a mediana traz canopla, flexivel cromado, RP DOCOLBASE e te 20-16-20 que a Pamaris nao usa. A cozinha da Pamaris e so tubo O20 + 1 adaptador 20 + coifa; as outras 4 tem 3-4 adaptadores 16 + 2 tes.
- Tubo: O16 74 rolos contra 41; O20 51 contra 93. (O25 nao conta neste braco: e ramal, vem do DXF.)

Leitura: **a biblioteca-mae por mediana nao generaliza.** O que muda de obra para obra e estrutural (tipo de registro, bitola de entrada da cozinha, coifas), nao um ajuste de +-10%. Isso fecha a decisao B1 na direcao de **receita propria por obra**, capturada de duas fontes: (a) campos declarados na abertura (registro, linha de produto, grupo de finais) e (b) a prancha de detalhe DTIP da propria obra.

**Braco B — receita lida do DTIP da Pamaris (Karina).** O conector le `PAMA-0C-HI-PE-0106-DTIP-R00.dwg` (detalhe dos kits) + `PAMA-0C-HI-PE-0101-TIPO-R00.dwg` (ramal) + campos de abertura e emite o `levantamento.xlsx`. E o braco que vale: se passar, o metodo esta pronto para obra nova sem depender de historico.

## 5. Divisao e prazo

- Karina: roda o braco B e devolve `levantamento.xlsx` (+ `kits.csv`). Antes, troca a semantica do tubo no conector (secao 0).
- Jose: guarda o gabarito, roda o `63_comparar_holdout.py`, devolve o veredito por criterio no mesmo dia.
- Tudo e local. A rodada cabe em dias.

## 6. Scripts

| Script | Faz |
|---|---|
| `61_biblioteca_sem_obra.py --sem 20251670` | biblioteca das 4 obras + predicao do braco A |
| `62_gabarito_holdout.py --obra 20251670` | gabarito por PECA_ID a partir do quantitativo (com as correcoes do Marcelo) — **so o Jose roda** |
| `63_comparar_holdout.py --obra 20251670 --resultado x.xlsx [--kits k.csv] [--receita receita_lida.csv]` | aplica C1-C4 e da o veredito; com `--receita`, decompoe por celula de kit e aplica o C3 ajustado (2b). Usa `holdout_receita_lida.py` |

O `gabarito_pamaris.xlsx` fica fora do repositorio (e a resposta da rodada e e dado da obra). A biblioteca das 4 obras e a predicao do braco A estao em `analise-sphe/saida/holdout_pamaris/`.

## 7. O que a rodada nao prova

Adocao. Para isso a obra e a HM89: tem DWG e levantamento gerado, falta o quantitativo manual do Hederson, feito do jeito de sempre e sem ver o nosso.
