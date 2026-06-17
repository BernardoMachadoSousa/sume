import subprocess
import webbrowser
import os
import json
from utils.logger import erro as log_erro

CATALOGO_CACHE = "dados/catalogo_programas.json"

def _carregar_catalogo() -> dict:
    if os.path.exists(CATALOGO_CACHE):
        try:
            with open(CATALOGO_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
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
    import re
    n = nome.lower().strip()
    n = re.sub(r'[^\w\s]', '', n)  # remove pontuação
    
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
            subprocess.Popen(exe, shell=True)
            return f"Abrindo {chave}."
    
    for nome_atalho, caminho in CATALOGO.items():
        if n in nome_atalho:
            os.startfile(caminho)
            return f"Abrindo {nome_atalho}."
    
    if " " not in n:
        webbrowser.open(f"https://www.{n}.com")
        return f"Abrindo {n}.com."
    
    return f"Não encontrei '{nome}'."

def _fechar(nome: str) -> str:
    n = nome.lower().strip()
    
    processos = {
        "calc": "CalculatorApp.exe", "calculadora": "CalculatorApp.exe",
        "notepad": "notepad.exe", "notas": "notepad.exe", "bloco": "notepad.exe",
        "cmd": "cmd.exe", "terminal": "cmd.exe",
        "explorer": "explorer.exe", "explorador": "explorer.exe", "arquivos": "explorer.exe",
        "chrome": "chrome.exe", "word": "winword.exe", "excel": "excel.exe",
    }
    
    for chave, proc in processos.items():
        if chave in n:
            os.system(f"taskkill /f /im {proc} 2>nul")
            return f"{chave} fechado."
    
    try:
        r = subprocess.run('tasklist /fo csv /nh', shell=True, capture_output=True, text=True)
        for linha in r.stdout.splitlines():
            if n in linha.lower():
                p = linha.split('","')[0].strip('"')
                os.system(f"taskkill /f /im {p} 2>nul")
                return f"{nome} fechado."
    except Exception as e:
        log_erro("automacoes", f"tasklist: {e}")
    
    os.system(f'taskkill /f /fi "IMAGENAME eq *{n}*" 2>nul')
    return f"Tentei fechar {nome}."

def executar(comando: str) -> str | None:
    c = comando.lower().strip()
    
    if c.startswith("abrir ") or c.startswith("abra ") or c.startswith("abre "):
        alvo = c.split(" ", 1)[1] if " " in c else ""
        return _abrir(alvo) if alvo else "O que quer abrir?"
    
    if c.startswith("fechar ") or c.startswith("fecha ") or c.startswith("feche "):
        alvo = c.split(" ", 1)[1] if " " in c else ""
        return _fechar(alvo) if alvo else "O que quer fechar?"
    
    if "pasta" in c:
        map_pastas = {
            "documentos": "Documents", "downloads": "Downloads",
            "área de trabalho": "Desktop", "desktop": "Desktop",
            "imagens": "Pictures", "fotos": "Pictures",
            "música": "Music", "musica": "Music",
            "vídeos": "Videos", "videos": "Videos",
        }
        for k, v in map_pastas.items():
            if k in c:
                os.startfile(os.path.expanduser(f"~/{v}"))
                return f"Abrindo {v}."
    
    return None