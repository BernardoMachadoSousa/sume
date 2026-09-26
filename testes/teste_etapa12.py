"""
Teste da Etapa 12: Recursos avancados de UI - filtros, ordenacao e exportacao.
Valida funcionalidades de filtro, ordenacao e exportacao de resultados.
"""

import sys
import os
import json
import csv
from io import StringIO
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from plugins.busca.filtros import (
    filtrar_por_tipo, filtrar_por_relevancia, ordenar_resultados,
    limitar_resultados, aplicar_filtros, TipoResultado, Ordenacao
)
from plugins.busca.exportacao import (
    exportar_json, exportar_csv, exportar_texto, exportar_markdown
)

def criar_dados_teste():
    """Cria dados de teste para filtros."""
    return {
        "notas": [
            {"titulo": "Python Tips", "trecho": "Python eh otimo", "caminho": "/notas/python.md", "relevancia": 0.95},
            {"titulo": "JavaScript", "trecho": "JS eh dinamico", "caminho": "/notas/js.md", "relevancia": 0.75},
            {"titulo": "Django", "trecho": "Framework web", "caminho": "/notas/django.md", "relevancia": 0.85},
        ],
        "arquivos": [
            {"nome": "script.py", "trecho": "print('hello')", "caminho": "/code/script.py", "relevancia": 0.80, "tamanho": 1024},
            {"nome": "index.html", "trecho": "<html>", "caminho": "/web/index.html", "relevancia": 0.70, "tamanho": 2048},
        ]
    }

def teste_filtro_por_tipo():
    """Testa filtro por tipo de resultado."""
    print("\n--- Filtro por tipo ---")
    dados = criar_dados_teste()
    
    # Apenas notas
    resultado = filtrar_por_tipo(dados, TipoResultado.NOTA)
    assert "notas" in resultado and len(resultado["notas"]) == 3, "Deve ter 3 notas"
    assert "arquivos" not in resultado or len(resultado.get("arquivos", [])) == 0, "Nao deve ter arquivos"
    print("  X filtro por notas funciona")
    
    # Apenas arquivos
    resultado = filtrar_por_tipo(dados, TipoResultado.ARQUIVO)
    assert "arquivos" in resultado and len(resultado["arquivos"]) == 2, "Deve ter 2 arquivos"
    assert "notas" not in resultado or len(resultado.get("notas", [])) == 0, "Nao deve ter notas"
    print("  X filtro por arquivos funciona")
    
    # Todos
    resultado = filtrar_por_tipo(dados, TipoResultado.TODOS)
    assert len(resultado["notas"]) == 3 and len(resultado["arquivos"]) == 2, "Deve ter todos"
    print("  X filtro por todos funciona")

def teste_filtro_por_relevancia():
    """Testa filtro por intervalo de relevancia."""
    print("\n--- Filtro por relevancia ---")
    dados = criar_dados_teste()
    
    # Apenas alta relevancia (>=0.8)
    resultado = filtrar_por_relevancia(dados, 0.8, 1.0)
    assert len(resultado["notas"]) == 2, "Deve ter 2 notas com relevancia >= 0.8"
    assert len(resultado["arquivos"]) == 1, "Deve ter 1 arquivo com relevancia >= 0.8"
    print("  X filtro de alta relevancia funciona")
    
    # Relevancia media (0.7-0.79)
    resultado = filtrar_por_relevancia(dados, 0.7, 0.79)
    assert len(resultado["notas"]) == 1, "Deve ter 1 nota com relevancia 0.7-0.79"
    assert len(resultado["arquivos"]) == 1, "Deve ter 1 arquivo com relevancia 0.7-0.79"
    print("  X filtro de relevancia media funciona")

def teste_ordenacao():
    """Testa ordenacao de resultados."""
    print("\n--- Ordenacao de resultados ---")
    dados = criar_dados_teste()
    
    # Ordenar por relevancia (descendente)
    resultado = ordenar_resultados(dados, Ordenacao.RELEVANCIA, descendente=True)
    relevencias_notas = [n["relevancia"] for n in resultado["notas"]]
    assert relevencias_notas == sorted(relevencias_notas, reverse=True), "Notas devem estar ordenadas por relevancia DESC"
    print("  X ordenacao por relevancia funciona")
    
    # Ordenar por nome
    resultado = ordenar_resultados(dados, Ordenacao.NOME, descendente=False)
    nomes_notas = [n["titulo"] for n in resultado["notas"]]
    assert nomes_notas == sorted(nomes_notas), "Notas devem estar ordenadas por nome ASC"
    print("  X ordenacao por nome funciona")

def teste_limitar_resultados():
    """Testa limitacao de resultados."""
    print("\n--- Limitacao de resultados ---")
    dados = criar_dados_teste()
    
    resultado = limitar_resultados(dados, limite=2)
    assert len(resultado["notas"]) == 2, "Deve limitar a 2 notas"
    assert len(resultado["arquivos"]) == 2, "Deve limitar a 2 arquivos"
    print("  X limitacao de resultados funciona")

def teste_aplicar_multiplos_filtros():
    """Testa aplicacao de multiplos filtros encadeados."""
    print("\n--- Multiplos filtros ---")
    dados = criar_dados_teste()
    
    resultado = aplicar_filtros(
        dados,
        tipo=TipoResultado.NOTA,
        min_relevancia=0.8,
        ordem=Ordenacao.RELEVANCIA,
        descendente=True,
        limite=2
    )
    
    assert "notas" in resultado and len(resultado["notas"]) <= 2, "Deve ter no maximo 2 notas"
    assert all(n["relevancia"] >= 0.8 for n in resultado["notas"]), "Todas notas devem ter relevancia >= 0.8"
    print("  X multiplos filtros aplicados corretamente")

def teste_exportar_json():
    """Testa exportacao em JSON."""
    print("\n--- Exportacao JSON ---")
    dados = criar_dados_teste()
    
    json_str = exportar_json(dados)
    parsed = json.loads(json_str)
    
    assert "notas" in parsed and len(parsed["notas"]) == 3, "JSON deve ter notas"
    assert "arquivos" in parsed and len(parsed["arquivos"]) == 2, "JSON deve ter arquivos"
    print("  X exportacao JSON funciona")

def teste_exportar_csv():
    """Testa exportacao em CSV."""
    print("\n--- Exportacao CSV ---")
    dados = criar_dados_teste()
    
    csv_str = exportar_csv(dados)
    
    assert "tipo" in csv_str, "CSV deve ter cabecalho tipo"
    assert "Nota" in csv_str, "CSV deve ter tipo Nota"
    assert "Arquivo" in csv_str, "CSV deve ter tipo Arquivo"
    assert "Python Tips" in csv_str, "CSV deve ter titulo"
    print("  X exportacao CSV funciona")

def teste_exportar_texto():
    """Testa exportacao em texto."""
    print("\n--- Exportacao Texto ---")
    dados = criar_dados_teste()
    
    txt_str = exportar_texto(dados, "python")
    
    assert "RESULTADOS DE BUSCA" in txt_str, "Deve ter titulo"
    assert "NOTAS ENCONTRADAS" in txt_str, "Deve ter secao notas"
    assert "ARQUIVOS ENCONTRADOS" in txt_str, "Deve ter secao arquivos"
    assert "python" in txt_str.lower(), "Deve ter termo de busca"
    print("  X exportacao texto funciona")

def teste_exportar_markdown():
    """Testa exportacao em Markdown."""
    print("\n--- Exportacao Markdown ---")
    dados = criar_dados_teste()
    
    md_str = exportar_markdown(dados, "python")
    
    assert "# Resultados de Busca" in md_str, "Deve ter titulo H1"
    assert "## Notas Encontradas" in md_str, "Deve ter secao H2"
    assert "## Arquivos Encontrados" in md_str, "Deve ter secao H2 arquivos"
    assert "**Termo:**" in md_str, "Deve ter termo destacado"
    print("  X exportacao markdown funciona")

def teste_compatibilidade_filtros_com_dados_reais():
    """Testa filtros com dados que vem dos handlers."""
    print("\n--- Compatibilidade com dados reais ---")
    
    from plugins.busca.handlers import buscar_notas_handler
    from modulos import vault
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        nota_file = os.path.join(tmpdir, "test.md")
        with open(nota_file, 'w', encoding='utf-8') as f:
            f.write("# Teste\n\nConteudo de teste")
        
        original_listar = vault.listar
        vault.listar = lambda: [{"titulo": "Teste", "caminho": nota_file}]
        
        try:
            resultado = buscar_notas_handler("teste")
            dados = resultado.dados
            
            # Aplicar filtros
            filtrado = aplicar_filtros(dados, tipo=TipoResultado.NOTA)
            assert "notas" in filtrado, "Filtro deve preservar estrutura"
            print("  X filtros funcionam com dados reais")
            
            # Exportar dados reais
            json_export = exportar_json(dados)
            parsed = json.loads(json_export)
            assert "notas" in parsed, "JSON export de dados reais funciona"
            print("  X exportacao de dados reais funciona")
            
        finally:
            vault.listar = original_listar

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 12: Recursos Avancados de UI")
    print("=" * 68)
    
    try:
        teste_filtro_por_tipo()
        teste_filtro_por_relevancia()
        teste_ordenacao()
        teste_limitar_resultados()
        teste_aplicar_multiplos_filtros()
        teste_exportar_json()
        teste_exportar_csv()
        teste_exportar_texto()
        teste_exportar_markdown()
        teste_compatibilidade_filtros_com_dados_reais()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 12 PASSARAM!")
        print("Recursos avancados de UI prontos para uso.")
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
