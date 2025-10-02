#!/usr/bin/env python3
"""
Pipeline Hygiene Checker - Versão com template específico
"""

import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import os

# Importa função utilitária para diretório de resultados
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from results_dir import get_dated_results_dir

class PipelineHygieneChecker:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self.today = datetime.now().date()
        
        # Mapeamento de estágios para comparação numérica
        self.stage_order = {
            'Prospect': 1,
            'Qualified': 2,
            'Technical Validation': 3,
            'Business Validation': 4,
            'Committed': 5,
            'Launched': 6,
            'Closed Lost': 0
        }
        
        # Lista de Partner Accounts excluídos de todas as verificações
        self.excluded_partners = [
            'Omie'
        ]
        
        self.load_data()
        
    def load_data(self):
        """Carrega os dados da planilha"""
        try:
            self.df = pd.read_html(self.file_path)[0]
            
            # Converte colunas de data
            if 'APN Target Launch Date' in self.df.columns:
                self.df['APN Target Launch Date'] = pd.to_datetime(
                    self.df['APN Target Launch Date'], errors='coerce'
                )
            if 'APN Partner Last Modified Date' in self.df.columns:
                self.df['APN Partner Last Modified Date'] = pd.to_datetime(
                    self.df['APN Partner Last Modified Date'], errors='coerce'
                )
            
            print(f"✅ Dados carregados: {len(self.df)} oportunidades")
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            
    def find_all_issues_by_contact(self):
        """Encontra todas as issues agrupadas por contato"""
        if self.df is None:
            return {}
            
        contacts = {}
        
        # Para cada linha, verifica todas as regras
        for _, row in self.df.iterrows():
            contact_email = row.get('APN Opportunity Owner Email', 'N/A')
            contact_name = row.get('Partner Account', 'Parceiro')
            
            if contact_email == 'N/A':
                continue
                
            # Inicializa contato se não existe
            if contact_email not in contacts:
                contacts[contact_email] = {
                    'contact_name': contact_name,
                    'contact_email': contact_email,
                    'opportunities': []
                }
            
            # Lista para armazenar as regras que esta oportunidade viola
            violated_rules = []
            additional_fields = {}
            
            # Condição base: Opportunity: Stage != Closed Lost
            if row.get('Opportunity: Stage') == 'Closed Lost':
                continue
            
            # Verificação de exclusão: pula parceiros na lista de exclusões
            partner_account = row.get('Partner Account', '')
            if partner_account in self.excluded_partners:
                continue
            
            # Regra 1: Launch Date Vencido
            if (not pd.isna(row.get('APN Target Launch Date')) and
                row.get('APN Partner Reported Stage') not in ['Launched', 'Closed Lost'] and
                row.get('APN Target Launch Date').date() < self.today):
                violated_rules.append('OPORTUNIDADES COM LAUNCH DATE VENCIDO')
                additional_fields['APN Partner Reported Stage'] = row.get('APN Partner Reported Stage', 'N/A')
                additional_fields['APN Target Launch Date'] = row.get('APN Target Launch Date', 'N/A')
            
            # Regra 2: Launch Date Próximo
            if (not pd.isna(row.get('APN Target Launch Date')) and
                row.get('APN Partner Reported Stage') not in ['Launched', 'Closed Lost'] and
                row.get('APN Target Launch Date').date() <= self.today + timedelta(days=30) and
                row.get('APN Target Launch Date').date() >= self.today):
                violated_rules.append('OPORTUNIDADES COM LAUNCH DATE PRÓXIMO')
                additional_fields['APN Target Launch Date'] = row.get('APN Target Launch Date', 'N/A')
            
            # Regra 3: Stalled
            if (not pd.isna(row.get('APN Partner Last Modified Date')) and
                row.get('APN Partner Last Modified Date').date() < self.today - timedelta(days=45) and
                row.get('APN Partner Reported Stage') != 'Launched'):
                violated_rules.append('STALLED OPPORTUNITIES')
                additional_fields['APN Partner Last Modified Date'] = row.get('APN Partner Last Modified Date', 'N/A')
            
            # Regra 4: FVO (excluindo oportunidades Launched e Closed Lost)
            if (row.get('ACE Opportunity Type') == 'Partner Sourced For Visibility Only' and
                row.get('Opportunity: Stage') not in ['Launched', 'Closed Lost'] and
                row.get('APN Partner Reported Stage') not in ['Launched', 'Closed Lost']):
                violated_rules.append('FVO OPPORTUNITIES')
            
            # Nova Regra 5: FVO com Valor Zero
            if (row.get('ACE Opportunity Type') == 'Partner Sourced For Visibility Only' and
                self._get_total_amount(row) == 0 and
                row.get('APN Partner Reported Stage') not in ['Launched', 'Closed Lost']):
                violated_rules.append('FVO ZERO AMOUNT OPPORTUNITIES')
                additional_fields['Total Opportunity Amount'] = row.get('Total Opportunity Amount', 'N/A')
                additional_fields['APN Partner Reported Stage'] = row.get('APN Partner Reported Stage', 'N/A')
            
            # Regra 6: Mismatch de Estágios (excluindo FVO)
            partner_stage = row.get('APN Partner Reported Stage')
            aws_stage = row.get('Opportunity: Stage')
            
            if (not pd.isna(partner_stage) and not pd.isna(aws_stage) and
                partner_stage != 'Launched' and partner_stage != aws_stage and
                row.get('ACE Opportunity Type') != 'Partner Sourced For Visibility Only'):
                
                # Verifica se ambos os estágios existem no mapeamento
                if partner_stage in self.stage_order and aws_stage in self.stage_order:
                    # Partner Stage Inferior ao AWS Stage
                    # EXCETO quando Partner Stage é "Closed Lost" (estado final, não pode ser alterado)
                    if (self.stage_order[partner_stage] < self.stage_order[aws_stage] and 
                        partner_stage != 'Closed Lost'):
                        violated_rules.append('PARTNER STAGE INFERIOR')
                        additional_fields['APN Partner Reported Stage'] = partner_stage
                        additional_fields['Opportunity: Stage'] = aws_stage
            
            # Se tem alguma regra violada, adiciona à lista
            if violated_rules:
                opportunity_data = {
                    'opportunity_id': row.get('APN Opportunity Identifier', 'N/A'),
                    'apn_opportunity_id': row.get('APN Opportunity ID', 'N/A'),
                    'opportunity_name': row.get('Opportunity: Opportunity Name', 'N/A'),
                    'account_name': row.get('Opportunity: Account Name', 'N/A'),
                    'monthly_revenue': row.get('Estimated AWS Monthly Recurring Revenue', 'N/A'),
                    'violated_rules': violated_rules,
                    'additional_fields': additional_fields
                }
                
                contacts[contact_email]['opportunities'].append(opportunity_data)
        
        # Remove contatos sem oportunidades
        contacts = {k: v for k, v in contacts.items() if v['opportunities']}
        
        return contacts
        
    def format_currency(self, value):
        """Formata valores monetários"""
        if pd.isna(value) or value == 'N/A':
            return 'N/A'
        try:
            return f"${float(value):,.2f}"
        except:
            return str(value)
            
    def format_date(self, date_value):
        """Formata datas"""
        if pd.isna(date_value) or date_value == 'N/A':
            return 'N/A'
        try:
            if isinstance(date_value, str):
                return date_value
            return date_value.strftime('%d/%m/%Y')
        except:
            return str(date_value)
    
    def _get_total_amount(self, row):
        """Converte Total Opportunity Amount para float, retorna 0 se inválido"""
        amount = row.get('Total Opportunity Amount', 0)
        if pd.isna(amount) or amount == 'N/A' or amount == '':
            return 0
        try:
            return float(amount)
        except (ValueError, TypeError):
            return 0
            
    def create_opportunity_link(self, opportunity_name: str, apn_opportunity_id: str) -> str:
        """Cria link para a oportunidade no Partner Central"""
        if pd.isna(apn_opportunity_id) or apn_opportunity_id == 'N/A' or not str(apn_opportunity_id).strip():
            return opportunity_name  # Retorna apenas o nome se não tiver ID
        
        url = f"https://partnercentral.awspartner.com/partnercentral2/s/editopportunity?id={apn_opportunity_id}"
        return f"{opportunity_name}\nLink: {url}"
            
    def generate_email(self, contact_info: Dict) -> str:
        """Gera email mais legível e assertivo para o AM"""
        contact_name = contact_info['contact_name']
        contact_email = contact_info['contact_email']
        opportunities = contact_info['opportunities']
        
        if pd.isna(contact_name) or not str(contact_name).strip():
            contact_name = "Parceiro"
            
        # Data atual formatada em português
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            current_date = datetime.now().strftime('%B de %Y')
        except:
            # Fallback para meses em português manualmente
            months_pt = {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }
            now = datetime.now()
            current_date = f"{months_pt[now.month]} de {now.year}"
        total_opps = len(opportunities)
        
        email_body = f"""Para: {contact_email}
Assunto: AWS <> {contact_name} - AÇÃO NECESSÁRIA - Atualização de oportunidades {current_date}

Olá {contact_name},

Identificamos as seguintes oportunidades em nosso pipeline que necessitam de atualização. Solicitamos seu apoio para realizar os ajustes necessários.

{'='*80}
"""
        
        # Lista todas as oportunidades com formato melhorado
        for i, opp in enumerate(opportunities, 1):
            opportunity_link = self.create_opportunity_link(opp['opportunity_name'], opp['apn_opportunity_id'])
            email_body += f"""
Oportunidade {i} - {opportunity_link}
Contato APN: {contact_email}
ID: {opp['opportunity_id']}
Cliente: {opp['account_name']}
Revenue Estimado: {self.format_currency(opp['monthly_revenue'])}

Ações recomendadas:
{self.format_attention_points_improved(opp)}

{'-'*80}
"""
        
        email_body += f"""

PRÓXIMOS PASSOS:
- Atualize as oportunidades no sistema Partner Central
- Confirme os dados com seus clientes
- Entre em contato conosco se precisar de suporte

Qualquer dúvida, responda este email ou entre em contato com nossa equipe.

Obrigado pela parceria!

Equipe AWS Partner
Email: Responda este email para dúvidas
Portal: Partner Central - https://partnercentral.awspartner.com
"""
        
        return email_body
        
    def generate_email_english(self, contact_info: Dict) -> str:
        """Generates email in English for international partners"""
        contact_name = contact_info['contact_name']
        contact_email = contact_info['contact_email']
        opportunities = contact_info['opportunities']
        
        if pd.isna(contact_name) or not str(contact_name).strip():
            contact_name = "Partner"
            
        # Current date formatted in English
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
            current_date = datetime.now().strftime('%B %Y')
        except:
            # Fallback para meses em inglês manualmente
            months_en = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }
            now = datetime.now()
            current_date = f"{months_en[now.month]} {now.year}"
        total_opps = len(opportunities)
        
        email_body = f"""To: {contact_email}
Subject: AWS <> {contact_name} - ACTION REQUIRED - Opportunity Updates {current_date}

Hello partner {contact_name},

We have identified the following opportunities in our pipeline that require updates. We request your support to make the necessary adjustments.

{'='*80}
"""
        
        # List all opportunities with improved format
        for i, opp in enumerate(opportunities, 1):
            opportunity_link = self.create_opportunity_link(opp['opportunity_name'], opp['apn_opportunity_id'])
            email_body += f"""
Opportunity {i} - {opportunity_link}
APN Contact: {contact_email}
ID: {opp['opportunity_id']}
Customer: {opp['account_name']}
Estimated Revenue: {self.format_currency(opp['monthly_revenue'])}

Recommended Actions:
{self.format_attention_points_improved_english(opp)}

{'-'*80}
"""
        
        email_body += f"""

NEXT STEPS:
- Update the opportunities in Partner Central system
- Confirm the data with your customers
- Contact us if you need support

If you have any questions, please reply to this email or contact our team.

Thank you for the partnership!

AWS Partner Team
Email: Reply to this email for questions
Portal: Partner Central - https://partnercentral.awspartner.com

---
Report automatically generated on {datetime.now().strftime('%m/%d/%Y at %H:%M')}
"""
        
        return email_body
        
    def format_attention_points(self, opp: Dict) -> str:
        """Formata os pontos de atenção de uma oportunidade"""
        violated_rules = opp['violated_rules']
        additional_fields = opp['additional_fields']
        
        attention_points = []
        
        for rule in violated_rules:
            if rule == 'OPORTUNIDADES COM LAUNCH DATE VENCIDO':
                launch_date = self.format_date(additional_fields.get('APN Target Launch Date', 'N/A'))
                attention_points.append(f"{rule}: APN Target Launch Date: {launch_date}")
                
            elif rule == 'OPORTUNIDADES COM LAUNCH DATE PRÓXIMO':
                launch_date = self.format_date(additional_fields.get('APN Target Launch Date', 'N/A'))
                attention_points.append(f"{rule}: APN Target Launch Date: {launch_date}")
                
            elif rule == 'STALLED OPPORTUNITIES':
                last_modified = self.format_date(additional_fields.get('APN Partner Last Modified Date', 'N/A'))
                attention_points.append(f"{rule}: APN Partner Last Modified Date: {last_modified}")
                
            elif rule == 'FVO OPPORTUNITIES':
                attention_points.append(rule)
                
            elif rule == 'PARTNER STAGE SUPERIOR':
                partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
                opp_stage = additional_fields.get('Opportunity: Stage', 'N/A')
                attention_points.append(f"{rule}\nAPN Partner Reported Stage: {partner_stage}\nOpportunity: Stage: {opp_stage}")
                
            elif rule == 'PARTNER STAGE INFERIOR':
                partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
                opp_stage = additional_fields.get('Opportunity: Stage', 'N/A')
                attention_points.append(f"{rule}\nAPN Partner Reported Stage: {partner_stage}\nOpportunity: Stage: {opp_stage}")
        
        return '\n'.join(attention_points)
        
    def format_attention_points_improved(self, opp: Dict) -> str:
        """Formata os pontos de atencao de forma mais legivel e assertiva"""
        additional_fields = opp['additional_fields']
        
        # REGRA ESPECIAL: Se AWS Stage é "Launched", só verificar Partner Stage mismatch
        aws_stage = additional_fields.get('Opportunity: Stage', '')
        if aws_stage == 'Launched':
            return self._check_partner_stage_for_launched(opp)
        
        # Lógica normal para outros casos
        return self._check_all_rules(opp)
    
    def _check_partner_stage_for_launched(self, opp: Dict) -> str:
        """Verifica apenas Partner Stage mismatch quando AWS Stage é Launched"""
        additional_fields = opp['additional_fields']
        partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
        aws_stage = additional_fields.get('Opportunity: Stage', 'Launched')
        
        attention_points = []
        
        # Se Partner não está em Launched, mostrar desalinhamento
        if partner_stage != 'Launched' and partner_stage != 'N/A':
            attention_points.append(f"Partner Sales Stage atrasado em relação à AWS:")
            attention_points.append(f"Seu estágio: {partner_stage}")
            attention_points.append(f"Estágio AWS: {aws_stage}")
            attention_points.append(f"Ação: É necessário ajustar o estágio atual da oportunidade para que esteja em conformidade com o status registrado na AWS. Caso haja discrepância, por favor, forneça uma descrição detalhada do estágio atual e dos próximos passos planejados, permitindo assim a atualização precisa do status na AWS")
        elif partner_stage == 'Launched':
            # Opcional: mensagem de sucesso quando alinhado
            attention_points.append(f"✅ Oportunidade finalizada com sucesso!")
            attention_points.append(f"Status AWS: {aws_stage}")
            attention_points.append(f"Status Partner: {partner_stage}")
            attention_points.append(f"Ação: Nenhuma ação necessária - oportunidade alinhada")
        else:
            # Caso Partner Stage seja N/A
            attention_points.append(f"Partner Sales Stage não informado:")
            attention_points.append(f"Seu estágio: {partner_stage}")
            attention_points.append(f"Estágio AWS: {aws_stage}")
            attention_points.append(f"Ação: Atualize seu stage no Partner Central para \"Launched\" para alinhar com o status final da oportunidade")
        
        return '\n'.join(attention_points)
    
    def _check_all_rules(self, opp: Dict) -> str:
        """Verifica todas as regras normalmente (quando AWS Stage não é Launched)"""
        violated_rules = opp['violated_rules']
        additional_fields = opp['additional_fields']
        
        attention_points = []
        
        for i, rule in enumerate(violated_rules):
            if i > 0:  # Adiciona linha em branco entre recomendações
                attention_points.append("")
            
            if rule == 'OPORTUNIDADES COM LAUNCH DATE VENCIDO':
                launch_date = self.format_date(additional_fields.get('APN Target Launch Date', 'N/A'))
                days_overdue = (self.today - additional_fields.get('APN Target Launch Date').date()).days if not pd.isna(additional_fields.get('APN Target Launch Date')) else 0
                attention_points.append(f"Launch date vencido ({days_overdue} dias em atraso):")
                attention_points.append(f"Data prevista: {launch_date}")
                attention_points.append(f"Ação: Atualize a data de lançamento ou status da oportunidade")
                
            elif rule == 'OPORTUNIDADES COM LAUNCH DATE PRÓXIMO':
                launch_date = self.format_date(additional_fields.get('APN Target Launch Date', 'N/A'))
                days_remaining = (additional_fields.get('APN Target Launch Date').date() - self.today).days if not pd.isna(additional_fields.get('APN Target Launch Date')) else 0
                attention_points.append(f"Launch date próximo ({days_remaining} dias restantes):")
                attention_points.append(f"Data prevista: {launch_date}")
                attention_points.append(f"Ação: Confirme se a data será cumprida ou atualize")
                
            elif rule == 'STALLED OPPORTUNITIES':
                last_modified = self.format_date(additional_fields.get('APN Partner Last Modified Date', 'N/A'))
                days_stalled = (self.today - additional_fields.get('APN Partner Last Modified Date').date()).days if not pd.isna(additional_fields.get('APN Partner Last Modified Date')) else 0
                attention_points.append(f"Oportunidade parada ({days_stalled} dias sem atualização):")
                attention_points.append(f"Última atualização: {last_modified}")
                attention_points.append(f"Ação: Atualize o status e próximos passos")
                
            elif rule == 'FVO OPPORTUNITIES':
                attention_points.append(f"Oportunidade apenas para visibilidade:")
                attention_points.append(f"Ação: Altere para 'Co-sell with AWS' se houver engajamento conjunto")
                
            elif rule == 'FVO ZERO AMOUNT OPPORTUNITIES':
                total_amount = self.format_currency(additional_fields.get('Total Opportunity Amount', 'N/A'))
                partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
                attention_points.append(f"Oportunidade de visibilidade com valor zero:")
                attention_points.append(f"Valor total: {total_amount}")
                attention_points.append(f"Status atual: {partner_stage}")
                attention_points.append(f"Ação: Confirme se o valor está correto ou atualize para refletir o valor real da oportunidade")
                
            elif rule == 'PARTNER STAGE SUPERIOR':
                partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
                opp_stage = additional_fields.get('Opportunity: Stage', 'N/A')
                attention_points.append(f"Partner Sales Stage à frente da AWS:")
                attention_points.append(f"Seu estágio: {partner_stage}")
                attention_points.append(f"Estágio AWS: {opp_stage}")
                attention_points.append(f"Ação: Poderia atualizar os próximos passos ou formalizar aqui no email qual status da oportunidade?")
                
            elif rule == 'PARTNER STAGE INFERIOR':
                partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
                opp_stage = additional_fields.get('Opportunity: Stage', 'N/A')
                attention_points.append(f"Partner Sales Stage atrasado em relação à AWS:")
                attention_points.append(f"Seu estágio: {partner_stage}")
                attention_points.append(f"Estágio AWS: {opp_stage}")
                attention_points.append(f"Ação: É necessário ajustar o estágio atual da oportunidade para que esteja em conformidade com o status registrado na AWS. Caso haja discrepância, por favor, forneça uma descrição detalhada do estágio atual e dos próximos passos planejados, permitindo assim a atualização precisa do status na AWS")
        
        return '\n'.join(attention_points)
        
    def format_attention_points_improved_english(self, opp: Dict) -> str:
        """Formats attention points in English for international partners"""
        additional_fields = opp['additional_fields']
        
        # SPECIAL RULE: If AWS Stage is "Launched", only check Partner Stage mismatch
        aws_stage = additional_fields.get('Opportunity: Stage', '')
        if aws_stage == 'Launched':
            return self._check_partner_stage_for_launched_english(opp)
        
        # Normal logic for other cases
        return self._check_all_rules_english(opp)
    
    def _check_partner_stage_for_launched_english(self, opp: Dict) -> str:
        """Checks only Partner Stage mismatch when AWS Stage is Launched (English version)"""
        additional_fields = opp['additional_fields']
        partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
        aws_stage = additional_fields.get('Opportunity: Stage', 'Launched')
        
        attention_points = []
        
        # If Partner is not in Launched, show misalignment
        if partner_stage != 'Launched' and partner_stage != 'N/A':
            attention_points.append(f"Partner Sales Stage behind AWS:")
            attention_points.append(f"Your stage: {partner_stage}")
            attention_points.append(f"AWS stage: {aws_stage}")
            attention_points.append(f"Action: It is necessary to adjust the current opportunity stage to comply with the status recorded in AWS. If there is a discrepancy, please provide a detailed description of the current stage and planned next steps, thus allowing accurate status update in AWS")
        elif partner_stage == 'Launched':
            # Optional: success message when aligned
            attention_points.append(f"✅ Opportunity successfully completed!")
            attention_points.append(f"AWS Status: {aws_stage}")
            attention_points.append(f"Partner Status: {partner_stage}")
            attention_points.append(f"Action: No action needed - opportunity aligned")
        else:
            # Case when Partner Stage is N/A
            attention_points.append(f"Partner Sales Stage not informed:")
            attention_points.append(f"Your stage: {partner_stage}")
            attention_points.append(f"AWS stage: {aws_stage}")
            attention_points.append(f"Action: Update your stage in Partner Central to \"Launched\" to align with the final opportunity status")
        
        return '\n'.join(attention_points)
    
    def _check_all_rules_english(self, opp: Dict) -> str:
        """Checks all rules normally (when AWS Stage is not Launched) - English version"""
        violated_rules = opp['violated_rules']
        additional_fields = opp['additional_fields']
        
        attention_points = []
        
        for i, rule in enumerate(violated_rules):
            if i > 0:  # Add blank line between recommendations
                attention_points.append("")
            
            if rule == 'OPORTUNIDADES COM LAUNCH DATE VENCIDO':
                launch_date = self.format_date(additional_fields.get('APN Target Launch Date', 'N/A'))
                days_overdue = (self.today - additional_fields.get('APN Target Launch Date').date()).days if not pd.isna(additional_fields.get('APN Target Launch Date')) else 0
                attention_points.append(f"Overdue launch date ({days_overdue} days overdue):")
                attention_points.append(f"Expected date: {launch_date}")
                attention_points.append(f"Action: Update the launch date or opportunity status")
                
            elif rule == 'OPORTUNIDADES COM LAUNCH DATE PRÓXIMO':
                launch_date = self.format_date(additional_fields.get('APN Target Launch Date', 'N/A'))
                days_remaining = (additional_fields.get('APN Target Launch Date').date() - self.today).days if not pd.isna(additional_fields.get('APN Target Launch Date')) else 0
                attention_points.append(f"Upcoming launch date ({days_remaining} days remaining):")
                attention_points.append(f"Expected date: {launch_date}")
                attention_points.append(f"Action: Confirm if the date will be met or update")
                
            elif rule == 'STALLED OPPORTUNITIES':
                last_modified = self.format_date(additional_fields.get('APN Partner Last Modified Date', 'N/A'))
                days_stalled = (self.today - additional_fields.get('APN Partner Last Modified Date').date()).days if not pd.isna(additional_fields.get('APN Partner Last Modified Date')) else 0
                attention_points.append(f"Stalled opportunity ({days_stalled} days without update):")
                attention_points.append(f"Last update: {last_modified}")
                attention_points.append(f"Action: Update status and next steps")
                
            elif rule == 'FVO OPPORTUNITIES':
                attention_points.append(f"For visibility only opportunity:")
                attention_points.append(f"Action: Change to 'Co-sell with AWS' if there is joint engagement")
                
            elif rule == 'FVO ZERO AMOUNT OPPORTUNITIES':
                total_amount = self.format_currency(additional_fields.get('Total Opportunity Amount', 'N/A'))
                partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
                attention_points.append(f"Visibility-only opportunity with zero value:")
                attention_points.append(f"Total amount: {total_amount}")
                attention_points.append(f"Current status: {partner_stage}")
                attention_points.append(f"Action: Please confirm if the value is correct or update to reflect the real opportunity value")
                
            elif rule == 'PARTNER STAGE SUPERIOR':
                partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
                opp_stage = additional_fields.get('Opportunity: Stage', 'N/A')
                attention_points.append(f"Partner Sales Stage ahead of AWS:")
                attention_points.append(f"Your stage: {partner_stage}")
                attention_points.append(f"AWS stage: {opp_stage}")
                attention_points.append(f"Action: Could you update the next steps or formalize in this email what is the opportunity status?")
                
            elif rule == 'PARTNER STAGE INFERIOR':
                partner_stage = additional_fields.get('APN Partner Reported Stage', 'N/A')
                opp_stage = additional_fields.get('Opportunity: Stage', 'N/A')
                attention_points.append(f"Partner Sales Stage behind AWS:")
                attention_points.append(f"Your stage: {partner_stage}")
                attention_points.append(f"AWS stage: {opp_stage}")
                attention_points.append(f"Action: It is necessary to adjust the current opportunity stage to comply with the status recorded in AWS. If there is a discrepancy, please provide a detailed description of the current stage and planned next steps, thus allowing accurate status update in AWS")
        
        return '\n'.join(attention_points)
        
    def generate_all_emails(self):
        """Gera todos os emails"""
        contacts = self.find_all_issues_by_contact()
        
        if not contacts:
            return "✅ Nenhuma oportunidade precisa de atenção"
            
        # Data atual formatada em português
        months_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        now = datetime.now()
        current_date = f"{months_pt[now.month]} de {now.year}"
        
        all_emails = f"""
EMAILS DE PIPELINE HYGIENE - {current_date.upper()}
Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
Total de contatos: {len(contacts)}

{'='*100}

"""
        
        for i, (email, contact_info) in enumerate(contacts.items(), 1):
            all_emails += f"""
EMAIL {i}:
{self.generate_email(contact_info)}

{'-'*100}

"""
        
        return all_emails
        
    def generate_all_emails_english(self):
        """Generates all emails in English"""
        contacts = self.find_all_issues_by_contact()
        
        if not contacts:
            return "✅ No opportunities need attention"
            
        # Current date formatted in English
        months_en = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        now = datetime.now()
        current_date = f"{months_en[now.month]} {now.year}"
        
        all_emails = f"""
PIPELINE HYGIENE EMAILS - {current_date.upper()}
Generated on: {datetime.now().strftime('%m/%d/%Y at %H:%M')}
Total contacts: {len(contacts)}

{'='*100}

"""
        
        for i, (email, contact_info) in enumerate(contacts.items(), 1):
            all_emails += f"""
EMAIL {i}:
{self.generate_email_english(contact_info)}

{'-'*100}

"""
        
        return all_emails
        
    def generate_summary_report(self):
        """Gera relatório resumo"""
        contacts = self.find_all_issues_by_contact()
        
        total_opportunities = sum(len(contact['opportunities']) for contact in contacts.values())
        
        # Conta regras por tipo
        rule_counts = {}
        for contact in contacts.values():
            for opp in contact['opportunities']:
                for rule in opp['violated_rules']:
                    rule_counts[rule] = rule_counts.get(rule, 0) + 1
        
        # Data atual formatada em português
        months_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        now = datetime.now()
        current_date = f"{months_pt[now.month]} de {now.year}"
        
        report = f"""
RELATÓRIO RESUMO - PIPELINE HYGIENE {current_date.upper()}
Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

{'='*100}

📊 RESUMO GERAL:
   • Total de contatos: {len(contacts)}
   • Total de oportunidades com issues: {total_opportunities}

📋 BREAKDOWN POR REGRA:
"""
        
        for rule, count in rule_counts.items():
            report += f"   • {rule}: {count} oportunidades\n"
        
        report += f"""
{'='*100}
"""
        
        return report
        
    def save_emails_to_file(self, filename: str = "pipeline_hygiene_emails.txt"):
        """Salva os emails em arquivo na pasta results com data"""
        # Usa diretório com data atual
        results_dir = get_dated_results_dir()
        
        # Caminho completo para o arquivo
        filepath = os.path.join(results_dir, filename)
        
        emails = self.generate_all_emails()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(emails)
                
        print(f"✅ Emails salvos em {filepath}")
        
    def save_emails_english_to_file(self, filename: str = "pipeline_hygiene_emails_english.txt"):
        """Saves emails in English to file in results folder"""
        import os
        
        # Usa diretório com data atual
        results_dir = get_dated_results_dir()
        
        # Full path to file
        filepath = os.path.join(results_dir, filename)
        
        emails = self.generate_all_emails_english()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(emails)
                
        print(f"✅ English emails saved to {filepath}")
        
    def save_report_to_file(self, filename: str = "pipeline_hygiene_report.txt"):
        """Salva o relatório em arquivo na pasta results"""
        import os
        
        # Usa diretório com data atual
        results_dir = get_dated_results_dir()
        
        # Caminho completo para o arquivo
        filepath = os.path.join(results_dir, filename)
        
        report = self.generate_summary_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
                
        print(f"✅ Relatório salvo em {filepath}")

if __name__ == "__main__":
    import sys
    
    # Verifica se foi passado arquivo como parâmetro
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        data_file = "report1755695670497.xls"
    
    checker = PipelineHygieneChecker(data_file)
    
    # Gera e salva emails em português
    checker.save_emails_to_file()
    
    # Gera e salva emails em inglês
    checker.save_emails_english_to_file()
    
    # Gera e salva relatório
    checker.save_report_to_file()
    
    # Gera interface HTML (se o gerador estiver disponível)
    try:
        import subprocess
        import sys
        result = subprocess.run([
            sys.executable, "html_email_generator.py", f"results/{datetime.now().strftime('%Y-%m-%d')}/pipeline_hygiene_emails.txt"
        ], capture_output=True, text=True, cwd=".")
        if result.returncode == 0:
            date_str = datetime.now().strftime('%Y-%m-%d')
            print(f"✅ Interface HTML gerada: results/{date_str}/pipeline_hygiene_emails.html")
    except:
        pass  # Ignora se não conseguir gerar HTML
    
    # Estatísticas
    contacts = checker.find_all_issues_by_contact()
    total_opportunities = sum(len(contact['opportunities']) for contact in contacts.values())
    
    print(f"\n📋 RESUMO:")
    print(f"Total de contatos: {len(contacts)}")
    print(f"Total de oportunidades com issues: {total_opportunities}")
    date_str = datetime.now().strftime('%Y-%m-%d')
    print(f"Emails em português salvos em: results/{date_str}/pipeline_hygiene_emails.txt")
    print(f"Emails em inglês salvos em: results/{date_str}/pipeline_hygiene_emails_english.txt")
    print(f"Relatório salvo em: results/{date_str}/pipeline_hygiene_report.txt")