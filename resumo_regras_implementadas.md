# Resumo das Regras Implementadas - Mensagens Slack e Emails para Parceiros

## 📱 MENSAGENS DO SLACK (Account Managers)

### Objetivo
Gerar mensagens consolidadas por Account Manager (AM) para Slack, identificando ações necessárias em oportunidades ativas do pipeline.

### 🔍 Regras de Análise Implementadas

#### **Regra 1: Technology Partners - Co-Sell Missing**
- **Condição**: Technology Partner + "I Attest to Providing Co-Sell on Opp" ≠ true + (AWS Stage = "Launched" OU Partner Stage = "Launched")
- **Ação**: Marcar confirmação de Co-Sell no PAI View
- **Instrução**: Campo obrigatório para validação do co-sell com ISV quando oportunidade já foi dada como launched

#### **Regra 2: Partner Stage à Frente**
- **Condição**: APN Partner Reported Stage > Opportunity Stage (excluindo partners finalizados)
- **Ação**: Atualizar stage no Salesforce conforme status do partner
- **Instrução**: Considerar atualizar o stage na AWS para refletir o estágio informado pelo parceiro
- **Nota**: Exclui casos onde partner já está "Launched" ou "Closed Lost"

#### **Regra 3: Desalinhamento - Partner Finalizou**
- **Condição**: APN Partner Reported Stage = "Closed Lost" ou "Launched" E AWS Stage ≠ "Closed Lost" ou "Launched"
- **Ação**: Sincronizar status final no Salesforce URGENTE
- **Instrução**: Definir status final apropriado - launched (impacto em goals) ou closed-lost (hygiene)

#### **Regra 4: Eligible to Share with Partner**
- **Condição**: ACE Opportunity Type = "Eligible to Share with Partner"
- **Ação**: Compartilhar oportunidade com o partner
- **Instrução**: Impacto direto na compliance e nos goals de Partner Attached Launched ARR

#### **Regra 5: Close Date nos Próximos 30 Dias**
- **Condição**: Opportunity: Close Date nos próximos 30 dias
- **Ação**: Validar se a data de fechamento está correta
- **Instrução**: Time sensitive - validar status atual de consumo AWS e confirmar se existe consumo real

#### **Regra 6: Oportunidades Sem Parceiro (próximos 60 dias)**
- **Condição**: Oportunidades sem parceiro com Close Date nos próximos 60 dias
- **Ação**: Avaliar potencial de parceria estratégica
- **Instrução**: Identificar parceiros relevantes para acelerar fechamento

#### **Regra 7: Oportunidades com Valor Zero**
- **Condição**: ACE Opportunity Type ≠ "Partner Sourced For Visibility Only" E Total Opportunity Amount = 0 E Stage ≠ "Launched/Closed Lost"
- **Ação**: Validar e atualizar valor da oportunidade
- **Instrução**: Oportunidades com valor zero podem impactar métricas de pipeline

#### **Regra 8: Shared But Not Accepted**
- **Condição**: APN Partner Reported Stage = "Rejected" E (É única oportunidade com esse ID OU todas as outras com mesmo ID também são "Rejected")
- **Ação**: Avaliar re-compartilhamento ou nova estratégia
- **Instrução**: 
  - Oportunidade única: Reavaliar com mesmo parceiro ou alternativo
  - Múltiplas rejeitadas: Considerar novos parceiros ou revisar abordagem
- **Objetivo**: Identificar oportunidades órfãs que precisam de nova estratégia

### 📊 Características das Mensagens Slack

- **Formato**: Mensagens consolidadas por AM com seções numeradas
- **Filtros**: Apenas oportunidades ativas (exclui Launched/Closed-Lost)
- **Separadores**: "--- FIM DA SEÇÃO X ---" entre cada regra
- **Links**: Links diretos para Salesforce
- **Estatísticas**: Resumo com total de ações, partners envolvidos, oportunidades ativas
- **Formatação**: Texto limpo, sem emojis, profissional

---

## 📧 EMAILS PARA PARCEIROS

### Objetivo
Gerar emails personalizados para parceiros identificando ações necessárias em suas oportunidades específicas.

### 🔍 Regras de Análise Implementadas

#### **Regra 1: Launch Date Vencido**
- **Condição**: APN Target Launch Date < data atual E Partner Stage ≠ "Launched/Closed Lost" E AWS Stage ≠ "Closed Lost"
- **Ação**: Atualizar data de lançamento ou status da oportunidade
- **Detalhes**: Mostra quantos dias em atraso

#### **Regra 2: Launch Date Próximo**
- **Condição**: APN Target Launch Date ≤ 30 dias E Partner Stage ≠ "Launched/Closed Lost"
- **Ação**: Confirmar se a data será cumprida ou atualizar
- **Detalhes**: Mostra quantos dias restantes

#### **Regra 3: Oportunidades Paradas (Stalled)**
- **Condição**: APN Partner Last Modified Date < 45 dias atrás E Partner Stage ≠ "Launched"
- **Ação**: Atualizar status e próximos passos
- **Detalhes**: Mostra quantos dias sem atualização

#### **Regra 4: FVO Opportunities**
- **Condição**: ACE Opportunity Type = "Partner Sourced For Visibility Only" E ambos stages ≠ "Launched/Closed Lost"
- **Ação**: Alterar para 'Co-sell with AWS' se houver engajamento conjunto

#### **Regra 5: FVO com Valor Zero**
- **Condição**: ACE Opportunity Type = "Partner Sourced For Visibility Only" E Total Amount = 0 E Partner Stage ≠ "Launched/Closed Lost"
- **Ação**: Confirmar se o valor está correto ou atualizar

#### **Regra 6: Partner Stage Superior**
- **Condição**: Partner Stage > AWS Stage (numericamente) E Partner Stage ≠ "Launched"
- **Ação**: Atualizar próximos passos ou formalizar status da oportunidade

#### **Regra 7: Partner Stage Inferior**
- **Condição**: Partner Stage < AWS Stage (numericamente)
- **Ação**: Atualizar stage no Partner Central para alinhar com progresso

### 📧 Características dos Emails

- **Idiomas**: Português e Inglês
- **Personalização**: Nome do parceiro, empresa, dados específicos
- **Formatação**: HTML com botões para Outlook
- **Consolidação**: Emails múltiplos da mesma empresa podem ser consolidados
- **Links**: Links diretos para Partner Central
- **Template**: Estrutura padronizada com introdução, oportunidades, próximos passos

### 🔧 Funcionalidades Especiais

#### **Regra Especial para AWS Stage "Launched"**
Quando AWS Stage = "Launched", apenas verifica alinhamento do Partner Stage:
- Se Partner ≠ "Launched": solicita atualização para alinhar
- Se Partner = "Launched": confirma alinhamento (mensagem de sucesso)
- Se Partner = "N/A": solicita atualização obrigatória

#### **Mapeamento de Estágios**
```
Prospect: 1
Qualified: 2
Technical Validation: 3
Business Validation: 4
Committed: 5
Launched: 6
Closed Lost: 0
```

#### **Interface HTML**
- Dashboard com estatísticas
- Botões para abrir Outlook automaticamente
- Busca e filtros por empresa
- Emails consolidados por empresa
- Cópia automática para clipboard

### 📈 Métricas e Estatísticas

#### **Slack Messages**
- Total de ações por tipo
- Partners envolvidos
- Oportunidades ativas analisadas
- Mensagens geradas por AM

#### **Email Interface**
- Total de emails gerados
- Empresas envolvidas
- Emails consolidáveis
- Oportunidades totais
- Data de geração

### 🎯 Objetivos de Negócio

1. **Compliance**: Garantir que oportunidades sejam compartilhadas adequadamente
2. **Pipeline Hygiene**: Manter dados atualizados e precisos
3. **Partner Engagement**: Melhorar comunicação e alinhamento com parceiros
4. **Revenue Recognition**: Assegurar que oportunidades launched sejam contabilizadas
5. **Operational Efficiency**: Automatizar identificação de ações necessárias

### 🔄 Fluxo de Execução

1. **Análise de Dados**: Carrega planilhas Excel/HTML
2. **Aplicação de Regras**: Executa todas as regras simultaneamente
3. **Agrupamento**: Organiza por AM (Slack) ou Parceiro (Email)
4. **Geração**: Cria mensagens/emails formatados
5. **Interface**: Gera HTML para facilitar envio
6. **Armazenamento**: Salva resultados em diretório datado

Este sistema automatiza completamente a identificação e comunicação de ações necessárias no pipeline de parceiros, garantindo compliance e melhorando a eficiência operacional.