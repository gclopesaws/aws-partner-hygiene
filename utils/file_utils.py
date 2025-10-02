#!/usr/bin/env python3
"""
Utilitários para manipulação de arquivos
Inclui funções robustas para leitura de arquivos com diferentes encodings
"""

import os
from typing import Optional

def read_file_robust(file_path: str, description: str = "arquivo") -> str:
    """
    Lê arquivo tentando diferentes encodings de forma robusta
    
    Args:
        file_path: Caminho para o arquivo
        description: Descrição do arquivo para logs
    
    Returns:
        Conteúdo do arquivo como string
        
    Raises:
        Exception: Se não conseguir ler o arquivo com nenhum encoding
    """
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    # Lista de encodings para tentar, em ordem de preferência
    encodings_to_try = [
        'utf-8',           # Padrão moderno
        'iso-8859-1',      # Latin-1, comum em sistemas antigos
        'cp1252',          # Windows-1252, comum no Windows
        'latin1',          # Alias para iso-8859-1
        'utf-16',          # Unicode 16-bit
        'ascii'            # ASCII puro
    ]
    
    content = None
    successful_encoding = None
    
    # Tenta cada encoding
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            successful_encoding = encoding
            print(f"✅ {description.capitalize()} lido com sucesso usando encoding: {encoding}")
            break
        except UnicodeDecodeError as e:
            print(f"⚠️  Falha ao ler {description} com encoding {encoding}: {e}")
            continue
        except Exception as e:
            print(f"❌ Erro inesperado ao ler {description} com encoding {encoding}: {e}")
            continue
    
    # Se nenhum encoding funcionou, tenta leitura binária com fallback
    if content is None:
        try:
            print(f"🔄 Tentando leitura binária para {description}...")
            with open(file_path, 'rb') as f:
                raw_content = f.read()
            
            # Tenta decodificar como UTF-8 ignorando erros
            content = raw_content.decode('utf-8', errors='ignore')
            successful_encoding = 'utf-8 (com erros ignorados)'
            print(f"⚠️  {description.capitalize()} lido com UTF-8 ignorando caracteres inválidos")
            
        except Exception as e:
            raise Exception(f"❌ Não foi possível ler o {description} {file_path} com nenhum método: {e}")
    
    if content is None:
        raise Exception(f"❌ Falha completa na leitura do {description} {file_path}")
    
    # Log de sucesso com estatísticas
    file_size = os.path.getsize(file_path)
    content_length = len(content)
    print(f"📊 {description.capitalize()} processado:")
    print(f"   📁 Arquivo: {os.path.basename(file_path)}")
    print(f"   📏 Tamanho: {file_size:,} bytes")
    print(f"   📝 Conteúdo: {content_length:,} caracteres")
    print(f"   🔤 Encoding: {successful_encoding}")
    
    return content

def write_file_safe(file_path: str, content: str, description: str = "arquivo") -> bool:
    """
    Escreve arquivo de forma segura com encoding UTF-8
    
    Args:
        file_path: Caminho para o arquivo
        content: Conteúdo a ser escrito
        description: Descrição do arquivo para logs
    
    Returns:
        True se sucesso, False caso contrário
    """
    
    try:
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Escreve arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Log de sucesso
        file_size = os.path.getsize(file_path)
        print(f"✅ {description.capitalize()} salvo com sucesso:")
        print(f"   📁 Arquivo: {os.path.basename(file_path)}")
        print(f"   📏 Tamanho: {file_size:,} bytes")
        print(f"   🔤 Encoding: UTF-8")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar {description} {file_path}: {e}")
        return False

def get_file_info(file_path: str) -> dict:
    """
    Obtém informações detalhadas sobre um arquivo
    
    Args:
        file_path: Caminho para o arquivo
    
    Returns:
        Dicionário com informações do arquivo
    """
    
    if not os.path.exists(file_path):
        return {"exists": False, "error": "Arquivo não encontrado"}
    
    try:
        stat = os.stat(file_path)
        
        return {
            "exists": True,
            "name": os.path.basename(file_path),
            "path": file_path,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": stat.st_mtime,
            "is_readable": os.access(file_path, os.R_OK),
            "is_writable": os.access(file_path, os.W_OK)
        }
        
    except Exception as e:
        return {"exists": True, "error": str(e)}

def validate_file_encoding(file_path: str) -> dict:
    """
    Valida e detecta o encoding de um arquivo
    
    Args:
        file_path: Caminho para o arquivo
    
    Returns:
        Dicionário com informações de encoding
    """
    
    if not os.path.exists(file_path):
        return {"valid": False, "error": "Arquivo não encontrado"}
    
    encodings_to_test = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
    results = {}
    
    for encoding in encodings_to_test:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            results[encoding] = {
                "valid": True,
                "content_length": len(content),
                "error": None
            }
        except UnicodeDecodeError as e:
            results[encoding] = {
                "valid": False,
                "content_length": 0,
                "error": str(e)
            }
        except Exception as e:
            results[encoding] = {
                "valid": False,
                "content_length": 0,
                "error": f"Erro inesperado: {str(e)}"
            }
    
    # Determina o melhor encoding
    valid_encodings = [enc for enc, result in results.items() if result["valid"]]
    best_encoding = valid_encodings[0] if valid_encodings else None
    
    return {
        "valid": len(valid_encodings) > 0,
        "best_encoding": best_encoding,
        "valid_encodings": valid_encodings,
        "results": results
    }