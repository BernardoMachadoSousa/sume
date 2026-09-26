import ctypes
from core.router import registrar
from utils.logger import info as log_info
from utils.resultado import Resultado

# Constantes do Windows para Virtual-Key Codes de Mídia
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3

def simular_tecla(vk_code):
    """Simula o pressionamento e soltura de uma tecla de mídia no teclado."""
    # keyDown
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    # keyUp
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

@registrar("SYSTEM_MEDIA")
def handle_media(alvo: str, comando_original: str) -> Resultado:
        c = comando_original.lower()
        
        log_info("media_plugin", f"Capturou requisição de mídia: {c}")
        
        # Pausar / Tocar
        if any(p in c for p in ["pause", "pausar", "tocar", "toque", "toca a", "continue a", "play"]):
            simular_tecla(VK_MEDIA_PLAY_PAUSE)
            if "pause" in c or "pausar" in c:
                return Resultado(True, "Música pausada.")
            return Resultado(True, "Voltando a tocar.")
        
        # Próxima
        if any(p in c for p in ["próxima", "pule", "pular", "avance"]):
            simular_tecla(VK_MEDIA_NEXT_TRACK)
            return Resultado(True, "Pulando para a próxima faixa.")
        
        # Anterior
        if any(p in c for p in ["anterior", "volte", "voltar"]):
            simular_tecla(VK_MEDIA_PREV_TRACK)
            return Resultado(True, "Voltando uma faixa.")
        
        # Volume (vamos simular apertar o botão 3 vezes para fazer diferença notável)
        if any(p in c for p in ["aumentar", "aumente", "aumenta"]):
            for _ in range(3):
                simular_tecla(VK_VOLUME_UP)
            return Resultado(True, "Aumentei o som.")
        
        if any(p in c for p in ["diminuir", "diminua", "diminui"]):
            for _ in range(3):
                simular_tecla(VK_VOLUME_DOWN)
            return Resultado(True, "Diminuí o som para você.")
        
        # Mute
        if any(p in c for p in ["mudo", "mutar", "tire o som", "silêncio"]):
            simular_tecla(VK_VOLUME_MUTE)
            return Resultado(True, "Pronto, mudei para o mudo.")
        
        return Resultado(True, "Feito.")
