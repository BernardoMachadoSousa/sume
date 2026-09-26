"""
Teste da Etapa 13: Otimizacao de performance - caching e indexacao.
Valida cache LRU, indexacao e performance de buscas.
"""

import sys
import os
import time
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from plugins.busca.cache import CacheLRU, cache_global, limpar_cache, stats_cache
from plugins.busca.indice import IndiceNotas, IndiceArquivos, atualizar_indice_notas, buscar_indice_notas
from plugins.busca.handlers import buscar_notas_handler
from modulos import vault

def teste_cache_lru_basico():
    """Testa funcionalidades basicas do cache LRU."""
    print("\n--- Cache LRU basico ---")
    
    cache = CacheLRU(tamanho_maximo=3)
    
    cache.guardar("python", {"notas": [{"titulo": "Python"}]})
    resultado = cache.obter("python")
    assert resultado is not None, "Cache deve ter resultado"
    print("  X guardar e obter funciona")
    
    cache.guardar("javascript", {"notas": [{"titulo": "JS"}]})
    cache.guardar("ruby", {"notas": [{"titulo": "Ruby"}]})
    cache.guardar("go", {"notas": [{"titulo": "Go"}]})
    
    assert cache.tamanho() <= 3, "Cache deve respeitar tamanho maximo"
    print("  X limite de tamanho respeitado")

def teste_cache_lru_evicao():
    """Testa evicao de itens menos usados."""
    print("\n--- Evicao LRU ---")
    
    cache = CacheLRU(tamanho_maximo=2)
    
    cache.guardar("a", {"dados": 1})
    cache.guardar("b", {"dados": 2})
    cache.guardar("c", {"dados": 3})
    
    resultado_a = cache.obter("a")
    assert resultado_a is None, "Item 'a' deve ter sido evicado"
    print("  X evicao funciona corretamente")
    
    cache.guardar("b", {"dados": 2})
    cache.guardar("d", {"dados": 4})
    
    resultado_c = cache.obter("c")
    assert resultado_c is None, "Item 'c' deve ter sido evicado"
    print("  X LRU order respeitada")

def teste_cache_ttl():
    """Testa expiracao de itens por TTL."""
    print("\n--- TTL do Cache ---")
    
    cache = CacheLRU(ttl_segundos=1)
    
    cache.guardar("temp", {"dados": "temporario"})
    resultado = cache.obter("temp")
    assert resultado is not None, "Deve ter resultado imediato"
    
    time.sleep(1.1)
    resultado_expirado = cache.obter("temp")
    assert resultado_expirado is None, "Item deve ter expirado"
    print("  X TTL funciona corretamente")

def teste_indice_notas():
    """Testa funcionalidades do indice de notas."""
    print("\n--- Indice de notas ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        indice = IndiceNotas(os.path.join(tmpdir, "indice.json"))
        
        indice.atualizar_nota("Python", "/notas/python.md", "Python eh uma linguagem versatil")
        assert len(indice.indice) == 1, "Deve ter 1 nota no indice"
        print("  X atualizar nota funciona")
        
        indice.atualizar_nota("JavaScript", "/notas/js.md", "JavaScript eh dinamico")
        indice.salvar()
        
        indice2 = IndiceNotas(os.path.join(tmpdir, "indice.json"))
        assert len(indice2.indice) >= 1, "Indice deve ser carregado do disco"
        print("  X persistencia funciona")

def teste_indice_palavras_chave():
    """Testa extracao de palavras-chave."""
    print("\n--- Palavras-chave do indice ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        indice = IndiceNotas(os.path.join(tmpdir, "indice.json"))
        
        conteudo = "Python eh uma linguagem de programacao versátil para ciência de dados"
        indice.atualizar_nota("Python", "/notas/python.md", conteudo)
        
        nota_indice = list(indice.indice.values())[0]
        palavras = nota_indice.get("palavras_chave", [])
        
        assert "python" in palavras, "Deve extrair 'python'"
        assert "linguagem" in palavras, "Deve extrair 'linguagem'"
        print("  X extracao de palavras-chave funciona")

def teste_cache_performance():
    """Testa ganho de performance com cache."""
    print("\n--- Performance do Cache ---")
    
    limpar_cache()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        nota_file = os.path.join(tmpdir, "test.md")
        with open(nota_file, 'w', encoding='utf-8') as f:
            f.write("# Teste\n\nConteudo para busca")
        
        original_listar = vault.listar
        vault.listar = lambda: [{"titulo": "Teste", "caminho": nota_file}]
        
        try:
            # Primeira busca (sem cache)
            inicio = time.time()
            resultado1 = buscar_notas_handler("teste")
            tempo_sem_cache = time.time() - inicio
            
            # Segunda busca (com cache)
            inicio = time.time()
            resultado2 = buscar_notas_handler("teste")
            tempo_com_cache = time.time() - inicio
            
            assert tempo_com_cache < tempo_sem_cache, "Cache deve ser mais rápido"
            ganho = (tempo_sem_cache - tempo_com_cache) / tempo_sem_cache * 100
            print(f"  X ganho de performance: {ganho:.1f}% mais rápido")
            
            stats = stats_cache()
            assert stats["itens_armazenados"] > 0, "Deve ter itens em cache"
            print(f"  X {stats['itens_armazenados']} item(s) em cache")
            
        finally:
            vault.listar = original_listar

def teste_indice_arquivos():
    """Testa funcionalidades do indice de arquivos."""
    print("\n--- Indice de arquivos ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        indice = IndiceArquivos(os.path.join(tmpdir, "indice.json"))
        
        arquivo_path = os.path.join(tmpdir, "script.py")
        with open(arquivo_path, 'w') as f:
            f.write("print('hello')")
        
        indice.atualizar_arquivo("script.py", arquivo_path, tamanho=1024, extensao=".py")
        assert len(indice.indice) == 1, "Deve ter 1 arquivo no indice"
        print("  X atualizar arquivo funciona")
        
        indice.salvar()
        indice2 = IndiceArquivos(os.path.join(tmpdir, "indice.json"))
        assert len(indice2.indice) >= 1, "Indice deve ser carregado"
        print("  X persistencia de arquivos funciona")

def teste_limpeza_indice_invalidos():
    """Testa limpeza de arquivos invalidos no indice."""
    print("\n--- Limpeza de indice invalido ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        indice = IndiceArquivos(os.path.join(tmpdir, "indice.json"))
        
        arquivo_path = os.path.join(tmpdir, "teste.txt")
        with open(arquivo_path, 'w') as f:
            f.write("conteudo")
        
        indice.atualizar_arquivo("teste.txt", arquivo_path, tamanho=100, extensao=".txt")
        assert len(indice.indice) == 1, "Deve ter 1 arquivo"
        
        os.remove(arquivo_path)
        removidos = indice.limpar_invalidos()
        
        assert removidos == 1, "Deve remover 1 arquivo invalido"
        assert len(indice.indice) == 0, "Indice deve estar vazio"
        print("  X limpeza de arquivos invalidos funciona")

def teste_cache_com_filtros():
    """Testa cache com filtros diferentes."""
    print("\n--- Cache com filtros ---")
    
    limpar_cache()
    cache = cache_global
    
    cache.guardar("python", {"notas": [{"titulo": "Python"}]}, tipo="notas", filtros={"min_rel": 0.8})
    cache.guardar("python", {"notas": [{"titulo": "Python2"}]}, tipo="notas", filtros={"min_rel": 0.5})
    
    resultado1 = cache.obter("python", tipo="notas", filtros={"min_rel": 0.8})
    resultado2 = cache.obter("python", tipo="notas", filtros={"min_rel": 0.5})
    
    assert resultado1 != resultado2, "Filtros diferentes devem ter cache separado"
    print("  X cache com filtros funciona corretamente")

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 13: Otimizacao de Performance")
    print("=" * 68)
    
    try:
        teste_cache_lru_basico()
        teste_cache_lru_evicao()
        teste_cache_ttl()
        teste_indice_notas()
        teste_indice_palavras_chave()
        teste_cache_performance()
        teste_indice_arquivos()
        teste_limpeza_indice_invalidos()
        teste_cache_com_filtros()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 13 PASSARAM!")
        print("Otimizacao de performance validada.")
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
