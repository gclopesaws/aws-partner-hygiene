# Follow-up Generator

## Descrição
O Follow-up Generator é um módulo que gera emails consolidados de follow-up por parceiro, listando todas as oportunidades ativas ordenadas por data de fechamento mais próxima.

## Funcionalidades

### 📧 Emails de Follow-up
- **Consolidação por parceiro**: Um email por parceiro com todas suas oportunidades ativas
- **Ordenação inteligente**: Oportunidades ordenadas por Close Date (mais próximo primeiro)
- **Informações completas**: Dados atuais de cada oportunidade para validação
- **Perguntas específicas**: Solicita atualizações e identifica onde AWS pode ajudar

### 🎯 Filtros Aplicados
- Exclui oportunidades com `Opportunity: Stage` = "Launched" ou "Closed Lost"
- Exclui oportunidades com `APN Partner Reported Stage` = "Launched" ou "Closed Lost"
- Inclui apenas parceiros com email válido
- Prioriza oportunidades com Close Date definido

### 📊 Métricas e Indicadores
- **Urgência por cores**: 🔴 Urgente (≤7 dias), 🟡 Próximo (≤30 dias), 🟢 Normal (≤90 dias)
- **Estatísticas do pipeline**: Total de oportunidades, valor total, oportunidades urgentes
- **Relatório resumo**: Visão executiva dos follow-ups gerados

## Como Usar

### Execução Básica
```bash
python3 "scripts/follow-up generator/followup_generator.py" partner.xls
```

### Arquivos Gerados
- `followup_emails.txt` - Emails completos prontos para envio
- `followup_emails.html` - Interface web interativa com botões mailto
- `followup_summary.txt` - Relatório resumo executivo

## Estrutura do Email

### Cabeçalho
- Saudação personalizada com nome do parceiro
- Contexto sobre o follow-up do pipeline conjunto
- Número total de oportunidades ativas

### Por Oportunidade
- **Informações atuais**: Close Date, Sales Stage, Valor, Última Atualização
- **Validação necessária**: Checklist para confirmar dados
- **Perguntas específicas**: 5 perguntas focadas em próximos passos e suporte
- **Link direto**: URL para Partner Central

### Resumo do Pipeline
- Estatísticas consolidadas do parceiro
- Próximos passos sugeridos
- Informações de contato da equipe AWS

## Critérios de Priorização

### Ordenação das Oportunidades
1. **Close Date** (mais próximo primeiro)
2. **Valor da oportunidade** (maior primeiro, como desempate)
3. **Última atualização** (mais antiga primeiro)

### Indicadores de Urgência
- **🔴 VENCIDO**: Close Date já passou
- **🔴 URGENTE**: Close Date ≤ 7 dias
- **🟡 PRÓXIMO**: Close Date ≤ 30 dias
- **🟢 NORMAL**: Close Date ≤ 90 dias
- **⚪ FUTURO**: Close Date > 90 dias
- **⚪ SEM DATA**: Close Date não informado

## Integração com Sistema

### Reutilização de Código
- Mesma lógica de carregamento de dados dos outros módulos
- Compatível com formatos Excel e HTML
- Tratamento robusto de erros e dados inválidos

### Adição ao Pipeline Principal
Para integrar ao `run_pipeline_analysis.py`, adicione:

```python
def run_followup_generator(data_file):
    """Executa o Follow-up Generator"""
    print("📧 EXECUTANDO: Follow-up Generator")
    print("Gerando emails de follow-up por parceiro...")
    
    try:
        script_path = os.path.join("scripts", "follow-up generator", "followup_generator.py")
        result = subprocess.run([
            sys.executable, script_path, data_file
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Follow-up Generator executado com sucesso!")
            print(result.stdout)
        else:
            print("❌ Erro no Follow-up Generator:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Erro ao executar Follow-up Generator: {e}")
        return False
    
    return True
```

## Casos de Uso

### 1. Follow-up Mensal
- Execução regular para manter parceiros engajados
- Revisão completa do pipeline conjunto

### 2. Follow-up de Urgência
- Foco em oportunidades com Close Date próximo
- Identificação proativa de riscos

### 3. Onboarding de Parceiros
- Primeiro follow-up após 15 dias de atividade
- Estabelecimento de processo de comunicação

### 4. Revisão Trimestral
- Análise profunda do pipeline
- Alinhamento estratégico com parceiros

## Benefícios

### Para AWS
- **Visibilidade**: Pipeline completo por parceiro
- **Proatividade**: Identificação de oportunidades em risco
- **Relacionamento**: Comunicação estruturada e regular
- **Previsibilidade**: Melhor forecast de fechamentos

### Para Parceiros
- **Organização**: Visão consolidada do pipeline
- **Suporte**: Canal claro para solicitar ajuda
- **Alinhamento**: Expectativas sincronizadas com AWS
- **Processo**: Fluxo estruturado para atualizações

## Interface HTML

### 🌐 Funcionalidades da Interface Web
- **Cards por parceiro**: Visualização organizada com estatísticas
- **Busca inteligente**: Filtro por nome, email ou empresa
- **Botões mailto**: Envio direto via cliente de email
- **Botões de cópia**: Cópia dos dados para uso manual
- **Indicadores visuais**: Urgência e alto valor destacados
- **Design responsivo**: Funciona em desktop e mobile

### 📊 Estatísticas Visuais
- Total de parceiros e oportunidades
- Contador de oportunidades urgentes
- Identificação de oportunidades de alto valor
- Data de geração do relatório

### 🎨 Recursos Visuais
- **Cores de urgência**: Vermelho para urgente, verde para alto valor
- **Animações**: Feedback visual ao copiar dados
- **Layout responsivo**: Adaptável a diferentes tamanhos de tela
- **Busca em tempo real**: Filtros instantâneos

## Próximas Melhorias

### Versão 2.0
- [x] Interface HTML interativa ✅
- [ ] Templates personalizáveis por tipo de parceiro
- [ ] Integração com calendário para agendamento
- [ ] Métricas de efetividade dos follow-ups

### Versão 3.0
- [ ] IA para personalização de mensagens
- [ ] Análise de sentimento das respostas
- [ ] Automação de follow-ups baseada em triggers
- [ ] Dashboard em tempo real