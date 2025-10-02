#!/usr/bin/env python3
"""
Utilitário para gerenciar diretórios de resultados
Suporta tanto execução via CLI quanto via Streamlit com diretórios específicos por execução
"""

import os
from datetime import datetime

def get_results_dir():
    """
    Retorna o diretório de resultados apropriado:
    - Se executado via Streamlit: usa PIPELINE_RESULTS_DIR (diretório específico da execução)
    - Se executado via CLI: usa results/YYYY-MM-DD (comportamento original)
    """
    # Verifica se foi definido um diretório específico (via Streamlit)
    pipeline_results_dir = os.environ.get('PIPELINE_RESULTS_DIR')
    
    if pipeline_results_dir:
        # Executado via Streamlit - usa diretório específico da execução
        os.makedirs(pipeline_results_dir, exist_ok=True)
        return pipeline_results_dir
    else:
        # Executado via CLI - usa comportamento original
        date_str = datetime.now().strftime('%Y-%m-%d')
        results_dir = os.path.join("results", date_str)
        os.makedirs(results_dir, exist_ok=True)
        return results_dir

def get_dated_results_dir():
    """
    Função de compatibilidade - mantém nome original
    """
    return get_results_dir()