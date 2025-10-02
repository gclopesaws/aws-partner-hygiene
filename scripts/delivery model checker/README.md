# Delivery Model Checker

## Descrição
Script para identificar oportunidades Technology Partner que precisam ajustar o Delivery Model para "SaaS or PaaS".

## Regra Aplicada
- **ACE Opportunity Type**: "Partner Sourced Opportunity", "Partner Sourced For Visibility Only", "AWS Opportunity Shared with Partner" ou valores nulos
- **Partner Type From Account**: "Technology Partner"
- **Delivery Model**: NÃO contém "SaaS or PaaS"
- **Stage**: Diferente de "Launched" ou "Closed Lost" (apenas oportunidades ativas)

## Como Usar

1. Coloque o arquivo de dados (planilha Excel/HTML) na raiz do projeto
2. Execute o script:
   ```bash
   python3 "scripts/delivery model checker/delivery_model_checker.py"
   ```
3. O relatório HTML será gerado em `results/delivery_model_report.html`

## Saída
- Relatório HTML com tabela das oportunidades que precisam correção
- Hyperlinks diretos para as oportunidades no Salesforce
- Informações de contato dos parceiros para ação

## Execução Recomendada
- **Frequência**: Semanal
- **Ação**: Revisar relatório e contatar parceiros para ajustar Delivery Model

## Estrutura do Relatório
- ID da Oportunidade
- Nome da Oportunidade (com link para Salesforce)
- Cliente
- Parceiro
- Stage atual
- Delivery Model atual
- Contato do parceiro
- Email para contato
- Ação necessária