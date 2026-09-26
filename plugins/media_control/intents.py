def detectar(comando: str) -> tuple:
    c = comando.lower().strip()
    
    gatilhos_midia = [
        "pause a música", "pausar a música", "pausar música", "pausa a música",
        "tocar música", "toque a música", "toca a música", "continue a música", "dê play",
        "próxima música", "pule a música", "pular música", "avance a música",
        "música anterior", "volte a música", "volte de música",
        "aumentar o volume", "aumente o som", "aumente o volume", "aumenta o som",
        "diminuir o volume", "diminua o som", "diminua o volume", "diminui o som",
        "mutar", "mude o som", "tire o som", "fique mudo"
    ]
    
    for g in gatilhos_midia:
        if g in c:
            return ("SYSTEM_MEDIA", comando, 0.95)
            
    return None
