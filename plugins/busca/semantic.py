"""
Busca semântica usando embeddings do Ollama.
Melhora a relevância dos resultados ao comparar similaridade semântica.
"""

import os
import json
from typing import List, Dict, Any, Optional
from utils.logger import info as log_info, erro as log_erro


def _obter_embedding(texto: str) -> Optional[List[float]]:
    """
    Gera um embedding para um texto usando Ollama (se disponível).
    Retorna None se Ollama não estiver disponível.
    """
    try:
        import ollama
        
        response = ollama.embeddings(
            model="nomic-embed-text",
            prompt=texto
        )
        return response.get("embedding")
    except Exception as e:
        log_erro("semantic", f"Erro ao gerar embedding: {e}")
        return None


def _similaridade_coseno(v1: List[float], v2: List[float]) -> float:
    """
    Calcula a similaridade de cosseno entre dois vetores.
    Retorna um valor entre 0 (muito diferente) e 1 (idêntico).
    """
    if not v1 or not v2:
        return 0.0
    
    if len(v1) != len(v2):
        return 0.0
    
    import math
    
    # Produto escalar
    dot_product = sum(a * b for a, b in zip(v1, v2))
    
    # Magnitudes
    mag_v1 = math.sqrt(sum(a * a for a in v1))
    mag_v2 = math.sqrt(sum(b * b for b in v2))
    
    if mag_v1 == 0 or mag_v2 == 0:
        return 0.0
    
    return dot_product / (mag_v1 * mag_v2)


def enriquecer_com_embeddings(resultados: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Enriquece resultados com scores de similaridade semântica.
    Se Ollama não estiver disponível, retorna os resultados sem modificação.
    """
    query_embedding = _obter_embedding(query)
    
    if query_embedding is None:
        return resultados
    
    for resultado in resultados:
        texto = resultado.get("trecho", "") or resultado.get("conteudo", "")
        
        if not texto:
            resultado["semantic_score"] = 0.0
            continue
        
        texto_embedding = _obter_embedding(texto[:500])
        
        if texto_embedding is None:
            resultado["semantic_score"] = 0.0
            continue
        
        similaridade = _similaridade_coseno(query_embedding, texto_embedding)
        resultado["semantic_score"] = similaridade
    
    return resultados


def combinar_scores(resultados: List[Dict[str, Any]], peso_tfidf: float = 0.5) -> List[Dict[str, Any]]:
    """
    Combina scores de TF-IDF e semântica em um score final.
    peso_tfidf: peso do score TF-IDF (0.0 a 1.0), o resto vai para semantic_score.
    """
    peso_semantic = 1.0 - peso_tfidf
    
    for resultado in resultados:
        tfidf_score = resultado.get("score", 0.0)
        semantic_score = resultado.get("semantic_score", 0.0)
        
        score_final = (tfidf_score * peso_tfidf) + (semantic_score * peso_semantic)
        resultado["combined_score"] = score_final
    
    resultados.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
    
    return resultados
