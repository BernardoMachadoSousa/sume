"""
Sistema de plugins extensivel para Sumé.
Permite que usuarios criem plugins customizados.
"""

import os
import json
import importlib.util
from typing import Dict, List, Any, Callable, Optional, Type
from abc import ABC, abstractmethod
from datetime import datetime
import inspect

class PluginBase(ABC):
    """Classe base para todos os plugins."""
    
    def __init__(self, nome: str, versao: str = "1.0.0", autor: str = "Unknown"):
        self.nome = nome
        self.versao = versao
        self.autor = autor
        self.ativado = True
        self.carregado_em = datetime.now().isoformat()
    
    @abstractmethod
    def inicializar(self) -> bool:
        """Inicializa o plugin. Deve retornar True se sucesso."""
        pass
    
    @abstractmethod
    def executar(self, comando: str, parametros: Dict = None) -> Any:
        """Executa comando do plugin."""
        pass
    
    def finalizar(self):
        """Finaliza o plugin (limpeza)."""
        pass
    
    def obter_info(self) -> Dict:
        """Retorna informacoes do plugin."""
        return {
            "nome": self.nome,
            "versao": self.versao,
            "autor": self.autor,
            "ativado": self.ativado,
            "carregado_em": self.carregado_em
        }
    
    def obter_comandos_suportados(self) -> List[str]:
        """Retorna lista de comandos suportados."""
        return []

class GerenciadorPlugins:
    """Gerencia carregamento, descarregamento e execucao de plugins."""
    
    def __init__(self, diretorio_plugins: str = None):
        self.diretorio_plugins = diretorio_plugins or os.path.expanduser("~/.sume/plugins_custom")
        self.plugins: Dict[str, PluginBase] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.config_plugins = os.path.join(self.diretorio_plugins, "config.json")
        self.carregar_configuracao()
    
    def carregar_configuracao(self):
        """Carrega configuracao de plugins."""
        os.makedirs(self.diretorio_plugins, exist_ok=True)
        if os.path.exists(self.config_plugins):
            try:
                with open(self.config_plugins, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except:
                self.config = {"plugins_ativados": []}
        else:
            self.config = {"plugins_ativados": []}
    
    def salvar_configuracao(self):
        """Salva configuracao de plugins."""
        os.makedirs(self.diretorio_plugins, exist_ok=True)
        with open(self.config_plugins, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def carregar_plugin(self, arquivo_plugin: str) -> bool:
        """Carrega plugin de arquivo Python."""
        try:
            nome_arquivo = os.path.basename(arquivo_plugin)
            nome_modulo = os.path.splitext(nome_arquivo)[0]
            
            spec = importlib.util.spec_from_file_location(nome_modulo, arquivo_plugin)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            
            # Procura classe que herda de PluginBase
            for nome, obj in inspect.getmembers(modulo):
                if inspect.isclass(obj) and issubclass(obj, PluginBase) and obj != PluginBase:
                    plugin = obj()
                    
                    if plugin.inicializar():
                        self.plugins[plugin.nome] = plugin
                        if plugin.nome not in self.config["plugins_ativados"]:
                            self.config["plugins_ativados"].append(plugin.nome)
                        self.salvar_configuracao()
                        return True
            
            return False
        except Exception as e:
            print(f"Erro ao carregar plugin: {str(e)}")
            return False
    
    def descarregar_plugin(self, nome: str) -> bool:
        """Descarrega plugin."""
        if nome not in self.plugins:
            return False
        
        try:
            self.plugins[nome].finalizar()
            del self.plugins[nome]
            
            if nome in self.config["plugins_ativados"]:
                self.config["plugins_ativados"].remove(nome)
            self.salvar_configuracao()
            return True
        except:
            return False
    
    def executar_plugin(self, nome: str, comando: str, parametros: Dict = None) -> Any:
        """Executa comando em plugin."""
        if nome not in self.plugins:
            return None
        
        plugin = self.plugins[nome]
        if not plugin.ativado:
            return None
        
        try:
            return plugin.executar(comando, parametros or {})
        except Exception as e:
            print(f"Erro ao executar plugin {nome}: {str(e)}")
            return None
    
    def ativar_plugin(self, nome: str) -> bool:
        """Ativa plugin."""
        if nome not in self.plugins:
            return False
        
        self.plugins[nome].ativado = True
        if nome not in self.config["plugins_ativados"]:
            self.config["plugins_ativados"].append(nome)
        self.salvar_configuracao()
        return True
    
    def desativar_plugin(self, nome: str) -> bool:
        """Desativa plugin."""
        if nome not in self.plugins:
            return False
        
        self.plugins[nome].ativado = False
        if nome in self.config["plugins_ativados"]:
            self.config["plugins_ativados"].remove(nome)
        self.salvar_configuracao()
        return True
    
    def listar_plugins(self) -> List[Dict]:
        """Lista todos os plugins carregados."""
        return [
            {
                "nome": nome,
                "info": plugin.obter_info(),
                "comandos": plugin.obter_comandos_suportados()
            }
            for nome, plugin in self.plugins.items()
        ]
    
    def registrar_hook(self, evento: str, funcao: Callable):
        """Registra funcao para ser executada em evento."""
        if evento not in self.hooks:
            self.hooks[evento] = []
        self.hooks[evento].append(funcao)
    
    def disparar_hook(self, evento: str, dados: Any = None):
        """Dispara hook para todos os listeners."""
        if evento not in self.hooks:
            return
        
        for funcao in self.hooks[evento]:
            try:
                funcao(dados)
            except Exception as e:
                print(f"Erro ao executar hook {evento}: {str(e)}")
    
    def obter_plugin(self, nome: str) -> Optional[PluginBase]:
        """Obtém instancia de plugin."""
        return self.plugins.get(nome)
    
    def carregar_todos_do_diretorio(self) -> int:
        """Carrega todos os plugins do diretorio."""
        carregados = 0
        
        if not os.path.exists(self.diretorio_plugins):
            return 0
        
        for arquivo in os.listdir(self.diretorio_plugins):
            if arquivo.endswith(".py") and not arquivo.startswith("_"):
                caminho_completo = os.path.join(self.diretorio_plugins, arquivo)
                if self.carregar_plugin(caminho_completo):
                    carregados += 1
        
        return carregados
    
    def obter_status(self) -> Dict:
        """Retorna status do gerenciador."""
        return {
            "total_plugins": len(self.plugins),
            "plugins_ativados": len([p for p in self.plugins.values() if p.ativado]),
            "diretorio": self.diretorio_plugins,
            "plugins": self.listar_plugins()
        }

class PluginProcessador(PluginBase):
    """Plugin exemplo: processa dados customizados."""
    
    def __init__(self):
        super().__init__("processador", "1.0.0", "Sumé Team")
    
    def inicializar(self) -> bool:
        return True
    
    def executar(self, comando: str, parametros: Dict = None) -> Any:
        parametros = parametros or {}
        
        if comando == "processar_texto":
            texto = parametros.get("texto", "")
            return self._processar_texto(texto)
        elif comando == "extrair_palavras":
            texto = parametros.get("texto", "")
            return self._extrair_palavras(texto)
        else:
            return None
    
    def _processar_texto(self, texto: str) -> Dict:
        """Processa texto e retorna estatisticas."""
        return {
            "comprimento": len(texto),
            "palavras": len(texto.split()),
            "maiuscula": texto.isupper(),
            "minuscula": texto.islower()
        }
    
    def _extrair_palavras(self, texto: str) -> List[str]:
        """Extrai palavras unicas."""
        palavras = texto.lower().split()
        return list(set(palavras))
    
    def obter_comandos_suportados(self) -> List[str]:
        return ["processar_texto", "extrair_palavras"]

class PluginAnalise(PluginBase):
    """Plugin exemplo: analisa sentimento e temas."""
    
    def __init__(self):
        super().__init__("analise", "1.0.0", "Sumé Team")
    
    def inicializar(self) -> bool:
        return True
    
    def executar(self, comando: str, parametros: Dict = None) -> Any:
        parametros = parametros or {}
        
        if comando == "analisar_sentimento":
            texto = parametros.get("texto", "")
            return self._analisar_sentimento(texto)
        elif comando == "contar_entidades":
            texto = parametros.get("texto", "")
            return self._contar_entidades(texto)
        else:
            return None
    
    def _analisar_sentimento(self, texto: str) -> Dict:
        """Analisa sentimento (exemplo simplificado)."""
        positivo = len([p for p in ["bom", "otimo", "excelente", "perfeito"] if p in texto.lower()])
        negativo = len([n for n in ["ruim", "pessimo", "horrivel", "terrible"] if n in texto.lower()])
        
        if positivo > negativo:
            sentimento = "positivo"
        elif negativo > positivo:
            sentimento = "negativo"
        else:
            sentimento = "neutro"
        
        return {
            "sentimento": sentimento,
            "score_positivo": positivo,
            "score_negativo": negativo
        }
    
    def _contar_entidades(self, texto: str) -> Dict:
        """Conta tipos de entidades."""
        return {
            "caracteres": len(texto),
            "palavras": len(texto.split()),
            "linhas": len(texto.split("\n")),
            "sentencas": len([s for s in texto.split(".") if s.strip()])
        }
    
    def obter_comandos_suportados(self) -> List[str]:
        return ["analisar_sentimento", "contar_entidades"]

# Gerenciador global
gerenciador_plugins_global = None

def inicializar_gerenciador(diretorio: str = None) -> GerenciadorPlugins:
    """Helper para inicializar gerenciador global."""
    global gerenciador_plugins_global
    gerenciador_plugins_global = GerenciadorPlugins(diretorio)
    return gerenciador_plugins_global

def obter_gerenciador() -> Optional[GerenciadorPlugins]:
    """Helper para obter gerenciador global."""
    return gerenciador_plugins_global

def carregar_plugin_customizado(arquivo: str) -> bool:
    """Helper para carregar plugin customizado."""
    if gerenciador_plugins_global is None:
        return False
    return gerenciador_plugins_global.carregar_plugin(arquivo)

def executar_plugin(nome: str, comando: str, parametros: Dict = None) -> Any:
    """Helper para executar comando de plugin."""
    if gerenciador_plugins_global is None:
        return None
    return gerenciador_plugins_global.executar_plugin(nome, comando, parametros)
