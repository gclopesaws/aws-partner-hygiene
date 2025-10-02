#!/usr/bin/env python3
"""
Follow-up Generator - Gera emails de follow-up por parceiro
Analisa oportunidades ativas e cria emails consolidados solicitando atualizações
"""

import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple

# Importa função utilitária para diretório de resultados
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(os.path.dirname(script_dir), 'utils')
sys.path.append(utils_dir)
from results_dir import get_dated_results_dir

class FollowUpGenerator:
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.df = None
        self.today = datetime.now().date()
        self.load_data()
        
    def load_data(self):
        """Carrega dados do arquivo Excel"""
        try:
            # Carrega arquivo principal
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
            
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            sys.exit(1)
    
    def filter_active_opportunities(self) -> pd.DataFrame:
        """Filtra oportunidades ativas para follow-up"""
        # Filtra oportunidades que não estão finalizadas
        active_df = self.df[
            (~self.df['Opportunity: Stage'].isin(['Launched', 'Closed Lost'])) &
            (~self.df['APN Partner Reported Stage'].isin(['Launched', 'Closed Lost'])) &
            (self.df['APN Opportunity Owner Email'].notna()) &
            (self.df['APN Opportunity Owner Email'] != '') &
            (self.df['APN Opportunity Owner Email'] != 'nan')
        ].copy()
        
        print(f"Oportunidades ativas para follow-up: {len(active_df)} de {len(self.df)} total")
        return active_df
    
    def parse_close_date(self, date_value):
        """Converte Close Date para datetime de forma segura"""
        if pd.isna(date_value) or date_value == '' or date_value == 'nan':
            return None
        
        try:
            if isinstance(date_value, str):
                # Tenta formato americano mm/dd/yyyy
                try:
                    return datetime.strptime(date_value, '%m/%d/%Y').date()
                except ValueError:
                    # Tenta outros formatos
                    try:
                        return datetime.strptime(date_value, '%Y-%m-%d').date()
                    except ValueError:
                        return None
            elif hasattr(date_value, 'date'):
                # Se já é um objeto datetime/date
                return date_value.date() if hasattr(date_value, 'date') else date_value
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    def calculate_days_remaining(self, close_date):
        """Calcula dias restantes até o close date"""
        if close_date is None:
            return float('inf')  # Sem data = menor prioridade
        
        return (close_date - self.today).days
    
    def get_urgency_indicator(self, days_remaining):
        """Retorna indicador de urgência baseado nos dias restantes"""
        if days_remaining == float('inf'):
            return "⚪ SEM DATA"
        elif days_remaining < 0:
            return f"🔴 VENCIDO ({abs(days_remaining)} dias)"
        elif days_remaining <= 7:
            return f"🔴 URGENTE ({days_remaining} dias)"
        elif days_remaining <= 30:
            return f"🟡 PRÓXIMO ({days_remaining} dias)"
        elif days_remaining <= 90:
            return f"🟢 NORMAL ({days_remaining} dias)"
        else:
            return f"⚪ FUTURO ({days_remaining} dias)"
    
    def format_currency(self, value):
        """Formata valores monetários"""
        if pd.isna(value) or value == '' or value == 'nan':
            return 'Não informado'
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    def format_date(self, date_value):
        """Formata datas para exibição"""
        if pd.isna(date_value) or date_value == '' or date_value == 'nan':
            return 'Não informado'
        try:
            if isinstance(date_value, str):
                return date_value
            return date_value.strftime('%d/%m/%Y')
        except:
            return str(date_value)
    
    def create_opportunity_link(self, opportunity_name: str, apn_opportunity_id: str) -> str:
        """Cria link para a oportunidade no Partner Central"""
        if pd.isna(apn_opportunity_id) or apn_opportunity_id == '' or apn_opportunity_id == 'nan':
            return opportunity_name
        
        url = f"https://partnercentral.awspartner.com/partnercentral2/s/editopportunity?id={apn_opportunity_id}"
        return f"{opportunity_name}\nLink: {url}"
    
    def group_opportunities_by_partner(self, active_df: pd.DataFrame) -> Dict[str, Dict]:
        """Agrupa oportunidades por parceiro (empresa) e por owner dentro do parceiro"""
        partners = defaultdict(lambda: {'emails': set(), 'partner_name': '', 'owners': defaultdict(lambda: {'email': '', 'opportunities': []})})
        
        for _, row in active_df.iterrows():
            partner_email = row['APN Opportunity Owner Email']
            partner_name = row.get('Partner Account', 'Parceiro')
            owner_name = row.get('Opportunity Owner Name', 'Responsável não informado')
            
            # Parse da data de fechamento
            close_date = self.parse_close_date(row.get('Opportunity: Close Date'))
            days_remaining = self.calculate_days_remaining(close_date)
            
            # Dados da oportunidade
            opportunity_data = {
                'opportunity_id': row.get('Opportunity: 18 Character Oppty ID', 'N/A'),
                'apn_opportunity_id': row.get('APN Opportunity ID', 'N/A'),
                'opportunity_name': row.get('Opportunity: Opportunity Name', 'N/A'),
                'account_name': row.get('Opportunity: Account Name', 'N/A'),
                'close_date': close_date,
                'close_date_formatted': self.format_date(row.get('Opportunity: Close Date')),
                'days_remaining': days_remaining,
                'urgency': self.get_urgency_indicator(days_remaining),
                'sales_stage': row.get('APN Partner Reported Stage', 'N/A'),
                'aws_stage': row.get('Opportunity: Stage', 'N/A'),
                'total_amount': self.format_currency(row.get('Total Opportunity Amount')),
                'last_modified': self.format_date(row.get('APN Partner Last Modified Date')),
                'next_steps': str(row.get('Next Step', 'Não informado')) if pd.notna(row.get('Next Step')) else 'Não informado',
                'partner_name': partner_name,
                'partner_email': partner_email,
                'owner_name': owner_name
            }
            
            # Agrupa por nome do parceiro (empresa) e depois por owner
            partners[partner_name]['emails'].add(partner_email)
            partners[partner_name]['partner_name'] = partner_name
            partners[partner_name]['owners'][owner_name]['email'] = partner_email
            partners[partner_name]['owners'][owner_name]['opportunities'].append(opportunity_data)
        
        # Ordena oportunidades por owner (Close Date mais próximo primeiro)
        for partner_name in partners:
            for owner_name in partners[partner_name]['owners']:
                partners[partner_name]['owners'][owner_name]['opportunities'].sort(
                    key=lambda x: (x['days_remaining'], -float(x['total_amount'].replace('$', '').replace(',', '')) if x['total_amount'] != 'Não informado' else 0)
                )
            # Converte set de emails para lista ordenada
            partners[partner_name]['emails'] = sorted(list(partners[partner_name]['emails']))
        
        return dict(partners)
    
    def generate_followup_email(self, partner_data: Dict) -> str:
        """Gera email de follow-up para um parceiro específico, organizado por responsável"""
        owners_data = partner_data['owners']
        partner_emails = partner_data['emails']
        partner_name = partner_data['partner_name']
        
        if not owners_data:
            return ""
        
        # Calcula total de oportunidades
        total_opps = sum(len(owner_data['opportunities']) for owner_data in owners_data.values())
        
        # Calcula estatísticas do pipeline
        total_value = 0
        urgent_count = 0
        next_30_days = 0
        
        for owner_data in owners_data.values():
            for opp in owner_data['opportunities']:
                # Valor total
                if opp['total_amount'] != 'Não informado':
                    try:
                        value = float(opp['total_amount'].replace('$', '').replace(',', ''))
                        total_value += value
                    except:
                        pass
                
                # Contadores de urgência
                if opp['days_remaining'] <= 7:
                    urgent_count += 1
                elif opp['days_remaining'] <= 30:
                    next_30_days += 1
        
        # Data atual formatada
        current_date = datetime.now().strftime('%B de %Y')
        
        # Consolida emails para o campo "Para"
        emails_str = ', '.join(partner_emails)
        
        # Corpo do email (sem cabeçalho Para/Assunto)
        email_body = f"""Olá {partner_name},

Gostaríamos de fazer um follow-up das oportunidades em andamento em nosso pipeline conjunto.

Abaixo estão listadas {total_opps} oportunidade{'s' if total_opps > 1 else ''} ativa{'s' if total_opps > 1 else ''}, organizadas por responsável:

"""
        
        # Ordena owners alfabeticamente
        sorted_owners = sorted(owners_data.items(), key=lambda x: x[0])
        
        # Contador global de oportunidades
        global_opp_counter = 1
        
        # Lista oportunidades por responsável
        for owner_name, owner_data in sorted_owners:
            owner_email = owner_data['email']
            opportunities = owner_data['opportunities']
            
            if not opportunities:
                continue
            
            # Cabeçalho do AWS Account Manager
            email_body += f"""{'='*80}
AWS Account Manager: {owner_name}
{'='*80}
"""
            
            # Lista oportunidades do responsável
            for opp in opportunities:
                # Cria o link da oportunidade
                link_url = f"https://partnercentral.awspartner.com/partnercentral2/s/editopportunity?id={opp['apn_opportunity_id']}" if opp['apn_opportunity_id'] != 'N/A' else ""
                
                # Formata o status de urgência para incluir na linha da oportunidade
                urgency_text = ""
                if opp['days_remaining'] == float('inf'):
                    urgency_text = " - Sem data de fechamento"
                elif opp['days_remaining'] < 0:
                    urgency_text = f" - Close date vencido ({abs(opp['days_remaining'])} dias)"
                elif opp['days_remaining'] <= 7:
                    urgency_text = f" - Close date urgente ({opp['days_remaining']} dias)"
                elif opp['days_remaining'] <= 30:
                    urgency_text = f" - Close date próximo ({opp['days_remaining']} dias)"
                
                email_body += f"""Cliente: {opp['account_name']}
APN Opportunity Owner: {opp['partner_email']}
Oportunidade {global_opp_counter} - {opp['opportunity_name']}{urgency_text}
Link: {link_url}
Sales Stage (Partner): {opp['sales_stage']}
Sales Stage (AWS): {opp['aws_stage']}
Valor: {opp['total_amount']}
Última Atualização: {opp['last_modified']}

Poderia validar as informações acima e nos informar qual next step?

{'-'*80}
"""
                global_opp_counter += 1
            
            email_body += "\n"
        
        # Rodapé simplificado
        email_body += f"""
Obrigado pela parceria!

Equipe AWS Partner
Portal: Partner Central - https://partnercentral.awspartner.com
"""
        
        return email_body
    
    def generate_all_followup_emails(self) -> Dict[str, str]:
        """Gera todos os emails de follow-up por parceiro"""
        print("Analisando oportunidades para follow-up...")
        
        # Filtra oportunidades ativas
        active_df = self.filter_active_opportunities()
        
        if active_df.empty:
            print("Nenhuma oportunidade ativa encontrada para follow-up")
            return {}
        
        # Agrupa por parceiro (empresa)
        partners_data = self.group_opportunities_by_partner(active_df)
        
        if not partners_data:
            print("Nenhum parceiro com oportunidades válidas encontrado")
            return {}
        
        print(f"Gerando emails para {len(partners_data)} parceiros...")
        
        # Gera emails
        emails = {}
        total_opportunities = 0
        
        for partner_name, partner_data in partners_data.items():
            email_content = self.generate_followup_email(partner_data)
            if email_content:
                # Armazena dados do email para uso posterior
                emails[partner_name] = {
                    'content': email_content,
                    'emails': partner_data['emails'],
                    'partner_name': partner_name
                }
                # Conta oportunidades de todos os owners
                for owner_data in partner_data['owners'].values():
                    total_opportunities += len(owner_data['opportunities'])
        
        print(f"Emails gerados: {len(emails)}")
        print(f"Total de oportunidades: {total_opportunities}")
        
        return emails
    
    def save_emails(self, emails: Dict[str, str], output_file: str = None):
        """Salva emails em arquivo"""
        if not emails:
            print("Nenhum email para salvar")
            return
        
        if output_file is None:
            output_file = os.path.join(get_dated_results_dir(), "followup_emails.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"EMAILS DE FOLLOW-UP - PIPELINE POR PARCEIRO\n")
            f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n")
            f.write(f"Total de parceiros: {len(emails)}\n")
            f.write("="*80 + "\n\n")
            
            for i, (partner_name, email_data) in enumerate(emails.items(), 1):
                # Adiciona cabeçalho Para/Assunto apenas no arquivo
                emails_str = ', '.join(email_data['emails'])
                current_date = datetime.now().strftime('%B de %Y')
                
                f.write(f"EMAIL {i} - {partner_name}\n")
                f.write("="*60 + "\n")
                f.write(f"Para: {emails_str}\n")
                f.write(f"Assunto: AWS <> {partner_name} - Follow-up Pipeline - {current_date}\n\n")
                f.write(email_data['content'])
                f.write("\n" + "="*60 + "\n\n")
        
        print(f"Emails salvos em: {output_file}")
    
    def generate_summary_report(self, emails: Dict[str, str]) -> str:
        """Gera relatório resumo do follow-up"""
        if not emails:
            return "Nenhum email gerado"
        
        summary_file = os.path.join(get_dated_results_dir(), "followup_summary.txt")
        
        # Coleta estatísticas
        total_partners = len(emails)
        total_opportunities = 0
        urgent_opportunities = 0
        high_value_opportunities = 0
        
        # Reprocessa dados para estatísticas
        active_df = self.filter_active_opportunities()
        partners_data = self.group_opportunities_by_partner(active_df)
        
        for partner_data in partners_data.values():
            for owner_data in partner_data['owners'].values():
                opportunities = owner_data['opportunities']
                total_opportunities += len(opportunities)
                for opp in opportunities:
                    if opp['days_remaining'] <= 7:
                        urgent_opportunities += 1
                    if opp['total_amount'] != 'Não informado':
                        try:
                            value = float(opp['total_amount'].replace('$', '').replace(',', ''))
                            if value >= 50000:
                                high_value_opportunities += 1
                        except:
                            pass
        
        summary_content = f"""RELATÓRIO RESUMO - FOLLOW-UP PIPELINE
Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

ESTATÍSTICAS GERAIS:
• Total de parceiros: {total_partners}
• Total de oportunidades: {total_opportunities}
• Oportunidades urgentes (≤7 dias): {urgent_opportunities}
• Oportunidades de alto valor (≥$50k): {high_value_opportunities}

PRÓXIMAS AÇÕES:
1. Enviar emails para {total_partners} parceiros
2. Acompanhar respostas e atualizações
3. Priorizar {urgent_opportunities} oportunidades urgentes
4. Dar atenção especial às {high_value_opportunities} oportunidades de alto valor

ARQUIVOS GERADOS:
• followup_emails.txt - Emails completos para envio
• followup_summary.txt - Este resumo executivo
"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"Resumo salvo em: {summary_file}")
        return summary_content
    
    def generate_html_interface(self, emails: Dict[str, str]):
        """Gera interface HTML para os emails de follow-up"""
        if not emails:
            print("Nenhum email para gerar interface HTML")
            return
        
        try:
            # Importa o gerador HTML
            import subprocess
            import sys
            
            # Caminho para o arquivo de emails
            emails_file = os.path.join(get_dated_results_dir(), "followup_emails.txt")
            
            # Executa o gerador HTML
            script_path = "followup_html_generator.py"
            result = subprocess.run([
                sys.executable, script_path, emails_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Interface HTML gerada com sucesso!")
                print(result.stdout)
            else:
                print("❌ Erro ao gerar interface HTML:")
                print(result.stderr)
        except Exception as e:
            print(f"❌ Erro ao executar gerador HTML: {e}")

def main():
    """Função principal"""
    print("="*60)
    print("FOLLOW-UP GENERATOR")
    print("="*60)
    print()
    
    # Verifica argumentos
    if len(sys.argv) < 2:
        print("❌ ERRO: Arquivo de dados não especificado")
        print()
        print("Uso:")
        print(f"   python3 {sys.argv[0]} <arquivo_dados.xls>")
        print()
        print("Exemplo:")
        print(f"   python3 {sys.argv[0]} partner.xls")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    
    # Verifica se o arquivo existe
    if not os.path.exists(excel_file):
        print(f"❌ ERRO: Arquivo '{excel_file}' não encontrado")
        sys.exit(1)
    
    print(f"📊 Arquivo de dados: {excel_file}")
    print(f"📊 Tamanho: {os.path.getsize(excel_file):,} bytes")
    print()
    
    # Inicializa gerador
    generator = FollowUpGenerator(excel_file)
    
    # Gera emails
    emails = generator.generate_all_followup_emails()
    
    if emails:
        # Salva emails
        generator.save_emails(emails)
        
        # Gera resumo
        generator.generate_summary_report(emails)
        
        # Gera interface HTML
        generator.generate_html_interface(emails)
        
        print("="*60)
        print("FOLLOW-UP EMAILS GERADOS!")
        print("="*60)
    else:
        print("❌ Nenhum email foi gerado")

if __name__ == "__main__":
    main()