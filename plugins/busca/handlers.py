"""
Handlers do plugin de busca.
Implementa as funções que são chamadas quando uma intent é reconhecida.
"""

import os
from typing import List, Dict, Any
from utils.resultado import Resultado
from . import notas, arquivos, ranker

def buscar_notas_handler(entidade: str) -> Resultado:
    """
    Busca nas notas do vault com base na entidade extraída do comando de voz.
    """
    if not entidade or not entidade.strip():
        return Resultado(False, "O termo de busca não pode ser vazio.")
    
    try:
        resultados = notas.buscar(entidade)
        if not resultados:
            return Resultado(True, f"Nenhuma nota encontrada para '{entidade}'.")
        
        respostas = []
        for nota in resultados[:5]:
            respostas.append(f"- {nota['titulo']}: {nota['trecho']}")
        
        mensagem = f"Encontrei {len(resultados)} nota(s):\n" + "\n".join(respostas)
        return Resultado(True, mensagem, dados={"notas": resultados})
    except Exception as e:
        return Resultado(False, f"Erro ao buscar nas notas: {str(e)}")

def buscar_arquivos_handler(entidade: str) -> Resultado:
    """
    Busca por arquivos no computador com base na entidade extraída do comando de voz.
    """
    if not entidade or not entidade.strip():
        return Resultado(False, "O termo de busca não pode ser vazio.")
    
    try:
        resultados = arquivos.buscar(entidade)
        if not resultados:
            return Resultado(True, f"Nenhum arquivo encontrado para '{entidade}'.")
        
        respostas = []
        for arq in resultados[:5]:
            respostas.append(f"- {arq['nome']} ({arq['caminho']})")
        
        mensagem = f"Encontrei {len(resultados)} arquivo(s):\n" + "\n".join(respostas)
        return Resultado(True, mensagem, dados={"arquivos": resultados})
    except Exception as e:
        return Resultado(False, f"Erro ao buscar arquivos: {str(e)}")