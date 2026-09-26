"""
Modulo de filtros e ordenacao para resultados de busca.
Fornece funcoes para filtrar e ordenar resultados de forma flexivel.
"""

from typing import List, Dict, Any, Callable
from enum import Enum

class TipoResultado(Enum):
    NOTA = "nota"
    ARQUIVO = "arquivo"
    TODOS = "todos"

class Ordenacao(Enum):
    RELEVANCIA = "relevancia"
    NOME = "nome"
    DATA = "data"
    TAMANHO = "tamanho"

def filtrar_por_tipo(resultados: Dict[str, List[Dict]], tipo: TipoResultado) -> Dict[str, List[Dict]]:
    """Filtra resultados por tipo (notas, arquivos ou ambos)."""
    if tipo == TipoResultado.TODOS:
        return resultados
    
    filtrado = {}
    if tipo == TipoResultado.NOTA and "notas" in resultados:
        filtrado["notas"] = resultados["notas"]
    elif tipo == TipoResultado.ARQUIVO and "arquivos" in resultados:
        filtrado["arquivos"] = resultados["arquivos"]
    
    return filtrado

def filtrar_por_relevancia(resultados: Dict[str, List[Dict]], min_relevancia: float = 0.0, max_relevancia: float = 1.0) -> Dict[str, List[Dict]]:
    """Filtra resultados por intervalo de relevancia."""
    filtrado = {}
    
    if "notas" in resultados:
        filtrado["notas"] = [
            nota for nota in resultados["notas"]
            if min_relevancia <= nota.get("relevancia", 0.5) <= max_relevancia
        ]
    
    if "arquivos" in resultados:
        filtrado["arquivos"] = [
            arq for arq in resultados["arquivos"]
            if min_relevancia <= arq.get("relevancia", 0.5) <= max_relevancia
        ]
    
    return filtrado

def ordenar_resultados(resultados: Dict[str, List[Dict]], ordem: Ordenacao, descendente: bool = True) -> Dict[str, List[Dict]]:
    """Ordena resultados por diferentes criterios."""
    ordenado = {}
    
    def ordenar_lista(items, key_fn):
        return sorted(items, key=key_fn, reverse=descendente)
    
    if ordem == Ordenacao.RELEVANCIA:
        if "notas" in resultados:
            ordenado["notas"] = ordenar_lista(resultados["notas"], lambda x: x.get("relevancia", 0))
        if "arquivos" in resultados:
            ordenado["arquivos"] = ordenar_lista(resultados["arquivos"], lambda x: x.get("relevancia", 0))
    
    elif ordem == Ordenacao.NOME:
        if "notas" in resultados:
            ordenado["notas"] = ordenar_lista(resultados["notas"], lambda x: x.get("titulo", "").lower())
        if "arquivos" in resultados:
            ordenado["arquivos"] = ordenar_lista(resultados["arquivos"], lambda x: x.get("nome", "").lower())
    
    elif ordem == Ordenacao.DATA:
        if "notas" in resultados:
            ordenado["notas"] = ordenar_lista(resultados["notas"], lambda x: x.get("data_modificacao", ""))
        if "arquivos" in resultados:
            ordenado["arquivos"] = ordenar_lista(resultados["arquivos"], lambda x: x.get("data_modificacao", ""))
    
    elif ordem == Ordenacao.TAMANHO:
        if "arquivos" in resultados:
            ordenado["arquivos"] = ordenar_lista(resultados["arquivos"], lambda x: x.get("tamanho", 0))
    
    return ordenado

def limitar_resultados(resultados: Dict[str, List[Dict]], limite: int = 10) -> Dict[str, List[Dict]]:
    """Limita numero de resultados retornados."""
    limitado = {}
    
    if "notas" in resultados:
        limitado["notas"] = resultados["notas"][:limite]
    
    if "arquivos" in resultados:
        limitado["arquivos"] = resultados["arquivos"][:limite]
    
    return limitado

def aplicar_filtros(resultados: Dict[str, List[Dict]], 
                   tipo: TipoResultado = TipoResultado.TODOS,
                   min_relevancia: float = 0.0,
                   max_relevancia: float = 1.0,
                   ordem: Ordenacao = Ordenacao.RELEVANCIA,
                   descendente: bool = True,
                   limite: int = None) -> Dict[str, List[Dict]]:
    """Aplica multiplos filtros aos resultados de forma encadeada."""
    resultado = resultados.copy()
    
    resultado = filtrar_por_tipo(resultado, tipo)
    resultado = filtrar_por_relevancia(resultado, min_relevancia, max_relevancia)
    resultado = ordenar_resultados(resultado, ordem, descendente)
    
    if limite:
        resultado = limitar_resultados(resultado, limite)
    
    return resultado
