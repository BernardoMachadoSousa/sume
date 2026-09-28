import subprocess
import webbrowser
import os
import json
import re
from utils.logger import erro as log_erro

CATALOGO_CACHE = "dados/catalogo_programas.json"

# Whitelist de executáveis permitidos - evita command injection
WHITELIST_EXE = {
    "calc.exe", "calculadora.exe",
    "notepad.exe", "notas.exe",
    "cmd.exe", "terminal.exe",
    "explorer.exe", "explorador.exe",
    "winword.exe", "word.exe",
    "excel.exe",
    "powerpnt.exe", "powerpoint.exe",
    "mspaint.exe", "paint.exe",
}

WHITELIST_PROC = {
    "CalculatorApp.exe", "calc.exe",
    "notepad.exe",
    "cmd.exe", "terminal.exe",
    "explorer.exe",
    "chrome.exe", "firefox.exe", "msedge.exe",
    "winword.exe", "excel.exe",
}

def _carregar_catalogo() -> dict:
    if os.path.exists(CATALOGO_CACHE):
        try:
            with open(CATALOGO_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log_erro("automacoes", f"Cache de catálogo corrompido/ilegível: {e}")
    return _gerar_catalogo()

def _gerar_catalogo() -> dict:
    catalogo = {}
    pastas = [
        os.path.expanduser("~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs"),
        "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs",
    ]
    for pasta in pastas:
        try:
            for raiz, _, arquivos in os.walk(pasta):
                for arq in arquivos:
                    nome = arq.lower().replace(".lnk", "").replace(".url", "")
                    caminho = os.path.join(raiz, arq)
                    catalogo[nome] = caminho
        except Exception as e:
            log_erro("automacoes", f"Catálogo: {e}")
    
    os.makedirs("dados", exist_ok=True)
    with open(CATALOGO_CACHE, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)
    
    return catalogo

CATALOGO = _carregar_catalogo()


def _abrir(nome: str) -> str:
    n = nome.lower().strip()
    n = re.sub(r'[^\w\s]', '', n)
    
    exes = {
        "calc": "calc.exe", "calculadora": "calc.exe",
        "notepad": "notepad.exe", "notas": "notepad.exe", "bloco": "notepad.exe",
        "cmd": "cmd.exe", "terminal": "cmd.exe", "prompt": "cmd.exe",
        "explorer": "explorer.exe", "explorador": "explorer.exe", "arquivos": "explorer.exe",
        "word": "winword.exe", "excel": "excel.exe", "powerpoint": "powerpnt.exe",
        "paint": "mspaint.exe",
    }
    for chave, exe in exes.items():
        if chave in n:
            if exe not in WHITELIST_EXE:
                log_erro("automacoes", f"Tentativa de abrir {exe} (não está na whitelist)")
                return f"Não consigo abrir {chave}."
            try:
                subprocess.Popen([exe])
                return f"Abrindo {chave}."
            except Exception as e:
                log_erro("automacoes", f"Erro ao abrir {exe}: {e}")
                return f"Erro ao abrir {chave}."
    
    for nome_atalho, caminho in CATALOGO.items():
        if n in nome_atalho:
            try:
                if not os.path.abspath(caminho).startswith(os.path.expanduser("~")):
                    log_erro("automacoes", f"Path traversal detectado: {caminho}")
                    return f"Caminho inválido."
                os.startfile(caminho)
                return f"Abrindo {nome_atalho}."
            except Exception as e:
                log_erro("automacoes", f"Erro ao abrir {caminho}: {e}")
                return f"Erro ao abrir {nome_atalho}."
    
    if " " not in n and re.match(r'^[a-z0-9\-]+$', n):
        webbrowser.open(f"https://www.{n}.com")
        return f"Abrindo {n}.com."
    
    return f"Não encontrei '{nome}'."

def _fechar(nome: str) -> str:
    n = nome.lower().strip()
    n = re.sub(r'[^\w\s]', '', n)
    
    processos = {
        "calc": "CalculatorApp.exe", "calculadora": "CalculatorApp.exe",
        "notepad": "notepad.exe", "notas": "notepad.exe", "bloco": "notepad.exe",
        "cmd": "cmd.exe", "terminal": "cmd.exe",
        "explorer": "explorer.exe", "explorador": "explorer.exe", "arquivos": "explorer.exe",
        "chrome": "chrome.exe", "word": "winword.exe", "excel": "excel.exe",
    }
    
    for chave, proc in processos.items():
        if chave in n:
            if proc not in WHITELIST_PROC:
                log_erro("automacoes", f"Tentativa de fechar {proc} (não está na whitelist)")
                return f"Não consigo fechar {chave}."
            try:
                subprocess.run(["taskkill", "/f", "/im", proc], capture_output=True, timeout=5)
                return f"{chave} fechado."
            except Exception as e:
                log_erro("automacoes", f"Erro ao fechar {proc}: {e}")
                return f"Erro ao fechar {chave}."
    
    try:
        r = subprocess.run(
            ['tasklist', '/fo', 'csv', '/nh'],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=10
        )
        for linha in r.stdout.splitlines():
            if n in linha.lower():
                p = linha.split('","')[0].strip('"')
                if re.match(r'^[a-zA-Z0-9\-_.]+\.exe$', p):
                    try:
                        subprocess.run(["taskkill", "/f", "/im", p], capture_output=True, timeout=5)
                        return f"{nome} fechado."
                    except Exception as e:
                        log_erro("automacoes", f"Erro ao fechar {p}: {e}")
    except Exception as e:
        log_erro("automacoes", f"tasklist error: {e}")
    
    return f"Tentei fechar {nome}."

def executar(comando: str) -> str | None:
    c = comando.lower().strip()
    
    if c.startswith("abrir ") or c.startswith("abra ") or c.startswith("abre "):
        alvo = c.split(" ", 1)[1] if " " in c else ""
        return _abrir(alvo) if alvo else "O que quer abrir?"
    
    if c.startswith("fechar ") or c.startswith("fecha ") or c.startswith("feche "):
        alvo = c.split(" ", 1)[1] if " " in c else ""
        return _fechar(alvo) if alvo else "O que quer fechar?"
    
    if c.startswith("pasta "):
        alvo = c.replace("pasta ", "").strip()
        map_pastas = {
            "documentos": "Documents", "downloads": "Downloads",
            "área de trabalho": "Desktop", "desktop": "Desktop",
            "imagens": "Pictures", "fotos": "Pictures",
            "música": "Music", "musica": "Music",
            "vídeos": "Videos", "videos": "Videos",
        }
        for k, v in map_pastas.items():
            if k in alvo:
                os.startfile(os.path.expanduser(f"~/{v}"))
                return f"Abrindo {v}."
        return f"Não encontrei a pasta '{alvo}'."
    
    return None