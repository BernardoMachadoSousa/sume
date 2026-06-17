"""
Sistema de logs do Sumé.
Registra comandos, intenções, resultados e erros.
"""

import os
from datetime import datetime

LOG_FILE = "dados/sume.log"

def _escrever(linha: str):
    os.makedirs("dados", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

def comando(original: str, transcrito: str):
    _escrever(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] COMANDO: original='{original}' transcrito='{transcrito}'")

def intent(intencao: str, alvo: str, confianca: float = 1.0):
    _escrever(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INTENT: {intencao} -> '{alvo}' (confianca={confianca})")

def resultado(sucesso: bool, mensagem: str, tempo_ms: float = 0):
    status = "SUCESSO" if sucesso else "FALHA"
    _escrever(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] RESULTADO: {status} | {mensagem} | {tempo_ms:.0f}ms")

def erro(modulo: str, erro_msg: str):
    _escrever(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERRO [{modulo}]: {erro_msg}")