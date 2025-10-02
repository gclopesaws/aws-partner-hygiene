#!/usr/bin/env python3
"""
HTML Email Generator - Gera interface HTML com botões para Outlook
Cada email tem um botão que abre o Outlook com dados preenchidos
"""

import os
import re
import sys
import urllib.parse
from datetime import datetime
from typing import Dict, List

# Importa função utilitária para diretório de resultados
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from results_dir import get_dated_results_dir

class HTMLEmailGenerator:
    def __init__(self):
        self.emails_data = []
        self.emails_english_data = []
        
    def parse_emails_file(self, file_path: str) -> List[Dict]:
        """Extrai emails individuais do arquivo gerado"""
        emails = []
        
        # Tenta diferentes encodings para ler o arquivo
        content = None
        encodings_to_try = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Arquivo lido com sucesso usando encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # Última tentativa: lê como binário e tenta decodificar
            try:
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
                content = raw_content.decode('utf-8', errors='ignore')
                print("Arquivo lido com encoding UTF-8 ignorando erros")
            except Exception as e:
                raise Exception(f"Não foi possível ler o arquivo {file_path}: {e}")
        
        # Primeiro, normaliza o conteúdo para garantir que todos os emails tenham quebra de linha antes
        content = re.sub(r'^EMAIL', r'\nEMAIL', content)  # Adiciona quebra no início se necessário
        content = re.sub(r'([^\n])EMAIL', r'\1\nEMAIL', content)  # Garante quebra antes de EMAIL
        
        # Divide por "EMAIL X:" mas mantém o delimitador
        email_sections = re.split(r'(\nEMAIL \d+:\n)', content)
        
        # Reconstrói as seções completas
        complete_sections = []
        for i in range(1, len(email_sections), 2):  # Pega delimitador + conteúdo
            if i + 1 < len(email_sections):
                complete_sections.append(email_sections[i] + email_sections[i + 1])
        
        # Se não encontrou seções com o padrão acima, tenta outros padrões
        if not complete_sections:
            # Tenta padrão sem quebra de linha antes
            email_sections = re.split(r'(EMAIL \d+:\n)', content)
            for i in range(1, len(email_sections), 2):
                if i + 1 < len(email_sections):
                    complete_sections.append(email_sections[i] + email_sections[i + 1])
        
        # Se ainda não encontrou, tenta padrão mais simples
        if not complete_sections:
            email_sections = re.split(r'(EMAIL \d+:)', content)
            for i in range(1, len(email_sections), 2):
                if i + 1 < len(email_sections):
                    complete_sections.append(email_sections[i] + email_sections[i + 1])
        

        
        for i, section in enumerate(complete_sections, 1):
            if not section.strip():
                continue
                
            # Extrai informações do email
            lines = section.split('\n')
            
            email_data = {
                'id': i,
                'to_email': '',
                'subject': '',
                'contact_name': '',
                'body': '',
                'opportunities_count': 0
            }
            
            # Processa linha por linha
            body_lines = []
            capturing_body = False
            
            for line in lines:
                if line.startswith('Para: '):
                    email_data['to_email'] = line.replace('Para: ', '').strip()
                elif line.startswith('Assunto: '):
                    email_data['subject'] = line.replace('Assunto: ', '').strip()
                elif line.startswith('Olá '):
                    # Extrai nome do contato
                    contact_match = re.search(r'Olá (.+?),', line)
                    if contact_match:
                        email_data['contact_name'] = contact_match.group(1)
                    capturing_body = True
                    body_lines.append(line)
                elif capturing_body:
                    # Captura tudo até encontrar o próximo EMAIL ou final do arquivo
                    if line.startswith('EMAIL ') and line.endswith(':'):
                        break
                    elif line.startswith('---') and 'Email gerado automaticamente' in line:
                        break
                    else:
                        body_lines.append(line)
            
            email_data['body'] = '\n'.join(body_lines).strip()
            
            # Conta oportunidades (novo formato)
            email_data['opportunities_count'] = email_data['body'].count('Oportunidade ')
            
            # Valida se tem email válido
            if email_data['to_email'] and '@' in email_data['to_email'] and email_data['to_email'] != 'nan':
                emails.append(email_data)
        
        return emails
    
    def parse_emails_english_file(self, file_path: str) -> List[Dict]:
        """Extracts individual emails from English file"""
        emails = []
        
        # Tenta diferentes encodings para ler o arquivo
        content = None
        encodings_to_try = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Arquivo inglês lido com sucesso usando encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # Última tentativa: lê como binário e tenta decodificar
            try:
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
                content = raw_content.decode('utf-8', errors='ignore')
                print("Arquivo inglês lido com encoding UTF-8 ignorando erros")
            except Exception as e:
                raise Exception(f"Não foi possível ler o arquivo inglês {file_path}: {e}")
        
        # Split by "EMAIL X:" but keep delimiter
        email_sections = re.split(r'(\n\nEMAIL \d+:\n)', content)
        
        # Rebuild complete sections
        complete_sections = []
        for i in range(1, len(email_sections), 2):  # Get delimiter + content
            if i + 1 < len(email_sections):
                complete_sections.append(email_sections[i] + email_sections[i + 1])
        
        for i, section in enumerate(complete_sections, 1):
            if not section.strip():
                continue
                
            # Extract email information
            lines = section.split('\n')
            
            email_data = {
                'id': i,
                'to_email': '',
                'subject': '',
                'contact_name': '',
                'body': '',
                'opportunities_count': 0
            }
            
            # Process line by line
            body_lines = []
            capturing_body = False
            
            for line in lines:
                if line.startswith('To: '):
                    email_data['to_email'] = line.replace('To: ', '').strip()
                elif line.startswith('Subject: '):
                    email_data['subject'] = line.replace('Subject: ', '').strip()
                elif line.startswith('Hello '):
                    # Extract contact name
                    contact_match = re.search(r'Hello (.+?),', line)
                    if contact_match:
                        email_data['contact_name'] = contact_match.group(1)
                    capturing_body = True
                    body_lines.append(line)
                elif capturing_body:
                    # Capture everything until next EMAIL or end of file
                    if line.startswith('EMAIL ') and line.endswith(':'):
                        break
                    elif line.startswith('---') and 'Report automatically generated' in line:
                        break
                    else:
                        body_lines.append(line)
            
            email_data['body'] = '\n'.join(body_lines).strip()
            
            # Count opportunities (new format)
            email_data['opportunities_count'] = email_data['body'].count('Opportunity ')
            
            # Validate if has valid email
            if email_data['to_email'] and '@' in email_data['to_email'] and email_data['to_email'] != 'nan':
                emails.append(email_data)
        
        return emails
    
    def create_outlook_url(self, email_data: Dict) -> str:
        """Cria URL para abrir Microsoft Outlook especificamente"""
        # Codifica os dados para URL
        to_email = urllib.parse.quote(email_data['to_email'])
        subject = urllib.parse.quote(email_data['subject'])
        body = urllib.parse.quote(email_data['body'])
        
        # URL específica do Microsoft Outlook para macOS
        outlook_url = f"ms-outlook://compose?to={to_email}&subject={subject}&body={body}"
        
        return outlook_url
    
    def create_mailto_url(self, email_data: Dict) -> str:
        """Cria URL mailto como fallback"""
        to_email = urllib.parse.quote(email_data['to_email'])
        subject = urllib.parse.quote(email_data['subject'])
        body = urllib.parse.quote(email_data['body'])
        
        return f"mailto:{to_email}?subject={subject}&body={body}"
    
    def create_html_email_file(self, email_data: Dict, file_id: str = None) -> str:
        """Cria arquivo .eml com HTML formatado que pode ser aberto no Outlook"""
        import tempfile
        import os
        from datetime import datetime
        
        # Usa a versão HTML se disponível, senão usa a versão texto
        html_body = email_data.get('body_html', email_data['body'])
        
        # Formata HTML para email
        html_body_formatted = self.format_html_for_email(html_body)
        
        # Codifica o assunto corretamente para evitar caracteres estranhos
        import base64
        subject_encoded = base64.b64encode(email_data['subject'].encode('utf-8')).decode('ascii')
        
        # Cria conteúdo do arquivo .eml COMO RASCUNHO
        eml_content = f"""X-Unsent: 1
To: {email_data['to_email']}
Subject: =?UTF-8?B?{subject_encoded}?=
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit

{email_data['body']}

--boundary123
Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: 8bit

<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #003366; font-size: 10pt; }}
        .opportunity-title {{ color: #FF8C00; font-weight: bold; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .field-label {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .field-value {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .link-field {{ color: #003366; text-decoration: underline; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .link-field:hover {{ color: #002244; text-decoration: underline; }}
        .actions-header {{ color: #003366; font-weight: bold; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .action-category {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .action-detail {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .action-required {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .email-intro {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .opportunity-section-title {{ color: #003366; font-weight: bold; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
    </style>
</head>
<body>
{html_body_formatted}
</body>
</html>

--boundary123--
"""
        
        # Cria arquivo temporário .eml
        if not file_id:
            file_id = email_data['to_email'].replace('@', '_').replace('.', '_').replace(';', '_')
        
        # Cria diretório temp e subpasta consolidated se não existir
        temp_dir = os.path.join(get_dated_results_dir(), 'temp_emails')
        consolidated_dir = os.path.join(temp_dir, 'consolidated')
        os.makedirs(consolidated_dir, exist_ok=True)
        
        eml_filename = f"email_{file_id}_{datetime.now().strftime('%H%M%S')}.eml"
        eml_path = os.path.join(consolidated_dir, eml_filename)
        
        # Salva arquivo .eml
        with open(eml_path, 'w', encoding='utf-8') as f:
            f.write(eml_content)
        
        # Retorna caminho relativo para uso no HTML (inclui subpasta)
        return os.path.join('consolidated', eml_filename)
    
    def format_html_for_email(self, html_content: str) -> str:
        """Formata HTML para ser compatível com clientes de email"""
        # Substitui classes CSS por estilos inline - Amazon Ember 10 e azul marinho escuro
        css_replacements = {
            '<span class="opportunity-title">': '<span style="color: #FF8C00; font-weight: bold; font-family: \'Amazon Ember\', \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt;">',
            '<span class="field-label">': '<span style="color: #003366; font-weight: normal; font-family: \'Amazon Ember\', \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt;">',
            '<span class="field-value">': '<span style="color: #003366; font-weight: normal; font-family: \'Amazon Ember\', \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt;">',
            '<a href="([^"]*)" class="link-field">': r'<a href="\1" style="color: #003366; text-decoration: underline; font-family: \'Amazon Ember\', \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt;">',
            '<span class="actions-header">': '<span style="color: #003366; font-weight: bold; font-family: \'Amazon Ember\', \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt;">',
            '<span class="action-category">': '<span style="color: #003366; font-weight: normal; font-family: \'Amazon Ember\', \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt;">',
            '<span class="action-detail">': '<span style="color: #003366; font-weight: normal; font-family: \'Amazon Ember\', \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt;">',
            '<span class="action-required">': '<span style="color: #003366; font-weight: normal; font-family: \'Amazon Ember\', \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt;">'
        }
        
        import re
        formatted_content = html_content
        for pattern, replacement in css_replacements.items():
            if 'href=' in pattern:  # Para links com regex
                formatted_content = re.sub(pattern, replacement, formatted_content)
            else:
                formatted_content = formatted_content.replace(pattern, replacement)
        
        # Converte quebras de linha para <br>
        formatted_content = formatted_content.replace('\n', '<br>')
        
        return formatted_content
    
    def get_company_from_email(self, email: str) -> str:
        """Extrai nome da empresa do email"""
        if '@' not in email:
            return 'Unknown'
        
        domain = email.split('@')[1]
        company = domain.split('.')[0]
        
        # Mapeia alguns domínios conhecidos para nomes mais amigáveis
        company_mapping = {
            'gmail': 'Gmail',
            'outlook': 'Microsoft',
            'hotmail': 'Microsoft',
            'yahoo': 'Yahoo',
            'vtex': 'VTEX',
            'aws': 'Amazon',
            'microsoft': 'Microsoft',
            'salesforce': 'Salesforce',
            'oracle': 'Oracle'
        }
        
        return company_mapping.get(company.lower(), company.title())
    
    def group_emails_by_company(self, emails: List[Dict]) -> Dict[str, List[Dict]]:
        """Agrupa emails por empresa baseado no domínio do email"""
        companies = {}
        for email in emails:
            company = self.get_company_from_email(email['to_email'])
            if company not in companies:
                companies[company] = []
            companies[company].append(email)
        return companies
    

    

    


    def _extract_opportunity_data(self, opportunity_text: str) -> Dict:
        """Extrai dados estruturados de uma oportunidade"""
        lines = opportunity_text.split('\n')
        opp_data = {}
        
        for line in lines:
            line = line.strip()
            # Títulos (PT e EN)
            if (line.startswith('Oportunidade ') or line.startswith('Opportunity ')) and ' - ' in line:
                opp_data['title'] = line
            # Cliente (PT e EN)
            elif line.startswith('Cliente: ') or line.startswith('Customer: '):
                client_text = line.replace('Cliente: ', '').replace('Customer: ', '').split(' | ')[0]
                opp_data['client'] = client_text
            # Revenue (PT e EN)
            elif line.startswith('Revenue Estimado: ') or line.startswith('Estimated Revenue: '):
                revenue_text = line.replace('Revenue Estimado: ', '').replace('Estimated Revenue: ', '').split(' | ')[0]
                opp_data['revenue'] = revenue_text
            # ID
            elif line.startswith('ID: '):
                opp_data['id'] = line.replace('ID: ', '')
            # Status Parceiro (PT e EN)
            elif line.startswith('Seu estágio: ') or line.startswith('Your stage: '):
                stage_text = line.replace('Seu estágio: ', '').replace('Your stage: ', '')
                opp_data['partner_stage'] = stage_text
            # Status AWS (PT e EN)
            elif line.startswith('Estágio AWS: ') or line.startswith('AWS stage: '):
                aws_stage_text = line.replace('Estágio AWS: ', '').replace('AWS stage: ', '')
                opp_data['aws_stage'] = aws_stage_text
            # Data Launch (PT e EN)
            elif line.startswith('Data prevista: ') or line.startswith('Expected date: '):
                date_text = line.replace('Data prevista: ', '').replace('Expected date: ', '')
                opp_data['launch_date'] = date_text
        
        # Se não encontrou alguns campos, tenta extrair do formato compacto
        if 'client' not in opp_data or 'revenue' not in opp_data:
            for line in lines:
                # Formato PT
                if 'Cliente: ' in line and 'Revenue Estimado: ' in line:
                    parts = line.split(' | ')
                    for part in parts:
                        if part.startswith('Cliente: '):
                            opp_data['client'] = part.replace('Cliente: ', '')
                        elif part.startswith('Revenue Estimado: '):
                            opp_data['revenue'] = part.replace('Revenue Estimado: ', '')
                # Formato EN
                elif 'Customer: ' in line and 'Estimated Revenue: ' in line:
                    parts = line.split(' | ')
                    for part in parts:
                        if part.startswith('Customer: '):
                            opp_data['client'] = part.replace('Customer: ', '')
                        elif part.startswith('Estimated Revenue: '):
                            opp_data['revenue'] = part.replace('Estimated Revenue: ', '')
        
        # Tenta extrair ID do final da linha de link se não encontrou
        if not opp_data.get('id'):
            for line in lines:
                if 'ID: ' in line:
                    # Procura por padrão ID: OXXXXXXX
                    import re
                    id_match = re.search(r'ID: (O\d+)', line)
                    if id_match:
                        opp_data['id'] = id_match.group(1)
        
        # Define valores padrão se não encontrados
        opp_data.setdefault('client', '')
        opp_data.setdefault('revenue', '$0.00')
        opp_data.setdefault('id', '')
        opp_data.setdefault('partner_stage', '')
        opp_data.setdefault('aws_stage', '')
        opp_data.setdefault('launch_date', '-')
        
        return opp_data

    def create_consolidated_email(self, company_emails: List[Dict]) -> Dict:
        """Cria um email consolidado para múltiplos destinatários da mesma empresa"""
        if not company_emails:
            return None
        
        # Combina todos os destinatários
        all_recipients = [email['to_email'] for email in company_emails]
        consolidated_recipients = ';'.join(all_recipients)
        
        # Usa o primeiro email como base para assunto e estrutura
        base_email = company_emails[0]
        
        # Extrai o nome da empresa do assunto (ex: "AWS <> A3Data" -> "A3Data")
        subject = base_email['subject']
        
        # Combina todas as oportunidades de todos os emails
        all_opportunities = []
        opportunities_data = []  # Nova estrutura para dados estruturados
        total_opportunities = 0
        
        for email in company_emails:
            # Extrai oportunidades do corpo do email
            body_lines = email['body'].split('\n')
            current_opportunity = []
            capturing_opportunity = False
            
            for line in body_lines:
                if line.startswith('Oportunidade ') and ' - ' in line:
                    if current_opportunity and capturing_opportunity:
                        all_opportunities.append('\n'.join(current_opportunity))
                        # Extrai dados estruturados da oportunidade anterior
                        opp_data = self._extract_opportunity_data('\n'.join(current_opportunity))
                        if opp_data:
                            opportunities_data.append(opp_data)
                    current_opportunity = [line]
                    capturing_opportunity = True
                    total_opportunities += 1
                elif capturing_opportunity:
                    if line.startswith('--------------------------------------------------------------------------------'):
                        if current_opportunity:
                            all_opportunities.append('\n'.join(current_opportunity))
                            # Extrai dados estruturados da oportunidade
                            opp_data = self._extract_opportunity_data('\n'.join(current_opportunity))
                            if opp_data:
                                opportunities_data.append(opp_data)
                            current_opportunity = []
                        capturing_opportunity = False
                    elif line.strip() and not line.startswith('Para: ') and not line.startswith('Assunto: '):
                        current_opportunity.append(line)
            
            # Adiciona a última oportunidade se existir
            if current_opportunity and capturing_opportunity:
                all_opportunities.append('\n'.join(current_opportunity))
                # Extrai dados estruturados da última oportunidade
                opp_data = self._extract_opportunity_data('\n'.join(current_opportunity))
                if opp_data:
                    opportunities_data.append(opp_data)
        
        # Reconstrói o corpo do email com todas as oportunidades
        # Cria texto introdutório personalizado
        company_name = base_email['contact_name']
        
        # Texto introdutório formatado
        intro_text = f"Olá time, tudo bem?"
        intro_text2 = "Identificamos as seguintes oportunidades em nosso pipeline que necessitam de atualização."
        intro_text3 = "Solicitamos seu apoio para realizar os ajustes necessários."
        
        # Versão HTML com formatação
        intro_lines_html = [
            f'<span class="email-intro">{intro_text}</span>',
            '',
            f'<span class="email-intro">{intro_text2}</span>',
            f'<span class="email-intro">{intro_text3}</span>',
            ''
        ]
        
        # Versão texto puro
        intro_lines_text = [
            intro_text,
            '',
            intro_text2,
            intro_text3,
            ''
        ]
        
        # Monta o corpo consolidado (versão HTML para visualização)
        consolidated_body_parts_html = intro_lines_html.copy()
        # Monta o corpo consolidado (versão texto puro para email)
        consolidated_body_parts_text = intro_lines_text.copy()
        
        # Detecta idioma baseado no conteúdo do email
        language = 'EN' if 'Hello' in base_email['body'] or 'Customer:' in base_email['body'] else 'PT'
        
        # Adiciona todas as oportunidades numeradas sequencialmente
        for i, opportunity in enumerate(all_opportunities, 1):
            # Renumera a oportunidade
            opportunity_lines = opportunity.split('\n')
            if opportunity_lines:
                # Processa cada linha para criar versão HTML (com cores) e texto puro
                formatted_lines_html = []
                formatted_lines_text = []
                
                # Coleta informações da oportunidade para formatação compacta
                opp_info = {}
                actions_started = False
                action_lines = []
                
                for line in opportunity_lines:
                    if line.startswith('Oportunidade ') and ' - ' in line:
                        # Título real da oportunidade (tem formato "Oportunidade X - Título")
                        parts = line.split(' - ', 1)
                        if len(parts) > 1:
                            opp_info['title'] = f'Oportunidade {i} - {parts[1]}'
                        else:
                            opp_info['title'] = line
                    elif line.startswith('Oportunidade parada'):
                        # Categoria de ação, não título - será processado nas action_lines
                        pass
                    elif line.startswith('Link: '):
                        opp_info['link'] = line.replace('Link: ', '')
                    elif line.startswith('Contato APN: '):
                        opp_info['contact'] = line.replace('Contato APN: ', '')
                    elif line.startswith('ID: '):
                        opp_info['id'] = line.replace('ID: ', '')
                    elif line.startswith('Cliente: '):
                        opp_info['client'] = line.replace('Cliente: ', '')
                    elif line.startswith('Revenue Estimado: '):
                        opp_info['revenue'] = line.replace('Revenue Estimado: ', '')
                    elif line.startswith('Ações recomendadas:'):
                        actions_started = True
                    elif actions_started and line.strip():
                        if not line.startswith('----------------'):
                            action_lines.append(line)
                
                # Formata no layout compacto
                # Título da oportunidade
                formatted_lines_text.append(opp_info.get('title', ''))
                formatted_lines_html.append(f'<span class="opportunity-title">{opp_info.get("title", "")}</span>')
                
                # Linha com Cliente e Revenue (MOVIDO PARA CIMA)
                client_revenue_text = f"Cliente: {opp_info.get('client', '')} | Revenue Estimado: {opp_info.get('revenue', '')}"
                client_revenue_html = f'<span class="field-label">Cliente:</span> <span class="field-value">{opp_info.get("client", "")}</span> | <span class="field-label">Revenue Estimado:</span> <span class="field-value">{opp_info.get("revenue", "")}</span>'
                
                formatted_lines_text.append(client_revenue_text)
                formatted_lines_html.append(client_revenue_html)
                
                # Linha com Link, Contato APN e ID (MOVIDO PARA BAIXO)
                info_line_text = f"Link: {opp_info.get('link', '')} | Contato APN: {opp_info.get('contact', '')} | ID: {opp_info.get('id', '')}"
                info_line_html = f'<span class="field-label">Link:</span> <a href="{opp_info.get("link", "")}" class="link-field">{opp_info.get("link", "")}</a> | <span class="field-label">Contato APN:</span> <span class="field-value">{opp_info.get("contact", "")}</span> | <span class="field-label">ID:</span> <span class="field-value">{opp_info.get("id", "")}</span>'
                
                formatted_lines_text.append(info_line_text)
                formatted_lines_html.append(info_line_html)
                
                # Ações recomendadas (se existirem)
                if action_lines:
                    formatted_lines_text.append('')
                    formatted_lines_html.append('')
                    formatted_lines_text.append('Ações recomendadas:')
                    formatted_lines_html.append('<span class="actions-header">Ações recomendadas:</span>')
                    
                    # Processa ações com espaçamento entre categorias
                    previous_was_category = False
                    category_count = 0
                    
                    for action_line in action_lines:
                        if action_line.startswith('Launch date') or action_line.startswith('Partner Sales Stage') or action_line.startswith('Oportunidade parada'):
                            # Adiciona espaço apenas a partir da segunda categoria
                            if category_count > 0:
                                formatted_lines_text.append('')
                                formatted_lines_html.append('')
                            formatted_lines_text.append(action_line)
                            formatted_lines_html.append(f'<span class="action-category">{action_line}</span>')
                            previous_was_category = True
                            category_count += 1
                        elif action_line.startswith('Data prevista:') or action_line.startswith('Seu estágio:') or action_line.startswith('Estágio AWS:') or action_line.startswith('Última atualização:'):
                            formatted_lines_text.append(action_line)
                            parts = action_line.split(': ', 1)
                            if len(parts) == 2:
                                formatted_lines_html.append(f'<span class="action-detail">{parts[0]}:</span> <span class="field-value">{parts[1]}</span>')
                            else:
                                formatted_lines_html.append(f'<span class="action-detail">{action_line}</span>')
                            previous_was_category = False
                        elif action_line.startswith('Ação:') or action_line.startswith('NEXT STEPS:'):
                            formatted_lines_text.append(action_line)
                            if action_line.startswith('Ação:'):
                                value = action_line.replace('Ação: ', '')
                                formatted_lines_html.append(f'<span class="action-detail">Ação:</span> <span class="action-required">{value}</span>')
                            else:
                                formatted_lines_html.append(f'<span class="action-required">{action_line}</span>')
                            previous_was_category = False
                        else:
                            formatted_lines_text.append(action_line)
                            formatted_lines_html.append(action_line)
                            previous_was_category = False
                
                consolidated_body_parts_html.extend(formatted_lines_html)
                consolidated_body_parts_html.append('--------------------------------------------------------------------------------')
                consolidated_body_parts_text.extend(formatted_lines_text)
                consolidated_body_parts_text.append('--------------------------------------------------------------------------------')
        
        # Adiciona rodapé padrão
        footer = [
            'PRÓXIMOS PASSOS:',
            '- Atualize as oportunidades no sistema Partner Central',
            '- Confirme os dados com seus clientes',
            '- Entre em contato conosco se precisar de suporte',
            '',
            'Qualquer dúvida, responda este email ou entre em contato com nossa equipe.',
            '',
            'Obrigado pela parceria!',
            '',
            'Equipe AWS Partner',
            'Email: Responda este email para dúvidas',
            'Portal: Partner Central - https://partnercentral.awspartner.com'
        ]
        
        consolidated_body_parts_html.extend(footer)
        consolidated_body_parts_text.extend(footer)
        
        consolidated_body_html = '\n'.join(consolidated_body_parts_html)
        consolidated_body_text = '\n'.join(consolidated_body_parts_text)
        
        return {
            'id': f"CONSOLIDATED_{base_email['id']}",
            'to_email': consolidated_recipients,
            'subject': subject,
            'contact_name': base_email['contact_name'],
            'body': consolidated_body_text,  # Versão texto puro para email
            'body_html': consolidated_body_html,  # Versão HTML para visualização
            'opportunities_count': total_opportunities,
            'is_consolidated': True,
            'individual_emails': len(company_emails)
        }
    
    def parse_individual_opportunities(self, body_text: str) -> List[Dict]:
        """Extrai oportunidades do email individual"""
        opportunities = []
        lines = body_text.split('\n')
        current_opp = {}
        actions_started = False
        action_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Oportunidade ') and ' - ' in line:
                # Salva oportunidade anterior se existir
                if current_opp:
                    if action_lines:
                        current_opp['actions'] = action_lines
                    opportunities.append(current_opp)
                
                # Inicia nova oportunidade
                current_opp = {'title': line}
                actions_started = False
                action_lines = []
                
            elif line.startswith('Link: '):
                current_opp['link'] = line.replace('Link: ', '')
            elif line.startswith('Contato APN: '):
                current_opp['contact'] = line.replace('Contato APN: ', '')
            elif line.startswith('ID: '):
                current_opp['id'] = line.replace('ID: ', '')
            elif line.startswith('Cliente: '):
                current_opp['client'] = line.replace('Cliente: ', '')
            elif line.startswith('Revenue Estimado: '):
                current_opp['revenue'] = line.replace('Revenue Estimado: ', '')
            elif line.startswith('Estimated Revenue: '):
                current_opp['revenue'] = line.replace('Estimated Revenue: ', '')
            elif line.startswith('Customer: '):
                current_opp['client'] = line.replace('Customer: ', '')
            elif line.startswith('APN Contact: '):
                current_opp['contact'] = line.replace('APN Contact: ', '')
            elif line.startswith('Ações recomendadas:') or line.startswith('Recommended Actions:'):
                actions_started = True
            elif actions_started and not line.startswith('----------------'):
                # Para de capturar ações se encontrar o rodapé
                if (line.startswith('PRÓXIMOS PASSOS:') or 
                    line.startswith('NEXT STEPS:') or
                    line.startswith('Qualquer dúvida,') or
                    line.startswith('If you have any questions,') or
                    line.startswith('Obrigado pela parceria!') or
                    line.startswith('Thank you for the partnership!') or
                    line.startswith('Equipe AWS Partner') or
                    line.startswith('AWS Partner Team')):
                    break
                action_lines.append(line)
        
        # Adiciona última oportunidade
        if current_opp:
            if action_lines:
                current_opp['actions'] = action_lines
            opportunities.append(current_opp)
        
        return opportunities
    
    def format_actions_html(self, actions: List[str], language: str = 'PT') -> str:
        """Formata ações recomendadas com HTML estruturado"""
        if not actions:
            return ''
        
        html_parts = []
        html_parts.append('')  # Linha em branco
        
        actions_header = 'Ações recomendadas:' if language == 'PT' else 'Recommended Actions:'
        html_parts.append(f'<span class="actions-header">{actions_header}</span>')
        
        category_count = 0
        for action_line in actions:
            if (action_line.startswith('Launch date') or 
                action_line.startswith('Partner Sales Stage') or 
                action_line.startswith('Oportunidade parada') or
                action_line.startswith('Overdue launch date') or
                action_line.startswith('Upcoming launch date') or
                action_line.startswith('Stalled opportunity')):
                
                # Adiciona espaço entre categorias
                if category_count > 0:
                    html_parts.append('')
                html_parts.append(f'<span class="action-category">{action_line}</span>')
                category_count += 1
                
            elif (action_line.startswith('Data prevista:') or 
                  action_line.startswith('Seu estágio:') or 
                  action_line.startswith('Estágio AWS:') or 
                  action_line.startswith('Última atualização:') or
                  action_line.startswith('Expected date:') or
                  action_line.startswith('Your stage:') or
                  action_line.startswith('AWS stage:') or
                  action_line.startswith('Last update:')):
                
                parts = action_line.split(': ', 1)
                if len(parts) == 2:
                    html_parts.append(f'<span class="action-detail">{parts[0]}:</span> <span class="field-value">{parts[1]}</span>')
                else:
                    html_parts.append(f'<span class="action-detail">{action_line}</span>')
                    
            elif action_line.startswith('Ação:') or action_line.startswith('Action:'):
                value = action_line.replace('Ação: ', '').replace('Action: ', '')
                label = 'Ação:' if language == 'PT' else 'Action:'
                html_parts.append(f'<span class="action-detail">{label}</span> <span class="action-required">{value}</span>')
            else:
                html_parts.append(f'<span class="action-detail">{action_line}</span>')
        
        return '\n'.join(html_parts)
    
    def format_opportunities_compact(self, opportunities: List[Dict], language: str = 'PT') -> str:
        """Aplica layout compacto igual aos emails consolidados"""
        html_parts = []
        
        for i, opp in enumerate(opportunities, 1):
            # Título com classe CSS (renumera sequencialmente)
            title = opp.get('title', '')
            if ' - ' in title:
                title_parts = title.split(' - ', 1)
                if len(title_parts) > 1:
                    title = f'Oportunidade {i} - {title_parts[1]}'
            
            html_parts.append(f'<span class="opportunity-title">{title}</span>')
            
            # Linha Cliente | Revenue (compacta)
            client = opp.get('client', '')
            revenue = opp.get('revenue', '')
            
            if language == 'PT':
                client_revenue = f'<span class="field-label">Cliente:</span> <span class="field-value">{client}</span> | <span class="field-label">Revenue Estimado:</span> <span class="field-value">{revenue}</span>'
            else:
                client_revenue = f'<span class="field-label">Customer:</span> <span class="field-value">{client}</span> | <span class="field-label">Estimated Revenue:</span> <span class="field-value">{revenue}</span>'
            
            html_parts.append(client_revenue)
            
            # Linha Link | Contato | ID (compacta)
            link = opp.get('link', '')
            contact = opp.get('contact', '')
            opp_id = opp.get('id', '')
            
            if language == 'PT':
                info_line = f'<span class="field-label">Link:</span> <a href="{link}" class="link-field">{link}</a> | <span class="field-label">Contato APN:</span> <span class="field-value">{contact}</span> | <span class="field-label">ID:</span> <span class="field-value">{opp_id}</span>'
            else:
                info_line = f'<span class="field-label">Link:</span> <a href="{link}" class="link-field">{link}</a> | <span class="field-label">APN Contact:</span> <span class="field-value">{contact}</span> | <span class="field-label">ID:</span> <span class="field-value">{opp_id}</span>'
            
            html_parts.append(info_line)
            
            # Ações recomendadas formatadas
            actions_html = self.format_actions_html(opp.get('actions', []), language)
            if actions_html:
                html_parts.append(actions_html)
            
            # Separador
            html_parts.append('--------------------------------------------------------------------------------')
        
        return '\n'.join(html_parts)
    
    def create_intro_html(self, email_data: Dict, language: str = 'PT') -> str:
        """Cria introdução formatada para email individual"""
        company_name = email_data.get('contact_name', self.get_company_from_email(email_data['to_email']))
        
        if language == 'PT':
            intro_text = f"Olá {company_name},"
            intro_text2 = "Identificamos as seguintes oportunidades em nosso pipeline que necessitam de atualização."
            intro_text3 = "Solicitamos seu apoio para realizar os ajustes necessários."
            section_title = "Oportunidades:"
        else:
            intro_text = f"Hello partner {company_name},"
            intro_text2 = "We have identified the following opportunities in our pipeline that require updates."
            intro_text3 = "We request your support to make the necessary adjustments."
            section_title = "Opportunities:"
        
        intro_html = [
            f'<span class="email-intro">{intro_text}</span>',
            '',
            f'<span class="email-intro">{intro_text2}</span>',
            f'<span class="email-intro">{intro_text3}</span>',
            '',
            f'<span class="opportunity-section-title">{section_title}</span>',
            '================================================================================'
        ]
        
        return '\n'.join(intro_html)
    
    def create_footer_html(self, language: str = 'PT') -> str:
        """Cria rodapé formatado para email individual"""
        if language == 'PT':
            footer_lines = [
                '',
                'PRÓXIMOS PASSOS:',
                '- Atualize as oportunidades no sistema Partner Central',
                '- Confirme os dados com seus clientes',
                '- Entre em contato conosco se precisar de suporte',
                '',
                'Qualquer dúvida, responda este email ou entre em contato com nossa equipe.',
                '',
                'Obrigado pela parceria!',
                '',
                'Equipe AWS Partner',
                'Email: Responda este email para dúvidas',
                'Portal: Partner Central - https://partnercentral.awspartner.com'
            ]
        else:
            footer_lines = [
                '',
                'NEXT STEPS:',
                '- Update the opportunities in Partner Central system',
                '- Confirm the data with your customers',
                '- Contact us if you need support',
                '',
                'If you have any questions, please reply to this email or contact our team.',
                '',
                'Thank you for the partnership!',
                '',
                'AWS Partner Team',
                'Email: Reply to this email for questions',
                'Portal: Partner Central - https://partnercentral.awspartner.com'
            ]
        
        return '\n'.join(footer_lines)
    
    def format_individual_email_html(self, email_data: Dict, language: str = 'PT') -> str:
        """Formata email individual com layout consolidado"""
        
        # Seleciona conteúdo baseado no idioma
        if language == 'EN':
            body_content = email_data.get('body_english', email_data['body'])
        else:
            body_content = email_data['body']
        
        # Remove o rodapé original para evitar duplicação
        footer_markers = [
            'PRÓXIMOS PASSOS:',
            'NEXT STEPS:',
            '----------------------------------------------------------------------------------------------------'
        ]
        
        for marker in footer_markers:
            if marker in body_content:
                body_content = body_content.split(marker)[0].strip()
                break
        
        # Extrai oportunidades do texto
        opportunities = self.parse_individual_opportunities(body_content)
        
        # Cria introdução formatada
        intro_html = self.create_intro_html(email_data, language)
        
        # Formata oportunidades com layout compacto
        opportunities_html = self.format_opportunities_compact(opportunities, language)
        
        # Cria rodapé formatado
        footer_html = self.create_footer_html(language)
        
        # Combina tudo
        return f"{intro_html}\n{opportunities_html}\n{footer_html}"

    def create_individual_email_file(self, email_data: Dict, language: str = 'PT') -> str:
        """Cria arquivo .eml individual como rascunho para Outlook"""
        import tempfile
        import os
        from datetime import datetime
        import base64
        

        
        # Seleciona conteúdo baseado no idioma
        if language == 'EN':
            subject = email_data.get('subject_english', email_data['subject'])
        else:
            subject = email_data['subject']
        
        # NOVA IMPLEMENTAÇÃO: Usa formatação HTML estruturada igual aos emails consolidados
        html_body = self.format_individual_email_html(email_data, language)
        
        # Para a parte texto, usa a versão HTML sem tags (será convertida)
        body_content = html_body
        
        # Formata HTML para email (converte classes CSS para estilos inline)
        html_body_formatted = self.format_html_for_email(html_body)
        
        # Codifica o assunto corretamente para evitar caracteres estranhos
        subject_encoded = base64.b64encode(subject.encode('utf-8')).decode('ascii')
        
        # Cria conteúdo do arquivo .eml COMO RASCUNHO
        eml_content = f"""X-Unsent: 1
To: {email_data['to_email']}
Subject: =?UTF-8?B?{subject_encoded}?=
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit

{body_content}

--boundary123
Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: 8bit

<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #003366; font-size: 10pt; }}
        .opportunity-title {{ color: #FF8C00; font-weight: bold; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .field-label {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .field-value {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .link-field {{ color: #003366; text-decoration: underline; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .link-field:hover {{ color: #002244; text-decoration: underline; }}
        .actions-header {{ color: #003366; font-weight: bold; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .action-category {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .action-detail {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .action-required {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .email-intro {{ color: #003366; font-weight: normal; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
        .opportunity-section-title {{ color: #003366; font-weight: bold; font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10pt; }}
    </style>
</head>
<body>
{html_body_formatted}
</body>
</html>

--boundary123--
"""
        
        # Cria identificador único para o arquivo
        company_name = self.get_company_from_email(email_data['to_email'])
        email_id = email_data.get('id', 'unknown')
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Cria diretório temp se não existir
        temp_dir = os.path.join(get_dated_results_dir(), 'temp_emails')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Nome do arquivo individual (inclui idioma para evitar sobrescrita)
        eml_filename = f"email_individual_{company_name}_{email_id}_{language}_{timestamp}.eml"
        eml_path = os.path.join(temp_dir, eml_filename)
        
        # Salva arquivo .eml
        with open(eml_path, 'w', encoding='utf-8') as f:
            f.write(eml_content)
        
        return eml_filename

    def generate_html(self, emails: List[Dict], emails_english: List[Dict] = None) -> str:
        """Gera HTML completo com interface de emails em português e inglês"""
        import os
        
        # Cria mapeamento de emails em português para inglês
        english_map = {}
        if emails_english:
            for eng_email in emails_english:
                english_map[eng_email['to_email']] = eng_email
        
        # Agrupa emails por empresa para melhor organização
        companies = self.group_emails_by_company(emails)
        
        # Calcula estatísticas de consolidação
        companies_with_multiple_emails = sum(1 for company_emails in companies.values() if len(company_emails) > 1)
        total_consolidatable_emails = sum(len(company_emails) for company_emails in companies.values() if len(company_emails) > 1)
        
        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pipeline Hygiene - Emails para Envio</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #232526 0%, #414345 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats {{
            background: #f8f9fa;
            padding: 20px 30px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            text-align: center;
            margin: 10px;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .search-box {{
            margin-bottom: 30px;
            position: relative;
        }}
        
        .search-input {{
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 1.1em;
            transition: border-color 0.3s;
        }}
        
        .search-input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .company-section {{
            margin-bottom: 40px;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .company-header {{
            background: #667eea;
            color: white;
            padding: 15px 20px;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .company-header:hover {{
            background: #5a6fd8;
        }}
        
        .company-count {{
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
        }}
        
        .emails-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            padding: 20px;
            background: #f8f9fa;
        }}
        
        .email-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .email-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}
        
        .email-header {{
            margin-bottom: 15px;
        }}
        
        .contact-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .email-address {{
            color: #667eea;
            font-size: 0.95em;
            word-break: break-all;
        }}
        
        .email-info {{
            margin-bottom: 20px;
        }}
        
        .info-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.9em;
        }}
        
        .info-label {{
            color: #6c757d;
            font-weight: 500;
        }}
        
        .info-value {{
            color: #2c3e50;
            font-weight: bold;
        }}
        
        .button-group {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        /* Estilos antigos removidos - usando apenas .btn */
        
        /* Novos estilos para o redesign - VERSÃO MELHORADA */
        .email-actions-container {{
            display: flex !important;
            flex-direction: column !important;
            gap: 20px !important;
            padding: 24px !important;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
            border-radius: 16px !important;
            border: 2px solid #e9ecef !important;
            box-shadow: 0 8px 24px rgba(0,0,0,0.08) !important;
            margin: 16px 0 !important;
        }}
        
        /* Seletores específicos para botões dentro dos cards */
        .email-card .btn {{
            padding: 14px 24px !important;
            border-radius: 12px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            cursor: pointer !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            text-decoration: none !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            border: none !important;
            min-width: 140px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            margin: 0 !important;
        }}
        
        .email-card .btn-copy {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
            color: white !important;
        }}
        
        .email-card .btn-send {{
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%) !important;
            color: white !important;
        }}
        
        .email-card .btn-outlook {{
            background: linear-gradient(135deg, #fd7e14 0%, #e55a00 100%) !important;
            color: white !important;
        }}
        
        .language-group {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .language-header {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 10px 16px;
            border-radius: 10px;
            border-left: 4px solid #007bff;
            font-size: 14px;
            font-weight: 800;
            color: #495057;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .buttons-row {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 14px 24px !important;
            border-radius: 12px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            cursor: pointer !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            text-decoration: none !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            border: none !important;
            min-width: 140px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            margin: 0 !important;
        }}
        
        .btn::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }}
        
        .btn:hover::before {{
            left: 100%;
        }}
        
        .btn:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2) !important;
        }}
        
        .btn:active {{
            transform: translateY(0) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
        }}
        
        .btn-copy {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
            color: white !important;
        }}
        
        .btn-copy:hover {{
            background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%) !important;
            box-shadow: 0 8px 20px rgba(40,167,69,0.3) !important;
        }}
        
        .btn-send {{
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%) !important;
            color: white !important;
        }}
        
        .btn-send:hover {{
            background: linear-gradient(135deg, #0056b3 0%, #004085 100%) !important;
            box-shadow: 0 8px 20px rgba(0,123,255,0.3) !important;
        }}
        
        .btn-outlook {{
            background: linear-gradient(135deg, #fd7e14 0%, #e55a00 100%) !important;
            color: white !important;
        }}
        
        .btn-outlook:hover {{
            background: linear-gradient(135deg, #e55a00 0%, #cc4900 100%) !important;
            box-shadow: 0 8px 20px rgba(253,126,20,0.3) !important;
            animation: pulse 0.5s;
        }}
        
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
        }}
        
        @keyframes shimmer {{
            0% {{ background-position: -200px 0; }}
            100% {{ background-position: calc(200px + 100%) 0; }}
        }}
        
        .btn-loading {{
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200px 100%;
            animation: shimmer 1.5s infinite;
            color: transparent !important;
        }}
        
        .btn-success {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
            animation: pulse 0.6s ease-in-out;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        
        .hidden {{
            display: none;
        }}
        
        .consolidated-email-section {{
            background: linear-gradient(135deg, #e8f4fd 0%, #f0f8ff 100%);
            border-left: 4px solid #0078d4;
            margin: 0;
        }}
        
        .consolidated-email-section h3 {{
            color: #0078d4;
            margin: 0;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .consolidated-email-section .button-group {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        
        .consolidated-button {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1em;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        
        .consolidated-button:hover {{
            background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(40,167,69,0.4);
        }}
        
        .consolidated-button.copy {{
            background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%);
        }}
        
        .consolidated-button.copy:hover {{
            background: linear-gradient(135deg, #106ebe 0%, #005a9e 100%);
            box-shadow: 0 5px 15px rgba(0,120,212,0.4);
        }}
        
        /* Classes para formatação colorida dos emails - Amazon Ember 10 e azul marinho escuro */
        .opportunity-title {{
            color: #FF8C00;
            font-weight: bold;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        .field-label {{
            color: #003366;
            font-weight: normal;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        .field-value {{
            color: #003366;
            font-weight: normal;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        .link-field {{
            color: #003366;
            text-decoration: underline;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        .link-field:hover {{
            color: #002244;
            text-decoration: underline;
        }}
        
        .actions-header {{
            color: #003366;
            font-weight: bold;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        .action-category {{
            color: #003366;
            font-weight: normal;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        .action-detail {{
            color: #003366;
            font-weight: normal;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        .action-required {{
            color: #003366;
            font-weight: normal;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        .email-intro {{
            color: #003366;
            font-weight: normal;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        .opportunity-section-title {{
            color: #003366;
            font-weight: bold;
            font-family: 'Amazon Ember', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
        }}
        
        @media (max-width: 768px) {{
            .emails-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats {{
                flex-direction: column;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .consolidated-email-section {{
                padding: 15px;
            }}
            
            .consolidated-email-section > div:first-child {{
                flex-direction: column;
                align-items: flex-start !important;
            }}
            
            /* Responsivo para novos botões */
            .email-actions-container {{
                padding: 20px 16px;
                margin: 12px 0;
            }}
            
            .buttons-row {{
                flex-direction: column;
                width: 100%;
                gap: 10px;
            }}
            
            .btn {{
                width: 100%;
                min-width: unset;
                padding: 16px 20px;
                font-size: 16px;
                border-radius: 10px;
                gap: 15px;
            }}
            
            .consolidated-email-section .button-group {{
                flex-direction: column;
                width: 100%;
            }}
            
            .consolidated-button {{
                width: 100%;
                justify-content: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Pipeline Hygiene</h1>
            <p>Emails prontos para envio via Outlook</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{len(emails)}</div>
                <div class="stat-label">Total de Emails</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(companies)}</div>
                <div class="stat-label">Empresas</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{companies_with_multiple_emails}</div>
                <div class="stat-label">Consolidáveis</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{sum(email['opportunities_count'] for email in emails)}</div>
                <div class="stat-label">Oportunidades</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{datetime.now().strftime('%d/%m')}</div>
                <div class="stat-label">Gerado em</div>
            </div>
        </div>
        
        <div class="content">
            <div class="search-box">
                <input type="text" class="search-input" placeholder="🔍 Buscar por nome, email ou empresa..." onkeyup="filterEmails()">
            </div>
"""
        
        # Gera seções por empresa
        for company, company_emails in sorted(companies.items()):
            # Cria email consolidado se há múltiplos emails para a empresa
            consolidated_email = None
            if len(company_emails) > 1:
                consolidated_email = self.create_consolidated_email(company_emails)
            
            html_content += f"""
            <div class="company-section" data-company="{company.lower()}">
                <div class="company-header" onclick="toggleCompany(this)">
                    <span>{company}</span>
                    <span class="company-count">{len(company_emails)} emails</span>
                </div>"""
            
            # Adiciona botão de email consolidado se aplicável
            if consolidated_email:
                # Cria URLs para ambas as versões
                consolidated_mailto_url_text = self.create_mailto_url(consolidated_email)  # Versão texto
                
                # Cria arquivo .eml para versão HTML
                company_safe = company.replace(' ', '_').replace('/', '_').replace('&', '_')
                consolidated_eml_path = self.create_html_email_file(consolidated_email, f"consolidated_{company_safe}")
                consolidated_eml_filename = consolidated_eml_path  # Usa o caminho completo incluindo subpasta
                
                # Usa a versão texto puro para o botão de cópia (compatibilidade)
                consolidated_body_js = consolidated_email['body'].replace('"', '\\"').replace('\n', '\\n')
                # Usa a versão HTML para visualização na interface
                consolidated_body_display = consolidated_email.get('body_html', consolidated_email['body'])
                
                # Usa a versão HTML para o botão de cópia formatada
                consolidated_body_html_js = consolidated_email.get('body_html', consolidated_email['body']).replace('"', '\\"').replace('\n', '\\n')
                
                html_content += f"""
                <div class="consolidated-email-section" style="background: #e8f4fd; padding: 15px 20px; border-bottom: 2px solid #0078d4;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div>
                            <h3 style="color: #0078d4; margin: 0; font-size: 1.1em;">📧 Email Consolidado</h3>
                            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">
                                Envie um único email para todos os {len(company_emails)} destinatários desta empresa
                            </p>
                        </div>
                        <div class="buttons-row" style="justify-content: flex-end; gap: 8px;">
                            <button onclick="copyEmailData('{consolidated_email['to_email']}', '{consolidated_email['subject']}', `{consolidated_body_js}`)" 
                                    class="btn btn-copy" style="min-width: 90px; padding: 10px 16px; font-size: 13px;">
                                📋 Copiar
                            </button>
                            <a href="{consolidated_mailto_url_text}" 
                               class="btn btn-send" style="min-width: 90px; padding: 10px 16px; font-size: 13px;">
                                📧 Enviar
                            </a>
                            <button onclick="downloadAndOpenEmail('{consolidated_eml_filename}')" 
                                    class="btn btn-outlook" style="min-width: 120px; padding: 10px 16px; font-size: 13px;">
                                🎨 Outlook ({consolidated_email['opportunities_count']} opps)
                            </button>
                        </div>
                    </div>
                    <div style="font-size: 0.85em; color: #666; margin-bottom: 15px;">
                        <strong>Para:</strong> {consolidated_email['to_email']}<br>
                        <strong>Oportunidades:</strong> {consolidated_email['opportunities_count']} de {len(company_emails)} emails individuais
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; max-height: 300px; overflow-y: auto;">
                        <h4 style="color: #0078d4; margin: 0 0 10px 0; font-size: 1em;">📋 Preview do Email:</h4>
                        <div style="font-family: monospace; font-size: 0.85em; line-height: 1.4; white-space: pre-line;">
{consolidated_body_display}
                        </div>
                    </div>
                </div>"""
            
            html_content += """
                <div class="emails-grid">
"""
            
            for email in company_emails:
                outlook_url = self.create_outlook_url(email)
                mailto_url = self.create_mailto_url(email)
                
                # Cria versão texto sem HTML para cópia
                import re
                email_body_text = re.sub(r'<a href="[^"]*" target="_blank">([^<]*)</a>', r'\1', email['body'])
                
                # Escapa aspas para JavaScript (versão texto)
                email_body_js = email_body_text.replace('"', '\\"').replace('\n', '\\n')
                
                # Versão do corpo com HTML renderizado para exibição na interface
                email_body_display = email['body'].replace('\n', '<br>')
                
                html_content += f"""
                    <div class="email-card" data-contact="{email['contact_name'].lower()}" data-email="{email['to_email'].lower()}">
                        <div class="email-header">
                            <div class="contact-name">{email['contact_name']}</div>
                            <div class="email-address">{email['to_email']}</div>
                        </div>
                        <div class="email-info">
                            <div class="info-item">
                                <span class="info-label">Oportunidades:</span>
                                <span class="info-value">{email['opportunities_count']}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">ID:</span>
                                <span class="info-value">#{email['id']:03d}</span>
                            </div>
                        </div>
                        <div class="email-actions-container">
                            <!-- Seção Português -->
                            <div class="language-group">
                                <div class="language-header">🇧🇷 PORTUGUÊS</div>
                                <div class="buttons-row">
                                    <button onclick="copyEmailData('{email['to_email']}', '{email['subject']}', `{email_body_js}`)" class="btn btn-copy">
                                        📋 Copiar
                                    </button>
                                    <a href="{mailto_url}" class="btn btn-send">
                                        📧 Enviar
                                    </a>"""
                
                # Gera arquivo .eml individual para português
                eml_filename_pt = self.create_individual_email_file(email, 'PT')
                html_content += f"""
                                    <button onclick="downloadAndOpenEmail('{eml_filename_pt}')" class="btn btn-outlook">
                                        🎨 Outlook Beta
                                    </button>
                                </div>
                            </div>"""
                
                # Adiciona botões em inglês se disponível (DENTRO do loop)
                if email['to_email'] in english_map:
                    english_email = english_map[email['to_email']]
                    # Remove HTML dos hyperlinks para versão texto
                    english_body_text = re.sub(r'<a href="[^"]*" target="_blank">([^<]*)</a>', r'\1', english_email['body'])
                    english_body_js = english_body_text.replace('`', '\\`').replace('\n', '\\n').replace('\r', '').replace("'", "\\'")
                    english_mailto_url = self.create_mailto_url(english_email)
                    
                    html_content += f"""
                            
                            <!-- Seção English -->
                            <div class="language-group">
                                <div class="language-header">🇺🇸 ENGLISH</div>
                                <div class="buttons-row">
                                    <button onclick="copyEmailData('{english_email['to_email']}', '{english_email['subject']}', `{english_body_js}`)" class="btn btn-copy">
                                        📋 Copy
                                    </button>
                                    <a href="{english_mailto_url}" class="btn btn-send">
                                        📧 Send
                                    </a>"""
                    
                    # Gera arquivo .eml individual para inglês usando o email em inglês
                    eml_filename_en = self.create_individual_email_file(english_email, 'EN')
                    html_content += f"""
                                    <button onclick="downloadAndOpenEmail('{eml_filename_en}')" class="btn btn-outlook">
                                        🎨 Outlook Beta
                                    </button>
                                </div>
                            </div>"""
                
                html_content += """
                        </div>
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | AWS Partner Pipeline Hygiene</p>
        </div>
    </div>
    
    <script>
        function toggleCompany(header) {{
            const section = header.parentElement;
            const grid = section.querySelector('.emails-grid');
            
            if (grid.style.display === 'none') {{
                grid.style.display = 'grid';
                header.style.background = '#667eea';
            }} else {{
                grid.style.display = 'none';
                header.style.background = '#95a5a6';
            }}
        }}
        
        function filterEmails() {{
            const searchTerm = document.querySelector('.search-input').value.toLowerCase();
            const emailCards = document.querySelectorAll('.email-card');
            const companySections = document.querySelectorAll('.company-section');
            
            emailCards.forEach(card => {{
                const contact = card.dataset.contact;
                const email = card.dataset.email;
                const company = card.closest('.company-section').dataset.company;
                
                if (contact.includes(searchTerm) || email.includes(searchTerm) || company.includes(searchTerm)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
            
            // Esconde seções de empresa que não têm emails visíveis
            companySections.forEach(section => {{
                const visibleCards = section.querySelectorAll('.email-card[style*="block"], .email-card:not([style*="none"])');
                if (visibleCards.length === 0 && searchTerm !== '') {{
                    section.style.display = 'none';
                }} else {{
                    section.style.display = 'block';
                }}
            }});
        }}
        
        // Função para copiar dados do email (texto puro)
        function copyEmailData(to, subject, body) {{
            const emailData = `Para: ${{to}}
Assunto: ${{subject}}

${{body}}`;
            
            // Tenta usar a API moderna de clipboard
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(emailData).then(() => {{
                    showCopySuccess(event.target);
                }}).catch(() => {{
                    fallbackCopy(emailData, event.target);
                }});
            }} else {{
                fallbackCopy(emailData, event.target);
            }}
        }}
        

        
        // Função para baixar e abrir arquivo .eml no Outlook
        function downloadAndOpenEmail(filename) {{
            const button = event.target;
            const originalText = button.innerHTML;
            
            // Feedback visual melhorado
            button.classList.add('btn-loading');
            button.innerHTML = '⏳ Preparando...';
            button.disabled = true;
            
            // Cria link para download do arquivo .eml
            const emlPath = `temp_emails/${{filename}}`;
            const link = document.createElement('a');
            link.href = emlPath;
            link.download = filename;
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Feedback de sucesso
            setTimeout(() => {{
                button.classList.remove('btn-loading');
                button.classList.add('btn-success');
                button.innerHTML = '✅ Arquivo Criado!';
            }}, 800);
            
            // Restaura botão após um tempo
            setTimeout(() => {{
                button.classList.remove('btn-success');
                button.innerHTML = originalText;
                button.disabled = false;
            }}, 3000);
            
            // Mostra instruções
            setTimeout(() => {{
                alert('📧 Arquivo de email baixado!\\n\\n📋 Instruções:\\n1. Localize o arquivo baixado (.eml)\\n2. Clique duas vezes para abrir no Outlook\\n3. O email abrirá com formatação colorida\\n4. Revise e envie!');
            }}, 500);
        }}
        
        // Fallback para navegadores mais antigos
        function fallbackCopy(text, button) {{
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {{
                document.execCommand('copy');
                showCopySuccess(button);
            }} catch (err) {{
                alert('Erro ao copiar. Tente manualmente.');
            }}
            
            document.body.removeChild(textArea);
        }}
        
        // Mostra feedback visual de cópia bem-sucedida
        function showCopySuccess(button) {{
            const originalText = button.innerHTML;
            
            // Feedback visual melhorado
            button.classList.add('btn-success');
            button.innerHTML = '✅ Copiado!';
            
            // Pequena animação de sucesso
            button.style.transform = 'scale(1.05)';
            
            setTimeout(() => {{
                button.style.transform = 'scale(1)';
            }}, 200);
            
            setTimeout(() => {{
                button.classList.remove('btn-success');
                button.innerHTML = originalText;
            }}, 2500);
        }}
        
        // Função para destacar emails consolidados
        function highlightConsolidatedEmails() {{
            const consolidatedSections = document.querySelectorAll('.consolidated-email-section');
            consolidatedSections.forEach(section => {{
                section.style.animation = 'pulse 2s infinite';
            }});
        }}
        
        // Inicializa com todas as seções abertas
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Pipeline Hygiene HTML carregado com {len(emails)} emails');
            
            // Adiciona instruções para macOS
            if (navigator.platform.indexOf('Mac') > -1) {{
                const header = document.querySelector('.header p');
                header.innerHTML += '<br><small>💡 Para macOS: Certifique-se de que o Microsoft Outlook está instalado</small>';
            }}
            
            // Destaca seções com emails consolidados
            const consolidatedCount = document.querySelectorAll('.consolidated-email-section').length;
            if (consolidatedCount > 0) {{
                console.log('📧 ' + consolidatedCount + ' empresas têm emails consolidados disponíveis');
            }}
        }});
    </script>
</body>
</html>"""
        
        return html_content
    
    def save_html_file(self, emails: List[Dict], emails_english: List[Dict] = None, filename: str = "pipeline_hygiene_emails.html"):
        """Salva o arquivo HTML com suporte para ambos os idiomas"""
        html_content = self.generate_html(emails, emails_english)
        
        filepath = os.path.join(get_dated_results_dir(), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Interface HTML salva em: {filepath}")
        return filepath

def main():
    """Função principal"""
    print("="*60)
    print("🌐 HTML EMAIL GENERATOR - OUTLOOK INTEGRATION")
    print("="*60)
    print()
    
    # Verifica argumentos
    if len(sys.argv) < 2:
        print("❌ ERRO: Arquivo de emails não especificado")
        print()
        print("Uso:")
        print(f"   python3 {sys.argv[0]} <arquivo_emails.txt>")
        print()
        print("Exemplo:")
        print(f"   python3 {sys.argv[0]} results/pipeline_hygiene_emails.txt")
        sys.exit(1)
    
    emails_file = sys.argv[1]
    
    # Verifica se arquivo existe
    if not os.path.exists(emails_file):
        print(f"❌ ERRO: Arquivo '{emails_file}' não encontrado")
        sys.exit(1)
    
    # Inicializa gerador
    generator = HTMLEmailGenerator()
    
    # Processa emails em português
    print(f"📂 Processando arquivo: {emails_file}")
    emails = generator.parse_emails_file(emails_file)
    
    print(f"📧 Emails em português encontrados: {len(emails)}")
    
    # Processa emails em inglês (se existir)
    emails_english_file = emails_file.replace('.txt', '_english.txt')
    emails_english = []
    
    if os.path.exists(emails_english_file):
        print(f"📂 Processando arquivo em inglês: {emails_english_file}")
        emails_english = generator.parse_emails_english_file(emails_english_file)
        print(f"📧 Emails em inglês encontrados: {len(emails_english)}")
    else:
        print("ℹ️  Arquivo de emails em inglês não encontrado - apenas português será usado")
    
    print()
    
    if not emails:
        print("❌ Nenhum email válido encontrado!")
        sys.exit(1)
    
    # Gera HTML com ambos os idiomas
    html_file = generator.save_html_file(emails, emails_english)
    
    print("="*60)
    print("🎉 INTERFACE HTML CRIADA!")
    print("="*60)
    print()
    print(f"📁 Arquivo: {html_file}")
    print()
    print("🌐 COMO USAR:")
    print("1. Abra o arquivo HTML no seu navegador")
    print("2. Use a busca para encontrar contatos específicos")
    print("3. Para empresas com múltiplos emails:")
    print("   📧 Use o botão 'Enviar Consolidado' (recomendado)")
    print("   📋 Ou copie os dados consolidados")
    print("4. Para emails individuais:")
    print("   ✉️ Clique em 'Enviar Email' para cada contato")
    print("5. O Outlook abrirá com todos os dados preenchidos")
    print("6. Revise e envie!")
    print()
    print("💡 DICA: Emails consolidados reduzem spam e melhoram a experiência")
    print("💡 DICA: Funciona com Outlook Desktop e Outlook Web")
    print("="*60)

if __name__ == "__main__":
    main()