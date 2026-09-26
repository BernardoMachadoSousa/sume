"""
Teste da Etapa 21: Monitoramento e logging avancado.
Valida logging estruturado, metricas, alertas e estatisticas.
"""

import sys
import os
import time
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from plugins.monitoramento import (
    NivelLog, EventoLog, LoggerSume, Metrica, GerenciadorMetricas,
    Alerta, GerenciadorAlertas, ColecionadorMetricasAuto,
    obter_logger, obter_metricas, obter_alertas
)

def teste_nivel_log():
    """Testa niveis de log."""
    print("\n--- Niveis de Log ---")
    
    assert NivelLog.DEBUG < NivelLog.INFO, "DEBUG deve ser menor que INFO"
    assert NivelLog.INFO < NivelLog.AVISO, "INFO deve ser menor que AVISO"
    assert NivelLog.AVISO < NivelLog.ERRO, "AVISO deve ser menor que ERRO"
    assert NivelLog.ERRO < NivelLog.CRITICO, "ERRO deve ser menor que CRITICO"
    print("  X ordem de niveis correta")
    
    assert NivelLog.NOMES[NivelLog.DEBUG] == "DEBUG", "Nome DEBUG correto"
    assert NivelLog.NOMES[NivelLog.CRITICO] == "CRITICO", "Nome CRITICO correto"
    print("  X nomes de niveis corretos")

def teste_evento_log():
    """Testa criacao de eventos de log."""
    print("\n--- Evento Log ---")
    
    evento = EventoLog(NivelLog.INFO, "Teste mensagem", "teste_modulo", {"chave": "valor"})
    
    assert evento.nivel == NivelLog.INFO, "Nivel correto"
    assert evento.mensagem == "Teste mensagem", "Mensagem correta"
    assert evento.modulo == "teste_modulo", "Modulo correto"
    assert evento.dados == {"chave": "valor"}, "Dados corretos"
    assert evento.id, "ID deve ser gerado"
    print("  X evento criado corretamente")
    
    evento_dict = evento.para_dict()
    assert "id" in evento_dict, "Dict deve ter id"
    assert "nivel" in evento_dict, "Dict deve ter nivel"
    assert "timestamp" in evento_dict, "Dict deve ter timestamp"
    print("  X conversao para dict correta")
    
    str_evento = str(evento)
    assert "INFO" in str_evento, "String deve ter nivel"
    assert "Teste mensagem" in str_evento, "String deve ter mensagem"
    print("  X string representation correta")

def teste_logger_basico():
    """Testa funcoes basicas do logger."""
    print("\n--- Logger Basico ---")
    
    logger = LoggerSume("teste", NivelLog.DEBUG)
    
    # Registrar eventos
    logger.debug("Mensagem debug", "modulo1")
    logger.info("Mensagem info", "modulo1")
    logger.aviso("Mensagem aviso", "modulo1")
    logger.erro("Mensagem erro", "modulo1")
    logger.critico("Mensagem critica", "modulo1")
    
    eventos = logger.obter_eventos()
    assert len(eventos) == 5, "Deve ter 5 eventos"
    print("  X registrar eventos funcionando")
    
    # Filtrar por nivel
    eventos_erro = logger.obter_eventos(nivel_minimo=NivelLog.ERRO)
    assert len(eventos_erro) == 2, "Deve ter 2 eventos de erro ou critico"
    print("  X filtro por nivel funcionando")
    
    # Filtrar por modulo
    eventos_mod = logger.obter_eventos(modulo="modulo1")
    assert len(eventos_mod) == 5, "Todos devem ser do modulo1"
    print("  X filtro por modulo funcionando")
    
    # Limite
    eventos_limite = logger.obter_eventos(limite=2)
    assert len(eventos_limite) == 2, "Deve retornar maximo 2"
    print("  X limite funcionando")

def teste_logger_arquivo():
    """Testa logging em arquivo."""
    print("\n--- Logger Arquivo ---")
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        arquivo = os.path.join(tmpdir, "teste.log")
        logger = LoggerSume("teste", NivelLog.INFO)
        logger.definir_arquivo_log(arquivo)
        
        logger.info("Teste arquivo", "modulo")
        logger.erro("Erro teste", "modulo")
        
        # Aguardar escrita
        time.sleep(0.1)
        
        # Verificar arquivo
        assert os.path.exists(arquivo), "Arquivo deve existir"
        with open(arquivo, 'r') as f:
            conteudo = f.read()
            assert "Teste arquivo" in conteudo, "Deve conter mensagem"
            assert "Erro teste" in conteudo, "Deve conter erro"
        
        print("  X arquivo de log criado e escrito")

def teste_logger_handler():
    """Testa handlers customizados do logger."""
    print("\n--- Logger Handler ---")
    
    eventos_capturados = []
    
    def handler(evento):
        eventos_capturados.append(evento)
    
    logger = LoggerSume("teste", NivelLog.INFO)
    logger.registrar_handler(handler)
    
    logger.info("Teste 1", "modulo")
    logger.erro("Teste 2", "modulo")
    
    time.sleep(0.1)
    
    assert len(eventos_capturados) == 2, "Deve capturar 2 eventos"
    assert eventos_capturados[0].mensagem == "Teste 1", "Primeiro evento correto"
    print("  X handlers funcionando")

def teste_metrica():
    """Testa classe Metrica."""
    print("\n--- Metrica ---")
    
    metrica = Metrica("latencia_ms", "histograma")
    
    # Registrar valores
    for i in range(10):
        metrica.registrar(float(i * 10))
    
    stats = metrica.obter_estatisticas()
    assert stats["count"] == 10, "Deve ter 10 valores"
    assert stats["total"] == 450, "Total deve ser 450"
    assert stats["media"] == 45, "Media deve ser 45"
    assert stats["minima"] == 0, "Minima deve ser 0"
    assert stats["maxima"] == 90, "Maxima deve ser 90"
    print("  X estatisticas corretas")
    
    assert "desvio_padrao" in stats, "Deve ter desvio padrao"
    assert stats["desvio_padrao"] > 0, "Desvio padrao deve ser positivo"
    print("  X desvio padrao calculado")

def teste_gerenciador_metricas():
    """Testa gerenciador de metricas."""
    print("\n--- Gerenciador Metricas ---")
    
    metricas = GerenciadorMetricas()
    
    # Criar e registrar
    metricas.registrar("requisicoes_total", 1)
    metricas.registrar("requisicoes_total", 1)
    metricas.registrar("requisicoes_total", 1)
    
    stats = metricas.obter_metrica("requisicoes_total")
    assert stats["count"] == 3, "Deve ter 3 registros"
    assert stats["total"] == 3, "Total deve ser 3"
    print("  X registrar e obter metrica")
    
    # Incrementar
    metricas.incrementar("cliques", 5)
    stats = metricas.obter_metrica("cliques")
    assert stats["total"] == 5, "Total deve ser 5"
    print("  X incrementar funcionando")
    
    # Definir gauge
    metricas.definir_gauge("usuarios_online", 42)
    stats = metricas.obter_metrica("usuarios_online")
    assert stats["total"] == 42, "Gauge deve ter valor 42"
    print("  X gauge funcionando")
    
    # Obter todas
    todas = metricas.obter_metricas()
    assert len(todas) >= 3, "Deve ter pelo menos 3 metricas"
    print("  X obter todas as metricas")

def teste_alerta():
    """Testa criacao e verificacao de alertas."""
    print("\n--- Alerta ---")
    
    # Alerta por CPU alta
    alerta = Alerta(
        "cpu_alta",
        lambda d: d.get("cpu", 0) > 80,
        "CRITICO"
    )
    
    # CPU normal
    assert not alerta.verificar({"cpu": 50}), "CPU 50% nao deve disparar"
    assert not alerta.ativo, "Alerta nao deve estar ativo"
    print("  X alerta nao dispara com condicao falsa")
    
    # CPU alta
    assert alerta.verificar({"cpu": 85}), "CPU 85% deve disparar"
    assert alerta.ativo, "Alerta deve estar ativo"
    print("  X alerta dispara com condicao verdadeira")
    
    # CPU voltar ao normal
    assert not alerta.verificar({"cpu": 40}), "CPU 40% deve desativar"
    assert not alerta.ativo, "Alerta deve estar inativo"
    print("  X alerta desativa quando condicao falsa")
    
    alerta_dict = alerta.para_dict()
    assert "nome" in alerta_dict, "Dict deve ter nome"
    assert "ativo" in alerta_dict, "Dict deve ter ativo"
    assert "contador" in alerta_dict, "Dict deve ter contador"
    print("  X conversao para dict correta")

def teste_gerenciador_alertas():
    """Testa gerenciador de alertas."""
    print("\n--- Gerenciador Alertas ---")
    
    logger = LoggerSume("teste")
    gerenciador = GerenciadorAlertas(logger)
    
    alertas_disparados = []
    
    def callback_alerta(alerta):
        alertas_disparados.append(alerta)
    
    gerenciador.registrar_callback(callback_alerta)
    
    # Registrar alertas
    gerenciador.registrar_alerta(
        "memoria_alta",
        lambda d: d.get("memoria", 0) > 85,
        "AVISO"
    )
    
    gerenciador.registrar_alerta(
        "disco_critico",
        lambda d: d.get("disco", 0) > 95,
        "CRITICO"
    )
    
    alertas = gerenciador.obter_alertas()
    assert len(alertas) == 2, "Deve ter 2 alertas"
    print("  X registrar alertas")
    
    # Verificar sem alerta
    gerenciador.verificar_alertas({"memoria": 50, "disco": 60})
    assert len(alertas_disparados) == 0, "Nenhum alerta deve disparar"
    print("  X verificacao sem alerta")
    
    # Verificar com alerta
    gerenciador.verificar_alertas({"memoria": 90, "disco": 60})
    assert len(alertas_disparados) == 1, "Um alerta deve disparar"
    print("  X alerta disparado via callback")
    
    # Obter alertas ativos
    ativos = gerenciador.obter_alertas_ativos()
    assert len(ativos) == 1, "Um alerta deve estar ativo"
    print("  X obter alertas ativos")

def teste_colecionador_metricas():
    """Testa colecao automatica de metricas."""
    print("\n--- Colecionador Metricas ---")
    
    metricas = GerenciadorMetricas()
    colecionador = ColecionadorMetricasAuto(metricas, intervalo=0.1)
    
    # Iniciar coleta
    colecionador.iniciar()
    assert colecionador.ativo, "Colecionador deve estar ativo"
    print("  X colecionador iniciado")
    
    # Aguardar coleta
    time.sleep(0.3)
    
    # Parar coleta
    colecionador.parar()
    assert not colecionador.ativo, "Colecionador deve estar inativo"
    print("  X colecionador parado")

def teste_logger_global():
    """Testa logger global."""
    print("\n--- Logger Global ---")
    
    logger = obter_logger()
    assert logger is not None, "Logger deve existir"
    
    logger.info("Teste global", "teste")
    eventos = logger.obter_eventos()
    assert len(eventos) > 0, "Deve ter eventos"
    print("  X logger global funcionando")

def teste_metricas_global():
    """Testa metricas global."""
    print("\n--- Metricas Global ---")
    
    metricas = obter_metricas()
    assert metricas is not None, "Metricas deve existir"
    
    metricas.registrar("teste_global", 42)
    stats = metricas.obter_metrica("teste_global")
    assert stats is not None, "Deve obter metrica"
    print("  X metricas global funcionando")

def teste_alertas_global():
    """Testa alertas global."""
    print("\n--- Alertas Global ---")
    
    alertas = obter_alertas()
    assert alertas is not None, "Alertas deve existir"
    
    alertas.registrar_alerta("teste", lambda d: False)
    todos = alertas.obter_alertas()
    assert "teste" in todos, "Alerta deve estar registrado"
    print("  X alertas global funcionando")

def teste_fluxo_completo_monitoramento():
    """Testa fluxo completo de monitoramento."""
    print("\n--- Fluxo Completo Monitoramento ---")
    
    logger = LoggerSume("app", NivelLog.INFO)
    metricas = GerenciadorMetricas()
    alertas = GerenciadorAlertas(logger)
    
    alertas_disparados = []
    alertas.registrar_callback(lambda a: alertas_disparados.append(a))
    
    print("  1. Sistema iniciado...")
    logger.info("Sistema iniciado", "main")
    
    print("  2. Registrando metricas...")
    for i in range(5):
        metricas.registrar("requisicoes_processadas", 1)
        metricas.definir_gauge("usuarios_conectados", 10 + i)
        time.sleep(0.05)
    
    print("  3. Registrando alertas...")
    alertas.registrar_alerta(
        "muitos_usuarios",
        lambda d: d.get("usuarios", 0) > 12,
        "AVISO"
    )
    
    print("  4. Verificando alertas...")
    alertas.verificar_alertas({"usuarios": 15})
    
    print("  5. Analisando dados...")
    stats_req = metricas.obter_metricas()
    assert "requisicoes_processadas" in stats_req, "Deve ter metricas"
    
    print("  6. Obtendo eventos...")
    eventos = logger.obter_eventos()
    assert len(eventos) > 0, "Deve ter eventos"
    
    print("  7. Verificando alertas ativos...")
    ativos = alertas.obter_alertas_ativos()
    assert len(ativos) > 0, "Deve ter alertas ativos"
    
    print("  X FLUXO COMPLETO FUNCIONANDO")

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 21: Monitoramento e Logging")
    print("=" * 68)
    
    try:
        teste_nivel_log()
        teste_evento_log()
        teste_logger_basico()
        teste_logger_arquivo()
        teste_logger_handler()
        teste_metrica()
        teste_gerenciador_metricas()
        teste_alerta()
        teste_gerenciador_alertas()
        teste_colecionador_metricas()
        teste_logger_global()
        teste_metricas_global()
        teste_alertas_global()
        teste_fluxo_completo_monitoramento()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 21 PASSARAM!")
        print("Monitoramento e logging validados.")
        print("=" * 68)
        return 0
        
    except AssertionError as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
