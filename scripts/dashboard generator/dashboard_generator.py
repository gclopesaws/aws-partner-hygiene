#!/usr/bin/env python3
"""
Dashboard Generator - Cria dashboard unificado com todos os relatórios HTML
Integra Delivery Model, Pipeline Hygiene e Slack Interface em uma única página
"""

import os
import sys
from datetime import datetime
from typing import Dict, List

# Importa função utilitária para diretório de resultados
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from results_dir import get_dated_results_dir

class DashboardGenerator:
    def __init__(self):
        self.results_dir = get_dated_results_dir()
        
    def check_html_files(self) -> Dict[str, bool]:
        """Verifica quais arquivos HTML existem"""
        files = {
            'delivery_model': os.path.exists(os.path.join(self.results_dir, 'delivery_model_report.html')),
            'pipeline_hygiene': os.path.exists(os.path.join(self.results_dir, 'pipeline_hygiene_emails.html')),
            'slack_interface': os.path.exists(os.path.join(self.results_dir, 'slack_interface.html')),
            'followup_emails': os.path.exists(os.path.join(self.results_dir, 'followup_emails.html'))
        }
        return files
    
    def get_slack_stats(self) -> Dict[str, int]:
        """Extrai estatísticas específicas do arquivo Slack"""
        slack_stats = {
            'total_messages': 0,
            'total_actions': 0,
            'total_partners': 0,
            'co_sell_missing': 0,
            'stage_ahead': 0,
            'partner_finalized': 0,
            'eligible_share': 0,
            'close_date_soon': 0,
            'no_partner_opportunities': 0,
            'zero_amount_opportunities': 0,
            'shared_not_accepted': 0
        }
        
        slack_file = os.path.join(self.results_dir, 'slack_messages.txt')
        if not os.path.exists(slack_file):
            return slack_stats
        
        try:
            with open(slack_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Conta mensagens
            slack_stats['total_messages'] = len([line for line in content.split('\n') if line.startswith('MENSAGEM ')])
            
            # Extrai estatísticas usando regex
            import re
            
            # Total de ações
            actions_matches = re.findall(r'Total de ações: (\d+)', content)
            slack_stats['total_actions'] = sum(int(match) for match in actions_matches)
            
            # Partners envolvidos
            partners_matches = re.findall(r'Partners envolvidos: (\d+)', content)
            slack_stats['total_partners'] = sum(int(match) for match in partners_matches)
            
            # Regras específicas
            slack_stats['co_sell_missing'] = len(re.findall(r'CO-SELL MISSING \((\d+)\)', content))
            slack_stats['stage_ahead'] = len(re.findall(r'PARTNER STAGE À FRENTE \((\d+)\)', content))
            slack_stats['partner_finalized'] = len(re.findall(r'PARTNER FINALIZOU \((\d+)\)', content))
            slack_stats['eligible_share'] = len(re.findall(r'COMPARTILHAR COM PARTNER \((\d+)\)', content))
            slack_stats['close_date_soon'] = len(re.findall(r'CLOSE DATE NOS PRÓXIMOS 30 DIAS \((\d+)\)', content))
            slack_stats['no_partner_opportunities'] = len(re.findall(r'OPORTUNIDADES SEM PARCEIRO.*?\((\d+)\)', content))
            slack_stats['zero_amount_opportunities'] = len(re.findall(r'OPORTUNIDADES COM VALOR ZERO.*?\((\d+)\)', content))
            slack_stats['shared_not_accepted'] = len(re.findall(r'OPORTUNIDADES REJEITADAS PARA RE-COMPARTILHAMENTO.*?\((\d+)\)', content))
            
        except Exception as e:
            print(f"Erro ao extrair estatísticas do Slack: {e}")
        
        return slack_stats
    
    def get_file_stats(self) -> Dict[str, Dict]:
        """Obtém estatísticas dos arquivos"""
        stats = {}
        
        files_info = {
            'delivery_model': {
                'path': 'delivery_model_report.html',
                'title': 'Delivery Model Report',
                'description': 'Oportunidades que precisam ajustar Delivery Model'
            },
            'pipeline_hygiene': {
                'path': 'pipeline_hygiene_emails.html',
                'title': 'Pipeline Hygiene Emails to Partners',
                'description': 'Interface para envio de emails de correção'
            },
            'slack_interface': {
                'path': 'slack_interface.html',
                'title': 'Pipeline Hygiene Emails to Account Managers',
                'description': 'Mensagens consolidadas por Account Manager'
            },
            'followup_emails': {
                'path': 'followup_emails.html',
                'title': 'Follow-up Emails',
                'description': 'Emails de follow-up organizados por AWS Account Manager'
            }
        }
        
        for key, info in files_info.items():
            file_path = os.path.join(self.results_dir, info['path'])
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                stats[key] = {
                    'title': info['title'],
                    'description': info['description'],
                    'path': info['path'],
                    'size': size,
                    'modified': modified,
                    'exists': True
                }
            else:
                stats[key] = {
                    'title': info['title'],
                    'description': info['description'],
                    'path': info['path'],
                    'exists': False
                }
        
        return stats
    
    def generate_dashboard_html(self) -> str:
        """Gera HTML do dashboard unificado"""
        
        stats = self.get_file_stats()
        available_reports = [k for k, v in stats.items() if v['exists']]
        slack_stats = self.get_slack_stats()
        
        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Partner Pipeline Analysis - Dashboard</title>
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
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-bar {{
            background: #f8f9fa;
            padding: 20px 40px;
            border-bottom: 1px solid #e9ecef;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
            color: #667eea;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .navigation {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .nav-card {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            border-left: 5px solid #667eea;
            cursor: pointer;
        }}
        
        .nav-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }}
        
        .nav-card.unavailable {{
            opacity: 0.5;
            cursor: not-allowed;
            border-left-color: #dc3545;
        }}
        
        .nav-card.unavailable:hover {{
            transform: none;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .nav-title {{
            font-size: 1.4em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .nav-description {{
            color: #6c757d;
            margin-bottom: 15px;
            line-height: 1.5;
        }}
        
        .nav-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
            color: #6c757d;
        }}
        
        .nav-button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s;
        }}
        
        .nav-button:hover {{
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            transform: scale(1.05);
        }}
        
        .nav-button.unavailable {{
            background: #dc3545;
            cursor: not-allowed;
        }}
        
        .iframe-container {{
            display: none;
            margin-top: 30px;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .iframe-container.active {{
            display: block;
        }}
        
        .iframe-header {{
            background: #667eea;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .iframe-title {{
            font-weight: bold;
            font-size: 1.1em;
        }}
        
        .close-btn {{
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .close-btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        .iframe-content {{
            width: 100%;
            height: 80vh;
            border: none;
            background: white;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 30px;
            font-size: 0.9em;
        }}
        
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        
        .status-available {{
            background: #28a745;
        }}
        
        .status-unavailable {{
            background: #dc3545;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2em;
            }}
            
            .navigation {{
                grid-template-columns: 1fr;
            }}
            
            .stats-bar {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AWS Partner Pipeline Analysis</h1>
            <p>Dashboard Unificado - Todos os Relatórios em um Local</p>
        </div>
        
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-number">{len(available_reports)}</div>
                <div class="stat-label">Relatórios Disponíveis</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{slack_stats['total_messages']}</div>
                <div class="stat-label">Mensagens Slack</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{slack_stats['total_actions']}</div>
                <div class="stat-label">Ações Totais</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{slack_stats['shared_not_accepted']}</div>
                <div class="stat-label">Rejeitadas</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{slack_stats['partner_finalized']}</div>
                <div class="stat-label">Críticas</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{datetime.now().strftime('%d/%m')}</div>
                <div class="stat-label">Gerado em</div>
            </div>
        </div>
        
        <div class="content">
            <div class="navigation">
"""
        
        # Gera cards para cada relatório
        for key, info in stats.items():
            status_class = "" if info['exists'] else "unavailable"
            status_indicator = "status-available" if info['exists'] else "status-unavailable"
            button_text = "Abrir Relatório" if info['exists'] else "Não Disponível"
            button_class = "" if info['exists'] else "unavailable"
            
            size_text = f"{info['size']:,} bytes" if info['exists'] else "N/A"
            modified_text = info['modified'].strftime('%d/%m/%Y %H:%M') if info['exists'] else "N/A"
            
            onclick = f"openReport('{key}', '{info['path']}', '{info['title']}')" if info['exists'] else ""
            
            html_content += f"""
                <div class="nav-card {status_class}" {f'onclick="{onclick}"' if info['exists'] else ''}>
                    <div class="nav-title">
                        <span class="status-indicator {status_indicator}"></span>
                        {info['title']}
                    </div>
                    <div class="nav-description">
                        {info['description']}
                    </div>
                    <div class="nav-meta">
                        <div>
                            <strong>Tamanho:</strong> {size_text}<br>
                            <strong>Modificado:</strong> {modified_text}
                        </div>
                        <a href="#" class="nav-button {button_class}" {f'onclick="{onclick}; return false;"' if info['exists'] else ''}>
                            {button_text}
                        </a>
                    </div>
                </div>
"""
        
        html_content += """
            </div>
            
            <!-- Containers para iframes -->
"""
        
        # Gera containers para cada iframe
        for key, info in stats.items():
            if info['exists']:
                html_content += f"""
            <div id="iframe-{key}" class="iframe-container">
                <div class="iframe-header">
                    <div class="iframe-title">{info['title']}</div>
                    <button class="close-btn" onclick="closeReport('{key}')">✕ Fechar</button>
                </div>
                <iframe id="frame-{key}" class="iframe-content" src=""></iframe>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>AWS Partner Pipeline Analysis Dashboard - Gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            <p>Versão 2.0.0 - Sistema Unificado de Relatórios</p>
        </div>
    </div>
    
    <script>
        function openReport(reportId, filePath, title) {{
            // Fecha todos os outros relatórios
            const containers = document.querySelectorAll('.iframe-container');
            containers.forEach(container => {{
                container.classList.remove('active');
            }});
            
            // Abre o relatório selecionado
            const container = document.getElementById(`iframe-${{reportId}}`);
            const iframe = document.getElementById(`frame-${{reportId}}`);
            
            if (container && iframe) {{
                iframe.src = filePath;
                container.classList.add('active');
                
                // Scroll para o iframe
                container.scrollIntoView({{ behavior: 'smooth' }});
            }}
        }}
        
        function closeReport(reportId) {{
            const container = document.getElementById(`iframe-${{reportId}}`);
            const iframe = document.getElementById(`frame-${{reportId}}`);
            
            if (container && iframe) {{
                container.classList.remove('active');
                iframe.src = '';
                
                // Scroll de volta para o topo
                document.querySelector('.navigation').scrollIntoView({{ behavior: 'smooth' }});
            }}
        }}
        
        // Inicialização
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Dashboard carregado com {len(available_reports)} relatórios disponíveis');
        }});
    </script>
</body>
</html>"""
        
        return html_content
    
    def save_dashboard(self, filename: str = "dashboard.html") -> str:
        """Salva o dashboard HTML"""
        html_content = self.generate_dashboard_html()
        
        filepath = os.path.join(self.results_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Dashboard salvo em: {filepath}")
        return filepath

def main():
    """Função principal"""
    print("="*60)
    print("DASHBOARD GENERATOR")
    print("="*60)
    print()
    
    # Inicializa gerador
    generator = DashboardGenerator()
    
    # Verifica arquivos disponíveis
    available_files = generator.check_html_files()
    available_count = sum(available_files.values())
    
    print(f"Arquivos HTML encontrados: {available_count}/4")
    for name, exists in available_files.items():
        status = "✅" if exists else "❌"
        print(f"   {status} {name.replace('_', ' ').title()}")
    
    print()
    
    if available_count == 0:
        print("❌ Nenhum arquivo HTML encontrado!")
        print("Execute primeiro: python3 run_pipeline_analysis.py <arquivo.xls>")
        sys.exit(1)
    
    # Gera dashboard
    dashboard_file = generator.save_dashboard()
    
    print("="*60)
    print("🎉 DASHBOARD CRIADO!")
    print("="*60)
    print()
    print(f"📁 Arquivo: {dashboard_file}")
    print()
    print("🌐 COMO USAR:")
    print("1. Abra o arquivo dashboard.html no seu navegador")
    print("2. Clique nos cards para abrir cada relatório")
    print("3. Use o botão 'Fechar' para voltar ao menu principal")
    print("4. Todos os relatórios ficam em uma única interface!")
    print()
    print("💡 DICA: O dashboard detecta automaticamente quais relatórios estão disponíveis")

if __name__ == "__main__":
    main()