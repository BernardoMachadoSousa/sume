"""
Busca nas notas do vault.
"""

import os
import re
from typing import List, Dict, Any
from modulos import vault
from . import ranker, semantic

def buscar(termo: str) -> List[Dict[str, Any]]:
    """
    Busca por `termo` em todas as notas do vault.
    Retorna uma lista de dicionários com chaves: 'titulo', 'trecho', 'caminho'.
    """
    if not termo or not termo.strip():
        return []
    
    termo_lower = termo.lower()
    resultados = []
    
    # Lista todas as notas do vault
    notas = vault.listar()
    for nota in notas:
        caminho = nota["caminho"]
        titulo = nota["titulo"]
        
        # Lê o conteúdo da nota
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
        except Exception:
            continue  # Pula a nota se não puder ler
        
        # Remove o frontmatter (tudo entre --- no início) para buscar apenas no conteúdo
        # Isso é uma simplificação; assume que o frontmatter está no início e termina com uma linha --- 
        lines = conteudo.split('\n')
        if lines and lines[0].strip() == '---':
            # Procura o próximo --- 
            end_idx = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    end_idx = i
                    break
            if end_idx != -1:
                conteudo = '\n'.join(lines[end_idx+1:])
            else:
                # Se não encontrar o segundo ---, assume que todo o resto é conteúdo após a primeira linha
                conteudo = '\n'.join(lines[1:])
        
        # Busca por termo (case-insensitive) no título ou conteúdo
        conteudo_lower = conteudo.lower()
        titulo_lower = titulo.lower()
        
        encontrou_titulo = termo_lower in titulo_lower
        encontrou_conteudo = termo_lower in conteudo_lower
        
        if encontrou_titulo or encontrou_conteudo:
            # Extrai um trecho ao redor do primeiro occurrence (prefere conteúdo)
            if encontrou_conteudo:
                idx = conteudo_lower.find(termo_lower)
                start = max(0, idx - 100)
                end = min(len(conteudo), idx + len(termo) + 100)
                trecho = conteudo[start:end]
                if start > 0:
                    trecho = "..." + trecho
                if end < len(conteudo):
                    trecho = trecho + "..."
            else:
                trecho = conteudo[:150]
                if len(conteudo) > 150:
                    trecho = trecho + "..."
            
            resultados.append({
                "titulo": titulo,
                "trecho": trecho,
                "caminho": caminho
            })
    
    if resultados:
        resultados = ranker.rank_results(resultados, termo)
        resultados = semantic.enriquecer_com_embeddings(resultados, termo)
        resultados = semantic.combinar_scores(resultados, peso_tfidf=0.6)
    
    return resultados