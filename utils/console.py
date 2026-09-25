"""
Ajuste de encoding do console.

O terminal do Windows abre em cp1252, que não tem emoji. Sem isto, qualquer
print com ✅, ❌ ou bandeira estoura UnicodeEncodeError e mata o script - foi o
que aconteceu com testes/teste_confianca.py, que morria na primeira linha de
resultado.

Acentos (á é ç õ) e travessão (—) existem em cp1252 e sempre funcionaram; o
problema é só com os símbolos.

A correção tem duas partes, e ambas são necessárias:

1. Colocar o console do Windows em UTF-8 (code page 65001), senão o terminal
   recebe bytes UTF-8 e mostra lixo.
2. Colocar stdout/stderr em UTF-8, senão o Python nem chega a escrever.

Uso: importe e chame logo no topo de qualquer script executável.

    from utils.console import configurar_console
    configurar_console()

Precisa vir depois do sys.path.insert, se o script tiver um.
Em Unix não faz nada de útil: o console já é UTF-8.
"""

import os
import sys


def _ajustar_code_page_windows() -> None:
    """Manda o console do Windows para UTF-8 (65001).

    Sem isso, o Python escreve UTF-8 e o terminal interpretando cp1252: o
    script deixa de quebrar, mas o emoji vira lixo na tela.
    """
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        # Sem console (serviço, IDE, stream redirecionado) não há code page.
        pass


def configurar_console() -> None:
    """Prepara console e streams para UTF-8 antes do primeiro print.

    O errors="replace" é a rede de segurança: se alguma coisa escapar (texto de
    LLM com caractere novo, saída de subprocesso), vira '?' em vez de derrubar
    o script inteiro.
    """
    _ajustar_code_page_windows()
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            # Stream substituído (pytest, capture, embed) pode não ter
            # reconfigure. Não é motivo para o script não rodar.
            pass
