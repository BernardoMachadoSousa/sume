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
    "modelo_ia": "groq",  # groq (nuvem) ou ollama (local)
    "atalho_global": "ctrl+space",
    "iniciar_com_windows": False,
    "tempo_escuta_max": 15,
    "silencios_para_parar": 1.2,
    "compartilhar_conteudo_nuvem": False,  # enviar trechos de notas/arquivos para IA remota?
    "groq_api_key": "",  # chave da Groq API (opcional; pode usar env GROQ_API_KEY)
    "pastas_busca": [
        "Documents",
        "Desktop",
        "Downloads",
        "Pictures"
    ],
    "extensoes_busca": [
        ".txt", ".md", ".pdf", ".docx", ".xlsx", ".pptx",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp",
        ".zip", ".rar", ".7z",
        ".py", ".js", ".ts", ".html", ".css",
        ".json", ".csv", ".xml", ".yaml", ".yml"
    ],
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

def get(chave: str, padrao=None):
    return carregar().get(chave, padrao)

def set(chave: str, valor):
    config = carregar()
    config[chave] = valor
    salvar(config)