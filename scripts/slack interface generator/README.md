# Slack Interface Generator

Gerador de interface HTML interativa para envio automatizado de mensagens Slack consolidadas por AM.

## 🎯 Funcionalidade

Transforma o arquivo `slack_messages.txt` em uma interface web moderna com botões para envio direto no Slack, similar ao sistema de emails.

## 🚀 Como Usar

### Execução Individual
```bash
python3 "scripts/slack interface generator/slack_interface_generator.py" results/slack_messages.txt
```

### Integrado ao Pipeline
```bash
python3 run_pipeline_analysis.py report.xls
```

## 📁 Arquivos

### Entrada
- **`results/slack_messages.txt`** - Mensagens geradas pelo Slack Message Generator

### Saída
- **`results/slack_interface.html`** - Interface web interativa

## 🎨 Interface

### 📊 Estatísticas Globais
- Total de AMs
- Total de ações
- Partners envolvidos
- Breakdown por tipo de ação

### 📱 Cards por AM
Cada AM tem um card com:
- **Nome e prioridade** (🔥 Crítica, 🚨 Alta, ⚠️ Média, ✅ Baixa)
- **Resumo de ações** por tipo
- **Botões de ação**:
  - `📱 Enviar no Slack` - Abre o Slack desktop
  - `📋 Copiar Mensagem` - Copia para clipboard

### 🔍 Funcionalidades
- **Busca em tempo real** por nome do AM
- **Ordenação automática** por prioridade
- **Design responsivo** para mobile/desktop
- **Feedback visual** para ações realizadas

## 🎯 Sistema de Prioridades

### 🔥 CRÍTICA
- Partner finalizou (Launched/Closed Lost) mas AWS ainda ativo

### 🚨 ALTA  
- Mais de 5 Co-Sell missing OU mais de 15 ações totais

### ⚠️ MÉDIA
- Mais de 5 ações totais

### ✅ BAIXA
- 5 ou menos ações totais

## 📱 Integração com Slack

### Método 1: Slack Desktop
- Clica em "📱 Enviar no Slack"
- Abre o Slack automaticamente
- Usuário navega para o canal/DM desejado
- Cola a mensagem

### Método 2: Cópia Manual
- Clica em "📋 Copiar Mensagem"
- Abre o Slack manualmente
- Cola no canal/DM desejado

## 🎨 Design

### Cores
- **Primária**: #4A154B (Slack Purple)
- **Secundária**: #350d36 (Dark Purple)
- **Sucesso**: #28a745 (Green)
- **Crítico**: #dc3545 (Red)

### Layout
- **Grid responsivo** para cards
- **Gradientes** para visual moderno
- **Sombras e hover** para interatividade
- **Badges** para prioridades

## 📊 Exemplo de Card

```
📱 FELIPE VELLOSO                    🚨 ALTA
┌─────────────────────────────────────────────┐
│ Co-Sell Missing:        11                  │
│ Stage à Frente:          2                  │
│ Partner Finalizou:       0                  │
│ Eligible to Share:       0                  │
│ Total de Ações:         23                  │
│ Partners:               11                  │
│                                             │
│ [📱 Enviar no Slack] [📋 Copiar Mensagem]   │
└─────────────────────────────────────────────┘
```

## 🔧 Tecnologias

- **HTML5 + CSS3** com Grid e Flexbox
- **JavaScript ES6** para interatividade
- **Clipboard API** para cópia moderna
- **CSS Gradients** para visual Slack-like
- **Responsive Design** para todos os dispositivos

## 📈 Estatísticas de Exemplo

```
📊 Interface carregada:
• 8 Account Managers
• 106 ações totais
• 63 Co-Sell missing
• 38 Stage à frente
• 0 Partner finalizou
• 5 Eligible to share
```

## 🚀 Próximas Melhorias

### Fase 2: Slack API Integration
- Envio direto via webhook
- Mapeamento AM → Canal Slack
- Log de mensagens enviadas

### Fase 3: Configurações
- Templates personalizáveis
- Filtros avançados
- Agendamento de envios

## 💡 Dicas de Uso

1. **Priorize críticas**: Cards vermelhos primeiro
2. **Use busca**: Para AMs específicos
3. **Teste cópia**: Se Slack não abrir automaticamente
4. **Mobile friendly**: Funciona em tablets/celulares
5. **Atualização**: Regenere após novos dados

---

**Interface desenvolvida para otimizar comunicação de ações do pipeline via Slack** 📱