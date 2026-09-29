def detectar(comando: str) -> tuple | None:
    # Chat intent is a fallback; return None to let Nexus core handle fallback when no other intent matches.
    return None