def detectar(comando: str) -> tuple:
    c = comando.lower().strip()
    
    gatilhos = [
        "previsão do tempo",
        "como está o clima",
        "qual o clima",
        "vai chover",
        "como está a temperatura",
        "qual a temperatura"
    ]
    
    for g in gatilhos:
        if g in c:
            return ("GET_WEATHER", comando, 0.9)
            
    return None
