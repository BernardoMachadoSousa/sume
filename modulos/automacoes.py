import subprocess
import webbrowser
import os

PROGRAMAS = {
    "calculadora": "calc.exe",
    "notas": "notepad.exe",
    "bloco": "notepad.exe",
    "explorador": "explorer.exe",
    "cmd": "cmd.exe",
    "terminal": "cmd.exe",
    "powerpoint": "powerpnt.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "paint": "mspaint.exe",
    "navegador": "https://google.com",
    "chrome": "chrome.exe",
}

SITES = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "github": "https://github.com",
    "gmail": "https://gmail.com",
    "netflix": "https://netflix.com",
    "spotify": "https://open.spotify.com",
}

def executar(comando: str) -> str | None:
    comando = comando.lower().strip()

    if "abrir" in comando or "abra" in comando:
        alvo = comando.replace("abrir", "").replace("abra", "").replace("o ", "").replace("a ", "").strip()

        # Tenta programas
        for nome, cmd in PROGRAMAS.items():
            if nome in alvo:
                try:
                    if cmd.startswith("http"):
                        webbrowser.open(cmd)
                    else:
                        subprocess.Popen(cmd, shell=True)
                    return f"Abrindo {nome}."
                except:
                    return f"Não consegui abrir {nome}."

        # Tenta sites
        for nome, url in SITES.items():
            if nome in alvo:
                webbrowser.open(url)
                return f"Abrindo {nome}."

        # Site genérico
        if "." in alvo or " " not in alvo:
            webbrowser.open(f"https://{alvo}.com")
            return f"Tentando abrir {alvo}.com"

        return f"Não encontrei o programa: {alvo}"

    if "fechar" in comando or "feche" in comando:
        alvo = comando.replace("fechar", "").replace("feche", "").replace("o ", "").replace("a ", "").strip()

        mapeamento_fechar = {
            "chrome": "chrome.exe",
            "notas": "notepad.exe",
            "bloco": "notepad.exe",
            "calculadora": "calculator.exe",
            "cmd": "cmd.exe",
        }

        for nome, processo in mapeamento_fechar.items():
            if nome in alvo:
                os.system(f"taskkill /f /im {processo} 2>nul")
                return f"{nome} fechado."

        return f"Ainda não sei fechar {alvo}."

    if "pasta" in comando:
        if "documentos" in comando:
            os.startfile(os.path.expanduser("~/Documents"))
            return "Abrindo pasta Documentos."
        if "downloads" in comando:
            os.startfile(os.path.expanduser("~/Downloads"))
            return "Abrindo pasta Downloads."
        if "área de trabalho" in comando or "desktop" in comando:
            os.startfile(os.path.expanduser("~/Desktop"))
            return "Abrindo Área de Trabalho."

    return None