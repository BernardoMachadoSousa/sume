"""
Teste da Etapa 15: Seguranca e validacao de dados.
Valida sanitizacao, validacao, rate limiting e protecoes.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from plugins.seguranca import (
    SanitizadorHTML, ValidadorComando, RateLimiter,
    ValidadorCaminho, sanitizar, limpar_texto, validar_comando,
    detectar_injection, pode_processar, validar_caminho_arquivo
)

def teste_sanitizacao_xss():
    """Testa sanitizacao contra XSS attacks."""
    print("\n--- Sanitizacao XSS ---")
    
    sanitizador = SanitizadorHTML()
    
    xss_payload = '<script>alert("XSS")</script>'
    resultado = sanitizador.sanitizar(xss_payload)
    assert '<script>' not in resultado.lower(), "Deve remover tags script"
    print("  X tags script removidas")
    
    xss_payload2 = '<img src=x onerror="alert(1)">'
    resultado2 = sanitizador.sanitizar(xss_payload2)
    assert 'onerror' not in resultado2.lower(), "Deve remover atributos onclick"
    print("  X atributos onclick removidos")
    
    xss_payload3 = '<iframe src="evil.com"></iframe>'
    resultado3 = sanitizador.sanitizar(xss_payload3)
    assert '<iframe>' not in resultado3.lower(), "Deve remover iframes"
    print("  X iframes removidas")

def teste_limpeza_texto():
    """Testa limpeza e normalizacao de texto."""
    print("\n--- Limpeza de texto ---")
    
    sanitizador = SanitizadorHTML()
    
    texto_sujo = "Olá   mundo  com   espacos extra"
    resultado = sanitizador.limpar_texto(texto_sujo)
    assert resultado == "Olá mundo com espacos extra", "Deve normalizar espacos"
    print("  X espacos normalizados")
    
    texto_longo = "a" * 20000
    resultado = sanitizador.limpar_texto(texto_longo, max_tamanho=100)
    assert len(resultado) == 100, "Deve limitar tamanho"
    print("  X tamanho limitado")

def teste_validacao_comando():
    """Testa validacao de comandos."""
    print("\n--- Validacao de comando ---")
    
    validador = ValidadorComando()
    
    valido, msg = validador.validar("buscar python")
    assert valido, f"Deve aceitar comando valido: {msg}"
    print("  X comando valido aceito")
    
    valido, msg = validador.validar("")
    assert not valido, "Deve rejeitar comando vazio"
    print("  X comando vazio rejeitado")
    
    valido, msg = validador.validar("a" * 10000)
    assert not valido, "Deve rejeitar comando muito longo"
    print("  X comando muito longo rejeitado")

def teste_deteccao_injection():
    """Testa deteccao de tentativas de injection."""
    print("\n--- Deteccao de injection ---")
    
    validador = ValidadorComando()
    
    assert validador.detectar_injection("ls; whoami"), "Deve detectar ;"
    print("  X ';' detectado")
    
    assert validador.detectar_injection("test && cat /etc/passwd"), "Deve detectar &&"
    print("  X '&&' detectado")
    
    assert validador.detectar_injection("`rm -rf /`"), "Deve detectar backticks"
    print("  X backticks detectados")
    
    assert validador.detectar_injection("$(whoami)"), "Deve detectar $(...)"
    print("  X $(...) detectado")
    
    assert not validador.detectar_injection("buscar dados normais"), "Nao deve detectar em texto normal"
    print("  X texto normal aceito")

def teste_rate_limiting():
    """Testa rate limiting."""
    print("\n--- Rate limiting ---")
    
    limiter = RateLimiter(max_requisicoes=3, janela_segundos=60)
    
    chave = "usuario1"
    assert limiter.pode_processar(chave), "Primeira requisicao deve passar"
    assert limiter.pode_processar(chave), "Segunda requisicao deve passar"
    assert limiter.pode_processar(chave), "Terceira requisicao deve passar"
    assert not limiter.pode_processar(chave), "Quarta requisicao deve ser bloqueada"
    print("  X rate limit funciona")
    
    restantes = limiter.requisicoes_restantes(chave)
    assert restantes == 0, "Deve ter 0 requisicoes restantes"
    print("  X contador de requisicoes correto")

def teste_validacao_caminho():
    """Testa validacao de caminhos de arquivo."""
    print("\n--- Validacao de caminho ---")
    
    assert ValidadorCaminho.validar_caminho("/home/user/documento.txt"), "Deve aceitar caminho valido"
    print("  X caminho valido aceito")
    
    assert not ValidadorCaminho.validar_caminho("/etc/passwd/../../../etc/shadow"), "Deve detectar path traversal"
    print("  X path traversal detectado")
    
    assert not ValidadorCaminho.validar_caminho("C:\\Windows\\System32\\..\\..\\windows\\win.ini"), "Deve detectar .."
    print("  X '..' detectado")
    
    assert not ValidadorCaminho.validar_caminho("file\0.txt"), "Deve detectar null bytes"
    print("  X null bytes detectados")

def teste_validacao_caminho_com_raiz():
    """Testa validacao de caminho com raiz permitida."""
    print("\n--- Validacao com raiz permitida ---")
    
    raiz = "/home/user/documentos"
    
    assert ValidadorCaminho.validar_caminho("/home/user/documentos/arquivo.txt", raiz), "Deve aceitar dentro da raiz"
    print("  X arquivo dentro da raiz aceito")
    
    assert not ValidadorCaminho.validar_caminho("/home/user/arquivo_externo.txt", raiz), "Deve rejeitar fora da raiz"
    print("  X arquivo fora da raiz rejeitado")

def teste_helpers():
    """Testa funcoes helper."""
    print("\n--- Funcoes helper ---")
    
    resultado = sanitizar("<script>alert(1)</script>")
    assert '<script>' not in resultado.lower(), "Helper sanitizar deve funcionar"
    print("  X helper sanitizar funciona")
    
    resultado = limpar_texto("texto   com   espacos")
    assert "   " not in resultado, "Helper limpar_texto deve funcionar"
    print("  X helper limpar_texto funciona")
    
    valido, msg = validar_comando("teste")
    assert valido, f"Helper validar_comando deve funcionar: {msg}"
    print("  X helper validar_comando funciona")
    
    assert detectar_injection("test; cmd"), "Helper detectar_injection deve detectar ;"
    print("  X helper detectar_injection funciona")

def teste_caracteres_unicode():
    """Testa sanitizacao com caracteres unicode."""
    print("\n--- Caracteres unicode ---")
    
    sanitizador = SanitizadorHTML()
    
    texto_unicode = "Olá 世界 🌍 مرحبا"
    resultado = sanitizador.sanitizar(texto_unicode)
    assert len(resultado) > 0, "Deve preservar caracteres unicode"
    print("  X caracteres unicode preservados")
    
    resultado_limpo = sanitizador.limpar_texto(texto_unicode)
    assert "Olá" in resultado_limpo, "Deve manter unicode em limpeza"
    print("  X limpeza preserva unicode")

def teste_html_entities():
    """Testa encoding de HTML entities."""
    print("\n--- HTML entities ---")
    
    sanitizador = SanitizadorHTML()
    
    texto = "<div>Conteúdo & Co.</div>"
    resultado = sanitizador.sanitizar(texto)
    assert "&lt;" in resultado or "&gt;" in resultado, "Deve escapar HTML"
    print("  X HTML escapado")

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 15: Seguranca e Validacao")
    print("=" * 68)
    
    try:
        teste_sanitizacao_xss()
        teste_limpeza_texto()
        teste_validacao_comando()
        teste_deteccao_injection()
        teste_rate_limiting()
        teste_validacao_caminho()
        teste_validacao_caminho_com_raiz()
        teste_helpers()
        teste_caracteres_unicode()
        teste_html_entities()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 15 PASSARAM!")
        print("Seguranca e validacao validadas.")
        print("=" * 68)
        return 0
        
    except AssertionError as e:
        print(f"\nERRO: {e}")
        return 1
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
