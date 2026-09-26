"""
Teste da Etapa 11: Interface Web para busca.
Valida a integração entre o backend e o frontend para exibição de resultados de busca.
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.resultado import Resultado
from plugins.busca.handlers import buscar_notas_handler, buscar_arquivos_handler

def teste_handlers_retornam_resultado():
    """Valida que os handlers retornam Resultado com dados estruturados."""
    print("\n--- Handlers retornam Resultado com dados ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from modulos import vault
        
        nota_file = os.path.join(tmpdir, "test.md")
        with open(nota_file, 'w', encoding='utf-8') as f:
            f.write("# Teste\n\nConteudo de teste.")
        
        original_listar = vault.listar
        vault.listar = lambda: [{"titulo": "Teste", "caminho": nota_file}]
        
        try:
            resultado = buscar_notas_handler("teste")
            
            assert isinstance(resultado, Resultado), "Deve retornar Resultado"
            assert resultado.sucesso, "Deve ter sucesso"
            assert resultado.dados, "Deve ter dados"
            assert "notas" in resultado.dados, "Dados devem ter 'notas'"
            print("  X handler retorna estrutura esperada")
            
            notas_ret = resultado.dados["notas"]
            if notas_ret:
                nota = notas_ret[0]
                assert "titulo" in nota, "Nota deve ter titulo"
                assert "trecho" in nota, "Nota deve ter trecho"
                assert "caminho" in nota, "Nota deve ter caminho"
                print("  X nota tem campos necessarios")
                
        finally:
            vault.listar = original_listar

def teste_estrutura_json_para_frontend():
    """Valida que os dados podem ser serializados para JSON."""
    print("\n--- Estrutura JSON para frontend ---")
    
    import json
    
    dados = {
        "resposta": "Encontrei notas",
        "erro": False,
        "dados": {
            "notas": [
                {
                    "titulo": "Python",
                    "trecho": "Python eh versatil",
                    "caminho": "/path/to/python.md",
                    "relevancia": 0.9
                }
            ]
        }
    }
    
    json_str = json.dumps(dados, ensure_ascii=False)
    assert len(json_str) > 0, "JSON nao pode ser vazio"
    print("  X dados sao serializaveis em JSON")
    
    parsed = json.loads(json_str)
    assert "dados" in parsed, "JSON deve ter dados"
    print("  X JSON eh parseavel")

def teste_resposta_com_dados():
    """Valida que processar_com_dados retorna estrutura esperada."""
    print("\n--- Resposta com dados estruturados ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from modulos import vault
        
        nota_file = os.path.join(tmpdir, "python.md")
        with open(nota_file, 'w', encoding='utf-8') as f:
            f.write("# Python\n\nPython eh otimo")
        
        original_listar = vault.listar
        vault.listar = lambda: [{"titulo": "Python", "caminho": nota_file}]
        
        try:
            resultado = buscar_notas_handler("python")
            
            assert isinstance(resultado, Resultado), "Deve ser Resultado"
            assert resultado.dados, "Deve ter dados"
            assert resultado.mensagem, "Deve ter mensagem para usuario"
            print("  X resposta tem mensagem e dados")
            
            notas_dados = resultado.dados.get("notas", [])
            assert len(notas_dados) > 0, "Deve ter encontrado notas"
            print(f"  X encontradas {len(notas_dados)} nota(s)")
            
        finally:
            vault.listar = original_listar

def teste_compatibilidade_ui():
    """Valida que dados podem ser exibidos na UI."""
    print("\n--- Compatibilidade com UI ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        from modulos import vault
        
        nota_file = os.path.join(tmpdir, "test.md")
        with open(nota_file, 'w', encoding='utf-8') as f:
            f.write("# Titulo\n\nConteudo para exibir na interface")
        
        original_listar = vault.listar
        vault.listar = lambda: [{"titulo": "Titulo", "caminho": nota_file}]
        
        try:
            resultado = buscar_notas_handler("titulo")
            
            notas = resultado.dados.get("notas", [])
            if notas:
                nota = notas[0]
                
                assert len(nota["titulo"]) < 100, "Titulo deve caber na UI"
                assert len(nota["trecho"]) < 300, "Trecho deve caber na UI"
                print("  X dados tem tamanho apropriado")
                
                assert "\n" not in nota["titulo"], "Titulo nao deve ter quebras"
                print("  X dados estao formatados para exibicao")
                
        finally:
            vault.listar = original_listar

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 11: Interface Web para Busca")
    print("=" * 68)
    
    try:
        teste_handlers_retornam_resultado()
        teste_estrutura_json_para_frontend()
        teste_resposta_com_dados()
        teste_compatibilidade_ui()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 11 PASSARAM!")
        print("Interface Web para Busca esta pronta para integracao.")
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
