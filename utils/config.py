"""
Módulo de configurações do Sumé.
Carrega e salva preferências em dados/config.json.
"""

import json
import os
import threading
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
    "caminho_obsidian": r"C:\Users\Bernardo Jonas\Documents\Obsidian Vault",  # Pasta principal do Vault
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

_config_cache = None
_config_lock = threading.Lock()

def carregar() -> dict:
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache.copy()
    
    with _config_lock:
        if _config_cache is not None:
            return _config_cache.copy()
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    _config_cache = {**PADRAO, **dados}
                    return _config_cache.copy()
            except (json.JSONDecodeError, OSError) as e:
                log_erro("config", f"config.json corrompido/ilegível, usando padrão: {e}")
        
        _config_cache = PADRAO.copy()
        return _config_cache.copy()

def salvar(config: dict):
    global _config_cache
    
    os.makedirs("dados", exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    with _config_lock:
        _config_cache = {**PADRAO, **config}

def get(chave: str, padrao=None):
    config = carregar()
    return config.get(chave, padrao)

def set(chave: str, valor):
    config = carregar()
    config[chave] = valor
    salvar(config)

def limpar_cache():
    """Limpa o cache de configurações (útil para testes)."""
    global _config_cache
    with _config_lock:
        _config_cache = None