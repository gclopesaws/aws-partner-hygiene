#!/usr/bin/env python3
"""
Pipeline Analysis Runner - Executa todos os checkers de pipeline
Uso: python3 run_pipeline_analysis.py <arquivo_dados.xls>
"""

import sys
import os
import subprocess
from datetime import datetime

def get_dated_results_dir():
    """Cria e retorna diretório results com data atual"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    results_dir = os.path.join("results", date_str)
    
    # Cria diretório se não existir
    os.makedirs(results_dir, exist_ok=True)
    
    return results_dir

def print_header():
    """Imprime cabeçalho do script"""
    print("="*80)
    print("🔍 AWS PARTNER PIPELINE ANALYSIS")
    print("="*80)
    print(f"Executado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    print()

def print_separator():
    """Imprime separador entre seções"""
    print("-"*80)

def run_delivery_model_checker(data_file):
    """Executa o Delivery Model Checker"""
    print("📋 EXECUTANDO: Delivery Model Checker")
    print("Verificando regras de Delivery Model...")
    print()
    
    try:
        # Muda para o diretório do script
        script_dir = "scripts/delivery model checker"
        script_path = os.path.join(script_dir, "delivery_model_checker.py")
        
        # Executa o script
        result = subprocess.run([
            sys.executable, script_path, data_file
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Delivery Model Checker executado com sucesso!")
            print(result.stdout)
        else:
            print("❌ Erro no Delivery Model Checker:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar Delivery Model Checker: {e}")
        return False
    
    return True

def run_pipeline_hygiene_checker(data_file):
    """Executa o Pipeline Hygiene Checker"""
    print("🔧 EXECUTANDO: Pipeline Hygiene Checker")
    print("Verificando Launch Dates, Stalled Opportunities e Mismatches...")
    print()
    
    try:
        # Muda para o diretório do script
        script_dir = "scripts/launch date checker"
        script_path = os.path.join(script_dir, "pipeline_hygiene_checker.py")
        
        # Executa o script
        result = subprocess.run([
            sys.executable, script_path, data_file
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Pipeline Hygiene Checker executado com sucesso!")
            print(result.stdout)
        else:
            print("❌ Erro no Pipeline Hygiene Checker:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar Pipeline Hygiene Checker: {e}")
        return False
    
    return True

def run_html_generator(data_file):
    """Executa o HTML Email Generator"""
    print("🌐 EXECUTANDO: HTML Email Generator")
    print("Gerando interface web para emails...")
    print()
    
    try:
        # Verifica se o arquivo de emails existe
        date_str = datetime.now().strftime('%Y-%m-%d')
        emails_file = f"results/{date_str}/pipeline_hygiene_emails.txt"
        if not os.path.exists(emails_file):
            print("⚠️  Arquivo de emails não encontrado, pulando geração HTML")
            return False
        
        # Executa o gerador HTML
        script_path = os.path.join("scripts", "html email generator", "html_email_generator.py")
        result = subprocess.run([
            sys.executable, script_path, emails_file
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ HTML Email Generator executado com sucesso!")
            print(result.stdout)
        else:
            print("❌ Erro no HTML Email Generator:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar HTML Email Generator: {e}")
        return False
    
    return True

def run_slack_generator(data_file, no_partner_file=None):
    """Executa o Slack Message Generator"""
    print("📱 EXECUTANDO: Slack Message Generator")
    print("Gerando mensagens consolidadas por AM...")
    print()
    
    try:
        # Executa o gerador de mensagens Slack
        script_path = os.path.join("scripts", "slack message generator", "slack_message_generator.py")
        
        # Adiciona arquivo sem parceiro se fornecido
        cmd_args = [sys.executable, script_path, data_file]
        if no_partner_file and os.path.exists(no_partner_file):
            cmd_args.append(no_partner_file)
            print(f"📋 Incluindo arquivo de oportunidades sem parceiro: {no_partner_file}")
        
        result = subprocess.run(cmd_args, capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Slack Message Generator executado com sucesso!")
            print(result.stdout)
        else:
            print("❌ Erro no Slack Message Generator:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar Slack Message Generator: {e}")
        return False
    
    return True

def run_slack_interface_generator():
    """Executa o Slack Interface Generator"""
    print("🌐 EXECUTANDO: Slack Interface Generator")
    print("Gerando interface web para mensagens Slack...")
    print()
    
    try:
        # Verifica se o arquivo de mensagens Slack existe
        date_str = datetime.now().strftime('%Y-%m-%d')
        slack_messages_file = f"results/{date_str}/slack_messages.txt"
        if not os.path.exists(slack_messages_file):
            print("⚠️  Arquivo de mensagens Slack não encontrado, pulando geração de interface")
            return False
        
        # Executa o gerador de interface Slack
        script_path = os.path.join("scripts", "slack interface generator", "slack_interface_generator.py")
        result = subprocess.run([
            sys.executable, script_path, slack_messages_file
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Slack Interface Generator executado com sucesso!")
            print(result.stdout)
        else:
            print("❌ Erro no Slack Interface Generator:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar Slack Interface Generator: {e}")
        return False
    
    return True

def run_followup_generator(data_file):
    """Executa o Follow-up Generator"""
    print("📧 EXECUTANDO: Follow-up Generator")
    print("Gerando emails de follow-up por parceiro...")
    print()
    
    try:
        # Executa o gerador de follow-up
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

def run_dashboard_generator():
    """Executa o Dashboard Generator"""
    print("📊 EXECUTANDO: Dashboard Generator")
    print("Criando dashboard unificado...")
    print()
    
    try:
        # Executa o gerador de dashboard
        script_path = os.path.join("scripts", "dashboard generator", "dashboard_generator.py")
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Dashboard Generator executado com sucesso!")
            print(result.stdout)
        else:
            print("❌ Erro no Dashboard Generator:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar Dashboard Generator: {e}")
        return False
    
    return True

def show_results():
    """Mostra os arquivos de resultado gerados"""
    print("📁 ARQUIVOS GERADOS:")
    print()
    
    results_dir = "results"
    if os.path.exists(results_dir):
        files = os.listdir(results_dir)
        if files:
            for file in sorted(files):
                file_path = os.path.join(results_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    # Adiciona ícones específicos para cada tipo de arquivo
                    if file.endswith('.html'):
                        icon = "🌐"
                    elif file.endswith('.txt'):
                        icon = "📧" if 'email' in file else "📄"
                    else:
                        icon = "📄"
                    print(f"   {icon} {file} ({size:,} bytes)")
        else:
            print("   ⚠️  Nenhum arquivo encontrado na pasta results")
    else:
        print("   ⚠️  Pasta results não encontrada")
    
    print()

def main():
    """Função principal"""
    print_header()
    
    # Verifica argumentos
    if len(sys.argv) < 2:
        print("❌ ERRO: Arquivo de dados não especificado")
        print()
        print("Uso:")
        print(f"   python3 {sys.argv[0]} <arquivo_com_parceiros.xls> [arquivo_sem_parceiros.xls]")
        print()
        print("Exemplos:")
        print(f"   python3 {sys.argv[0]} ricarger-partner.xls")
        print(f"   python3 {sys.argv[0]} ricarger-partner.xls ricarger-nopartner.xls")
        sys.exit(1)
    
    data_file = sys.argv[1]
    no_partner_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Verifica se o arquivo principal existe
    if not os.path.exists(data_file):
        print(f"❌ ERRO: Arquivo '{data_file}' não encontrado")
        sys.exit(1)
    
    # Verifica se o arquivo sem parceiro existe (se fornecido)
    if no_partner_file and not os.path.exists(no_partner_file):
        print(f"❌ ERRO: Arquivo sem parceiro '{no_partner_file}' não encontrado")
        sys.exit(1)
    
    print(f"📊 Arquivo de dados: {data_file}")
    print(f"📊 Tamanho: {os.path.getsize(data_file):,} bytes")
    
    if no_partner_file:
        print(f"📊 Arquivo sem parceiros: {no_partner_file}")
        print(f"📊 Tamanho: {os.path.getsize(no_partner_file):,} bytes")
    
    print()
    
    # Cria pasta results se não existir
    if not os.path.exists("results"):
        os.makedirs("results")
        print("📁 Pasta 'results' criada")
        print()
    
    success_count = 0
    total_checkers = 7  # Agora são 7 checkers (incluindo follow-up generator)
    
    # Executa Delivery Model Checker
    print_separator()
    if run_delivery_model_checker(data_file):
        success_count += 1
    
    print_separator()
    
    # Executa Pipeline Hygiene Checker
    if run_pipeline_hygiene_checker(data_file):
        success_count += 1
    
    print_separator()
    
    # Executa HTML Email Generator
    if run_html_generator(data_file):
        success_count += 1
    
    print_separator()
    
    # Executa Slack Message Generator
    if run_slack_generator(data_file, no_partner_file):
        success_count += 1
    
    print_separator()
    
    # Executa Slack Interface Generator
    if run_slack_interface_generator():
        success_count += 1
    
    print_separator()
    
    # Executa Follow-up Generator
    if run_followup_generator(data_file):
        success_count += 1
    
    print_separator()
    
    # Executa Dashboard Generator
    if run_dashboard_generator():
        success_count += 1
    
    print_separator()
    
    # Mostra resultados
    show_results()
    
    # Resumo final
    print("🎯 RESUMO DA EXECUÇÃO:")
    print(f"   ✅ Checkers executados com sucesso: {success_count}/{total_checkers}")
    
    if success_count == total_checkers:
        print("   🎉 Todos os checkers foram executados com sucesso!")
        date_str = datetime.now().strftime('%Y-%m-%d')
        print(f"   📧 Emails e relatórios estão prontos na pasta 'results/{date_str}'")
        print(f"   🌐 Interface HTML disponível em: results/{date_str}/pipeline_hygiene_emails.html")
        print(f"   📱 Mensagens Slack disponíveis em: results/{date_str}/slack_messages.txt")
        print(f"   🌐 Interface Slack disponível em: results/{date_str}/slack_interface.html")
        print(f"   📧 Follow-up emails disponíveis em: results/{date_str}/followup_emails.txt")
        print(f"   🌐 Interface Follow-up disponível em: results/{date_str}/followup_emails.html")
        print(f"   📊 Dashboard Unificado disponível em: results/{date_str}/dashboard.html")
    else:
        print("   ⚠️  Alguns checkers falharam. Verifique os erros acima.")
    
    print()
    print("="*80)

if __name__ == "__main__":
    main()