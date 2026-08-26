# Respostas do Hederson — validação SPHE

**Origem:** portal `tecnomontagem-validacao-sphe.netlify.app` (Supabase, tabela `resposta_pendencia`)
**Data das respostas:** 06/08/2026, entre 14:11 e 14:58 — as 14 numa única sessão
**Extraído em:** 06/08/2026
**Anexos:** 4 (`térreo.xlsx` em 1.1, `ia.png` em 1.2 e 1.3, `89.png` em 4.1)

Status de cada item: CRAVA (vira regra), REVISAR (resposta conflita ou não responde), CONTEXTO.

---

## Bloco 1 — Living Only Ipiranga, regra de alocação

### 1.1 — Térreo (finais 1, 3, 5, 7) — CRAVA
**Pergunta:** os 4 aptos do térreo não têm coluna própria. Entram nas colunas de ramal do "1º ao 19º", 2 aptos em cada grupo de finais?

**Resposta:** "Na realidade, os apartamentos do térreo já estão sendo contemplados dentro desses valores, sem eles o grupo A (1/2/7/8) teria 76 apartametnos e o grupo B (3/4/5/6) teria 80 apartamentos. Conseguimos ver isto no esquema vertical que elaboramos ao analisar o projeto (anexo)." — anexo `térreo.xlsx`

**Leitura:** confirma a regra de dobra. O térreo não some, é absorvido nas colunas do tipo.
**A conferir contra o anexo:** ele cita grupo A = 76 e grupo B = 80 SEM o térreo. Nossa reconciliação de 02/07 derivou 78 = 19 pav × 4 finais + 2 do térreo. Bater os dois números com o `térreo.xlsx` antes de codificar.

### 1.2 — 20º pavimento regular, finais 3 a 6 — CRAVA
**Pergunta:** a coluna "20º pavimento finais 3/4/5/6" está zerada. Esses 4 aptos foram absorvidos na coluna "1º ao 19º finais 3/4/5/6"?

**Resposta:** "Na verdade, eles deixam de existir, pois, como se trata do último pavimento, neste caso, os reservatórios se encontram neste pavimento (círculo verde), por isso, ocorre este fator de zerar essas unidades." — anexo `ia.png`

**Leitura:** NÃO é absorção, é inexistência. A coluna zerada está correta.
**Confirmado pelo anexo:** a planta do 20º mostra os 5 reservatórios ocupando toda a faixa central (círculo verde), e só F1, F2, F7, F8 marcados em vermelho nas pontas. Os finais 3/4/5/6 não existem nesse pavimento.
**Corrige premissa nossa:** a pergunta partia de "foram absorvidos"; a resposta é que nunca existiram. Zero não é dado faltante.

### 1.3 — Duplex, coluna "20º pav – duplex" = 4 — REVISAR
**Pergunta:** ela cobre só o pavimento inferior do duplex (finais 1/2/7/8)? O superior (21º) entra onde?

**Resposta:** idêntica à do 1.2, com o mesmo anexo.

**Problema:** a resposta não serve para esta pergunta. Três evidências:
1. o `ia.png` que ele anexou mostra F1, F2, F7 e F8 EXISTINDO no 20º — só 3/4/5/6 é que somem;
2. ele próprio, em 1.5, diz "4 vieram do duplex superior", ou seja, o duplex superior existe e é contado;
3. a contagem da coluna é 4, não zero.

**Conclusão:** copiar-colar do 1.2. A pergunta do 21º (pavimento superior do duplex) continua em aberto. **Reperguntar.**

### 1.4 — Chuveiro / chicote de banho tipo = 332 — CRAVA
**Pergunta:** são os 328 banhos tipo mais os 4 banhos master do duplex superior?
**Resposta:** "Sim. Exatamente."
**Leitura:** confirma a decomposição 332 = 328 + 4. Fecha a regra do duplex superior para chicote de banho.

### 1.5 — Chicote de lavabo finais 1/2/7/8 = 82 — CRAVA
**Pergunta:** o RESUMO deriva 76. De onde vêm os 6 a mais?
**Resposta:** "4 vieram do duplex superior e 2 das unidades 1 e 7 que estão no térreo."
**Leitura:** 82 = 76 + 4 (duplex superior) + 2 (térreo, finais 1 e 7). Bate exatamente com o residual que a reconciliação de 02/07 tinha calculado. A regra de dobra está fechada para lavabo.

---

## Bloco 2 — Prumadas e complemento vertical

### 2.1 — Prumada PEX 32 — CRAVA
**Pergunta:** 340 blocos `PRUM-PX-32` na PVTIPO = 17 prumadas × 20 pavimentos? E o metro linear já está embutido na receita do ramal aéreo?
**Resposta:** "Isso, exatamente."
**Leitura:** confirma as duas coisas. A prumada PEX não tem linha própria na planilha porque o DN32 já está dentro da receita do RAMAL AÉREO. Não somar de novo — o risco aqui era contagem dupla.

### 2.2 — Complemento vertical "de cabeça" — CRAVA (o mais valioso do bloco)
**Resposta, tabela preenchida:**

| Ponto | Complemento |
|---|---|
| Ponto de chuveiro | 1,00 m |
| Lavatório | 1,00 m |
| Vaso / caixa acoplada | 0,40 m |
| Entrada do apto | 1,50 m |
| Descida de prumada | 1,50 m |

**Leitura:** este era o último tácito puro do modelo — a regra que ele somava de cabeça e não estava em documento nenhum. Agora é número.
**Teste imediato:** o script 18 mediu AQ da Living com razão 0,85 contra a receita real, ou seja, faltavam ~15%. Aplicar esta tabela sobre o medido e ver se a razão vai para 1,00. Se for, o complemento vertical está provado e não só declarado.

---

## Bloco 3 — Ramal aéreo em obra nova

### 3.1 — Metragem pré-medida resolve? — CONTEXTO
**Resposta:** "Pode não resolver, porém facilita o nosso trabalho."
**Leitura:** resposta morna, e é informação honesta. Ele não aceita a medição automática como final — aceita como rascunho que ele confere. Define o posicionamento do produto: entrega pré-levantamento para conferência, não substituição do projetista. Não prometer "levantamento pronto" para a Tecnomontagem.

### 3.2 — Roda o teste em paralelo na próxima obra SPHE? — CRAVA
**Resposta:** "Sim."
**Leitura:** é o compromisso mais importante das 14. Sem obra-piloto em paralelo não há como medir assertividade real. **Precisa de data e de qual obra** — cobrar.

---

## Bloco 4 — HM89, o que ficou em aberto no teste cego

### 4.1 — Ramal aéreo por DN — CRAVA, e derruba nossa conclusão
**Pergunta:** a SPHE não marca o DN no traço do ramal, a classificação automática só alcançou 21%. Correto?
**Resposta:** "Na verdade, está escrito no projeto sim." — anexo `89.png`

**O anexo mostra:** rótulos de texto em verde (`25-PEX`, `20-PEX`) escritos ao lado das polylines verdes do ramal, na própria planta.

**Verificado no DXF real em 06/08 — ele está certo e nós estávamos errados.** O script 18 procurava a notação `%%C` (diâmetro), que a SPHE não usa nesse desenho. O padrão real é o texto `<DN>-PEX`. Contagem de rótulos nos DXF da HM89:

| Desenho | 16-PEX | 20-PEX | 25-PEX | Total |
|---|---|---|---|---|
| TIPA | 22 | 113 | 74 | 209 |
| TIPB | 22 | 113 | 74 | 209 |
| UTPA / UTPB | 22 | 113 | 74 | 209 cada |
| TIPO (DET) | 22 | 113 | 74 | 209 |
| TERA | 60 | 76 | 41 | 177 |
| TERB | 52 | 66 | 27 | 145 |
| SUBA | 26 | 54 | 13 | 93 |
| SUBB | 0 | 21 | 12 | 33 |

Zero ocorrências de `32-PEX` nas plantas de ramal — coerente com o 2.1, o DN32 é prumada (`PRUM-PX-32`), não ramal.

**Consequência:** o DN do ramal deixa de ser tácito. A regra vira "DN = rótulo `<DN>-PEX` mais próximo da polyline". Isso ataca direto a REGRA-MÃE de 03/07 ("kit vem de biblioteca, ramal vem do desenho"): o ramal continua vindo do desenho, mas agora dá para extrair o DN automaticamente, sem depender do Hederson obra a obra. **É o item que mais destrava a Fase 1.**

### 4.2 — Prumada vertical / altura — CRAVA
**Resposta:** "A altura de pavimento a pavimento é de 2,80. A altura (descida do aéreo) é sempre de 1,50 que consideramos, porém, essa medida é adotada apenas na saída do cavalete e na entrada do apartamento, esse fator multiplicação, sempre é conforme o número de apartamentos existentes no andar."

**Leitura:** pé-direito 2,80 m. A descida de 1,50 m não é por ponto — é 2 × 1,50 m por apartamento (saída do cavalete + entrada do apto), multiplicado pelo número de aptos do andar. Fecha a lacuna "altura do shaft não cotada", que era um dos motivos de a prumada ter ficado fora do LEVANTAMENTO_HM89.
**Atenção:** cruzar com o 1,50 m de "descida de prumada" do 2.2 — provavelmente é a mesma medida contada uma vez só. Não duplicar.

### 4.3 — Travessa de manifold / aquecedor na HM89 — CRAVA
**Resposta:** "Nesse empreendimento o gás é apenas para fazer alimentação do ponto do fogão, não existe travessa manifold e travessa aquecedor."
**Leitura:** na HM89 esses dois itens são zero. Some uma pendência do LEVANTAMENTO_HM89 sem precisar de receita. É específico desta obra, não regra geral da SPHE.

### 4.4 — Lavabo — REVISAR, pergunta estava errada
**Resposta:** "Se refere ao lavatório do banheiro, este é um artigo de louça, precisa orientá-lo para diferenciar lavatório de lavabo. (Lavabo, um banheiro sem kit chuveiro) (Lavatório, artigo de louça, mais conhecido como pia do banheiro)"

**Leitura:** ele corrigiu a nossa terminologia, com razão. Nós lemos "LAVATÓRIO" no DETIPO e perguntamos sobre lavabo — são coisas diferentes:
- **lavatório** = louça, a pia do banheiro;
- **lavabo** = ambiente, banheiro sem chuveiro.

**A pergunta continua sem resposta.** Reperguntar direto: quantos finais da HM89 têm lavabo (banheiro sem chuveiro)?
**Ação no código:** corrigir o glossário do parser — hoje ele trata os dois termos como sinônimos, e isso contamina a contagem de kit.

### 4.5 — Térreo, subsolo e barrilete — CRAVA
**Resposta:** "Eles entram no mesmo orçamento, no subsolo e no térreo também existem unidades, já o barrilete deste empreendimento é diferente dos outros, ele fica externo da torre, com isso, o 9º pavimento acaba sendo o último andar do empreendimento."

**Leitura:**
1. térreo e subsolo entram no mesmo orçamento e TÊM unidades — não podem ficar de fora como ficaram na primeira passada;
2. o barrilete da HM89 é externo à torre, então o 9º é o último andar. Confirma a leitura da pilha ESQG de 08/07 e o total de 216 aptos como base do tipo, mas o levantamento tem de ganhar as unidades de térreo e subsolo.
**Consistente com os DXF:** SUBA/SUBB e TERA/TERB têm rótulos `<DN>-PEX` próprios (93, 33, 177, 145), ou seja, têm ramal desenhado e mensurável.

---

## Resumo

| Situação | Itens |
|---|---|
| Cravam como regra | 1.1, 1.2, 1.4, 1.5, 2.1, 2.2, 3.2, 4.1, 4.2, 4.3, 4.5 — 11 |
| Precisam voltar pro Hederson | 1.3 (copiou-colou o 1.2), 4.4 (pergunta mal formulada nossa) — 2 |
| Contexto, não regra | 3.1 — 1 |

**Maior ganho:** 4.1. O DN do ramal está escrito no desenho e nós procurávamos no lugar errado.
**Segundo maior:** 2.2 + 4.2. O complemento vertical, único tácito puro que restava, virou tabela numérica.
**Custo de reabrir:** 2 perguntas, uma delas erro nosso de terminologia.
