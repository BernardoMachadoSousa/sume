def detectar(comando: str) -> tuple | None:
    # "tchau"/"desligar" quase não têm outro sentido no contexto de comando.
    # "sair" é palavra comum ("sair de casa", "sair mais cedo") e sozinha é
    # sinal mais fraco, por isso confiança menor.
    if "tchau" in comando:
        return ("EXIT", "", 0.95)
    if "desligar" in comando:
        return ("EXIT", "", 0.9)
    if "sair" in comando:
        return ("EXIT", "", 0.6)
    return None