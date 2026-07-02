# Sistema de Cotação — Tecnomontagem

Automação do processo de orçamento: do levantamento de quantitativos por obra à geração de planilhas de cotação por fornecedor.

## Requisitos

- Python 3.10 ou superior
- Instalar dependências: `pip install -r requirements.txt`

## Dados-base (pasta `dados\` — cópia canônica)

| Arquivo | Conteúdo | Quem mantém |
|---------|----------|-------------|
| `catalogo_pecas.xlsx` | 1.883 peças canônicas, 8 sistemas (PEX, PPR, PVC...) | Gerado dos templates oficiais |
| `equivalencias.xlsx` | 4.377 pares peça × fornecedor × código | Gerado dos templates oficiais |
| `fornecedores.xlsx` | 9 fornecedores ativos, contatos e e-mails | Hederson preenche e-mails à mão |

Atenção: edições manuais nesses arquivos são a fonte da verdade. Os scripts recusam sobrescrever sem `--force` (que cria backup automático antes).

## Fluxo de uso

### Via expressa — obra com template OBRA-QUANTITATIVO já preenchido

```bash
# importa o quantitativo direto do arquivo que o Hederson já preenche
python 04_importar_template.py NOME_OBRA "caminho\OBRA-QUANTITATIVO PEX-R00.xlsx" --construtora Cyrela
#    -> cria obras\NOME_OBRA\levantamento.xlsx já preenchido
#    -> importacao_relatorio.txt (como cada item casou)
#    -> importacao_revisao.xlsx (itens sem match, com top-3 candidatos do catálogo)

python 03_gerar_planilhas.py NOME_OBRA
```

Match em 3 camadas: código de fornecedor (determinístico) → descrição exata → fuzzy (aceita a partir de 0.85 e registra no relatório; abaixo disso o item vai para revisão manual). Abas ocultas também são varridas — há obras com dados preenchidos em aba escondida.

### Via manual — obra sem template preenchido

```bash
# 1. (uma vez) gerar fornecedores.xlsx
python 01_gerar_fornecedores.py

# 2. para cada obra nova: gerar o modelo de levantamento
python 02_modelo_levantamento.py NOME_OBRA --sistemas PEX,PPR
#    -> cria obras\NOME_OBRA\levantamento.xlsx
#    -> Hederson preenche a coluna QTD_TOTAL (células amarelas)

# 3. gerar as planilhas de cotação
python 03_gerar_planilhas.py NOME_OBRA
#    -> obras\NOME_OBRA\saida\: 1 planilha por fornecedor + MESTRE-generico.xlsx + _relatorio.txt
```

## Validação automática

O passo 3 gera avisos no console e no `_relatorio.txt` quando encontra:

- quantidade digitada como texto (ex.: "16.600");
- quantidade negativa;
- PECA_ID inválido ou inexistente no catálogo.

Revisar os avisos antes de enviar as planilhas aos fornecedores.

## Scripts auxiliares

| Script | Função |
|--------|--------|
| `99_simular_joao_dias.py` | Preenche a obra de teste com dados reais (uso em desenvolvimento) |
| `99_validar_saida.py` | Inspeção visual das planilhas geradas |
| `diag_encoding.py` / `diag_encoding_completo.py` | Diagnóstico de encoding dos xlsx (já executado, zero problemas) |

## Estrutura do projeto (pasta-mãe)

| Pasta | Conteúdo |
|-------|----------|
| `sistema\` | Este código + dados canônicos |
| `projetos\` | DWG/xlsx recebidos por obra |
| `projetos_dxf\` | Extração de quantitativos via DXF (M07) |
| `Levantamento de Informações _ Hederson\` | Histórico de materiais recebidos, por data |
| `materiais\` | Vídeos, áudios, frames e transcrições do processo original |
| `docs\` | Checklist e geradores de documentos |
| `_arquivo\` | Versão 1 do sistema (obsoleta) e artefatos descartados |
