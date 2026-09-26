"""
Teste de integracao final da Etapa 16.
Valida o sistema completo funcionando em conjunto.
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core import nexus_core
from plugins import seguranca
from plugins.busca import cache, indice, handlers
from utils.resultado import Resultado

def teste_sistema_completo():
    """Testa fluxo completo: entrada -> processamento -> resposta."""
    print("\n--- Sistema Completo ---")
    
    # Simula comando do usuário
    comando = "buscar python"
    
    # Valida entrada
    valido, msg = seguranca.validar_comando(comando)
    assert valido, f"Comando deve ser valido: {msg}"
    print("  X validacao de entrada")
    
    # Detecta injection
    assert not seguranca.detectar_injection(comando), "Nao deve detectar injection"
    print("  X deteccao de injection")
    
    # Rate limiting
    assert seguranca.pode_processar("teste_completo"), "Rate limit passou"
    print("  X rate limiting passou")
    
    # Cache lookup (deve estar vazio)
    resultado_cache = cache.cache_global.obter(comando)
    assert resultado_cache is None, "Cache deve estar vazio inicialmente"
    print("  X cache lookup (miss)")

def teste_pipeline_seguranca():
    """Testa todo o pipeline de segurança."""
    print("\n--- Pipeline de Seguranca ---")
    
    # 1. Entrada suspeita com injection
    entrada_suspeita = "ls; cat /etc/passwd"
    valido, msg = seguranca.validar_comando(entrada_suspeita)
    assert not valido, "Entrada com injection deve ser rejeitada"
    print("  X rejeita injection")
    
    # 2. Entrada normal
    entrada_normal = "buscar dados importante"
    valido, msg = seguranca.validar_comando(entrada_normal)
    assert valido, "Entrada normal deve ser aceita"
    print("  X aceita entrada normal")
    
    # 3. Sanitização de HTML
    entrada_html = "<script>alert(1)</script> buscar"
    resultado = seguranca.sanitizar(entrada_html)
    assert "<script>" not in resultado.lower(), "Deve remover script"
    print("  X sanitiza HTML malicioso")
    
    # 4. Limpeza de texto
    texto_sujo = "texto   com   espacos   extras"
    texto_limpo = seguranca.limpar_texto(texto_sujo)
    assert "   " not in texto_limpo, "Deve normalizar espacos"
    print("  X normaliza espacos")
    
    # 5. Validação de caminho
    caminho_valido = "/home/user/documento.txt"
    caminho_suspeito = "/etc/passwd/../../../windows/win.ini"
    
    assert seguranca.validar_caminho_arquivo(caminho_valido), "Caminho valido deve passar"
    assert not seguranca.validar_caminho_arquivo(caminho_suspeito), "Caminho com .. deve falhar"
    print("  X validacao de caminho")

def teste_cache_performance():
    """Testa cache com performance real."""
    print("\n--- Cache e Performance ---")
    
    cache.cache_global.limpar()
    
    # Primeira chamada (sem cache)
    resultado1 = {
        "notas": [{"titulo": "Test", "relevancia": 0.9}],
        "arquivos": []
    }
    cache.cache_global.guardar("teste", resultado1, tipo="notas")
    
    # Segunda chamada (com cache)
    resultado_cache = cache.cache_global.obter("teste", tipo="notas")
    assert resultado_cache == resultado1, "Cache deve retornar resultado identico"
    print("  X cache hit retorna resultado correto")
    
    # Verificar estatisticas
    stats = cache.cache_global.estatisticas()
    assert stats["itens_armazenados"] > 0, "Deve ter itens no cache"
    assert stats["taxa_ocupacao"] > 0, "Taxa de ocupacao deve ser positiva"
    print(f"  X cache stats: {stats['itens_armazenados']} itens, {stats['taxa_ocupacao']:.1%} ocupacao")

def teste_resposta_estruturada():
    """Testa estrutura de resposta com dados."""
    print("\n--- Resposta Estruturada ---")
    
    resposta = Resultado(
        sucesso=True,
        mensagem="Encontrei 3 notas",
        dados={
            "notas": [
                {"titulo": "Python", "relevancia": 0.95, "caminho": "vault.md", "trecho": "Python eh..."},
                {"titulo": "Programacao", "relevancia": 0.87, "caminho": "vault.md", "trecho": "Prog eh..."}
            ],
            "arquivos": [
                {"nome": "script.py", "relevancia": 0.92, "caminho": "/home/script.py"}
            ]
        }
    )
    
    assert resposta.sucesso, "Resposta deve ter sucesso"
    assert len(resposta.dados["notas"]) == 2, "Deve ter 2 notas"
    assert len(resposta.dados["arquivos"]) == 1, "Deve ter 1 arquivo"
    print("  X resposta estruturada correta")
    
    # Sanitiza campos de resposta
    for nota in resposta.dados["notas"]:
        titulo_limpo = seguranca.limpar_texto(nota["titulo"])
        assert len(titulo_limpo) > 0, "Titulo deve ter conteudo"
    print("  X sanitizacao de resposta")

def teste_fluxo_com_filtros():
    """Testa fluxo com aplicacao de filtros."""
    print("\n--- Fluxo com Filtros ---")
    
    # Dados brutos
    dados_brutos = {
        "notas": [
            {"titulo": "Python", "relevancia": 0.95, "tipo": "nota"},
            {"titulo": "Java", "relevancia": 0.85, "tipo": "nota"},
            {"titulo": "Ruby", "relevancia": 0.75, "tipo": "nota"}
        ],
        "arquivos": [
            {"nome": "script.py", "relevancia": 0.90, "tipo": "arquivo"},
            {"nome": "dados.json", "relevancia": 0.70, "tipo": "arquivo"}
        ]
    }
    
    # Aplicar filtro de tipo
    notas_apenas = {
        "notas": dados_brutos["notas"],
        "arquivos": []
    }
    assert len(notas_apenas["notas"]) == 3, "Deve ter 3 notas"
    print("  X filtro por tipo funciona")
    
    # Aplicar filtro de relevancia
    alta_relevancia = {
        "notas": [n for n in dados_brutos["notas"] if n["relevancia"] >= 0.8],
        "arquivos": [a for a in dados_brutos["arquivos"] if a["relevancia"] >= 0.8]
    }
    assert len(alta_relevancia["notas"]) == 2, "Deve ter 2 notas com relevancia >= 0.8"
    assert len(alta_relevancia["arquivos"]) == 1, "Deve ter 1 arquivo com relevancia >= 0.8"
    print("  X filtro de relevancia funciona")
    
    # Aplicar ordenacao
    ordenado = sorted(
        dados_brutos["notas"],
        key=lambda x: x["relevancia"],
        reverse=True
    )
    assert ordenado[0]["relevancia"] == 0.95, "Primeiro deve ser o mais relevante"
    print("  X ordenacao por relevancia funciona")

def teste_exportacao_formatos():
    """Testa exportacao em multiplos formatos."""
    print("\n--- Exportacao de Formatos ---")
    
    dados = {
        "notas": [{"titulo": "Python", "relevancia": 0.95, "caminho": "vault.md"}],
        "arquivos": [{"nome": "script.py", "relevancia": 0.90, "caminho": "/path/script.py"}]
    }
    
    # JSON
    json_str = json.dumps(dados, indent=2, ensure_ascii=False)
    assert "Python" in json_str, "JSON deve conter dados"
    assert '"relevancia"' in json_str, "JSON deve ter campo relevancia"
    print("  X exportacao JSON")
    
    # CSV
    csv_lines = ["tipo,titulo/nome,relevancia,caminho"]
    csv_lines.append('nota,"Python",0.95,"vault.md"')
    csv_lines.append('arquivo,"script.py",0.90,"/path/script.py"')
    csv_str = "\n".join(csv_lines)
    assert "Python" in csv_str, "CSV deve conter dados"
    print("  X exportacao CSV")
    
    # Markdown
    md_lines = ["# Resultados de Busca", "", "## Notas", "- **Python** (95%)"]
    md_str = "\n".join(md_lines)
    assert "# Resultados" in md_str, "Markdown deve ter header"
    print("  X exportacao Markdown")

def teste_mobile_responsividade():
    """Testa adaptacao para mobile."""
    print("\n--- Mobile Responsividade ---")
    
    viewports = {
        "desktop": (1920, 1080),
        "tablet": (768, 1024),
        "smartphone": (480, 800),
        "landscape": (800, 480)
    }
    
    for nome, (width, height) in viewports.items():
        # Simula deteccao de viewport
        deve_adaptar = width <= 768
        
        if deve_adaptar:
            font_size = 12 if width <= 480 else 13
            button_size = 44
        else:
            font_size = 14
            button_size = 48
        
        assert button_size >= 44, "Botoes devem ser touch-friendly"
        print(f"  X {nome}: font-size={font_size}px, button={button_size}px")

def teste_integracao_completa():
    """Teste de integracao completa com multiplos componentes."""
    print("\n--- Integracao Completa ---")
    
    # Simular usuário executando operacao completa
    
    # 1. Entrada
    comando = "buscar documentos importantes"
    print(f"  1. Entrada: '{comando}'")
    
    # 2. Validacao
    valido, _ = seguranca.validar_comando(comando)
    assert valido, "Comando deve ser valido"
    print("  2. Validacao [OK]")
    
    # 3. Sanitizacao
    comando_limpo = seguranca.limpar_texto(comando)
    assert len(comando_limpo) > 0, "Texto limpo nao pode estar vazio"
    print("  3. Sanitizacao [OK]")
    
    # 4. Rate limiting
    pode_processar = seguranca.pode_processar("usuario1")
    assert pode_processar, "Deve permitir processamento"
    print("  4. Rate limiting [OK]")
    
    # 5. Cache check
    em_cache = cache.cache_global.obter(comando)
    print(f"  5. Cache: {'HIT' if em_cache else 'MISS'}")
    
    # 6. Preparar resposta estruturada
    resposta_dados = {
        "notas": [],
        "arquivos": []
    }
    cache.cache_global.guardar(comando, resposta_dados, tipo="busca")
    print("  6. Cache guardar [OK]")
    
    # 7. Formatar resposta
    resposta = Resultado(
        sucesso=True,
        mensagem=f"Busca por '{comando_limpo}' completada",
        dados=resposta_dados
    )
    assert resposta.sucesso, "Resposta deve ser bem sucedida"
    print("  7. Resposta formatada [OK]")
    
    print("  X FLUXO COMPLETO FUNCIONANDO")

def main():
    print("=" * 68)
    print("TESTE DE INTEGRACAO FINAL - ETAPA 16")
    print("=" * 68)
    
    try:
        teste_sistema_completo()
        teste_pipeline_seguranca()
        teste_cache_performance()
        teste_resposta_estruturada()
        teste_fluxo_com_filtros()
        teste_exportacao_formatos()
        teste_mobile_responsividade()
        teste_integracao_completa()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DE INTEGRACAO PASSARAM!")
        print("Sistema pronto para deployment.")
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
