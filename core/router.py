"""
Router do Sumé.

Mapeia cada ação de intenção (ex: "GET_TIME", "OPEN_APP") para uma função
handler, em vez do if/elif monolítico que existia antes no nexus_core.

Cada handler recebe (alvo, comando) e devolve um Resultado, ou None se
não conseguiu tratar o comando (nesse caso o nexus_core cai no fallback
de conversa, preservando o comportamento que já existia).
"""
from typing import Callable, Optional
from utils.resultado import Resultado

_handlers: dict[str, Callable[[str, str], Optional[Resultado]]] = {}


def registrar(acao: str):
    """Decorator para registrar um handler para uma ação específica."""
    def decorator(func: Callable[[str, str], Optional[Resultado]]):
        _handlers[acao] = func
        return func
    return decorator


def rotear(acao: str, alvo: str, comando: str) -> Optional[Resultado]:
    """Encontra e executa o handler certo para a ação. None se não houver handler ou ele não tratar."""
    handler = _handlers.get(acao)
    if handler is None:
        return None
    return handler(alvo, comando)


def acoes_registradas() -> list:
    """Útil para debug/testes: lista todas as ações que têm handler."""
    return list(_handlers.keys())
