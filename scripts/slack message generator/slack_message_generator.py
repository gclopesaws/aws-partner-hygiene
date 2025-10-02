#!/usr/bin/env python3
"""
Slack Message Generator - Gera mensagens consolidadas por AM
Analisa oportunidades e cria mensagens de Slack formatadas com ações necessárias
"""

import pandas as pd
import sys
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

# Importa função utilitária para diretório de resultados
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from results_dir import get_dated_results_dir

class SlackMessageGenerator:
    def __init__(self, excel_file: str, no_partner_file: str = None):
        self.excel_file = excel_file
        self.no_partner_file = no_partner_file
        self.df = None
        self.no_partner_df = None
        self.load_data()
        
    def load_data(self):
        """Carrega dados do arquivo Excel"""
        try:
            # Carrega arquivo principal (com parceiros)
            try:
                self.df = pd.read_excel(self.excel_file, engine='openpyxl')
            except:
                try:
                    self.df = pd.read_excel(self.excel_file, engine='xlrd')
                except:
                    try:
                        # Se for um arquivo HTML disfarçado de Excel
                        with open(self.excel_file, 'r', encoding='utf-8') as f:
                            self.df = pd.read_html(f)[0]
                    except:
                        # Última tentativa com encoding diferente
                        with open(self.excel_file, 'r', encoding='iso-8859-1') as f:
                            self.df = pd.read_html(f)[0]
            
            print(f"Dados carregados: {len(self.df)} oportunidades")
            print(f"Colunas disponíveis: {len(self.df.columns)}")
            
            # Carrega arquivo de oportunidades sem parceiro (opcional)
            if self.no_partner_file:
                try:
                    try:
                        self.no_partner_df = pd.read_excel(self.no_partner_file, engine='openpyxl')
                    except:
                        try:
                            self.no_partner_df = pd.read_excel(self.no_partner_file, engine='xlrd')
                        except:
                            # Se for um arquivo HTML disfarçado de Excel
                            self.no_partner_df = pd.read_html(self.no_partner_file)[0]
                    
                    print(f"Dados sem parceiro carregados: {len(self.no_partner_df)} oportunidades")
                except Exception as e:
                    print(f"Aviso: Não foi possível carregar arquivo sem parceiro: {e}")
                    self.no_partner_df = None
            
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            sys.exit(1)
    
    def filter_active_opportunities(self) -> pd.DataFrame:
        """Filtra apenas oportunidades ativas do lado AWS (não Launched/Closed-Lost)"""
        # Filtra oportunidades que não estão finalizadas pela AWS
        # IMPORTANTE: Não filtra por partner stage, pois queremos detectar quando partner finalizou mas AWS não
        active_df = self.df[
            ~self.df['Opportunity: Stage'].isin(['Launched', 'Closed Lost'])
        ].copy()
        
        print(f"Oportunidades ativas (AWS): {len(active_df)} de {len(self.df)} total")
        return active_df
    
    def check_co_sell_missing(self, df: pd.DataFrame) -> List[Dict]:
        """
        Regra 1: Technology Partners - Co-Sell Missing
        Se a oportunidade for com technology partner, verificar se a opção 
        'I Attest to Providing Co-Sell on Opp' não estiver true.
        Esta regra só é válida se alguma das colunas Stage ou APN Partner Stage for igual a Launched.
        
        MODIFICAÇÕES: 
        - Usa DataFrame completo (self.df) para incluir oportunidades onde ambos os stages estão "Launched"
        - Exclui oportunidades "Partner Sourced For Visibility Only" (compartilhadas apenas para visualização)
        - Aplica threshold de $100 - apenas oportunidades com valor >= $100 são incluídas
        """
        issues = []
        
        # USA SELF.DF (completo) em vez de df (filtrado) para incluir casos AWS=Launched + Partner=Launched
        # EXCETO oportunidades "Partner Sourced For Visibility Only" (compartilhadas apenas para visualização)
        tech_partners = self.df[
            (self.df['Partner Type From Account'] == 'Technology Partner') &
            (self.df['I Attest to Providing Co-Sell on Opp'] != 1) &
            ((self.df['Opportunity: Stage'] == 'Launched') | (self.df['APN Partner Reported Stage'] == 'Launched')) &
            (self.df['ACE Opportunity Type'] != 'Partner Sourced For Visibility Only')
        ]
        
        # Aplicar threshold de $100 - apenas oportunidades com valor >= $100
        for _, row in tech_partners.iterrows():
            total_amount_value = row.get('Total Opportunity Amount', 0)
            try:
                # Converte para float, tratando valores nulos como 0
                if pd.isna(total_amount_value) or total_amount_value == '' or total_amount_value is None:
                    amount = 0
                else:
                    amount = float(total_amount_value)
            except (ValueError, TypeError):
                # Se não conseguir converter, trata como 0
                amount = 0
                print(f"Warning: Valor inválido para oportunidade {row.get('Opportunity: 18 Character Oppty ID', 'N/A')}: {total_amount_value}")
            
            # Só inclui se valor >= $100
            if amount >= 100:
                issues.append({
                    'type': 'co_sell_missing',
                    'opportunity_id': row['Opportunity: 18 Character Oppty ID'],
                    'opportunity_name': row['Opportunity: Opportunity Name'],
                    'account_name': row['Opportunity: Account Name'],
                    'partner_name': row['Partner Account'],
                    'aws_stage': row['Opportunity: Stage'],
                    'partner_stage': row['APN Partner Reported Stage'],
                    'owner': row['Opportunity Owner Name'],
                    'link': f"https://aws-crm.lightning.force.com/lightning/r/Opportunity/{row['Opportunity: 18 Character Oppty ID']}/view"
                })
        
        return issues
    
    def check_partner_stage_ahead(self, df: pd.DataFrame) -> List[Dict]:
        """
        Regra 2: Partner Stage à Frente
        Se APN Partner Reported Stage > Opportunity: Stage
        """
        issues = []
        
        # Mapeamento de estágios para comparação numérica
        stage_order = {
            'Prospect': 1,
            'Qualified': 2,
            'Technical Validation': 3,
            'Business Validation': 4,
            'Committed': 5,
            'Launched': 6,
            'Closed Lost': 0
        }
        
        for _, row in df.iterrows():
            partner_stage = row['APN Partner Reported Stage']
            aws_stage = row['Opportunity: Stage']
            
            # IMPORTANTE: Exclui oportunidades onde PARTNER já finalizou (Launched/Closed Lost)
            # Essas devem ser tratadas pela regra de desalinhamento, não stage à frente
            if partner_stage in ['Launched', 'Closed Lost']:
                continue
            
            # Verifica se ambos os estágios existem no mapeamento
            if partner_stage in stage_order and aws_stage in stage_order:
                if stage_order[partner_stage] > stage_order[aws_stage]:
                    issues.append({
                        'type': 'partner_stage_ahead',
                        'opportunity_id': row['Opportunity: 18 Character Oppty ID'],
                        'opportunity_name': row['Opportunity: Opportunity Name'],
                        'account_name': row['Opportunity: Account Name'],
                        'partner_name': row['Partner Account'],
                        'partner_stage': partner_stage,
                        'aws_stage': aws_stage,
                        'owner': row['Opportunity Owner Name'],
                        'link': f"https://aws-crm.lightning.force.com/lightning/r/Opportunity/{row['Opportunity: 18 Character Oppty ID']}/view"
                    })
        
        return issues
    
    def check_partner_finalized(self, df: pd.DataFrame) -> List[Dict]:
        """
        Regra 3: Desalinhamento - Partner Finalizou
        Se APN Partner Reported Stage = closed-lost ou launched
        """
        issues = []
        
        finalized_partners = df[
            df['APN Partner Reported Stage'].isin(['Closed Lost', 'Launched']) &
            (~df['Opportunity: Stage'].isin(['Closed Lost', 'Launched']))
        ]
        
        for _, row in finalized_partners.iterrows():
            issues.append({
                'type': 'partner_finalized',
                'opportunity_id': row['Opportunity: 18 Character Oppty ID'],
                'opportunity_name': row['Opportunity: Opportunity Name'],
                'account_name': row['Opportunity: Account Name'],
                'partner_name': row['Partner Account'],
                'partner_stage': row['APN Partner Reported Stage'],
                'aws_stage': row['Opportunity: Stage'],
                'owner': row['Opportunity Owner Name'],
                'link': f"https://aws-crm.lightning.force.com/lightning/r/Opportunity/{row['Opportunity: 18 Character Oppty ID']}/view"
            })
        
        return issues
    
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
    
    def check_close_date_soon(self, df: pd.DataFrame) -> List[Dict]:
        """
        Regra 5: Close Date nos Próximos 30 Dias
        Se Opportunity: Close Date estiver nos próximos 30 dias
        """
        issues = []
        
        from datetime import datetime, timedelta
        import pandas as pd
        
        # Data atual e data limite (30 dias à frente)
        today = datetime.now()
        thirty_days_ahead = today + timedelta(days=30)
        
        for _, row in df.iterrows():
            close_date_value = row['Opportunity: Close Date']
            
            # Pula se não há data de fechamento
            if pd.isna(close_date_value) or close_date_value == '':
                continue
            
            try:
                # Tenta converter para datetime
                if isinstance(close_date_value, str):
                    # Usa apenas formato americano mm/dd/yyyy
                    try:
                        close_date = datetime.strptime(close_date_value, '%m/%d/%Y')
                    except ValueError:
                        # Se formato americano não funcionou, pula
                        continue
                elif hasattr(close_date_value, 'date'):
                    # Se já é um objeto datetime/date
                    close_date = close_date_value if isinstance(close_date_value, datetime) else datetime.combine(close_date_value, datetime.min.time())
                else:
                    continue
                
                # Verifica se está nos próximos 30 dias
                if today <= close_date <= thirty_days_ahead:
                    days_until_close = (close_date - today).days
                    
                    issues.append({
                        'type': 'close_date_soon',
                        'opportunity_id': row['Opportunity: 18 Character Oppty ID'],
                        'opportunity_name': row['Opportunity: Opportunity Name'],
                        'account_name': row['Opportunity: Account Name'],
                        'partner_name': row['Partner Account'],
                        'aws_stage': row['Opportunity: Stage'],
                        'close_date': close_date.strftime('%m/%d/%Y'),
                        'days_until_close': days_until_close,
                        'owner': row['Opportunity Owner Name'],
                        'link': f"https://aws-crm.lightning.force.com/lightning/r/Opportunity/{row['Opportunity: 18 Character Oppty ID']}/view"
                    })
                    
            except (ValueError, TypeError) as e:
                # Se houver erro na conversão, pula esta oportunidade
                continue
        
        return issues
    
    def check_no_partner_opportunities(self) -> List[Dict]:
        """
        Regra 6: Oportunidades Sem Parceiro com Close Date nos Próximos 60 Dias
        Identifica oportunidades sem parceiro que fecham em breve
        """
        issues = []
        
        if self.no_partner_df is None:
            return issues
        
        from datetime import datetime, timedelta
        import pandas as pd
        
        # Data atual e data limite (60 dias à frente)
        today = datetime.now()
        sixty_days_ahead = today + timedelta(days=60)
        
        for _, row in self.no_partner_df.iterrows():
            close_date_value = row['Close Date']
            
            # Pula se não há data de fechamento
            if pd.isna(close_date_value) or close_date_value == '':
                continue
            
            try:
                # Tenta converter para datetime
                if isinstance(close_date_value, str):
                    # Usa apenas formato americano mm/dd/yyyy
                    try:
                        close_date = datetime.strptime(close_date_value, '%m/%d/%Y')
                    except ValueError:
                        # Se formato americano não funcionou, pula
                        continue
                elif hasattr(close_date_value, 'date'):
                    # Se já é um objeto datetime/date
                    close_date = close_date_value if isinstance(close_date_value, datetime) else datetime.combine(close_date_value, datetime.min.time())
                else:
                    continue
                
                # Verifica se está nos próximos 60 dias
                if today <= close_date <= sixty_days_ahead:
                    days_until_close = (close_date - today).days
                    
                    # Trata o campo next_step para evitar valores NaN
                    next_step_value = row.get('Next Step', '')
                    next_step_safe = str(next_step_value) if pd.notna(next_step_value) and next_step_value != '' else ''
                    
                    issues.append({
                        'type': 'no_partner_opportunity',
                        'opportunity_id': row['18 Character Oppty ID'],
                        'opportunity_name': row['Opportunity Name'],
                        'account_name': row['Account Name'],
                        'stage': row['Stage'],
                        'amount': row.get('Annualized Revenue (converted)', 0),
                        'currency': row.get('Annualized Revenue (converted) Currency', 'USD'),
                        'age': row.get('Age', 0),
                        'next_step': next_step_safe,
                        'close_date': close_date.strftime('%m/%d/%Y'),
                        'days_until_close': days_until_close,
                        'owner': row['Opportunity Owner'],
                        'link': f"https://aws-crm.lightning.force.com/lightning/r/Opportunity/{row['18 Character Oppty ID']}/view"
                    })
                    
            except (ValueError, TypeError) as e:
                # Se houver erro na conversão, pula esta oportunidade
                continue
        
        return issues
    
    def check_zero_amount_opportunities(self, df: pd.DataFrame) -> List[Dict]:
        """
        Regra 7: Oportunidades com Valor Zero (não para visibilidade)
        Se ACE Opportunity Type != 'Partner Sourced For Visibility Only' 
        E Total Opportunity Amount = 0 
        E Opportunity: Stage != 'Launched' ou 'Closed Lost'
        """
        issues = []
        
        for _, row in df.iterrows():
            # Verifica se ACE Opportunity Type existe e não é nulo
            ace_opportunity_type = row.get('ACE Opportunity Type', '')
            if pd.isna(ace_opportunity_type):
                continue
            
            # Filtro 1: ACE Opportunity Type != "Partner Sourced For Visibility Only"
            if ace_opportunity_type == 'Partner Sourced For Visibility Only':
                continue
            
            # Filtro 2: Total Opportunity Amount = 0 (tratamento seguro de valores nulos e não numéricos)
            total_amount_value = row.get('Total Opportunity Amount', 0)
            try:
                # Converte para float, tratando valores nulos como 0
                if pd.isna(total_amount_value) or total_amount_value == '' or total_amount_value is None:
                    amount = 0
                else:
                    amount = float(total_amount_value)
            except (ValueError, TypeError):
                # Se não conseguir converter, trata como 0
                amount = 0
                print(f"Warning: Valor inválido para oportunidade {row.get('Opportunity: 18 Character Oppty ID', 'N/A')}: {total_amount_value}")
            
            # Só continua se o valor for zero
            if amount != 0:
                continue
            
            # Filtro 3: Stages ativos (não Launched/Closed Lost)
            opportunity_stage = row.get('Opportunity: Stage', '')
            if opportunity_stage in ['Launched', 'Closed Lost']:
                continue
            
            # Se chegou até aqui, a oportunidade atende todos os critérios
            issues.append({
                'type': 'zero_amount_opportunity',
                'opportunity_id': row.get('Opportunity: 18 Character Oppty ID', ''),
                'opportunity_name': row.get('Opportunity: Opportunity Name', ''),
                'account_name': row.get('Opportunity: Account Name', ''),
                'partner_name': row.get('Partner Account', ''),
                'ace_opportunity_type': ace_opportunity_type,
                'total_amount': amount,
                'aws_stage': opportunity_stage,
                'owner': row.get('Opportunity Owner Name', ''),
                'link': f"https://aws-crm.lightning.force.com/lightning/r/Opportunity/{row.get('Opportunity: 18 Character Oppty ID', '')}/view"
            })
        
        return issues
    
    def check_shared_but_not_accepted(self, df: pd.DataFrame) -> List[Dict]:
        """
        Regra 8: Shared But Not Accepted
        Se APN Partner Reported Status = "Rejected" E
        (É única oportunidade com esse ID OU todas as outras com mesmo ID também são "Rejected")
        """
        issues = []
        
        for index, row in df.iterrows():
            # Verifica se o status é "Rejected" - CAMPO CORRETO: APN Partner Reported Status
            if row.get('APN Partner Reported Status') != 'Rejected':
                continue
            
            oppty_id = row.get('Opportunity: 18 Character Oppty ID')
            if pd.isna(oppty_id) or not str(oppty_id).strip():
                continue  # ID inválido
            
            # Buscar outras oportunidades com mesmo ID
            same_id_mask = (self.df['Opportunity: 18 Character Oppty ID'] == oppty_id)
            same_id_opps = self.df[same_id_mask & (self.df.index != index)]
            
            should_apply_rule = False
            scenario = 'Unknown'
            
            if len(same_id_opps) == 0:
                # Caso 1: Oportunidade única rejeitada
                should_apply_rule = True
                scenario = 'Unique'
            else:
                # Caso 2: Verificar se TODAS as outras também estão "Rejected"
                all_rejected = all(same_id_opps['APN Partner Reported Status'] == 'Rejected')
                
                if all_rejected:
                    should_apply_rule = True
                    scenario = 'All_Rejected'
            
            if should_apply_rule:
                issues.append({
                    'type': 'shared_but_not_accepted',
                    'opportunity_id': row.get('Opportunity: 18 Character Oppty ID', ''),
                    'opportunity_name': row.get('Opportunity: Opportunity Name', ''),
                    'account_name': row.get('Opportunity: Account Name', ''),
                    'partner_name': row.get('Partner Account', ''),
                    'partner_status': 'Rejected',
                    'aws_stage': row.get('Opportunity: Stage', ''),
                    'other_opportunities_count': len(same_id_opps),
                    'scenario': scenario,
                    'owner': row.get('Opportunity Owner Name', ''),
                    'link': f"https://aws-crm.lightning.force.com/lightning/r/Opportunity/{row.get('Opportunity: 18 Character Oppty ID', '')}/view"
                })
        
        return issues
    
    def group_issues_by_owner(self, all_issues: List[Dict]) -> Dict[str, List[Dict]]:
        """Agrupa issues por Opportunity Owner"""
        grouped = defaultdict(list)
        
        for issue in all_issues:
            owner = issue['owner']
            grouped[owner].append(issue)
        
        return dict(grouped)
    
    def generate_slack_message(self, owner: str, issues: List[Dict]) -> str:
        """Gera mensagem de Slack formatada para um AM específico"""
        
        # Conta issues por tipo
        co_sell_issues = [i for i in issues if i['type'] == 'co_sell_missing']
        stage_ahead_issues = [i for i in issues if i['type'] == 'partner_stage_ahead']
        finalized_issues = [i for i in issues if i['type'] == 'partner_finalized']
        share_issues = [i for i in issues if i['type'] == 'eligible_to_share']
        close_date_issues = [i for i in issues if i['type'] == 'close_date_soon']
        zero_amount_issues = [i for i in issues if i['type'] == 'zero_amount_opportunity']
        shared_not_accepted_issues = [i for i in issues if i['type'] == 'shared_but_not_accepted']
        
        # Conta partners únicos (apenas para issues que têm partner_name)
        unique_partners = len(set(issue['partner_name'] for issue in issues if 'partner_name' in issue))
        
        # Cabeçalho da mensagem
        message = f"""AÇÕES CONSOLIDADAS - {owner.upper()} (APENAS OPORTUNIDADES ATIVAS)

RESUMO:
Total de ações: {len(issues)}
Partners envolvidos: {unique_partners}
Oportunidades ativas: {len(issues)}

NOTA: Foram excluídas oportunidades já finalizadas (Launched/Closed-Lost)

"""
        
        # Seção 1: Co-Sell Missing
        if co_sell_issues:
            message += f"""1. TECHNOLOGY PARTNERS - CO-SELL MISSING ({len(co_sell_issues)})
Problema: Confirmação de Co-Sell não marcada no PAI View
Ação: Marcar "I Attest to Providing Co-Sell on Opp" para cada oportunidade
INSTRUÇÃO: Campo obrigatório para validação do co-sell com ISV. Atualize essa parte da mensagem informando que a oportunidade já foi dada como launched pelo parceiro ou pela AWS.

"""
            for i, issue in enumerate(co_sell_issues, 1):
                message += f"""{i}. {issue['account_name']}-{issue['opportunity_name']}
Partner: {issue['partner_name']}
AWS Stage: {issue['aws_stage']}
Partner Stage: {issue['partner_stage']}
Link: {issue['link']}

"""
            message += "--- FIM DA SEÇÃO 1 ---\n\n"
        
        # Seção 2: Partner Stage à Frente
        if stage_ahead_issues:
            message += f"""2. PARTNER STAGE À FRENTE ({len(stage_ahead_issues)})
Problema: Partner atualizou stage, AWS precisa sincronizar
Ação: Atualizar stage no Salesforce conforme status do partner
INSTRUÇÃO: Considerar atualizar o stage na AWS para refletir o estágio informado pelo parceiro e fazer a progressão correta da oportunidade

"""
            for i, issue in enumerate(stage_ahead_issues, 1):
                message += f"""{i}. {issue['account_name']}-{issue['opportunity_name']}
Partner: {issue['partner_name']}
Partner Stage: {issue['partner_stage']} → AWS Stage: {issue['aws_stage']}
Link: {issue['link']}

"""
            message += "--- FIM DA SEÇÃO 2 ---\n\n"
        
        # Seção 3: Partner Finalizou
        if finalized_issues:
            message += f"""3. DESALINHAMENTO - PARTNER FINALIZOU ({len(finalized_issues)})
CRÍTICO: Partner finalizou mas AWS ainda está ativo
Ação: Sincronizar status final no Salesforce URGENTE
INSTRUÇÃO: Definir status final apropriado. Alterar para launched (impacto em goals de partner attach) ou closed-lost (hygiene)

"""
            for i, issue in enumerate(finalized_issues, 1):
                message += f"""{i}. {issue['account_name']}-{issue['opportunity_name']}
Partner: {issue['partner_name']}
Partner Status: {issue['partner_stage']} vs AWS: {issue['aws_stage']}
Link: {issue['link']}

"""
            message += "--- FIM DA SEÇÃO 3 ---\n\n"
        
        # Seção 4: Eligible to Share
        if share_issues:
            message += f"""4. COMPARTILHAR COM PARTNER ({len(share_issues)})
Problema: Oportunidade elegível para compartilhamento
Ação: Compartilhar oportunidade com o partner
INSTRUÇÃO: Impacto direto na compliance e nos goals de Partner Attached Launched ARR. Risco de oportunidades não serem contabilizadas como launched. Identificar e compartilhar oportunidades com parceiros relevantes.

"""
            for i, issue in enumerate(share_issues, 1):
                message += f"""{i}. {issue['account_name']}-{issue['opportunity_name']}
Partner: {issue['partner_name']}
AWS Stage: {issue['aws_stage']}
Link: {issue['link']}

"""
            message += "--- FIM DA SEÇÃO 4 ---\n\n"
        
        # Seção 5: Close Date nos Próximos 30 Dias
        if close_date_issues:
            message += f"""5. CLOSE DATE NOS PRÓXIMOS 30 DIAS ({len(close_date_issues)})
Problema: Oportunidades com fechamento próximo
Ação: Validar se a data de fechamento está correta
INSTRUÇÃO: Time sensitive requerendo ação imediata. Validar status atual de consumo AWS. Confirmar se existe consumo real que justifique status launched nos próximos dias ou alterar o Close Date se necessário

"""
            for i, issue in enumerate(close_date_issues, 1):
                days_text = f"{issue['days_until_close']} dias" if issue['days_until_close'] > 1 else "1 dia"
                urgency = "HOJE" if issue['days_until_close'] == 0 else f"em {days_text}"
                
                message += f"""{i}. {issue['account_name']}-{issue['opportunity_name']}
Partner: {issue['partner_name']}
AWS Stage: {issue['aws_stage']}
Close Date: {issue['close_date']} ({urgency})
Link: {issue['link']}

"""
            message += "--- FIM DA SEÇÃO 5 ---\n\n"
        
        # Seção 6: Oportunidades Sem Parceiro
        no_partner_issues = [i for i in issues if i['type'] == 'no_partner_opportunity']
        if no_partner_issues:
            message += f"""6. OPORTUNIDADES SEM PARCEIRO - PRÓXIMOS 60 DIAS ({len(no_partner_issues)})
Problema: Oportunidades avançadas sem envolvimento de parceiros
Ação: Avaliar potencial de parceria estratégica
INSTRUÇÃO: Identificar parceiros relevantes para acelerar fechamento e aumentar valor da oportunidade. Considerar parceiros por vertical, tecnologia ou geografia.

"""
            for i, issue in enumerate(no_partner_issues, 1):
                days_text = f"{issue['days_until_close']} dias" if issue['days_until_close'] > 1 else "1 dia"
                urgency = "HOJE" if issue['days_until_close'] == 0 else f"em {days_text}"
                
                # Formata valor monetário
                amount_str = f"{issue['currency']} {issue['amount']:,.0f}" if issue['amount'] > 0 else "Valor não informado"
                age_str = f"{issue['age']:.0f} dias" if issue['age'] > 0 else "N/A"
                
                message += f"""{i}. {issue['account_name']} - {issue['opportunity_name']}
Stage: {issue['stage']} | Valor: {amount_str} | Idade: {age_str}
Close Date: {issue['close_date']} ({urgency})
Próximo Passo: {issue['next_step'][:100]}{'...' if len(issue['next_step']) > 100 else ''}
Link: {issue['link']}

"""
            message += "--- FIM DA SEÇÃO 6 ---\n\n"
        
        # Seção 7: Oportunidades com Valor Zero
        if zero_amount_issues:
            message += f"""7. OPORTUNIDADES COM VALOR ZERO ({len(zero_amount_issues)})
Problema: Oportunidades ativas sem valor definido
Ação: Validar e atualizar valor da oportunidade
INSTRUÇÃO: Oportunidades com valor zero podem impactar métricas de pipeline. Verificar se o valor está correto ou se a oportunidade deve ser atualizada/fechada.

"""
            for i, issue in enumerate(zero_amount_issues, 1):
                message += f"""{i}. {issue['account_name']} - {issue['opportunity_name']}
Partner: {issue['partner_name']}
AWS Stage: {issue['aws_stage']}
ACE Opportunity Type: {issue['ace_opportunity_type']}
Total Amount: {issue['total_amount']}
Link: {issue['link']}

"""
            message += "--- FIM DA SEÇÃO 7 ---\n\n"
        
        # Seção 8: Shared But Not Accepted
        if shared_not_accepted_issues:
            message += f"""8. OPORTUNIDADES REJEITADAS PARA RE-COMPARTILHAMENTO ({len(shared_not_accepted_issues)})
Problema: Oportunidades rejeitadas por parceiros sem alternativas ativas
Ação: Avaliar re-compartilhamento ou nova estratégia
INSTRUÇÃO: Considerar nova abordagem com mesmo parceiro, parceiro alternativo ou revisar posicionamento da oportunidade

"""
            for i, issue in enumerate(shared_not_accepted_issues, 1):
                scenario_text = ""
                if issue['scenario'] == 'Unique':
                    scenario_text = "Oportunidade única rejeitada"
                elif issue['scenario'] == 'All_Rejected':
                    total_partners = issue['other_opportunities_count'] + 1
                    scenario_text = f"{total_partners} parceiros rejeitaram esta oportunidade"
                
                message += f"""{i}. {issue['account_name']} - {issue['opportunity_name']}
Partner: {issue['partner_name']}
Status: {scenario_text}
AWS Stage: {issue['aws_stage']}
Link: {issue['link']}

"""
            message += "--- FIM DA SEÇÃO 8 ---\n\n"
        
        # Rodapé
        current_date = datetime.now().strftime('%d/%m/%Y às %H:%M')
        message += f"""---
Data: {current_date}
Para: @{owner.lower().replace(' ', '')}
Prioridade: ALTA
Escopo: Apenas oportunidades ativas (não Launched/Closed-Lost)
Dica: Use os links diretos para acessar cada oportunidade no Salesforce.
"""
        
        return message
    
    def generate_all_messages(self) -> Dict[str, str]:
        """Gera todas as mensagens de Slack por AM"""
        print("Analisando oportunidades...")
        
        # Filtra oportunidades ativas
        active_df = self.filter_active_opportunities()
        
        if active_df.empty:
            print("Nenhuma oportunidade ativa encontrada")
            return {}
        
        # Executa todas as verificações
        print("Verificando Co-Sell missing...")
        co_sell_issues = self.check_co_sell_missing(active_df)
        
        print("Verificando Partner Stage à frente...")
        stage_ahead_issues = self.check_partner_stage_ahead(active_df)
        
        print("Verificando Partner finalizou...")
        finalized_issues = self.check_partner_finalized(active_df)
        
        print("Verificando Eligible to Share...")
        share_issues = self.check_eligible_to_share(active_df)
        
        print("Verificando Close Date próximo...")
        close_date_issues = self.check_close_date_soon(active_df)
        
        print("Verificando oportunidades sem parceiro...")
        no_partner_issues = self.check_no_partner_opportunities()
        
        print("Verificando oportunidades com valor zero...")
        zero_amount_issues = self.check_zero_amount_opportunities(active_df)
        
        print("Verificando oportunidades rejeitadas para re-compartilhamento...")
        shared_not_accepted_issues = self.check_shared_but_not_accepted(active_df)
        
        # Combina todos os issues
        all_issues = co_sell_issues + stage_ahead_issues + finalized_issues + share_issues + close_date_issues + no_partner_issues + zero_amount_issues + shared_not_accepted_issues
        
        if not all_issues:
            print("Nenhuma ação necessária encontrada!")
            return {}
        
        print(f"Total de ações encontradas: {len(all_issues)}")
        print(f"   Co-Sell missing: {len(co_sell_issues)}")
        print(f"   Partner stage à frente: {len(stage_ahead_issues)}")
        print(f"   Partner finalizou: {len(finalized_issues)}")
        print(f"   Eligible to share: {len(share_issues)}")
        print(f"   Close date próximo: {len(close_date_issues)}")
        print(f"   Oportunidades sem parceiro: {len(no_partner_issues)}")
        print(f"   Oportunidades com valor zero: {len(zero_amount_issues)}")
        print(f"   Oportunidades rejeitadas: {len(shared_not_accepted_issues)}")
        
        # Agrupa por owner
        grouped_issues = self.group_issues_by_owner(all_issues)
        
        # Gera mensagens
        messages = {}
        for owner, owner_issues in grouped_issues.items():
            messages[owner] = self.generate_slack_message(owner, owner_issues)
        
        print(f"Mensagens geradas para {len(messages)} AMs")
        
        # Salva relatório detalhado das oportunidades onde partner finalizou
        if finalized_issues:
            self.save_partner_finalized_report(finalized_issues)
        
        return messages
    
    def save_messages(self, messages: Dict[str, str], output_file: str = None):
        """Salva mensagens em arquivo"""
        if not messages:
            print("Nenhuma mensagem para salvar")
            return
        
        if output_file is None:
            output_file = os.path.join(get_dated_results_dir(), "slack_messages.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"MENSAGENS DE SLACK - AÇÕES CONSOLIDADAS POR AM\n")
            f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n")
            f.write(f"Total de AMs: {len(messages)}\n")
            f.write("="*80 + "\n\n")
            
            for i, (owner, message) in enumerate(messages.items(), 1):
                f.write(f"MENSAGEM {i} - {owner}\n")
                f.write("="*60 + "\n")
                f.write(message)
                f.write("\n" + "="*60 + "\n\n")
        
        print(f"Mensagens salvas em: {output_file}")
    
    def save_partner_finalized_report(self, finalized_issues: List[Dict], output_file: str = None):
        """Salva relatório detalhado das oportunidades onde o partner finalizou"""
        if not finalized_issues:
            print("Nenhuma oportunidade 'Partner Finalizou' encontrada")
            return
        
        if output_file is None:
            output_file = os.path.join(get_dated_results_dir(), "partner_finalizou_detalhado.txt")
        
        # Agrupa por owner para melhor organização
        grouped_by_owner = defaultdict(list)
        for issue in finalized_issues:
            grouped_by_owner[issue['owner']].append(issue)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"RELATÓRIO DETALHADO - OPORTUNIDADES ONDE PARTNER FINALIZOU\n")
            f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n")
            f.write(f"Total de oportunidades: {len(finalized_issues)}\n")
            f.write(f"Total de AMs envolvidos: {len(grouped_by_owner)}\n")
            f.write("="*100 + "\n\n")
            
            f.write("RESUMO POR STATUS DO PARTNER:\n")
            launched_count = len([i for i in finalized_issues if i['partner_stage'] == 'Launched'])
            closed_lost_count = len([i for i in finalized_issues if i['partner_stage'] == 'Closed Lost'])
            f.write(f"• Partner = Launched: {launched_count} oportunidades\n")
            f.write(f"• Partner = Closed Lost: {closed_lost_count} oportunidades\n\n")
            
            f.write("DETALHAMENTO POR AM:\n")
            f.write("="*100 + "\n\n")
            
            for owner, owner_issues in sorted(grouped_by_owner.items()):
                f.write(f"AM: {owner}\n")
                f.write(f"Oportunidades: {len(owner_issues)}\n")
                f.write("-" * 80 + "\n")
                
                for i, issue in enumerate(owner_issues, 1):
                    f.write(f"{i}. OPORTUNIDADE: {issue['opportunity_name']}\n")
                    f.write(f"   ID: {issue['opportunity_id']}\n")
                    f.write(f"   Account: {issue['account_name']}\n")
                    f.write(f"   Partner: {issue['partner_name']}\n")
                    f.write(f"   Status AWS: {issue['aws_stage']}\n")
                    f.write(f"   Status Partner: {issue['partner_stage']}\n")
                    f.write(f"   Link: {issue['link']}\n")
                    f.write(f"   AÇÃO NECESSÁRIA: {'Atualizar para Launched' if issue['partner_stage'] == 'Launched' else 'Atualizar para Closed Lost'}\n")
                    f.write("\n")
                
                f.write("=" * 80 + "\n\n")
            
            f.write("LISTA CONSOLIDADA (PARA ANÁLISE RÁPIDA):\n")
            f.write("="*100 + "\n")
            f.write("ID_OPORTUNIDADE | ACCOUNT | PARTNER | AWS_STAGE | PARTNER_STAGE | AM\n")
            f.write("-" * 100 + "\n")
            
            for issue in sorted(finalized_issues, key=lambda x: (x['owner'], x['partner_stage'])):
                f.write(f"{issue['opportunity_id']} | {issue['account_name'][:25]:<25} | {issue['partner_name'][:20]:<20} | {issue['aws_stage']:<15} | {issue['partner_stage']:<12} | {issue['owner']}\n")
        
        print(f"Relatório detalhado 'Partner Finalizou' salvo em: {output_file}")

def main():
    """Função principal"""
    print("="*60)
    print("SLACK MESSAGE GENERATOR")
    print("="*60)
    print()
    
    # Verifica argumentos
    if len(sys.argv) < 2:
        print("ERRO: Arquivo Excel não especificado")
        print()
        print("Uso:")
        print(f"   python3 {sys.argv[0]} <arquivo.xls> [arquivo_sem_parceiro.xls]")
        print()
        print("Exemplo:")
        print(f"   python3 {sys.argv[0]} report1755715103376.xls")
        print(f"   python3 {sys.argv[0]} report1755715103376.xls ricarger-nopartner.xls")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    no_partner_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Inicializa gerador
    generator = SlackMessageGenerator(excel_file, no_partner_file)
    
    # Gera mensagens
    messages = generator.generate_all_messages()
    
    # Salva mensagens
    generator.save_messages(messages)
    
    print("="*60)
    print("MENSAGENS DE SLACK GERADAS!")
    print("="*60)

if __name__ == "__main__":
    main()