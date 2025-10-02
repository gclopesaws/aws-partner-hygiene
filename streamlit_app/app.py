#!/usr/bin/env python3
"""
AWS Partner Pipeline Analysis - Interface Streamlit
Interface web simples para execução da análise de pipeline sem linha de comando
"""

import streamlit as st
import pandas as pd
import os
import sys
import subprocess
import tempfile
import zipfile
import io
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import uuid
import hashlib

# Configuração da página
st.set_page_config(
    page_title="AWS Partner Pipeline Analysis",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adiciona o diretório raiz ao path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

def get_session_id():
    """Gera ou recupera ID único da sessão para isolamento entre usuários"""
    if 'session_id' not in st.session_state:
        # Cria ID único baseado em timestamp + random para evitar colisões
        session_data = f"{datetime.now().isoformat()}_{uuid.uuid4().hex[:8]}"
        st.session_state.session_id = hashlib.md5(session_data.encode()).hexdigest()[:12]
    return st.session_state.session_id

def get_dated_results_dir(create_execution_subdir=False):
    """Cria e retorna diretório results com data atual e isolamento por sessão"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    base_results_dir = root_dir / "results" / date_str
    
    if create_execution_subdir:
        # Cria subdiretório único para esta execução com ID da sessão
        timestamp = datetime.now().strftime('%Hh%Mm%Ss')
        session_id = get_session_id()
        execution_dir = base_results_dir / f"run_{timestamp}_{session_id}"
        execution_dir.mkdir(parents=True, exist_ok=True)
        return execution_dir
    else:
        # Comportamento original para compatibilidade - NUNCA deve ser usado para ZIP
        base_results_dir.mkdir(parents=True, exist_ok=True)
        return base_results_dir

def cleanup_old_results(days_to_keep=7):
    """Remove resultados antigos para economizar espaço"""
    try:
        results_base = root_dir / "results"
        if not results_base.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for date_dir in results_base.iterdir():
            if date_dir.is_dir() and date_dir.name.count('-') == 2:  # formato YYYY-MM-DD
                try:
                    dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d')
                    if dir_date < cutoff_date:
                        shutil.rmtree(date_dir)
                except (ValueError, OSError):
                    # Ignora diretórios com nomes inválidos ou erros de remoção
                    continue
    except Exception:
        # Falha silenciosa na limpeza para não afetar funcionalidade principal
        pass

def save_uploaded_file(uploaded_file, temp_dir):
    """Salva arquivo enviado em diretório temporário"""
    if uploaded_file is not None:
        file_path = temp_dir / uploaded_file.name
        
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Reset file pointer again for future reads
        uploaded_file.seek(0)
        
        return file_path
    return None

def validate_uploaded_file(uploaded_file):
    """Valida arquivo enviado"""
    if uploaded_file is None:
        return False, "Nenhum arquivo selecionado"
    
    # Verifica extensão
    valid_extensions = ('.xls', '.xlsx', '.html', '.htm')
    if not uploaded_file.name.lower().endswith(valid_extensions):
        return False, f"Invalid format. Use {', '.join(valid_extensions)}"
    
    # Verifica tamanho (50MB max)
    max_size = 50 * 1024 * 1024
    if uploaded_file.size > max_size:
        return False, f"File too large. Maximum {max_size//1024//1024}MB"
    
    return True, "Valid file"

def diagnose_file(uploaded_file):
    """Diagnostica o tipo e formato do arquivo"""
    uploaded_file.seek(0)
    
    # Lê os primeiros bytes para identificar o tipo
    first_bytes = uploaded_file.read(100)
    uploaded_file.seek(0)
    
    file_info = {
        'name': uploaded_file.name,
        'size': uploaded_file.size,
        'extension': uploaded_file.name.split('.')[-1].lower(),
        'first_bytes': first_bytes[:20],
        'is_html': b'<html' in first_bytes.lower() or b'<!doctype' in first_bytes.lower(),
        'is_excel_new': first_bytes.startswith(b'PK'),  # XLSX é um ZIP
        'is_excel_old': first_bytes.startswith(b'\xd0\xcf\x11\xe0'),  # XLS formato antigo
    }
    
    return file_info

def read_excel_robust(file_path_or_buffer):
    """Lê arquivo Excel de forma robusta tentando diferentes engines"""
    
    # Se é um arquivo uploadado, faz diagnóstico
    if hasattr(file_path_or_buffer, 'name'):
        file_info = diagnose_file(file_path_or_buffer)
        
        # Se detectou HTML, vai direto para read_html
        if file_info['is_html']:
            file_path_or_buffer.seek(0)
            return pd.read_html(file_path_or_buffer)[0]
    
    # Tenta diferentes engines para Excel
    engines_to_try = []
    
    # Se é arquivo novo (XLSX), prioriza openpyxl
    if hasattr(file_path_or_buffer, 'name'):
        if file_info['is_excel_new'] or file_info['extension'] in ['xlsx']:
            engines_to_try = ['openpyxl', 'xlrd', None]
        elif file_info['is_excel_old'] or file_info['extension'] in ['xls']:
            engines_to_try = ['xlrd', 'openpyxl', None]
        else:
            engines_to_try = ['openpyxl', 'xlrd', None]
    else:
        engines_to_try = ['openpyxl', 'xlrd', None]
    
    last_error = None
    
    for engine in engines_to_try:
        try:
            if hasattr(file_path_or_buffer, 'seek'):
                file_path_or_buffer.seek(0)
            
            if engine:
                return pd.read_excel(file_path_or_buffer, engine=engine)
            else:
                return pd.read_excel(file_path_or_buffer)
                
        except Exception as e:
            last_error = e
            continue
    
    # Se chegou aqui, nenhum engine funcionou, tenta HTML como último recurso
    try:
        if hasattr(file_path_or_buffer, 'seek'):
            file_path_or_buffer.seek(0)
        return pd.read_html(file_path_or_buffer)[0]
    except Exception as html_error:
        # Retorna erro mais informativo
        error_msg = f"Não foi possível ler o arquivo '{getattr(file_path_or_buffer, 'name', 'unknown')}'.\n"
        error_msg += f"Último erro Excel: {str(last_error)}\n"
        error_msg += f"Erro HTML: {str(html_error)}"
        raise Exception(error_msg)

def preview_file_data(uploaded_file):
    """Mostra preview dos dados do arquivo"""
    try:
        # Reset file pointer
        uploaded_file.seek(0)
        
        # Diagnóstico do arquivo
        file_info = diagnose_file(uploaded_file)
        
        # Mostra informações de diagnóstico
        with st.expander("File Information"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Nome:** {file_info['name']}")
                st.write(f"**Tamanho:** {file_info['size']:,} bytes")
                st.write(f"**Extensão:** .{file_info['extension']}")
            with col2:
                st.write(f"**Detected format:**")
                if file_info['is_html']:
                    st.write("HTML")
                elif file_info['is_excel_new']:
                    st.write("Excel (XLSX)")
                elif file_info['is_excel_old']:
                    st.write("Excel (XLS)")
                else:
                    st.write("Format not identified")
        
        # Usa função robusta para ler o arquivo
        df = read_excel_robust(uploaded_file)
        
        st.success(f"File loaded: {len(df):,} rows, {len(df.columns)} columns")
        
        # Mostra preview
        with st.expander("Data Preview (first 5 rows)"):
            st.dataframe(df.head(), use_container_width=True)
        
        # Verifica colunas importantes
        required_columns = [
            'Opportunity: 18 Character Oppty ID',
            'Opportunity: Opportunity Name',
            'Opportunity Owner Name',
            'Partner Account'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.warning(f"Important columns not found: {', '.join(missing_columns)}")
            with st.expander("All available columns"):
                st.write(list(df.columns))
        else:
            st.success("All important columns found")
        
        return True, df
        
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        
        # Mostra diagnóstico mesmo com erro
        try:
            file_info = diagnose_file(uploaded_file)
            st.info("**File diagnosis:**")
            st.info(f"• Extension: .{file_info['extension']}")
            st.info(f"• Size: {file_info['size']:,} bytes")
            if file_info['is_html']:
                st.info("• Detected as HTML - try renaming to .html")
            elif file_info['is_excel_new']:
                st.info("• Detected as Excel (XLSX)")
            elif file_info['is_excel_old']:
                st.info("• Detected as Excel (XLS)")
        except:
            pass
        
        st.info("**Troubleshooting tips:**")
        st.info("• Try saving the file as .xlsx (modern Excel)")
        st.info("• Or export as .html from the original system")
        st.info("• Check if the file is not corrupted")
        st.info("• If it's an HTML file, rename the extension to .html")
        
        return False, None

def run_pipeline_module(module_name, script_path, main_file_path, no_partner_file_path=None, execution_results_dir=None):
    """Executa um módulo específico do pipeline"""
    try:
        # Usa diretório de execução específico se fornecido
        results_dir = execution_results_dir if execution_results_dir else get_dated_results_dir()
        
        # Verifica dependências específicas para alguns módulos
        if script_path.name == "html_email_generator.py":
            # HTML Email Generator precisa do arquivo de emails do Pipeline Hygiene
            emails_file = results_dir / "pipeline_hygiene_emails.txt"
            if not emails_file.exists():
                return False, "Arquivo pipeline_hygiene_emails.txt não encontrado. Execute Pipeline Hygiene Checker primeiro."
            cmd_args = [sys.executable, str(script_path), str(emails_file)]
        elif script_path.name == "slack_interface_generator.py":
            # Slack Interface Generator precisa do arquivo de mensagens Slack
            slack_file = results_dir / "slack_messages.txt"
            if not slack_file.exists():
                return False, "Arquivo slack_messages.txt não encontrado. Execute Slack Message Generator primeiro."
            cmd_args = [sys.executable, str(script_path), str(slack_file)]
        else:
            # Módulos normais
            cmd_args = [sys.executable, str(script_path), str(main_file_path)]
            if no_partner_file_path and script_path.name == "slack_message_generator.py":
                cmd_args.append(str(no_partner_file_path))
        
        # Configura ambiente para melhor tratamento de encoding
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Define diretório de resultados específico da execução
        if execution_results_dir:
            env['PIPELINE_RESULTS_DIR'] = str(execution_results_dir)
        
        result = subprocess.run(
            cmd_args,
            cwd=str(root_dir),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos timeout
            env=env
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            # Tenta decodificar stderr se houver problemas de encoding
            error_msg = result.stderr
            if not error_msg and result.stdout:
                error_msg = result.stdout
            
            # Se ainda houver problemas de encoding, tenta diferentes abordagens
            if "UnicodeDecodeError" in error_msg or "codec can't decode" in error_msg:
                error_msg += "\n\n💡 Dica: Problema de encoding detectado. Tentando correção automática..."
                
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, "Timeout: Módulo demorou mais de 5 minutos para executar"
    except UnicodeDecodeError as e:
        return False, f"Erro de encoding: {str(e)}\n💡 Tente salvar seus arquivos com encoding UTF-8"
    except Exception as e:
        return False, f"Erro ao executar módulo: {str(e)}"

def run_complete_analysis(main_file_path, no_partner_file_path=None):
    """Executa análise completa do pipeline"""
    
    # Cria diretório único para esta execução
    execution_results_dir = get_dated_results_dir(create_execution_subdir=True)
    execution_id = execution_results_dir.name  # ex: "run_14h30m15s"
    
    # Armazena informações da execução no session state
    st.session_state.execution_id = execution_id
    st.session_state.execution_results_dir = str(execution_results_dir)
    st.session_state.generated_files_list = []
    
    st.info(f"📁 Execução: {execution_id}")
    st.info(f"📂 Diretório: {execution_results_dir}")
    
    # Módulos a serem executados
    modules = [
        {
            'name': 'Delivery Model Checker',
            'script': 'scripts/delivery model checker/delivery_model_checker.py',
            'description': 'Verificando Delivery Models...'
        },
        {
            'name': 'Pipeline Hygiene Checker', 
            'script': 'scripts/launch date checker/pipeline_hygiene_checker.py',
            'description': 'Analisando Launch Dates e Hygiene...'
        },
        {
            'name': 'Slack Message Generator',
            'script': 'scripts/slack message generator/slack_message_generator.py', 
            'description': 'Gerando mensagens para Slack...'
        },
        {
            'name': 'Follow-up Generator',
            'script': 'scripts/follow-up generator/followup_generator.py',
            'description': 'Criando emails de follow-up...'
        },
        {
            'name': 'HTML Email Generator',
            'script': 'scripts/html email generator/html_email_generator.py',
            'description': 'Gerando interfaces HTML...',
            'depends_on': 'Pipeline Hygiene Checker'
        },
        {
            'name': 'Slack Interface Generator', 
            'script': 'scripts/slack interface generator/slack_interface_generator.py',
            'description': 'Criando interface Slack...',
            'depends_on': 'Slack Message Generator'
        },
        {
            'name': 'Dashboard Generator',
            'script': 'scripts/dashboard generator/dashboard_generator.py',
            'description': 'Montando dashboard final...'
        }
    ]
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_container = st.container()
    
    results = []
    total_modules = len(modules)
    
    for i, module in enumerate(modules):
        # Atualiza status
        progress = (i + 1) / total_modules
        progress_bar.progress(progress)
        
        with status_container:
            st.info(f"Processing: {module['description']}")
        
        # Executa módulo
        script_path = root_dir / module['script']
        success, output = run_pipeline_module(
            module['name'], 
            script_path, 
            main_file_path, 
            no_partner_file_path,
            execution_results_dir
        )
        
        # Debug: mostra output do módulo
        if output and len(output.strip()) > 0:
            with st.expander(f"Detailed Log - {module['name']}"):
                st.text(output)
        
        # Verifica se arquivos esperados foram gerados e os adiciona à lista
        expected_files = {
            'Delivery Model Checker': ['delivery_model_report.html'],
            'Pipeline Hygiene Checker': ['pipeline_hygiene_emails.txt'],
            'Slack Message Generator': ['slack_messages.txt'],
            'Follow-up Generator': ['followup_emails.txt'],
            'HTML Email Generator': ['pipeline_hygiene_emails.html'],
            'Slack Interface Generator': ['slack_interface.html'],
            'Dashboard Generator': ['dashboard.html']
        }
        
        if module['name'] in expected_files:
            files_generated = []
            for expected_file in expected_files[module['name']]:
                file_path = execution_results_dir / expected_file
                if file_path.exists():
                    files_generated.append(expected_file)
                    # Adiciona à lista de arquivos gerados nesta execução
                    if expected_file not in st.session_state.generated_files_list:
                        st.session_state.generated_files_list.append(expected_file)
            
            if files_generated:
                with status_container:
                    st.info(f"Files generated: {', '.join(files_generated)}")
        
        results.append({
            'name': module['name'],
            'success': success,
            'output': output
        })
        
        # Mostra resultado
        with status_container:
            if success:
                st.success(f"{module['name']} completed")
            else:
                # Verifica se é erro de dependência
                if "não encontrado" in output and "Execute" in output:
                    st.warning(f"{module['name']}: {output}")
                    # Continua execução mesmo com erro de dependência
                else:
                    st.error(f"Error in {module['name']}: {output}")
                    return False, results
    
    # Finaliza
    progress_bar.progress(1.0)
    with status_container:
        st.success("Analysis completed successfully!")
    
    return True, results

def get_generated_files():
    """Obtém lista de arquivos gerados na execução atual - APENAS da sessão atual"""
    # SEMPRE usa diretório específico da execução - NUNCA faz fallback para pasta geral
    if hasattr(st.session_state, 'execution_results_dir') and st.session_state.execution_results_dir:
        results_dir = Path(st.session_state.execution_results_dir)
        
        # Verifica se o diretório ainda existe
        if not results_dir.exists():
            return []  # Retorna lista vazia se diretório não existe
    else:
        # Se não há execução ativa, retorna lista vazia
        return []
    
    file_mappings = {
        'delivery_model_report.html': {
            'title': 'Delivery Model Report',
            'description': 'Report of opportunities that need Delivery Model adjustment',
            'mime': 'text/html'
        },
        'pipeline_hygiene_emails.txt': {
            'title': 'Pipeline Hygiene Emails',
            'description': 'Emails to partners about necessary corrections',
            'mime': 'text/plain'
        },
        'pipeline_hygiene_emails.html': {
            'title': 'Email Interface',
            'description': 'Web interface for sending emails',
            'mime': 'text/html'
        },
        'slack_messages.txt': {
            'title': 'Slack Messages',
            'description': 'Messages consolidated by Account Manager',
            'mime': 'text/plain'
        },
        'slack_interface.html': {
            'title': 'Slack Interface',
            'description': 'Web interface for Slack messages',
            'mime': 'text/html'
        },
        'followup_emails.txt': {
            'title': 'Follow-up Emails',
            'description': 'Follow-up emails by partner',
            'mime': 'text/plain'
        },
        'followup_emails.html': {
            'title': 'Follow-up Interface',
            'description': 'Web interface for follow-up emails',
            'mime': 'text/html'
        },
        'dashboard.html': {
            'title': 'Unified Dashboard',
            'description': 'Consolidated dashboard with all reports',
            'mime': 'text/html'
        }
    }
    
    generated_files = []
    
    # Se temos lista específica da execução, usa apenas esses arquivos
    if hasattr(st.session_state, 'generated_files_list') and st.session_state.generated_files_list:
        files_to_check = st.session_state.generated_files_list
    else:
        # Fallback: verifica todos os arquivos possíveis
        files_to_check = file_mappings.keys()
    
    for filename in files_to_check:
        if filename in file_mappings:
            file_path = results_dir / filename
            if file_path.exists():
                size = file_path.stat().st_size
                info = file_mappings[filename]
                generated_files.append({
                    'filename': filename,
                    'path': file_path,
                    'title': info['title'],
                    'description': info['description'],
                    'mime': info['mime'],
                    'size': size
                })
    
    return generated_files

def create_results_zip():
    """Cria arquivo ZIP com todos os resultados da execução atual - APENAS da sessão atual"""
    # SEMPRE usa diretório específico da execução - NUNCA faz fallback para pasta geral
    if hasattr(st.session_state, 'execution_results_dir') and st.session_state.execution_results_dir:
        results_dir = Path(st.session_state.execution_results_dir)
        
        # Verifica se o diretório ainda existe
        if not results_dir.exists():
            raise FileNotFoundError("Diretório de resultados não encontrado. Execute uma nova análise.")
    else:
        # Se não há execução ativa, não permite download
        raise ValueError("Nenhuma execução ativa encontrada. Execute uma análise primeiro.")
    
    # Cria ZIP em memória
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Inclui todos os arquivos recursivamente APENAS do diretório específico
        for file_path in results_dir.rglob('*'):
            if file_path.is_file():
                # Mantém estrutura de pastas no ZIP
                relative_path = file_path.relative_to(results_dir)
                zip_file.write(file_path, str(relative_path))
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def main():
    """Função principal da aplicação Streamlit"""
    
    # Limpeza automática de arquivos antigos (executa uma vez por sessão)
    if 'cleanup_done' not in st.session_state:
        cleanup_old_results()
        st.session_state.cleanup_done = True
    
    # Header
    st.title("AWS Partner Pipeline Analysis")
    st.markdown("**Automated analysis of AWS partner pipeline**")
    st.divider()
    
    # Sidebar com informações
    with st.sidebar:
        st.header("How to Use")
        st.markdown("""
        1. **Upload main file** (required)
        2. **Upload no-partner file** (optional)  
        3. **Click 'Execute Analysis'**
        4. **Wait for processing**
        5. **Download results**
        """)
        
        st.header("Included Modules")
        st.markdown("""
        - Delivery Model Report
        - Pipeline Hygiene Emails  
        - Slack Messages
        - Follow-up Generator
        - HTML Interfaces
        - Unified Dashboard
        """)
        
        st.header("Accepted Formats")
        st.markdown("""
        - Excel (.xls, .xlsx)
        - HTML (.html)
        - Maximum size: 50MB
        """)
        
        st.header("Privacy & Security")
        session_id = get_session_id()
        st.markdown(f"""
        🔒 **Session ID:** `{session_id[:8]}...`
        
        - Your results are isolated from other users
        - Downloads contain only your execution files
        - Old results are automatically cleaned up
        """)
        st.caption("Each user session has a unique identifier to prevent file mixing")
    
    # Área principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("File Upload")
        
        # Upload arquivo principal
        main_file = st.file_uploader(
            "Arquivo Principal (com parceiros)",
            type=['xls', 'xlsx', 'html', 'htm'],
            help="Arquivo Excel ou HTML com dados de oportunidades e parceiros"
        )
        
        # Validação e preview do arquivo principal
        main_file_valid = False
        if main_file:
            is_valid, message = validate_uploaded_file(main_file)
            if is_valid:
                preview_success, df = preview_file_data(main_file)
                main_file_valid = preview_success
            else:
                st.error(message)
        
        # Upload arquivo opcional
        no_partner_file = st.file_uploader(
            "Arquivo Sem Parceiros (opcional)",
            type=['xls', 'xlsx', 'html', 'htm'],
            help="Arquivo adicional com oportunidades sem parceiros"
        )
        
        # Validação do arquivo opcional
        if no_partner_file:
            is_valid, message = validate_uploaded_file(no_partner_file)
            if is_valid:
                st.success(f"Valid additional file: {no_partner_file.name}")
            else:
                st.error(message)
    
    with col2:
        st.header("Status")
        
        if main_file:
            st.success(f"Main file: {main_file.name}")
            st.info(f"Size: {main_file.size:,} bytes")
        else:
            st.warning("Main file required")
        
        if no_partner_file:
            st.success(f"Additional file: {no_partner_file.name}")
            st.info(f"Size: {no_partner_file.size:,} bytes")
        
        # Informações da última execução
        base_results_dir = get_dated_results_dir()
        if base_results_dir.exists():
            # Conta execuções do dia
            execution_dirs = [d for d in base_results_dir.iterdir() if d.is_dir() and d.name.startswith('run_')]
            if execution_dirs:
                st.info(f"📁 {len(execution_dirs)} execuções hoje")
                latest_execution = max(execution_dirs, key=lambda x: x.name)
                st.info(f"🕒 Última: {latest_execution.name}")
            else:
                existing_files = list(base_results_dir.glob('*'))
                if existing_files:
                    st.info(f"📁 {len(existing_files)} arquivos na pasta de hoje")
    
    st.divider()
    
    # Botão de execução
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        execute_button = st.button(
            "Execute Complete Analysis", 
            type="primary", 
            disabled=not main_file_valid,
            use_container_width=True
        )
    
    # Processamento
    if execute_button and main_file_valid:
        st.header("Processing in Progress")
        
        # Cria diretório temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Salva arquivos
            main_file_path = save_uploaded_file(main_file, temp_path)
            no_partner_file_path = save_uploaded_file(no_partner_file, temp_path) if no_partner_file else None
            
            # Executa análise
            success, results = run_complete_analysis(main_file_path, no_partner_file_path)
            
            if success:
                # Armazena no session state para persistir após rerun
                st.session_state.analysis_completed = True
                st.session_state.analysis_timestamp = datetime.now()
                st.rerun()
    
    # Seção de resultados
    if getattr(st.session_state, 'analysis_completed', False):
        st.divider()
        st.header("Analysis Complete")
        
        # Informações da execução
        if hasattr(st.session_state, 'execution_id'):
            st.info(f"📁 Execução: {st.session_state.execution_id}")
        if hasattr(st.session_state, 'analysis_timestamp'):
            st.info(f"🕒 Concluída em: {st.session_state.analysis_timestamp.strftime('%d/%m/%Y às %H:%M:%S')}")
        
        # Obtém arquivos gerados
        generated_files = get_generated_files()
        
        if generated_files:
            # Métricas em colunas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Files Generated", len(generated_files))
            with col2:
                total_size = sum(f['size'] for f in generated_files)
                st.metric("Total Size", f"{total_size:,} bytes")
            with col3:
                html_files = len([f for f in generated_files if f['filename'].endswith('.html')])
                st.metric("HTML Interfaces", html_files)
            with col4:
                txt_files = len([f for f in generated_files if f['filename'].endswith('.txt')])
                st.metric("Text Files", txt_files)
            
            st.divider()
            
            # Lista de arquivos gerados (apenas visualização)
            st.subheader("Generated Files")
            
            for file_info in generated_files:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.write(f"**{file_info['title']}**")
                        st.caption(file_info['description'])
                    
                    with col2:
                        if file_info['size'] > 1024:
                            size_str = f"{file_info['size']/1024:.1f} KB"
                        else:
                            size_str = f"{file_info['size']} bytes"
                        st.write(size_str)
            
            # Download completo (ZIP) - Destaque principal
            st.divider()
            st.subheader("Download Results")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                try:
                    zip_data = create_results_zip()
                    # Usa execution_id se disponível, senão usa timestamp atual
                    if hasattr(st.session_state, 'execution_id'):
                        filename_suffix = st.session_state.execution_id
                    else:
                        filename_suffix = datetime.now().strftime('%Y%m%d_%H%M')
                    
                    st.download_button(
                        "Download Complete Package (ZIP)",
                        data=zip_data,
                        file_name=f"pipeline_analysis_{filename_suffix}.zip",
                        mime="application/zip",
                        use_container_width=True,
                        type="primary"
                    )
                    st.caption("Contains all generated reports and HTML interfaces from this execution only")
                    
                    # Mostra informações de segurança
                    session_id = get_session_id()
                    st.caption(f"🔒 Session ID: {session_id[:8]}... (isolated results)")
                    
                except (FileNotFoundError, ValueError) as e:
                    st.error(f"Cannot create download: {str(e)}")
                    st.info("Please run a new analysis to generate fresh results.")
                except Exception as e:
                    st.error(f"Unexpected error creating download: {str(e)}")
                    st.info("Please try running the analysis again.")
            
            # Botão para nova análise
            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("New Analysis", use_container_width=True):
                    # Limpa session state da execução
                    keys_to_clear = [
                        'analysis_completed', 
                        'analysis_timestamp', 
                        'execution_id', 
                        'execution_results_dir', 
                        'generated_files_list'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        
        else:
            st.warning("No files were generated. Please check for errors during processing.")

if __name__ == "__main__":
    main()