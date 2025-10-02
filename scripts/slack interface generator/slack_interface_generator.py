#!/usr/bin/env python3
"""
Slack Interface Generator - Gera interface HTML para envio de mensagens Slack
Similar ao HTML Email Generator, mas focado em mensagens consolidadas por AM
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

class SlackInterfaceGenerator:
    def __init__(self):
        self.messages_data = []
        
    def parse_slack_messages_file(self, file_path: str) -> List[Dict]:
        """Extrai mensagens individuais do arquivo gerado pelo Slack Message Generator"""
        messages = []
        
        # Tenta diferentes encodings para ler o arquivo
        content = None
        encodings_to_try = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Arquivo Slack lido com sucesso usando encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # Última tentativa: lê como binário e tenta decodificar
            try:
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
                content = raw_content.decode('utf-8', errors='ignore')
                print("Arquivo Slack lido com encoding UTF-8 ignorando erros")
            except Exception as e:
                raise Exception(f"Não foi possível ler o arquivo Slack {file_path}: {e}")
        
        # Divide por "MENSAGEM X - " mas mantém o delimitador
        message_sections = re.split(r'(\nMENSAGEM \d+ - [^\n]+\n)', content)
        
        # Reconstrói as seções completas
        complete_sections = []
        for i in range(1, len(message_sections), 2):  # Pega delimitador + conteúdo
            if i + 1 < len(message_sections):
                complete_sections.append(message_sections[i] + message_sections[i + 1])
        
        for i, section in enumerate(complete_sections, 1):
            if not section.strip():
                continue
                
            # Extrai informações da mensagem
            lines = section.split('\n')
            
            message_data = {
                'id': i,
                'am_name': '',
                'body': '',
                'total_actions': 0,
                'partners_count': 0,
                'co_sell_missing': 0,
                'stage_ahead': 0,
                'partner_finalized': 0,
                'eligible_share': 0,
                'close_date_soon': 0,
                'no_partner_opportunities': 0,
                'zero_amount_opportunities': 0,
                'shared_not_accepted': 0
            }
            
            # Processa linha por linha
            body_lines = []
            capturing_body = False
            
            for line in lines:
                if line.startswith('MENSAGEM ') and ' - ' in line:
                    # Extrai nome do AM
                    am_match = re.search(r'MENSAGEM \d+ - (.+)', line)
                    if am_match:
                        message_data['am_name'] = am_match.group(1).strip()
                elif line.startswith('AÇÕES CONSOLIDADAS - '):
                    capturing_body = True
                    body_lines.append(line)
                elif capturing_body:
                    # Captura tudo até encontrar a próxima MENSAGEM ou final
                    if line.startswith('MENSAGEM ') and ' - ' in line:
                        break
                    elif line.startswith('============================================================'):
                        if body_lines:  # Se já capturou conteúdo, para aqui
                            break
                    else:
                        body_lines.append(line)
                        
                        # Extrai estatísticas do conteúdo
                        if 'Total de ações:' in line:
                            actions_match = re.search(r'Total de ações: (\d+)', line)
                            if actions_match:
                                message_data['total_actions'] = int(actions_match.group(1))
                        elif 'Partners envolvidos:' in line:
                            partners_match = re.search(r'Partners envolvidos: (\d+)', line)
                            if partners_match:
                                message_data['partners_count'] = int(partners_match.group(1))
                        elif 'CO-SELL MISSING (' in line:
                            co_sell_match = re.search(r'CO-SELL MISSING \((\d+)\)', line)
                            if co_sell_match:
                                message_data['co_sell_missing'] = int(co_sell_match.group(1))
                        elif 'PARTNER STAGE À FRENTE (' in line:
                            stage_match = re.search(r'PARTNER STAGE À FRENTE \((\d+)\)', line)
                            if stage_match:
                                message_data['stage_ahead'] = int(stage_match.group(1))
                        elif 'PARTNER FINALIZOU (' in line:
                            finalized_match = re.search(r'PARTNER FINALIZOU \((\d+)\)', line)
                            if finalized_match:
                                message_data['partner_finalized'] = int(finalized_match.group(1))
                        elif 'COMPARTILHAR COM PARTNER (' in line:
                            share_match = re.search(r'COMPARTILHAR COM PARTNER \((\d+)\)', line)
                            if share_match:
                                message_data['eligible_share'] = int(share_match.group(1))
                        elif 'CLOSE DATE NOS PRÓXIMOS 30 DIAS (' in line:
                            close_date_match = re.search(r'CLOSE DATE NOS PRÓXIMOS 30 DIAS \((\d+)\)', line)
                            if close_date_match:
                                message_data['close_date_soon'] = int(close_date_match.group(1))
                        elif 'OPORTUNIDADES SEM PARCEIRO' in line and '(' in line:
                            no_partner_match = re.search(r'OPORTUNIDADES SEM PARCEIRO.*?\((\d+)\)', line)
                            if no_partner_match:
                                message_data['no_partner_opportunities'] = int(no_partner_match.group(1))
                        elif 'OPORTUNIDADES COM VALOR ZERO' in line and '(' in line:
                            zero_amount_match = re.search(r'OPORTUNIDADES COM VALOR ZERO.*?\((\d+)\)', line)
                            if zero_amount_match:
                                message_data['zero_amount_opportunities'] = int(zero_amount_match.group(1))
                        elif 'OPORTUNIDADES REJEITADAS PARA RE-COMPARTILHAMENTO' in line and '(' in line:
                            shared_not_accepted_match = re.search(r'OPORTUNIDADES REJEITADAS PARA RE-COMPARTILHAMENTO.*?\((\d+)\)', line)
                            if shared_not_accepted_match:
                                message_data['shared_not_accepted'] = int(shared_not_accepted_match.group(1))
            
            message_data['body'] = '\n'.join(body_lines).strip()
            
            # Valida se tem nome do AM válido
            if message_data['am_name'] and message_data['body']:
                messages.append(message_data)
        
        return messages
    
    def create_slack_url(self, message_data: Dict) -> str:
        """Cria URL para abrir Slack Enterprise da Amazon com DM específico"""
        am_name = message_data['am_name']
        
        # Mapeamento de AMs para emails/IDs do Slack
        am_to_slack_id = {
            'FELIPE VELLOSO': 'sntfeli@amazon.com',
            'Felipe Velloso': 'sntfeli@amazon.com',
            # Adicione outros AMs aqui conforme necessário
            # 'OUTRO AM': 'email@amazon.com',
        }
        
        # Pega o email/ID do Slack para o AM
        slack_user_id = am_to_slack_id.get(am_name, None)
        
        if slack_user_id:
            # URL para abrir DM específico no Slack Enterprise da Amazon
            # Formato: https://amazon.enterprise.slack.com/messages/@email
            slack_url = f"https://amazon.enterprise.slack.com/messages/@{slack_user_id}"
        else:
            # Fallback: abre o Slack Enterprise geral
            slack_url = "https://amazon.enterprise.slack.com/"
        
        return slack_url
    
    def get_slack_user_id(self, am_name: str) -> str:
        """Retorna o ID/email do usuário no Slack para um AM específico"""
        am_to_slack_id = {
            'FELIPE VELLOSO': 'sntfeli@amazon.com',
            'Felipe Velloso': 'sntfeli@amazon.com',
            'BRUNO SANTOS': 'brunosnt@amazon.com',
            'Bruno Santos': 'brunosnt@amazon.com',
            'CASSIA CRUZ': 'cassiacr@amazon.com',
            'Cassia Cruz': 'cassiacr@amazon.com',
            'JOJI WATANABE': 'jojiwata@amazon.com',
            'Joji Watanabe': 'jojiwata@amazon.com',
            'REINALDO CAMILO': 'rcamilo@amazon.com',
            'Reinaldo Camilo': 'rcamilo@amazon.com',
            'CHRIS NICOLETTI': 'chrisnic@amazon.com',
            'Chris Nicoletti': 'chrisnic@amazon.com',
            'THIAGO ALBANO': 'thialbano@amazon.com',
            'Thiago Albano': 'thialbano@amazon.com',
            # Adicione outros AMs aqui conforme necessário
        }
        
        return am_to_slack_id.get(am_name, am_name.lower().replace(' ', '').replace('.', '') + '@amazon.com')
    
    def get_priority_level(self, message_data: Dict) -> str:
        """Determina nível de prioridade baseado nos tipos de ação"""
        if message_data['partner_finalized'] > 0:
            return "🔥 CRÍTICA"
        elif message_data['co_sell_missing'] > 5 or message_data['total_actions'] > 15:
            return "🚨 ALTA"
        elif message_data['total_actions'] > 5:
            return "⚠️ MÉDIA"
        else:
            return "✅ BAIXA"
    
    def generate_html(self, messages: List[Dict]) -> str:
        """Gera HTML completo com interface de mensagens Slack"""
        
        # Calcula estatísticas gerais
        total_actions = sum(msg['total_actions'] for msg in messages)
        total_partners = sum(msg['partners_count'] for msg in messages)
        total_co_sell = sum(msg['co_sell_missing'] for msg in messages)
        total_stage_ahead = sum(msg['stage_ahead'] for msg in messages)
        total_finalized = sum(msg['partner_finalized'] for msg in messages)
        total_share = sum(msg['eligible_share'] for msg in messages)
        total_close_date = sum(msg['close_date_soon'] for msg in messages)
        total_no_partner = sum(msg['no_partner_opportunities'] for msg in messages)
        total_zero_amount = sum(msg['zero_amount_opportunities'] for msg in messages)
        total_shared_not_accepted = sum(msg['shared_not_accepted'] for msg in messages)
        
        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pipeline Actions - Mensagens Slack</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #4A154B 0%, #350d36 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4A154B 0%, #350d36 100%);
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
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #4A154B;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 5px;
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
            border-color: #4A154B;
        }}
        
        .messages-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 25px;
        }}
        
        .message-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            border-left: 5px solid #4A154B;
        }}
        
        .message-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }}
        
        .message-header {{
            margin-bottom: 20px;
        }}
        
        .am-name {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .slack-id {{
            font-size: 0.9em;
            color: #4A154B;
            font-weight: 500;
            margin-bottom: 8px;
        }}
        
        .priority-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        
        .priority-critica {{ background: #dc3545; color: white; }}
        .priority-alta {{ background: #fd7e14; color: white; }}
        .priority-media {{ background: #ffc107; color: black; }}
        .priority-baixa {{ background: #28a745; color: white; }}
        
        .actions-summary {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        
        .action-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
        }}
        
        .action-label {{
            color: #6c757d;
            font-weight: 500;
        }}
        
        .action-count {{
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 12px;
            background: #4A154B;
            color: white;
            font-size: 0.8em;
        }}
        
        .action-count.zero {{
            background: #e9ecef;
            color: #6c757d;
        }}
        
        .button-group {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .slack-button, .copy-button {{
            padding: 15px 20px;
            border-radius: 10px;
            font-size: 1.05em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            border: none;
        }}
        
        .slack-button {{
            background: linear-gradient(135deg, #4A154B 0%, #350d36 100%);
            color: white;
            font-size: 1.1em;
        }}
        
        .slack-button:hover {{
            background: linear-gradient(135deg, #350d36 0%, #2d0a2e 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(74,21,75,0.4);
        }}
        
        .copy-button {{
            background: linear-gradient(135deg, #4A154B 0%, #350d36 100%);
            color: white;
            width: 100%;
        }}
        
        .copy-button:hover {{
            background: linear-gradient(135deg, #350d36 0%, #2d0a2e 100%);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(74,21,75,0.4);
        }}
        
        .slack-info {{
            text-align: center;
            margin-top: 10px;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 3px solid #4A154B;
        }}
        
        .slack-info small {{
            color: #6c757d;
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
        
        .instructions {{
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        .instructions h3 {{
            color: #1976d2;
            margin-bottom: 10px;
        }}
        
        .instructions ul {{
            margin-left: 20px;
            color: #424242;
        }}
        
        .instructions li {{
            margin-bottom: 5px;
        }}
        
        @media (max-width: 768px) {{
            .messages-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .actions-summary {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Pipeline Actions</h1>
            <p>Mensagens consolidadas por AM para Slack</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{len(messages)}</div>
                <div class="stat-label">Account Managers</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_actions}</div>
                <div class="stat-label">Total de Ações</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_partners}</div>
                <div class="stat-label">Partners Envolvidos</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_co_sell}</div>
                <div class="stat-label">Co-Sell Missing</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_stage_ahead}</div>
                <div class="stat-label">Stage à Frente</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_finalized}</div>
                <div class="stat-label">Partner Finalizou</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_share}</div>
                <div class="stat-label">Eligible to Share</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_close_date}</div>
                <div class="stat-label">Close Date Próximo</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_no_partner}</div>
                <div class="stat-label">Sem Parceiro</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_zero_amount}</div>
                <div class="stat-label">Valor Zero</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_shared_not_accepted}</div>
                <div class="stat-label">Rejeitadas</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{datetime.now().strftime('%d/%m')}</div>
                <div class="stat-label">Gerado em</div>
            </div>
        </div>
        
        <div class="content">
            <div class="instructions">
                <h3>📋 Como usar esta interface:</h3>
                <ul>
                    <li><strong>📋 Copiar Mensagem:</strong> Copia o texto formatado para colar no Slack</li>
                    <li><strong>📧 Email do destinatário:</strong> Mostrado em cada card para facilitar localização</li>
                    <li><strong>🔍 Busca:</strong> Filtra AMs por nome</li>
                    <li><strong>🎯 Prioridade:</strong> Baseada no tipo e quantidade de ações</li>
                    <li><strong>📱 Processo:</strong> Copie → Abra Slack → Procure AM → Cole mensagem</li>
                </ul>
            </div>
            
            <div class="search-box">
                <input type="text" class="search-input" placeholder="🔍 Buscar por nome do AM..." onkeyup="filterMessages()">
            </div>
            
            <div class="messages-grid">
"""
        
        # Gera cards para cada mensagem
        for message in messages:
            priority = self.get_priority_level(message)
            priority_class = priority.lower().replace('🔥 ', '').replace('🚨 ', '').replace('⚠️ ', '').replace('✅ ', '')
            
            # Escapa aspas para JavaScript
            message_body_js = message['body'].replace('`', '\\`').replace('\n', '\\n').replace('\r', '').replace("'", "\\'")
            
            html_content += f"""
                <div class="message-card" data-am="{message['am_name'].lower()}">
                    <div class="message-header">
                        <div class="am-name">{message['am_name']}</div>
                        <div class="slack-id">📧 {self.get_slack_user_id(message['am_name'])}</div>
                        <div class="priority-badge priority-{priority_class}">{priority}</div>
                    </div>
                    
                    <div class="actions-summary">
                        <div class="action-item">
                            <span class="action-label">Co-Sell Missing:</span>
                            <span class="action-count {'zero' if message['co_sell_missing'] == 0 else ''}">{message['co_sell_missing']}</span>
                        </div>
                        <div class="action-item">
                            <span class="action-label">Stage à Frente:</span>
                            <span class="action-count {'zero' if message['stage_ahead'] == 0 else ''}">{message['stage_ahead']}</span>
                        </div>
                        <div class="action-item">
                            <span class="action-label">Partner Finalizou:</span>
                            <span class="action-count {'zero' if message['partner_finalized'] == 0 else ''}">{message['partner_finalized']}</span>
                        </div>
                        <div class="action-item">
                            <span class="action-label">Eligible to Share:</span>
                            <span class="action-count {'zero' if message['eligible_share'] == 0 else ''}">{message['eligible_share']}</span>
                        </div>
                        <div class="action-item">
                            <span class="action-label">Close Date Próximo:</span>
                            <span class="action-count {'zero' if message['close_date_soon'] == 0 else ''}">{message['close_date_soon']}</span>
                        </div>
                        <div class="action-item">
                            <span class="action-label">Sem Parceiro:</span>
                            <span class="action-count {'zero' if message['no_partner_opportunities'] == 0 else ''}">{message['no_partner_opportunities']}</span>
                        </div>
                        <div class="action-item">
                            <span class="action-label">Valor Zero:</span>
                            <span class="action-count {'zero' if message['zero_amount_opportunities'] == 0 else ''}">{message['zero_amount_opportunities']}</span>
                        </div>
                        <div class="action-item">
                            <span class="action-label">Rejeitadas:</span>
                            <span class="action-count {'zero' if message['shared_not_accepted'] == 0 else ''}">{message['shared_not_accepted']}</span>
                        </div>
                        <div class="action-item">
                            <span class="action-label">Total de Ações:</span>
                            <span class="action-count">{message['total_actions']}</span>
                        </div>
                        <div class="action-item">
                            <span class="action-label">Partners:</span>
                            <span class="action-count">{message['partners_count']}</span>
                        </div>
                    </div>
                    
                    <div class="button-group">
                        <button onclick="copySlackMessage({message['id']})" class="copy-button" style="width: 100%;">
                            📋 Clique para copiar o Email
                        </button>
                        <div class="slack-info">
                            <small>📧 Enviar para: <strong>{self.get_slack_user_id(message['am_name'])}</strong></small>
                        </div>
                    </div>
                    
                    <!-- Dados da mensagem escondidos -->
                    <script type="application/json" id="message-data-{message['id']}">{message_body_js}</script>
                </div>
"""
        
        html_content += f"""
            </div>
        </div>
        
        <div class="footer">
            <p>Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | AWS Partner Pipeline Actions</p>
        </div>
    </div>
    
    <script>
        function filterMessages() {{
            const searchTerm = document.querySelector('.search-input').value.toLowerCase();
            const messageCards = document.querySelectorAll('.message-card');
            
            messageCards.forEach(card => {{
                const amName = card.dataset.am;
                
                if (amName.includes(searchTerm)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
        

        function copySlackMessage(messageId) {{
            console.log('copySlackMessage chamado:', messageId);
            
            // Pega a mensagem do elemento escondido
            const messageElement = document.getElementById(`message-data-${{messageId}}`);
            if (!messageElement) {{
                console.error('Elemento de mensagem não encontrado:', `message-data-${{messageId}}`);
                alert('❌ Erro: Dados da mensagem não encontrados');
                return;
            }}
            
            let slackMessage = messageElement.textContent;
            console.log('Mensagem original:', slackMessage.substring(0, 100) + '...');
            
            // Converte formatação para Slack mantendo legibilidade
            slackMessage = slackMessage
                .replace(/\\*\\*(.+?)\\*\\*/g, '*$1*')  // Bold: **texto** → *texto*
                .replace(/\\n\\n/g, '\\n\\n')           // Mantém parágrafos duplos
                .replace(/\\n/g, '\\n')                 // Quebras de linha simples
                .replace(/\\\\n/g, '\\n')               // Corrige escape duplo
                .replace(/\\\\t/g, '  ')                // Tabs para espaços
                .replace(/\\\\r/g, '')                  // Remove carriage returns
                .replace(/\\\\(.)/g, '$1');             // Remove escapes desnecessários
            
            console.log('Mensagem formatada:', slackMessage.substring(0, 100) + '...');
            
            // Tenta usar a API moderna de clipboard
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(slackMessage).then(() => {{
                    console.log('Mensagem copiada com sucesso');
                    showCopySuccess(event.target);
                    
                    // Mostra instruções para o usuário
                    setTimeout(() => {{
                        alert('✅ Mensagem copiada para clipboard!\\n\\n📱 Próximos passos:\\n1. Abra o Slack manualmente\\n2. Procure pelo AM ou abra o DM\\n3. Cole a mensagem (Cmd+V / Ctrl+V)\\n4. Revise e envie!');
                    }}, 300);
                }}).catch((err) => {{
                    console.error('Erro ao copiar:', err);
                    fallbackCopy(slackMessage, event.target);
                }});
            }} else {{
                console.log('Usando fallback para copiar');
                fallbackCopy(slackMessage, event.target);
            }}
        }}
        
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
        
        function showCopySuccess(button) {{
            const originalText = button.innerHTML;
            button.innerHTML = '✅ Copiado!';
            button.classList.add('copy-success');
            
            setTimeout(() => {{
                button.innerHTML = originalText;
                button.classList.remove('copy-success');
            }}, 2000);
        }}
        
        // Inicialização
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Slack Interface carregada com {len(messages)} mensagens');
            
            // Ordena cards por prioridade (crítica primeiro)
            const grid = document.querySelector('.messages-grid');
            const cards = Array.from(grid.children);
            
            cards.sort((a, b) => {{
                const priorityA = a.querySelector('.priority-badge').textContent;
                const priorityB = b.querySelector('.priority-badge').textContent;
                
                const priorityOrder = {{'🔥 CRÍTICA': 4, '🚨 ALTA': 3, '⚠️ MÉDIA': 2, '✅ BAIXA': 1}};
                
                return (priorityOrder[priorityB] || 0) - (priorityOrder[priorityA] || 0);
            }});
            
            // Reordena no DOM
            cards.forEach(card => grid.appendChild(card));
        }});
    </script>
</body>
</html>"""
        
        return html_content
    
    def save_html_file(self, messages: List[Dict], filename: str = "slack_interface.html"):
        """Salva o arquivo HTML da interface Slack"""
        html_content = self.generate_html(messages)
        
        filepath = os.path.join(get_dated_results_dir(), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Interface Slack salva em: {filepath}")
        return filepath

def main():
    """Função principal"""
    print("="*60)
    print("📱 SLACK INTERFACE GENERATOR")
    print("="*60)
    print()
    
    # Verifica argumentos
    if len(sys.argv) < 2:
        print("❌ ERRO: Arquivo de mensagens Slack não especificado")
        print()
        print("Uso:")
        print(f"   python3 {sys.argv[0]} <arquivo_slack_messages.txt>")
        print()
        print("Exemplo:")
        print(f"   python3 {sys.argv[0]} results/slack_messages.txt")
        sys.exit(1)
    
    messages_file = sys.argv[1]
    
    # Verifica se arquivo existe
    if not os.path.exists(messages_file):
        print(f"❌ ERRO: Arquivo '{messages_file}' não encontrado")
        sys.exit(1)
    
    # Inicializa gerador
    generator = SlackInterfaceGenerator()
    
    # Processa mensagens
    print(f"📂 Processando arquivo: {messages_file}")
    messages = generator.parse_slack_messages_file(messages_file)
    
    print(f"📱 Mensagens encontradas: {len(messages)}")
    print()
    
    if not messages:
        print("❌ Nenhuma mensagem válida encontrada!")
        sys.exit(1)
    
    # Gera HTML
    html_file = generator.save_html_file(messages)
    
    print("="*60)
    print("🎉 INTERFACE SLACK CRIADA!")
    print("="*60)
    print()
    print(f"📁 Arquivo: {html_file}")
    print()
    print("📱 COMO USAR:")
    print("1. Abra o arquivo HTML no seu navegador")
    print("2. Use a busca para encontrar AMs específicos")
    print("3. Clique em '📱 Enviar no Slack' para abrir o app")
    print("4. Ou use '📋 Copiar Mensagem' para colar manualmente")
    print("5. Mensagens estão ordenadas por prioridade!")
    print()
    print("💡 DICA: Funciona com Slack Desktop e Web")
    print("="*60)

if __name__ == "__main__":
    main()