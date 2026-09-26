"""
Handlers do plugin de busca.
Implementa as funcoes que sao chamadas quando uma intent eh reconhecida.
"""

import os
from typing import List, Dict, Any
from utils.resultado import Resultado
from . import notas, arquivos, ranker, cache, indice

def buscar_notas_handler(entidade: str) -> Resultado:
    """
    Busca nas notas do vault com base na entidade extraida do comando de voz.
    """
    if not entidade or not entidade.strip():
        return Resultado(False, "O termo de busca nao pode ser vazio.")
    
    try:
        resultado_cache = cache.obter_cache(entidade, tipo="notas")
        if resultado_cache:
            return Resultado(True, f"Encontrei {len(resultado_cache)} nota(s) (do cache).", dados={"notas": resultado_cache})
        
        resultados = notas.buscar(entidade)
        if not resultados:
            return Resultado(True, f"Nenhuma nota encontrada para '{entidade}'.")
        
        cache.guardar_cache(entidade, resultados, tipo="notas")
        
        respostas = []
        for nota in resultados[:5]:
            respostas.append(f"- {nota['titulo']}: {nota['trecho']}")
        
        mensagem = f"Encontrei {len(resultados)} nota(s):\n" + "\n".join(respostas)
        return Resultado(True, mensagem, dados={"notas": resultados})
    except Exception as e:
        return Resultado(False, f"Erro ao buscar nas notas: {str(e)}")

def buscar_arquivos_handler(entidade: str) -> Resultado:
    """
    Busca por arquivos no computador com base na entidade extraida do comando de voz.
    """
    if not entidade or not entidade.strip():
        return Resultado(False, "O termo de busca nao pode ser vazio.")
    
    try:
        resultado_cache = cache.obter_cache(entidade, tipo="arquivos")
        if resultado_cache:
            return Resultado(True, f"Encontrei {len(resultado_cache)} arquivo(s) (do cache).", dados={"arquivos": resultado_cache})
        
        resultados = arquivos.buscar(entidade)
        if not resultados:
            return Resultado(True, f"Nenhum arquivo encontrado para '{entidade}'.")
        
        cache.guardar_cache(entidade, resultados, tipo="arquivos")
        
        respostas = []
        for arq in resultados[:5]:
            respostas.append(f"- {arq['nome']} ({arq['caminho']})")
        
        mensagem = f"Encontrei {len(resultados)} arquivo(s):\n" + "\n".join(respostas)
        return Resultado(True, mensagem, dados={"arquivos": resultados})
    except Exception as e:
        return Resultado(False, f"Erro ao buscar arquivos: {str(e)}")