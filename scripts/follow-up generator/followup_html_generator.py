#!/usr/bin/env python3
"""
Follow-up HTML Generator - Gera interface HTML para emails de follow-up
Cria interface web com botões mailto para envio dos emails de follow-up
"""

import os
import re
import sys
import urllib.parse
from datetime import datetime
from typing import Dict, List

# Importa função utilitária para diretório de resultados
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(os.path.dirname(script_dir), 'utils')
sys.path.append(utils_dir)
from results_dir import get_dated_results_dir

class FollowUpHTMLGenerator:
    def __init__(self):
        self.emails_data = []
        
    def parse_followup_emails_file(self, file_path: str) -> List[Dict]:
        """Extrai emails individuais do arquivo de follow-up gerado"""
        emails = []
        
        # Tenta diferentes encodings para ler o arquivo
        content = None
        encodings_to_try = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Arquivo follow-up lido com sucesso usando encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # Última tentativa: lê como binário e tenta decodificar
            try:
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
                content = raw_content.decode('utf-8', errors='ignore')
                print("Arquivo follow-up lido com encoding UTF-8 ignorando erros")
            except Exception as e:
                raise Exception(f"Não foi possível ler o arquivo follow-up {file_path}: {e}")
        
        # Nova estrutura: EMAIL X - Nome do Parceiro
        # Primeiro, divide por EMAIL X - Nome
        email_pattern = r'EMAIL \d+ - (.+?)\n=+'
        matches = re.finditer(email_pattern, content)
        
        complete_sections = []
        last_end = 0
        
        for match in matches:
            partner_name = match.group(1).strip()
            start_pos = match.end()
            
            # Encontra o próximo EMAIL ou fim do arquivo
            next_match = re.search(r'EMAIL \d+ - ', content[start_pos:])
            if next_match:
                end_pos = start_pos + next_match.start()
                section_content = content[start_pos:end_pos].strip()
            else:
                section_content = content[start_pos:].strip()
            
            if section_content:
                complete_sections.append((partner_name, section_content))
        
        for i, (partner_name, section_content) in enumerate(complete_sections, 1):
            if not section_content.strip():
                continue
                
            # Extrai informações do email
            lines = section_content.split('\n')
            
            email_data = {
                'id': i,
                'to_email': '',
                'to_emails_list': [],
                'subject': '',
                'partner_name': partner_name,
                'body': section_content,  # Usa o conteúdo completo da seção
                'opportunities_count': 0,
                'urgent_count': 0,
                'high_value_count': 0
            }
            
            # Extrai Para e Assunto das primeiras linhas e remove do corpo
            body_start_index = 0
            for i, line in enumerate(lines):
                if line.startswith('Para: '):
                    email_data['to_email'] = line.replace('Para: ', '').strip()
                    # Separa múltiplos emails se houver
                    email_data['to_emails_list'] = [email.strip() for email in email_data['to_email'].split(',')]
                elif line.startswith('Assunto: '):
                    email_data['subject'] = line.replace('Assunto: ', '').strip()
                elif line.startswith('Olá parceiro '):
                    body_start_index = i
                    break  # Para quando encontrar o início do corpo
            
            # Extrai apenas o corpo do email (sem Para/Assunto)
            if body_start_index > 0:
                email_data['body'] = '\n'.join(lines[body_start_index:]).strip()
            else:
                email_data['body'] = section_content
            
            # Conta oportunidades e analisa urgência usando o corpo do email
            email_data['opportunities_count'] = email_data['body'].count('Oportunidade ')
            email_data['urgent_count'] = email_data['body'].count('Close date vencido') + email_data['body'].count('Close date urgente')
            
            # Conta oportunidades de alto valor (>= $10,000)
            values = re.findall(r'Valor: \$([0-9,]+\.\d{2})', email_data['body'])
            high_value = 0
            for value_str in values:
                try:
                    value = float(value_str.replace(',', ''))
                    if value >= 10000:
                        high_value += 1
                except:
                    pass
            email_data['high_value_count'] = high_value
            
            # Valida se tem pelo menos um email válido
            valid_emails = [email for email in email_data['to_emails_list'] if '@' in email and email != 'nan']
            if valid_emails:
                emails.append(email_data)
        
        return emails
    
    def create_mailto_url(self, email_data: Dict) -> str:
        """Cria URL mailto para o email (suporta múltiplos destinatários)"""
        to_email = urllib.parse.quote(email_data['to_email'])
        subject = urllib.parse.quote(email_data['subject'])
        body = urllib.parse.quote(email_data['body'])
        
        return f"mailto:{to_email}?subject={subject}&body={body}"
    
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
    
    def generate_html(self, emails: List[Dict]) -> str:
        """Gera HTML completo com interface de follow-up emails"""
        
        # Calcula estatísticas gerais
        total_emails = len(emails)
        total_opportunities = sum(email['opportunities_count'] for email in emails)
        total_urgent = sum(email['urgent_count'] for email in emails)
        total_high_value = sum(email['high_value_count'] for email in emails)
        
        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Follow-up Pipeline - Emails para Parceiros</title>
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
        
        .emails-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 20px;
        }}
        
        .email-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s, box-shadow 0.3s;
            border: 1px solid #e9ecef;
        }}
        
        .email-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}
        
        .email-header {{
            margin-bottom: 15px;
        }}
        
        .partner-name {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .email-address {{
            color: #667eea;
            font-size: 0.95em;
            word-break: break-all;
        }}
        
        .email-count {{
            color: #6c757d;
            font-size: 0.85em;
            margin-top: 5px;
            font-style: italic;
        }}
        
        .email-stats {{
            display: flex;
            justify-content: space-between;
            margin: 15px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            font-size: 0.9em;
        }}
        
        .stat-badge {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }}
        
        .stat-badge .number {{
            font-weight: bold;
            font-size: 1.2em;
            color: #2c3e50;
        }}
        
        .stat-badge .label {{
            color: #6c757d;
            font-size: 0.8em;
        }}
        
        .urgent {{
            color: #dc3545 !important;
        }}
        
        .high-value {{
            color: #28a745 !important;
        }}
        
        .button-group {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .copy-button, .email-button {{
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            border: none;
        }}
        
        .copy-button {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }}
        
        .copy-button:hover {{
            background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(40,167,69,0.4);
        }}
        
        .email-button {{
            background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%);
            color: white;
        }}
        
        .email-button:hover {{
            background: linear-gradient(135deg, #106ebe 0%, #005a9e 100%);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,120,212,0.4);
        }}
        
        .copy-success {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
            animation: pulse 0.5s;
        }}
        
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
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
            
            .email-stats {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Follow-up Pipeline</h1>
            <p>Emails de follow-up para parceiros - Prontos para envio</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{total_emails}</div>
                <div class="stat-label">Parceiros</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_opportunities}</div>
                <div class="stat-label">Oportunidades</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_urgent}</div>
                <div class="stat-label">Urgentes</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_high_value}</div>
                <div class="stat-label">Alto Valor</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{datetime.now().strftime('%d/%m')}</div>
                <div class="stat-label">Gerado em</div>
            </div>
        </div>
        
        <div class="content">
            <div class="search-box">
                <input type="text" class="search-input" placeholder="🔍 Buscar por parceiro, email ou empresa..." onkeyup="filterEmails()">
            </div>
            
            <div class="emails-grid">"""
        
        # Gera cards para cada email
        for email in emails:
            mailto_url = self.create_mailto_url(email)
            body_js = email['body'].replace('"', '\\"').replace('\n', '\\n')
            
            # Determina classes CSS para urgência
            urgent_class = "urgent" if email['urgent_count'] > 0 else ""
            high_value_class = "high-value" if email['high_value_count'] > 0 else ""
            
            html_content += f"""
                <div class="email-card" data-partner="{email['partner_name'].lower()}" data-email="{email['to_email'].lower()}">
                    <div class="email-header">
                        <div class="partner-name">{email['partner_name']}</div>
                        <div class="email-address">{email['to_email']}</div>
                        {f'<div class="email-count">📧 {len(email["to_emails_list"])} contato{"s" if len(email["to_emails_list"]) > 1 else ""}</div>' if len(email['to_emails_list']) > 1 else ''}
                    </div>
                    
                    <div class="email-stats">
                        <div class="stat-badge">
                            <div class="number">{email['opportunities_count']}</div>
                            <div class="label">Oportunidades</div>
                        </div>
                        <div class="stat-badge">
                            <div class="number {urgent_class}">{email['urgent_count']}</div>
                            <div class="label">Urgentes</div>
                        </div>
                        <div class="stat-badge">
                            <div class="number {high_value_class}">{email['high_value_count']}</div>
                            <div class="label">Alto Valor</div>
                        </div>
                    </div>
                    
                    <div class="button-group">
                        <button onclick="copyEmailData('{email['to_email']}', '{email['subject']}', `{body_js}`)" 
                                class="copy-button">
                            📋 Copiar Dados do Email
                        </button>
                        <a href="{mailto_url}" class="email-button">
                            ✉️ Enviar Follow-up ({email['opportunities_count']} oportunidades)
                        </a>
                    </div>
                </div>"""
        
        html_content += f"""
            </div>
        </div>
        
        <div class="footer">
            <p>Follow-up Pipeline Generator - AWS Partner Team</p>
            <p>Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | Total: {total_emails} parceiros, {total_opportunities} oportunidades</p>
        </div>
    </div>

    <script>
        function copyEmailData(to, subject, body) {{
            const emailData = `Para: ${{to}}\\nAssunto: ${{subject}}\\n\\n${{body}}`;
            
            if (navigator.clipboard) {{
                navigator.clipboard.writeText(emailData).then(function() {{
                    // Feedback visual
                    event.target.textContent = '✅ Copiado!';
                    event.target.classList.add('copy-success');
                    
                    setTimeout(() => {{
                        event.target.textContent = '📋 Copiar Dados do Email';
                        event.target.classList.remove('copy-success');
                    }}, 2000);
                }}).catch(function() {{
                    fallbackCopy(emailData);
                }});
            }} else {{
                fallbackCopy(emailData);
            }}
        }}
        
        function fallbackCopy(text) {{
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            
            try {{
                document.execCommand('copy');
                event.target.textContent = '✅ Copiado!';
                event.target.classList.add('copy-success');
                
                setTimeout(() => {{
                    event.target.textContent = '📋 Copiar Dados do Email';
                    event.target.classList.remove('copy-success');
                }}, 2000);
            }} catch (err) {{
                alert('Erro ao copiar. Use Ctrl+C manualmente.');
            }}
            
            document.body.removeChild(textArea);
        }}
        
        function filterEmails() {{
            const searchTerm = document.querySelector('.search-input').value.toLowerCase();
            const emailCards = document.querySelectorAll('.email-card');
            
            emailCards.forEach(card => {{
                const partnerName = card.dataset.partner;
                const email = card.dataset.email;
                const company = email.split('@')[1] || '';
                
                if (partnerName.includes(searchTerm) || 
                    email.includes(searchTerm) || 
                    company.includes(searchTerm)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
        
        // Adiciona contador de emails visíveis
        document.querySelector('.search-input').addEventListener('input', function() {{
            setTimeout(() => {{
                const visibleCards = document.querySelectorAll('.email-card:not([style*="display: none"])').length;
                const totalCards = document.querySelectorAll('.email-card').length;
                
                if (this.value.trim()) {{
                    this.placeholder = `🔍 Mostrando ${{visibleCards}} de ${{totalCards}} parceiros...`;
                }} else {{
                    this.placeholder = '🔍 Buscar por parceiro, email ou empresa...';
                }}
            }}, 100);
        }});
    </script>
</body>
</html>"""
        
        return html_content
    
    def generate_html_file(self, emails_file: str, output_file: str = None):
        """Gera arquivo HTML a partir do arquivo de emails de follow-up"""
        if not os.path.exists(emails_file):
            print(f"❌ Arquivo de emails não encontrado: {emails_file}")
            return False
        
        # Parse dos emails
        emails = self.parse_followup_emails_file(emails_file)
        
        if not emails:
            print("❌ Nenhum email válido encontrado no arquivo")
            return False
        
        print(f"📧 Emails de follow-up encontrados: {len(emails)}")
        
        # Gera HTML
        html_content = self.generate_html(emails)
        
        # Define arquivo de saída
        if output_file is None:
            output_file = os.path.join(get_dated_results_dir(), "followup_emails.html")
        
        # Salva arquivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Interface HTML salva em: {output_file}")
        return True

def main():
    """Função principal"""
    print("="*60)
    print("🌐 FOLLOW-UP HTML GENERATOR")
    print("="*60)
    print()
    
    # Verifica argumentos
    if len(sys.argv) < 2:
        print("❌ ERRO: Arquivo de emails não especificado")
        print()
        print("Uso:")
        print(f"   python3 {sys.argv[0]} <arquivo_followup_emails.txt>")
        print()
        print("Exemplo:")
        print(f"   python3 {sys.argv[0]} results/2025-09-11/followup_emails.txt")
        sys.exit(1)
    
    emails_file = sys.argv[1]
    
    # Verifica se o arquivo existe
    if not os.path.exists(emails_file):
        print(f"❌ ERRO: Arquivo '{emails_file}' não encontrado")
        sys.exit(1)
    
    print(f"📂 Processando arquivo: {emails_file}")
    
    # Gera interface HTML
    generator = FollowUpHTMLGenerator()
    
    if generator.generate_html_file(emails_file):
        print("="*60)
        print("🎉 INTERFACE HTML CRIADA!")
        print("="*60)
        print()
        print(f"📁 Arquivo: {os.path.join(get_dated_results_dir(), 'followup_emails.html')}")
        print()
        print("🌐 COMO USAR:")
        print("1. Abra o arquivo HTML no seu navegador")
        print("2. Use a busca para encontrar parceiros específicos")
        print("3. Clique em '✉️ Enviar Follow-up' para abrir o email")
        print("4. Ou use '📋 Copiar Dados' para colar manualmente")
        print("5. O email abrirá com todos os dados preenchidos")
        print()
        print("💡 DICA: Funciona com qualquer cliente de email que suporte mailto")
        print("💡 DICA: Use os filtros para priorizar parceiros urgentes")
        print("="*60)
    else:
        print("❌ Falha ao gerar interface HTML")

if __name__ == "__main__":
    main()