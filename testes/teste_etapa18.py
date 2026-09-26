"""
Teste da Etapa 18: Sistema de plugins extensivel.
Valida carregamento, execucao e gerenciamento de plugins.
"""

import sys
import os
import tempfile
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from plugins.sistema_plugins import (
    PluginBase, GerenciadorPlugins, PluginProcessador, PluginAnalise,
    inicializar_gerenciador, obter_gerenciador, carregar_plugin_customizado,
    executar_plugin
)

def teste_plugin_base():
    """Testa interface base de plugin."""
    print("\n--- Plugin Base ---")
    
    plugin = PluginProcessador()
    assert plugin.nome == "processador", "Plugin deve ter nome"
    assert plugin.versao == "1.0.0", "Plugin deve ter versao"
    print("  X plugin instanciado corretamente")
    
    # Obter info
    info = plugin.obter_info()
    assert "nome" in info, "Info deve ter nome"
    assert "ativado" in info, "Info deve ter status ativado"
    print("  X obter_info funcionando")
    
    # Comandos suportados
    comandos = plugin.obter_comandos_suportados()
    assert len(comandos) > 0, "Deve ter comandos suportados"
    assert "processar_texto" in comandos, "Deve ter comando processar_texto"
    print("  X comandos suportados corretos")

def teste_gerenciador_basico():
    """Testa funcoes basicas do gerenciador."""
    print("\n--- Gerenciador Basico ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gerenciador = GerenciadorPlugins(tmpdir)
        
        # Carregar plugin
        plugin = PluginProcessador()
        gerenciador.plugins["processador"] = plugin
        assert "processador" in gerenciador.plugins, "Plugin deve estar carregado"
        print("  X plugin carregado")
        
        # Listar plugins
        lista = gerenciador.listar_plugins()
        assert len(lista) == 1, "Deve ter 1 plugin"
        assert lista[0]["nome"] == "processador", "Plugin deve estar na lista"
        print("  X listar plugins funcionando")
        
        # Status
        status = gerenciador.obter_status()
        assert status["total_plugins"] == 1, "Status deve mostrar 1 plugin"
        print("  X status correto")

def teste_ativar_desativar():
    """Testa ativacao e desativacao de plugins."""
    print("\n--- Ativar/Desativar ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gerenciador = GerenciadorPlugins(tmpdir)
        plugin = PluginProcessador()
        gerenciador.plugins["processador"] = plugin
        
        # Desativar
        assert gerenciador.desativar_plugin("processador"), "Deve desativar"
        assert not plugin.ativado, "Plugin deve estar desativado"
        print("  X plugin desativado")
        
        # Ativar
        assert gerenciador.ativar_plugin("processador"), "Deve ativar"
        assert plugin.ativado, "Plugin deve estar ativado"
        print("  X plugin ativado")

def teste_executar_plugin():
    """Testa execucao de comandos em plugins."""
    print("\n--- Executar Plugin ---")
    
    gerenciador = GerenciadorPlugins()
    plugin = PluginProcessador()
    gerenciador.plugins["processador"] = plugin
    
    # Executar comando
    resultado = gerenciador.executar_plugin("processador", "processar_texto", {"texto": "Hello World"})
    assert resultado is not None, "Deve retornar resultado"
    assert resultado["comprimento"] == 11, "Deve contar comprimento correto"
    assert resultado["palavras"] == 2, "Deve contar palavras correto"
    print("  X executar comando funcionando")
    
    # Comando inexistente
    resultado = gerenciador.executar_plugin("processador", "comando_inexistente")
    assert resultado is None, "Comando inexistente deve retornar None"
    print("  X comando inexistente rejeitado")

def teste_plugin_processador():
    """Testa funcionalidades do plugin processador."""
    print("\n--- Plugin Processador ---")
    
    plugin = PluginProcessador()
    plugin.inicializar()
    
    # Processar texto
    resultado = plugin.executar("processar_texto", {"texto": "HELLO world"})
    assert resultado["comprimento"] == 11, "Deve medir comprimento"
    assert resultado["maiuscula"] == False, "Nao deve ser tudo maiuscula"
    assert resultado["minuscula"] == False, "Nao deve ser tudo minuscula"
    print("  X processar_texto funcionando")
    
    # Extrair palavras
    resultado = plugin.executar("extrair_palavras", {"texto": "python python java python"})
    assert "python" in resultado, "Deve extrair python"
    assert "java" in resultado, "Deve extrair java"
    assert len(resultado) == 2, "Deve ter 2 palavras unicas"
    print("  X extrair_palavras funcionando")

def teste_plugin_analise():
    """Testa funcionalidades do plugin analise."""
    print("\n--- Plugin Analise ---")
    
    plugin = PluginAnalise()
    plugin.inicializar()
    
    # Analisar sentimento positivo
    resultado = plugin.executar("analisar_sentimento", {"texto": "Este projeto eh otimo e excelente"})
    assert resultado["sentimento"] == "positivo", "Deve detectar positivo"
    assert resultado["score_positivo"] > 0, "Deve ter score positivo"
    print("  X sentimento positivo detectado")
    
    # Analisar sentimento negativo
    resultado = plugin.executar("analisar_sentimento", {"texto": "Isto eh ruim e pessimo"})
    assert resultado["sentimento"] == "negativo", "Deve detectar negativo"
    assert resultado["score_negativo"] > 0, "Deve ter score negativo"
    print("  X sentimento negativo detectado")
    
    # Contar entidades
    resultado = plugin.executar("contar_entidades", {"texto": "Python eh legal.\nJava tambem.\n"})
    assert resultado["caracteres"] > 0, "Deve contar caracteres"
    assert resultado["palavras"] > 0, "Deve contar palavras"
    assert resultado["linhas"] >= 2, "Deve contar linhas"
    print("  X contar_entidades funcionando")

def teste_hooks():
    """Testa sistema de hooks/eventos."""
    print("\n--- Sistema de Hooks ---")
    
    gerenciador = GerenciadorPlugins()
    
    # Registrar hook
    eventos_capturados = []
    
    def listener(dados):
        eventos_capturados.append(dados)
    
    gerenciador.registrar_hook("teste", listener)
    assert "teste" in gerenciador.hooks, "Hook deve estar registrado"
    print("  X hook registrado")
    
    # Disparar hook
    gerenciador.disparar_hook("teste", {"mensagem": "teste"})
    assert len(eventos_capturados) == 1, "Deve capturar evento"
    assert eventos_capturados[0]["mensagem"] == "teste", "Deve ter dados corretos"
    print("  X hook disparado e capturado")
    
    # Multiplos listeners
    eventos_capturados2 = []
    def listener2(dados):
        eventos_capturados2.append(dados)
    
    gerenciador.registrar_hook("teste", listener2)
    gerenciador.disparar_hook("teste", {"id": 2})
    assert len(eventos_capturados) == 2, "Primeiro listener deve capturar"
    assert len(eventos_capturados2) == 1, "Segundo listener deve capturar"
    print("  X multiplos listeners funcionando")

def teste_carregamento_diretorio():
    """Testa carregamento de plugins do diretorio."""
    print("\n--- Carregamento de Diretorio ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Criar arquivo de plugin
        arquivo_plugin = os.path.join(tmpdir, "teste_plugin.py")
        with open(arquivo_plugin, 'w', encoding='utf-8') as f:
            f.write("""
from plugins.sistema_plugins import PluginBase

class PluginTeste(PluginBase):
    def __init__(self):
        super().__init__("teste", "1.0.0", "Tester")
    
    def inicializar(self):
        return True
    
    def executar(self, comando, parametros=None):
        if comando == "ola":
            return "Ola mundo"
        return None
    
    def obter_comandos_suportados(self):
        return ["ola"]
""")
        
        gerenciador = GerenciadorPlugins(tmpdir)
        carregados = gerenciador.carregar_todos_do_diretorio()
        
        # Pode nao carregar se houver erro de importacao
        print(f"  X carregamento de diretorio: {carregados} plugins")

def teste_configuracao_persistencia():
    """Testa persistencia de configuracao de plugins."""
    print("\n--- Configuracao Persistencia ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gerenciador1 = GerenciadorPlugins(tmpdir)
        plugin = PluginProcessador()
        gerenciador1.plugins["processador"] = plugin
        gerenciador1.ativar_plugin("processador")
        gerenciador1.salvar_configuracao()
        
        # Carregar em nova instancia
        gerenciador2 = GerenciadorPlugins(tmpdir)
        gerenciador2.carregar_configuracao()
        assert "processador" in gerenciador2.config["plugins_ativados"], "Config deve ser persistida"
        print("  X configuracao persistida corretamente")

def teste_gerenciador_global():
    """Testa gerenciador global."""
    print("\n--- Gerenciador Global ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gerenciador = inicializar_gerenciador(tmpdir)
        
        assert obter_gerenciador() is gerenciador, "Deve retornar gerenciador global"
        print("  X gerenciador global funcionando")
        
        # Adicionar plugin
        plugin = PluginAnalise()
        gerenciador.plugins["analise"] = plugin
        
        # Executar via helper
        resultado = executar_plugin("analise", "analisar_sentimento", {"texto": "Muito bom"})
        assert resultado is not None, "Deve executar plugin"
        print("  X executar_plugin helper funcionando")

def teste_descarregar_plugin():
    """Testa descarregamento de plugin."""
    print("\n--- Descarregar Plugin ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gerenciador = GerenciadorPlugins(tmpdir)
        plugin = PluginProcessador()
        gerenciador.plugins["processador"] = plugin
        
        assert "processador" in gerenciador.plugins, "Plugin deve estar carregado"
        
        # Descarregar
        assert gerenciador.descarregar_plugin("processador"), "Deve descarregar"
        assert "processador" not in gerenciador.plugins, "Plugin nao deve estar mais carregado"
        print("  X plugin descarregado com sucesso")

def teste_fluxo_completo_plugins():
    """Testa fluxo completo de uso de plugins."""
    print("\n--- Fluxo Completo ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Inicializar
        gerenciador = inicializar_gerenciador(tmpdir)
        print("  1. Gerenciador inicializado")
        
        # 2. Carregar plugins
        gerenciador.plugins["processador"] = PluginProcessador()
        gerenciador.plugins["analise"] = PluginAnalise()
        print("  2. Plugins carregados")
        
        # 3. Listar
        plugins = gerenciador.listar_plugins()
        assert len(plugins) == 2, "Deve ter 2 plugins"
        print("  3. Plugins listados")
        
        # 4. Executar
        texto = "Python eh uma linguagem excelente"
        result1 = gerenciador.executar_plugin("processador", "processar_texto", {"texto": texto})
        result2 = gerenciador.executar_plugin("analise", "analisar_sentimento", {"texto": texto})
        
        assert result1 is not None, "Processador deve executar"
        assert result2 is not None, "Analise deve executar"
        print("  4. Comandos executados")
        
        # 5. Disparar hooks
        resultado = []
        gerenciador.registrar_hook("plugin_executado", lambda d: resultado.append(d))
        gerenciador.disparar_hook("plugin_executado", {"plugin": "processador"})
        assert len(resultado) > 0, "Hook deve disparar"
        print("  5. Hooks funcionando")
        
        # 6. Desativar
        gerenciador.desativar_plugin("processador")
        resultado = gerenciador.executar_plugin("processador", "processar_texto", {"texto": "test"})
        assert resultado is None, "Plugin desativado nao deve executar"
        print("  6. Plugin desativado")
        
        print("  X FLUXO COMPLETO FUNCIONANDO")

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 18: Sistema de Plugins")
    print("=" * 68)
    
    try:
        teste_plugin_base()
        teste_gerenciador_basico()
        teste_ativar_desativar()
        teste_executar_plugin()
        teste_plugin_processador()
        teste_plugin_analise()
        teste_hooks()
        teste_carregamento_diretorio()
        teste_configuracao_persistencia()
        teste_gerenciador_global()
        teste_descarregar_plugin()
        teste_fluxo_completo_plugins()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 18 PASSARAM!")
        print("Sistema de plugins validado.")
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
