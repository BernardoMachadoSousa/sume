"""
Módulo de configurações do Sumé.
Carrega e salva preferências em dados/config.json.
"""

import json
import os
from utils.logger import erro as log_erro

CONFIG_FILE = "dados/config.json"

PADRAO = {
    "voz": "pt-BR-AntonioNeural",
    "velocidade_fala": "+10%",
    "tema": "dark",
    "modelo_ia": "phi3",  # phi3 ou deepseek
    "atalho_global": "ctrl+space",
    "iniciar_com_windows": False,
    "tempo_escuta_max": 15,
    "silencios_para_parar": 1.2,
    "usar_omniroute": False,  # local por padrão; o gateway remoto é opt-in
    "modelo_omniroute": "SUME-CLAUDE",
    "endpoint_omniroute": "http://localhost:20128/v1",
    "compartilhar_contexto_omniroute": False,  # memória/vault só vão com isso ligado
    "timeout_omniroute": 120,
}

def carregar() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return {**PADRAO, **dados}  # mescla com padrão
        except (json.JSONDecodeError, OSError) as e:
            log_erro("config", f"config.json corrompido/ilegível, usando padrão: {e}")
    return PADRAO.copy()

def salvar(config: dict):
    os.makedirs("dados", exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get(chave: str):
    return carregar().get(chave)

def set(chave: str, valor):
    config = carregar()
    config[chave] = valor
    salvar(config)