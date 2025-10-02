#!/usr/bin/env python3
"""
Delivery Model Checker - Verifica e gera relatório para correção de Delivery Model
Regra 1: Partner Sourced Opportunity + Technology Partner + Delivery Model != "SaaS or PaaS"
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List
import re
import os

# Importa função utilitária para diretório de resultados
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from results_dir import get_dated_results_dir

class DeliveryModelChecker:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Carrega os dados da planilha"""
        try:
            # Lê o arquivo HTML/Excel
            self.df = pd.read_html(self.file_path)[0]
            print(f"✅ Dados carregados: {len(self.df)} oportunidades")
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            
    def find_delivery_model_issues(self) -> pd.DataFrame:
        """
        Encontra oportunidades que precisam ajustar o Delivery Model
        Regra: ACE Opportunity Type = "Partner Sourced Opportunity" (ou similares)
               AND Partner Type From Account = "Technology Partner"
               AND Delivery Model != "SaaS or PaaS"
               AND Stage != "Launched" ou "Closed Lost"
        """
        if self.df is None:
            return pd.DataFrame()
            
        # Primeiro, cria uma máscara para valores que NÃO contêm "SaaS or PaaS"
        delivery_model_mask = (
            self.df['Delivery Model'].isna() |  # Valores nulos
            (~self.df['Delivery Model'].str.contains('SaaS or PaaS', case=False, na=True))  # Não contém "SaaS or PaaS"
        )
        
        issues = self.df[
            (
                (self.df['ACE Opportunity Type'] == 'Partner Sourced Opportunity') |
                (self.df['ACE Opportunity Type'] == 'Partner Sourced For Visibility Only') |
                (self.df['ACE Opportunity Type'] == 'AWS Opportunity Shared with Partner') |
                (self.df['ACE Opportunity Type'].isna())  # Inclui valores nulos
            ) &
            (self.df['Partner Type From Account'] == 'Technology Partner') &
            delivery_model_mask &
            (~self.df['Opportunity: Stage'].isin(['Launched', 'Closed Lost']))
        ].copy()
        
        print(f"🔍 Encontradas {len(issues)} oportunidades que precisam ajustar Delivery Model")
        
        return issues
        
    def generate_html_report(self) -> str:
        """
        Gera relatório HTML simples das oportunidades que precisam correção
        """
        issues = self.find_delivery_model_issues()
        
        if issues.empty:
            return """
<!DOCTYPE html>
<html>
<head>
    <title>Relatório - Delivery Model</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
    </style>
</head>
<body>
    <h1>✅ Nenhuma oportunidade precisa ajustar Delivery Model</h1>
</body>
</html>
"""
            
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Relatório - Delivery Model para Correção</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #f0f0f0;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid #007cba;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        .opp-id {{
            font-weight: bold;
            color: #007cba;
        }}
        .delivery-model {{
            background-color: #fff3cd;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .action {{
            background-color: #d4edda;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
            color: #155724;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
            text-align: center;
        }}
        a {{
            color: #007cba;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>Relatório - Delivery Model para Correção</h1>
    
    <div class="summary">
        <strong>Total de oportunidades encontradas:</strong> {len(issues)}<br>
        <strong>Critério:</strong> Technology Partner + Delivery Model ≠ "SaaS or PaaS" + Stage ativo
    </div>
    
    <table>
        <thead>
            <tr>
                <th>ID Oportunidade</th>
                <th>Nome da Oportunidade</th>
                <th>Cliente</th>
                <th>Parceiro</th>
                <th>Stage</th>
                <th>Delivery Model Atual</th>
                <th>Contato</th>
                <th>Email</th>
                <th>Ação</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for _, opp in issues.iterrows():
            contact_name = opp.get('APN Partner Sales Contact Name', 'N/A')
            if pd.isna(contact_name):
                contact_name = 'N/A'
            
            # Cria o link para o Salesforce
            opp_id_18char = opp.get('Opportunity: 18 Character Oppty ID', 'N/A')
            opp_name = opp.get('Opportunity: Opportunity Name', 'N/A')
            
            if opp_id_18char != 'N/A' and pd.notna(opp_id_18char):
                salesforce_url = f"https://aws-crm.lightning.force.com/lightning/r/Opportunity/{opp_id_18char}/view"
                opp_name_link = f'<a href="{salesforce_url}" target="_blank">{opp_name}</a>'
            else:
                opp_name_link = opp_name
                
            html_content += f"""
            <tr>
                <td class="opp-id">{opp.get('APN Opportunity Identifier', 'N/A')}</td>
                <td>{opp_name_link}</td>
                <td>{opp.get('Opportunity: Account Name', 'N/A')}</td>
                <td>{opp.get('Partner Account', 'N/A')}</td>
                <td>{opp.get('Opportunity: Stage', 'N/A')}</td>
                <td><span class="delivery-model">{opp.get('Delivery Model', 'N/A')}</span></td>
                <td>{contact_name}</td>
                <td>{opp.get('APN Opportunity Owner Email', 'N/A')}</td>
                <td><span class="action">Alterar para "SaaS or PaaS"</span></td>
            </tr>
"""
        
        html_content += f"""
        </tbody>
    </table>
    
    <div class="footer">
        Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
    </div>
</body>
</html>
"""
        
        return html_content
        
    def save_html_report_to_file(self, filename: str = None):
        """
        Salva o relatório HTML em arquivo
        """
        if filename is None:
            filename = os.path.join(get_dated_results_dir(), "delivery_model_report.html")
        
        html_report = self.generate_html_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_report)
                
        print(f"✅ Relatório HTML salvo em {filename}")

if __name__ == "__main__":
    import sys
    
    # Verifica se foi passado arquivo como parâmetro
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        data_file = "report1755695670497.xls"
    
    # Executa o checker
    checker = DeliveryModelChecker(data_file)
    checker.save_html_report_to_file()
    
    # Mostra preview do relatório
    issues = checker.find_delivery_model_issues()
    if not issues.empty:
        print(f"\n📋 RESUMO:")
        print(f"Total de oportunidades para correção: {len(issues)}")
        date_str = datetime.now().strftime('%Y-%m-%d')
        print(f"Relatório HTML salvo em: results/{date_str}/delivery_model_report.html")
    else:
        print("✅ Nenhuma ação necessária - todas as oportunidades estão corretas!")