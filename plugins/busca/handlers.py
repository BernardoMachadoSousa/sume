"""
Handlers do plugin de busca.
Implementa as funcoes que sao chamadas quando uma intent eh reconhecida.
"""

import os
from typing import List, Dict, Any
from utils.resultado import Resultado
from . import notas, arquivos, ranker, cache, indice
from plugins import seguranca

def buscar_notas_handler(entidade: str) -> Resultado:
    """
    Busca nas notas do vault com base na entidade extraida do comando de voz.
    """
    if not entidade or not entidade.strip():
        return Resultado(False, "O termo de busca nao pode ser vazio.")
    
    entidade = entidade.strip()
    valido, msg = seguranca.validar_comando(entidade)
    if not valido:
        return Resultado(False, f"Termo de busca invalido: {msg}")
    
    if seguranca.detectar_injection(entidade):
        return Resultado(False, "Comando contem padroes suspeitos.")
    
    if not seguranca.pode_processar("buscar_notas"):
        return Resultado(False, "Muitas requisicoes. Tente novamente em alguns segundos.")
    
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
            titulo_limpo = seguranca.limpar_texto(nota['titulo'])
            trecho_limpo = seguranca.limpar_texto(nota['trecho'])
            respostas.append(f"- {titulo_limpo}: {trecho_limpo}")
        
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
    
    entidade = entidade.strip()
    valido, msg = seguranca.validar_comando(entidade)
    if not valido:
        return Resultado(False, f"Termo de busca invalido: {msg}")
    
    if seguranca.detectar_injection(entidade):
        return Resultado(False, "Comando contem padroes suspeitos.")
    
    if not seguranca.pode_processar("buscar_arquivos"):
        return Resultado(False, "Muitas requisicoes. Tente novamente em alguns segundos.")
    
    try:
        resultado_cache = cache.obter_cache(entidade, tipo="arquivos")
        if resultado_cache:
            return Resultado(True, f"Encontrei {len(resultado_cache)} arquivo(s) (do cache).", dados={"arquivos": resultado_cache})
        
        resultados = arquivos.buscar(entidade)
        if not resultados:
            return Resultado(True, f"Nenhum arquivo encontrado para '{entidade}'.")
        
        cache.guardar_cache(entidade, resultados, tipo="arquivos")
        
        resultados_seguros = []
        for arq in resultados:
            caminho = arq.get('caminho', '')
            if seguranca.validar_caminho_arquivo(caminho):
                resultados_seguros.append(arq)
        
        if not resultados_seguros:
            return Resultado(True, "Nenhum arquivo valido encontrado.")
        
        respostas = []
        for arq in resultados_seguros[:5]:
            nome_limpo = seguranca.limpar_texto(arq['nome'])
            respostas.append(f"- {nome_limpo} ({arq['caminho']})")
        
        mensagem = f"Encontrei {len(resultados_seguros)} arquivo(s):\n" + "\n".join(respostas)
        return Resultado(True, mensagem, dados={"arquivos": resultados_seguros})
    except Exception as e:
        return Resultado(False, f"Erro ao buscar arquivos: {str(e)}")
