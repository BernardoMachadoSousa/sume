"""
Ranker para resultados de busca.
Implementa funções para classificar e melhorar os resultados de busca.
"""

import re
import math
from collections import Counter
from typing import List, Dict, Any

def tfidf_score(term: str, text: str) -> float:
    """
    Calcula uma pontuação simplificada de TF-IDF para um termo em um texto.
    """
    if not term or not text:
        return 0.0
    
    # Normaliza
    term = term.lower()
    text = text.lower()
    
    # Contagem de termos no documento (tf)
    words = re.findall(r'\w+', text)
    if not words:
        return 0.0
    tf = words.count(term) / len(words)
    
    # Vamos usar um idf fixo para simplificar (assumindo que o termo é raro)
    # Em uma implementação real, calcularíamos idf com base em todos os documentos
    idf = math.log(1 + 1)  # log(2) ~ 0.693, assumindo que o termo aparece em metade dos documentos
    
    return tf * idf

def rank_results(results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Classifica uma lista de resultados com base na relevância da consulta.
    Cada resultado deve ter pelo menos os campos: 'titulo' e 'conteudo' (ou similar).
    """
    if not results or not query:
        return results
    
    query_terms = set(re.findall(r'\w+', query.lower()))
    
    for result in results:
        # Combine campos relevantes para pontuação
        text_fields = []
        for field in ['titulo', 'conteudo', 'nome', 'trecho']:
            if field in result and result[field]:
                text_fields.append(str(result[field]))
        
        full_text = " ".join(text_fields)
        
        # Calcula pontuação baseada em TF-IDF para cada termo da consulta
        score = 0.0
        for term in query_terms:
            score += tfidf_score(term, full_text)
        
        # Normaliza pela quantidade de termos da consulta
        if query_terms:
            score /= len(query_terms)
        
        result['score'] = score
    
    # Ordena por pontuação decrescente
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return results