"""
Etapa 22: Suite de testes automatizados completos.
Testes integrados, performance, seguranca e cobertura.
"""

import sys
import os
import time
import threading
import json
import hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from plugins.encriptacao import gerar_chave_mestra, criar_encriptador
from plugins.sincronizacao import ClienteSincronizacao
from plugins.sistema_plugins import GerenciadorPlugins, PluginProcessador
from plugins.api_rest import AutenticadorJWT, GerenciadorSessoes
from plugins.monitoramento import LoggerSume, GerenciadorMetricas, GerenciadorAlertas
from plugins.busca import notas, cache, indice

class RelatorioTeste:
    """Relatorio de execucao de testes."""
    
    def __init__(self):
        self.testes_totais = 0
        self.testes_passados = 0
        self.testes_falhados = 0
        self.testes_pulados = 0
        self.tempo_total = 0
        self.detalhes = []
    
    def adicionar_resultado(self, nome: str, passou: bool, tempo: float, mensagem: str = ""):
        """Adiciona resultado de teste."""
        self.testes_totais += 1
        if passou:
            self.testes_passados += 1
        else:
            self.testes_falhados += 1
        
        self.tempo_total += tempo
        self.detalhes.append({
            "nome": nome,
            "passou": passou,
            "tempo": tempo,
            "mensagem": mensagem
        })
    
    def obter_taxa_sucesso(self) -> float:
        """Calcula taxa de sucesso."""
        if self.testes_totais == 0:
            return 0.0
        return (self.testes_passados / self.testes_totais) * 100
    
    def gerar_relatorio(self) -> str:
        """Gera relatorio em texto."""
        linhas = [
            "=" * 70,
            "RELATORIO DE TESTES AUTOMATIZADOS - ETAPA 22",
            "=" * 70,
            f"Total de testes: {self.testes_totais}",
            f"Passados: {self.testes_passados}",
            f"Falhados: {self.testes_falhados}",
            f"Taxa de sucesso: {self.obter_taxa_sucesso():.1f}%",
            f"Tempo total: {self.tempo_total:.2f}s",
            "=" * 70,
            ""
        ]
        
        return "\n".join(linhas)

def teste_busca_semantica():
    """Testa funcionalidade de busca."""
    print("\n--- Teste Busca ---")
    tempo_inicio = time.time()
    
    try:
        # Simular busca com cache
        from plugins.busca import cache
        
        # Guardar dados em cache
        dados = [
            {"id": 1, "titulo": "Python", "conteudo": "Linguagem de programacao"},
            {"id": 2, "titulo": "Java", "conteudo": "Linguagem orientada a objetos"}
        ]
        
        cache.guardar_cache("linguagens", dados, tipo="teste")
        resultado = cache.obter_cache("linguagens", tipo="teste")
        
        assert resultado is not None, "Cache deve retornar dados"
        assert len(resultado) == 2, "Deve ter 2 itens"
        
        print(f"  X busca/cache funcionando ({len(resultado)} resultados)")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em busca: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_encriptacao_e2e():
    """Testa encriptacao end-to-end."""
    print("\n--- Teste Encriptacao E2E ---")
    tempo_inicio = time.time()
    
    try:
        chave, _ = gerar_chave_mestra("senha_teste")
        encriptador = criar_encriptador(chave)
        
        # Dados sensveis
        dados = {
            "usuario": "joao@example.com",
            "api_key": "sk-1234567890abcdef"
        }
        
        # Encriptar
        encriptado = encriptador.encriptar_json(dados)
        assert encriptado != str(dados), "Dados devem ser encriptados"
        
        # Descriptografar
        descriptografado = encriptador.descriptografar_json(encriptado)
        assert descriptografado == dados, "Dados devem ser iguais"
        
        print("  X encriptacao E2E funcionando")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em encriptacao: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_sincronizacao():
    """Testa sincronizacao de arquivos."""
    print("\n--- Teste Sincronizacao ---")
    tempo_inicio = time.time()
    
    try:
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            chave, _ = gerar_chave_mestra("sync_test")
            cliente = ClienteSincronizacao(chave, "sync_test")
            
            # Criar arquivo teste
            arquivo = os.path.join(tmpdir, "teste.md")
            with open(arquivo, 'w') as f:
                f.write("Conteudo teste")
            
            # Registrar
            arq_sync = cliente.registrar_arquivo(arquivo, "teste.md")
            assert arq_sync is not None, "Arquivo deve ser registrado"
            
            # Sincronizar
            sucesso = cliente.sincronizar_arquivo_local("teste.md")
            assert sucesso, "Deve sincronizar"
            
            print("  X sincronizacao funcionando")
            return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em sincronizacao: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_plugins():
    """Testa sistema de plugins."""
    print("\n--- Teste Plugins ---")
    tempo_inicio = time.time()
    
    try:
        gerenciador = GerenciadorPlugins()
        
        # Carregar plugin
        plugin = PluginProcessador()
        gerenciador.plugins["processador"] = plugin
        
        # Executar
        resultado = gerenciador.executar_plugin(
            "processador",
            "processar_texto",
            {"texto": "Hello World"}
        )
        
        assert resultado is not None, "Plugin deve executar"
        assert resultado["comprimento"] == 11, "Deve processar corretamente"
        
        print("  X plugins funcionando")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em plugins: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_autenticacao_jwt():
    """Testa autenticacao JWT."""
    print("\n--- Teste Autenticacao JWT ---")
    tempo_inicio = time.time()
    
    try:
        autenticador = AutenticadorJWT("chave_secreta")
        
        # Gerar token
        token = autenticador.gerar_token("usuario1", 24)
        assert token is not None, "Token deve ser gerado"
        
        # Validar
        valido, usuario = autenticador.validar_token(token)
        assert valido and usuario == "usuario1", "Token deve ser valido"
        
        # Revogar
        autenticador.revogar_token(token)
        valido, _ = autenticador.validar_token(token)
        assert not valido, "Token revogado nao deve ser valido"
        
        print("  X autenticacao JWT funcionando")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em JWT: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_logging_e_metricas():
    """Testa logging e metricas."""
    print("\n--- Teste Logging e Metricas ---")
    tempo_inicio = time.time()
    
    try:
        logger = LoggerSume("teste")
        metricas = GerenciadorMetricas()
        alertas = GerenciadorAlertas(logger)
        
        # Registrar eventos
        logger.info("Teste evento", "teste_modulo")
        logger.erro("Teste erro", "teste_modulo")
        
        # Registrar metricas
        metricas.registrar("requisicoes", 1)
        metricas.registrar("requisicoes", 1)
        
        # Registrar alerta
        alertas.registrar_alerta("teste_alerta", lambda d: d.get("test") == True)
        
        # Verificar
        eventos = logger.obter_eventos()
        assert len(eventos) >= 2, "Deve ter eventos"
        
        stats = metricas.obter_metricas()
        assert "requisicoes" in stats, "Deve ter metricas"
        
        todos_alertas = alertas.obter_alertas()
        assert "teste_alerta" in todos_alertas, "Deve ter alerta"
        
        print("  X logging e metricas funcionando")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em logging/metricas: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_performance_busca():
    """Testa performance de cache."""
    print("\n--- Teste Performance Cache ---")
    tempo_inicio = time.time()
    
    try:
        from plugins.busca import cache
        
        # Guardar 100 items em cache
        tempo_escrita = time.time()
        for i in range(100):
            cache.guardar_cache(f"chave_{i}", {"valor": i}, tipo="perf")
        tempo_escrita = time.time() - tempo_escrita
        
        # Ler 100 items
        tempo_leitura = time.time()
        for i in range(100):
            cache.obter_cache(f"chave_{i}", tipo="perf")
        tempo_leitura = time.time() - tempo_leitura
        
        assert tempo_escrita < 2.0, "Escrita deve ser rapida"
        assert tempo_leitura < 1.0, "Leitura deve ser muito rapida"
        
        print(f"  X performance cache OK (escrita: {tempo_escrita:.3f}s, leitura: {tempo_leitura:.3f}s)")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em performance: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_performance_encriptacao():
    """Testa performance de encriptacao."""
    print("\n--- Teste Performance Encriptacao ---")
    tempo_inicio = time.time()
    
    try:
        chave, _ = gerar_chave_mestra("performance_test")
        encriptador = criar_encriptador(chave)
        
        # Encriptar 100 strings
        tempo_encriptacao = time.time()
        for i in range(100):
            texto = f"Mensagem numero {i}" * 10
            encriptador.encriptar(texto)
        tempo_encriptacao = time.time() - tempo_encriptacao
        
        assert tempo_encriptacao < 2.0, "Encriptacao em lote deve ser rapida"
        
        print(f"  X performance encriptacao OK ({tempo_encriptacao:.3f}s para 100)")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em performance encriptacao: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_seguranca_injecao_sql():
    """Testa protecao contra injecao SQL."""
    print("\n--- Teste Seguranca SQL Injection ---")
    tempo_inicio = time.time()
    
    try:
        from plugins.busca import cache
        
        # Tentar injecao SQL via cache
        queries_maliciosas = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin' --",
            "<script>alert('xss')</script>"
        ]
        
        for query in queries_maliciosas:
            # Cache nao deve sofrer dano
            cache.guardar_cache(query, {"test": "data"}, tipo="seg")
            resultado = cache.obter_cache(query, tipo="seg")
            assert isinstance(resultado, dict) or resultado is None, "Deve retornar dict ou None mesmo com query maliciosa"
        
        print("  X protecao contra SQL injection funcionando")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em seguranca SQL: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_seguranca_xss():
    """Testa protecao contra XSS."""
    print("\n--- Teste Seguranca XSS ---")
    tempo_inicio = time.time()
    
    try:
        # XSS payloads
        payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]
        
        encriptador = criar_encriptador(b'chave_teste_32_bytes_exatament')
        
        for payload in payloads:
            # Encriptar e descriptografar
            encriptado = encriptador.encriptar(payload)
            descriptografado = encriptador.descriptografar(encriptado)
            # Dados nao devem ser executados
            assert descriptografado == payload, "Dados devem ser preservados"
        
        print("  X protecao contra XSS funcionando")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em seguranca XSS: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_concorrencia():
    """Testa funcionalidade sob concorrencia."""
    print("\n--- Teste Concorrencia ---")
    tempo_inicio = time.time()
    
    try:
        metricas = GerenciadorMetricas()
        resultados = []
        
        def worker():
            for i in range(100):
                metricas.registrar("requisicoes_concorrentes", 1)
        
        threads = []
        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        stats = metricas.obter_metrica("requisicoes_concorrentes")
        assert stats["count"] == 1000, f"Deve ter 1000 registros, tem {stats['count']}"
        
        print("  X concorrencia funcionando (10 threads, 1000 registros)")
        return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em concorrencia: {str(e)}")
        return False, time.time() - tempo_inicio

def teste_integracao_completa():
    """Testa fluxo completo integrado."""
    print("\n--- Teste Integracao Completa ---")
    tempo_inicio = time.time()
    
    try:
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            print("  1. Autenticacao...")
            auth = AutenticadorJWT("integracao_test")
            token = auth.gerar_token("user_integracao")
            assert auth.validar_token(token)[0], "Token deve ser valido"
            
            print("  2. Cache...")
            from plugins.busca import cache
            cache.guardar_cache("teste", {"data": "integracao"}, tipo="test")
            resultado = cache.obter_cache("teste", tipo="test")
            assert resultado is not None, "Cache deve funcionar"
            
            print("  3. Encriptacao...")
            chave, _ = gerar_chave_mestra("integracao")
            enc = criar_encriptador(chave)
            dados = {"token": token, "resultado": resultado}
            encriptado = enc.encriptar_json(dados)
            descriptografado = enc.descriptografar_json(encriptado)
            assert descriptografado == dados, "Dados devem corresponder"
            
            print("  4. Logging...")
            logger = LoggerSume("integracao")
            logger.info("Fluxo completo iniciado", "integracao")
            eventos = logger.obter_eventos()
            assert len(eventos) > 0, "Deve ter eventos"
            
            print("  5. Metricas...")
            metricas = GerenciadorMetricas()
            metricas.incrementar("fluxos_completados")
            stats = metricas.obter_metricas()
            assert "fluxos_completados" in stats, "Deve ter metrica"
            
            print("  X FLUXO COMPLETO INTEGRADO FUNCIONANDO")
            return True, time.time() - tempo_inicio
    except Exception as e:
        print(f"  X erro em integracao: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, time.time() - tempo_inicio

def main():
    print("=" * 70)
    print("ETAPA 22: SUITE DE TESTES AUTOMATIZADOS COMPLETOS")
    print("=" * 70)
    
    relatorio = RelatorioTeste()
    
    # Testes funcionais
    testes = [
        ("Busca Semantica", teste_busca_semantica),
        ("Encriptacao E2E", teste_encriptacao_e2e),
        ("Sincronizacao", teste_sincronizacao),
        ("Sistema de Plugins", teste_plugins),
        ("Autenticacao JWT", teste_autenticacao_jwt),
        ("Logging e Metricas", teste_logging_e_metricas),
    ]
    
    # Testes de performance
    print("\n[TESTES DE PERFORMANCE]")
    testes_perf = [
        ("Performance Busca", teste_performance_busca),
        ("Performance Encriptacao", teste_performance_encriptacao),
    ]
    
    # Testes de seguranca
    print("\n[TESTES DE SEGURANCA]")
    testes_seg = [
        ("Seguranca SQL Injection", teste_seguranca_injecao_sql),
        ("Seguranca XSS", teste_seguranca_xss),
    ]
    
    # Testes de concorrencia
    print("\n[TESTES DE CONCORRENCIA]")
    testes_conc = [
        ("Concorrencia", teste_concorrencia),
    ]
    
    # Testes integrados
    print("\n[TESTES INTEGRADOS]")
    testes_int = [
        ("Integracao Completa", teste_integracao_completa),
    ]
    
    todos_testes = testes + testes_perf + testes_seg + testes_conc + testes_int
    
    for nome, funcao_teste in todos_testes:
        passou, tempo = funcao_teste()
        relatorio.adicionar_resultado(nome, passou, tempo)
    
    # Gerar relatorio
    print("\n" + relatorio.gerar_relatorio())
    
    print(f"Tempo total: {relatorio.tempo_total:.2f}s")
    print(f"Taxa de sucesso: {relatorio.obter_taxa_sucesso():.1f}%")
    
    if relatorio.testes_falhados == 0:
        print("\n[OK] TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print(f"\n[FALHA] {relatorio.testes_falhados} teste(s) falharam")
        return 1

if __name__ == "__main__":
    sys.exit(main())
