# Correção da Regra "Eligible to Share with Partner"

## Problema Identificado

A oportunidade **"Apex Group - #GenAI - Intelligent search legal use-case - #Kendra #Bedrock - BrLink"** aparecia incorretamente na regra "Eligible to Share with Partner", mesmo já tendo sido compartilhada com um parceiro.

### Cenário Específico:
- **4 ocorrências** da mesma oportunidade (ID: `006RU00000FnC93YAF`)
- **3 ocorrências** com status `"Eligible to Share with Partner"` (parceiros: NTT DATA Inc, GFT Technologies SE, COMPASS UOL)
- **1 ocorrência** com status `"AWS Opportunity Shared with Partner"` (parceiro: BrLink)

### Problema na Lógica Anterior:
A regra processava **cada linha individualmente**, sem considerar se a mesma oportunidade (mesmo ID) já havia sido compartilhada com algum parceiro.

## Solução Implementada

### Nova Lógica:
1. **Identificar oportunidades já compartilhadas**: Criar um conjunto com todos os IDs de oportunidades que têm pelo menos uma ocorrência com status `"AWS Opportunity Shared with Partner"`
2. **Filtrar antes de processar**: Excluir da regra todas as ocorrências `"Eligible to Share with Partner"` cujo ID já está no conjunto de oportunidades compartilhadas
3. **Processar apenas oportunidades nunca compartilhadas**: Aplicar a regra apenas para oportunidades que nunca foram compartilhadas com nenhum parceiro

### Código Implementado:

```python
def check_eligible_to_share(self, df: pd.DataFrame) -> List[Dict]:
    """
    Regra 4: Eligible to Share with Partner
    Se ACE Opportunity Type = Eligible to Share with Partner
    EXCETO se a mesma oportunidade já foi compartilhada com algum parceiro
    """
    issues = []
    
    # Primeiro, identificar oportunidades que já foram compartilhadas
    shared_opportunities = set(
        df[df['ACE Opportunity Type'] == 'AWS Opportunity Shared with Partner']
        ['Opportunity: 18 Character Oppty ID'].unique()
    )
    
    # Filtrar apenas oportunidades "Eligible to Share" que NÃO foram compartilhadas
    eligible_opps = df[
        (df['ACE Opportunity Type'] == 'Eligible to Share with Partner') &
        (~df['Opportunity: 18 Character Oppty ID'].isin(shared_opportunities))
    ]
    
    for _, row in eligible_opps.iterrows():
        issues.append({
            'type': 'eligible_to_share',
            'opportunity_id': row['Opportunity: 18 Character Oppty ID'],
            'opportunity_name': row['Opportunity: Opportunity Name'],
            'account_name': row['Opportunity: Account Name'],
            'partner_name': row['Partner Account'],
            'aws_stage': row['Opportunity: Stage'],
            'owner': row['Opportunity Owner Name'],
            'link': f"https://aws-crm.lightning.force.com/lightning/r/Opportunity/{row['Opportunity: 18 Character Oppty ID']}/view"
        })
    
    return issues
```

## Resultados da Correção

### Teste com Dados Reais (helo_partner_150925.xls):

**ANTES da correção:**
- Total de registros "Eligible to Share": **16**
- Registros Apex Group "Eligible to Share": **3** (falsos positivos)

**APÓS a correção:**
- Total de issues "Eligible to Share": **4** (redução de 75%)
- Issues da oportunidade Apex Group: **0** (problema resolvido)

### Casos de Teste Validados:

✅ **Cenário Apex Group**: Oportunidade com múltiplas ocorrências, algumas "Eligible" e pelo menos uma "Shared"
- **Resultado**: NÃO aparece na regra (correto)

✅ **Cenário Nunca Compartilhada**: Oportunidade apenas com ocorrências "Eligible to Share"
- **Resultado**: Aparece na regra (correto)

✅ **Cenário Totalmente Compartilhada**: Oportunidade apenas com ocorrências "AWS Opportunity Shared"
- **Resultado**: NÃO aparece na regra (correto)

## Benefícios

1. **Elimina falsos positivos**: Oportunidades já compartilhadas não aparecem mais como "não compartilhadas"
2. **Melhora a precisão**: Redução de 75% no número de alertas desnecessários
3. **Lógica de negócio correta**: Reflete que uma oportunidade compartilhada com 1 parceiro não precisa ser compartilhada com todos
4. **Melhora a eficiência**: Reduz ruído nos relatórios e dashboards

## Arquivos Modificados

- `scripts/slack message generator/slack_message_generator.py` - Implementação da correção
- `scripts/slack message generator/test_eligible_to_share_fix.py` - Testes unitários
- `scripts/slack message generator/test_real_data_validation.py` - Validação com dados reais

## Data da Implementação

**15 de Setembro de 2025**

---

**Status**: ✅ **IMPLEMENTADO E VALIDADO**