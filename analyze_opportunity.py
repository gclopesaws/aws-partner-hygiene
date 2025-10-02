#!/usr/bin/env python3
"""
Script para analisar a oportunidade 006RU00000GBKVFYA5 no arquivo Excel
"""

import pandas as pd
import sys

def analyze_opportunity():
    # Carrega o arquivo Excel (que pode ser HTML disfarçado)
    try:
        # Tenta diferentes encodings para HTML
        encodings = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_html('report1758543270930.xls', encoding=encoding)[0]
                print(f"Arquivo carregado com encoding: {encoding}")
                break
            except:
                continue
        
        if df is None:
            # Se HTML não funcionou, tenta Excel
            try:
                df = pd.read_excel('report1758543270930.xls', engine='openpyxl')
            except:
                df = pd.read_excel('report1758543270930.xls', engine='xlrd')
                
    except Exception as e:
        print(f"Erro ao carregar arquivo: {e}")
        return

    print('Colunas disponíveis:')
    for i, col in enumerate(df.columns):
        print(f'{i}: {col}')

    print(f'\nTotal de linhas: {len(df)}')

    # Busca pela oportunidade específica
    target_id = '006RU00000GBKVFYA5'
    matching_rows = df[df['Opportunity: 18 Character Oppty ID'] == target_id]

    print(f'\nOportunidades encontradas com ID {target_id}: {len(matching_rows)}')

    if len(matching_rows) > 0:
        print('\nDetalhes das oportunidades encontradas:')
        for idx, row in matching_rows.iterrows():
            print(f'\nLinha {idx}:')
            print(f'  ID: {row.get("Opportunity: 18 Character Oppty ID", "N/A")}')
            print(f'  Nome: {row.get("Opportunity: Opportunity Name", "N/A")}')
            print(f'  Partner: {row.get("Partner Account", "N/A")}')
            print(f'  APN Partner Stage: {row.get("APN Partner Reported Stage", "N/A")}')
            print(f'  AWS Stage: {row.get("Opportunity: Stage", "N/A")}')
            print(f'  Owner: {row.get("Opportunity Owner Name", "N/A")}')
            
        # Análise da regra check_shared_but_not_accepted (CAMPO CORRETO)
        print('\n=== ANÁLISE DA REGRA check_shared_but_not_accepted ===')
        print('USANDO CAMPO CORRETO: APN Partner Reported Status')
        
        for idx, row in matching_rows.iterrows():
            partner_status = row.get('APN Partner Reported Status', '')
            partner_stage = row.get('APN Partner Reported Stage', '')
            print(f'\nOportunidade {idx}:')
            print(f'  APN Partner Reported Status: "{partner_status}"')
            print(f'  APN Partner Reported Stage: "{partner_stage}"')
            print(f'  Status é "Rejected"? {partner_status == "Rejected"}')
            
            if partner_status == 'Rejected':
                # Buscar outras oportunidades com mesmo ID
                same_id_mask = (df['Opportunity: 18 Character Oppty ID'] == target_id)
                same_id_opps = df[same_id_mask & (df.index != idx)]
                
                print(f'  Outras oportunidades com mesmo ID: {len(same_id_opps)}')
                
                if len(same_id_opps) == 0:
                    print('  Cenário: Oportunidade única rejeitada - DEVERIA APLICAR REGRA')
                else:
                    print('  Outras oportunidades encontradas:')
                    for other_idx, other_row in same_id_opps.iterrows():
                        other_status = other_row.get('APN Partner Reported Status', '')
                        print(f'    Linha {other_idx}: Partner Status = "{other_status}"')
                    
                    all_rejected = all(same_id_opps['APN Partner Reported Status'] == 'Rejected')
                    print(f'  Todas as outras também são "Rejected"? {all_rejected}')
                    
                    if all_rejected:
                        print('  Cenário: Todas rejeitadas - DEVERIA APLICAR REGRA')
                    else:
                        print('  Cenário: Nem todas rejeitadas - NÃO APLICA REGRA')
    else:
        print(f'Nenhuma oportunidade encontrada com ID {target_id}')
        print('\nVerificando se há IDs similares...')
        similar_ids = df[df['Opportunity: 18 Character Oppty ID'].str.contains('006RU', na=False)]
        print(f'IDs que contêm "006RU": {len(similar_ids)}')
        if len(similar_ids) > 0:
            print('IDs similares encontrados:')
            for idx, row in similar_ids.iterrows():
                print(f'  {row.get("Opportunity: 18 Character Oppty ID", "N/A")}')

    # Verificar se há oportunidades com status "Rejected" no campo correto
    print('\n=== VERIFICANDO OPORTUNIDADES COM STATUS "Rejected" ===')
    print('CAMPO CORRETO: APN Partner Reported Status')
    rejected_opps = df[df['APN Partner Reported Status'] == 'Rejected']
    print(f'Total de oportunidades com APN Partner Reported Status = "Rejected": {len(rejected_opps)}')
    
    if len(rejected_opps) > 0:
        print('\nPrimeiras 5 oportunidades rejeitadas:')
        for idx, row in rejected_opps.head().iterrows():
            print(f'  Linha {idx}: {row.get("Opportunity: 18 Character Oppty ID", "N/A")} - {row.get("Partner Account", "N/A")}')
    
    # Verificar todos os valores únicos de APN Partner Reported Status
    print('\n=== VALORES ÚNICOS DE APN Partner Reported Status ===')
    unique_status = df['APN Partner Reported Status'].value_counts(dropna=False)
    print(unique_status)
    
    # Também mostrar APN Partner Reported Stage para comparação
    print('\n=== VALORES ÚNICOS DE APN Partner Reported Stage (para comparação) ===')
    unique_stages = df['APN Partner Reported Stage'].value_counts(dropna=False)
    print(unique_stages)

if __name__ == "__main__":
    analyze_opportunity()