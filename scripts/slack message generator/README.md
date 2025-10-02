# Slack Message Generator

Gerador de mensagens consolidadas por AM (Account Manager) para Slack, identificando ações necessárias em oportunidades ativas.

## 🎯 Funcionalidade

Analisa oportunidades do pipeline e gera mensagens formatadas para Slack com ações consolidadas por AM, seguindo 5 regras principais:

### 📋 Regras de Análise

#### 1. **Technology Partners - Co-Sell Missing**
- **Condição**: Technology Partner + "I Attest to Providing Co-Sell on Opp" ≠ true
- **Ação**: Marcar confirmação de Co-Sell no PAI View

#### 2. **Partner Stage à Frente**  
- **Condição**: APN Partner Reported Stage > Opportunity Stage (excluindo partners finalizados)
- **Ação**: Atualizar stage no Salesforce conforme status do partner
- **Nota**: Exclui casos onde partner já está "Launched" ou "Closed Lost"

#### 3. **Desalinhamento - Partner Finalizou**
- **Condição**: APN Partner Reported Stage = "Closed Lost" ou "Launched"
- **Ação**: Sincronizar status final no Salesforce URGENTE

#### 4. **Eligible to Share with Partner**
- **Condição**: ACE Opportunity Type = "Eligible to Share with Partner"
- **Ação**: Compartilhar oportunidade com o partner

#### 5. **Close Date nos Próximos 30 Dias** (NOVA!)
- **Condição**: Opportunity: Close Date nos próximos 30 dias
- **Ação**: Validar se a data de fechamento está correta
- **Detalhes**: Mostra quantos dias restam, marca "HOJE" se for urgente

## 📊 Exemplo de Saída (Versão Simplificada)

```
AÇÕES CONSOLIDADAS - FELIPE VELLOSO (APENAS OPORTUNIDADES ATIVAS)

RESUMO:
Total de ações: 23
Partners envolvidos: 11
Oportunidades ativas: 23

NOTA: Foram excluídas oportunidades já finalizadas (Launched/Closed-Lost)

1. TECHNOLOGY PARTNERS - CO-SELL MISSING (11)
Problema: Confirmação de Co-Sell não marcada no PAI View
Ação: Marcar "I Attest to Providing Co-Sell on Opp" para cada oportunidade

1. Nuclea - CIP S.A.-Nuclea_ NDR_ Tempest
Partner: Trellix
AWS Stage: Prospect
Link: https://aws-crm.lightning.force.com/lightning/r/Opportunity/006RU00000Id4MLYAZ/view

--- FIM DA SEÇÃO 1 ---

5. CLOSE DATE NOS PRÓXIMOS 30 DIAS (5)
Problema: Oportunidades com fechamento próximo
Ação: Validar se a data de fechamento está correta

1. Empresa ABC-Projeto XYZ
Partner: Partner ABC
AWS Stage: Business Validation
Close Date: 25/08/2025 (em 3 dias)
Link: https://aws-crm.lightning.force.com/...

--- FIM DA SEÇÃO 5 ---
```

## 🚀 Como Usar

### Execução Individual
```bash
python3 "scripts/slack message generator/slack_message_generator.py" report.xls
```

### Integrado ao Pipeline
```bash
python3 run_pipeline_analysis.py report.xls
```

## 📁 Arquivos Gerados

- **`results/slack_messages.txt`** - Mensagens consolidadas por AM

## 📊 Colunas Necessárias no Excel

O arquivo Excel deve conter as seguintes colunas:

- `Opportunity: 18 Character Oppty ID`
- `Opportunity: Opportunity Name`
- `Opportunity: Account Name`
- `Opportunity: Stage`
- `APN Partner Reported Stage`
- `Partner Type From Account`
- `I Attest to Providing Co-Sell on Opp`
- `ACE Opportunity Type`
- `Partner Account`
- `Opportunity Owner Name`

## 🔍 Filtros Aplicados

### Oportunidades Ativas
Exclui oportunidades com status:
- `Launched` (AWS ou Partner)
- `Closed Lost` (AWS ou Partner)

### Mapeamento de Estágios
Para comparação Partner vs AWS:
```python
stage_order = {
    'Prospect': 1,
    'Qualified': 2,
    'Technical Validation': 3,
    'Business Validation': 4,
    'Committed': 5,
    'Launched': 6,
    'Closed Lost': 0
}
```

## 📈 Estatísticas de Exemplo (Versão Atual)

```
Oportunidades ativas: 434 de 1204 total
Total de ações encontradas: 262
   Co-Sell missing: 92
   Partner stage à frente: 44
   Partner finalizou: 26
   Eligible to share: 47
   Close date próximo: 53
Mensagens geradas para 11 AMs
```

## 🎨 Formato da Mensagem (Versão Simplificada)

Cada mensagem inclui:

- **Cabeçalho limpo** com nome do AM
- **Resumo** com estatísticas essenciais
- **5 seções organizadas** por tipo de ação
- **Separadores visuais** entre seções (--- FIM DA SEÇÃO X ---)
- **Links diretos** para Salesforce
- **Rodapé** com metadados
- **Formatação sem emojis** para melhor legibilidade

## 🔧 Tecnologias

- **Python 3** + Pandas
- **Leitura Excel** multi-engine (openpyxl, xlrd, HTML)
- **Formatação Slack** com emojis e markdown
- **Agrupamento** por Opportunity Owner

## ⚡ Performance

- **1,204 oportunidades** processadas
- **434 oportunidades ativas** analisadas
- **5 regras** aplicadas simultaneamente
- **11 AMs** com mensagens geradas
- **Execução**: ~3 segundos

## 🆕 Melhorias Recentes (v2.0)

### ✅ **Formatação Simplificada**
- **Removidos emojis e asteriscos** das mensagens
- **Texto mais limpo** e profissional
- **Melhor legibilidade** para Account Managers

### ✅ **Separadores Visuais**
- **Separadores entre seções** (--- FIM DA SEÇÃO X ---)
- **Organização clara** das regras
- **Navegação mais fácil** nas mensagens

### ✅ **Nova Regra: Close Date Próximo**
- **Detecta oportunidades** com fechamento nos próximos 30 dias
- **Mostra urgência** (quantos dias restam)
- **Validação proativa** de datas de fechamento

### ✅ **Lógica Aprimorada**
- **Partner Stage à Frente** exclui partners já finalizados
- **Melhor separação** entre regras de stage e desalinhamento
- **Detecção mais precisa** de casos críticos