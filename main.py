import webview
import threading
import os
from utils.console import configurar_console
from core.nexus_core import processar, ultima_intencao as ultima_intencao_nucleo
from modulos import memoria
from utils.escuta import ouvir, _carregar_modelo
from utils.voz import falar

class NexusAPI:
    def processar_comando(self, comando: str) -> str:
        """Processa comando (voz ou texto) e retorna resposta"""
        return self.processar_comando_info(comando)["resposta"]

    def processar_comando_info(self, comando: str) -> dict:
        """Processa e devolve a resposta com um flag de erro, para a UI."""
        resposta = processar(comando)
        if resposta and resposta != "desligar":
            falar(resposta)
        if resposta == "desligar":
            threading.Timer(0.5, window.destroy).start()
        return {
            "resposta": resposta,
            "erro": self._mensagem_de_erro(resposta),
        }

    @staticmethod
    def _mensagem_de_erro(resposta: str) -> bool:
        from modulos.ia_conversacional import FALHA_OLLAMA
        return bool(resposta) and (
            resposta == FALHA_OLLAMA
            or "ocorreu um erro ao processar" in resposta
        )

    def ver_memorias(self) -> list:
        """O que o Sumé sabe agora, para o painel lateral (Etapa 4)."""
        itens = []
        for camada in (memoria.SESSAO, memoria.CURTA, memoria.PERMANENTE):
            for chave, valor in sorted((memoria.carregar(camada) or {}).items()):
                itens.append({"camada": camada, "chave": chave, "valor": valor})
        return itens

    def ultima_intencao(self) -> dict:
        """Intenção mais recente reconhecida, para o indicador da interface."""
        return ultima_intencao_nucleo()

    def ouvir_comando(self) -> str:
        """Captura áudio e retorna texto reconhecido"""
        return ouvir()

    def minimizar(self):
        window.minimize()

    def fechar(self):
        window.destroy()


if __name__ == "__main__":
    configurar_console()  # a escuta e a voz imprimem; o console do Windows é cp1252

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