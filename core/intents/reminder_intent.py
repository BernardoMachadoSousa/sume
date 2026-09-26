import re


def detectar(comando: str) -> tuple | None:
    c = comando.lower()

    _criacao = any(p in c for p in (
        "lembre-me", "lembre me", "me lembra", "me lembre",
        "lembrete de", "lembrete:",
    ))
    if _criacao:
        return ("REMINDER_SET", comando, 0.92)

    _lista = any(p in c for p in (
        "quais lembretes", "meus lembretes", "ver lembretes",
        "listar lembretes", "lembretes pendentes",
    ))
    if _lista:
        return ("REMINDER_LIST", "", 0.90)

    _cancela = any(p in c for p in (
        "cancelar lembrete", "cancela lembrete",
        "apagar lembrete", "remover lembrete",
    ))
    if _cancela:
        trecho = re.sub(
            r"(cancelar|cancela|apagar|remover)\s+lembrete\s*(de|sobre)?\s*",
            "", c, flags=re.I,
        ).strip()
        return ("REMINDER_CANCEL", trecho, 0.90)

    return None
