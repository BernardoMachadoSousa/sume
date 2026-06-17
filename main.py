import webview
import threading
import os
from core.nexus_core import processar
from utils.escuta import ouvir, _carregar_modelo
from utils.voz import falar

class NexusAPI:
    def processar_comando(self, comando: str) -> str:
        """Processa comando (voz ou texto) e retorna resposta"""
        resposta = processar(comando)
        if resposta and resposta != "desligar":
            falar(resposta)
        if resposta == "desligar":
            threading.Timer(0.5, window.destroy).start()
        return resposta

    def ouvir_comando(self) -> str:
        """Captura áudio e retorna texto reconhecido"""
        return ouvir()

    def minimizar(self):
        window.minimize()

    def fechar(self):
        window.destroy()


if __name__ == "__main__":
    api = NexusAPI()

    html_path = os.path.join(os.path.dirname(__file__), "interface", "index.html")

    window = webview.create_window(
        title="Nexus",
        url=html_path,
        js_api=api,
        width=350,
        height=450,
        resizable=True,
        frameless=True,
        easy_drag=True,
        background_color="#0a0a0f",
        on_top=True
    )

    # Pré-carrega Whisper em background
    threading.Thread(target=_carregar_modelo, daemon=True).start()

    webview.start(debug=False)