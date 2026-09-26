"""
Sistema de monitoramento e logging avancado para Sumé.
Implementa logging estruturado, metricas, alertas e estatisticas.
"""

import os
import json
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib

class NivelLog:
    """Niveis de severidade de log."""
    DEBUG = 10
    INFO = 20
    AVISO = 30
    ERRO = 40
    CRITICO = 50
    
    NOMES = {
        DEBUG: "DEBUG",
        INFO: "INFO",
        AVISO: "AVISO",
        ERRO: "ERRO",
        CRITICO: "CRITICO"
    }

class EventoLog:
    """Representa um evento de log."""
    
    def __init__(self, nivel: int, mensagem: str, modulo: str = "", dados: Dict = None):
        self.nivel = nivel
        self.mensagem = mensagem
        self.modulo = modulo
        self.dados = dados or {}
        self.timestamp = datetime.now()
        self.id = hashlib.md5(f"{datetime.now().isoformat()}{mensagem}".encode()).hexdigest()[:12]
    
    def para_dict(self) -> Dict:
        """Converte para dicionario."""
        return {
            "id": self.id,
            "nivel": NivelLog.NOMES.get(self.nivel, "DESCONHECIDO"),
            "mensagem": self.mensagem,
            "modulo": self.modulo,
            "timestamp": self.timestamp.isoformat(),
            "dados": self.dados
        }
    
    def __str__(self) -> str:
        """Representacao em string."""
        nivel_nome = NivelLog.NOMES.get(self.nivel, "???")
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {nivel_nome:8} [{self.modulo:15}] {self.mensagem}"

class LoggerSume:
    """Logger estruturado para Sumé."""
    
    def __init__(self, nome: str = "Sumé", nivel_minimo: int = NivelLog.INFO):
        self.nome = nome
        self.nivel_minimo = nivel_minimo
        self.eventos = deque(maxlen=1000)  # Manter ultimos 1000 eventos
        self.arquivo_log = None
        self.lock = threading.Lock()
        self.handlers = []
    
    def definir_arquivo_log(self, caminho: str):
        """Define arquivo para log."""
        self.arquivo_log = caminho
        os.makedirs(os.path.dirname(caminho) if os.path.dirname(caminho) else ".", exist_ok=True)
    
    def registrar_handler(self, handler: Callable):
        """Registra handler customizado."""
        self.handlers.append(handler)
    
    def _registrar_evento(self, evento: EventoLog):
        """Registra um evento internamente."""
        if evento.nivel < self.nivel_minimo:
            return
        
        with self.lock:
            self.eventos.append(evento)
            
            # Escrever em arquivo se configurado
            if self.arquivo_log:
                try:
                    with open(self.arquivo_log, 'a', encoding='utf-8') as f:
                        f.write(str(evento) + "\n")
                except:
                    pass
            
            # Chamar handlers
            for handler in self.handlers:
                try:
                    handler(evento)
                except:
                    pass
    
    def debug(self, mensagem: str, modulo: str = "", dados: Dict = None):
        """Registra log DEBUG."""
        evento = EventoLog(NivelLog.DEBUG, mensagem, modulo, dados)
        self._registrar_evento(evento)
    
    def info(self, mensagem: str, modulo: str = "", dados: Dict = None):
        """Registra log INFO."""
        evento = EventoLog(NivelLog.INFO, mensagem, modulo, dados)
        self._registrar_evento(evento)
    
    def aviso(self, mensagem: str, modulo: str = "", dados: Dict = None):
        """Registra log AVISO."""
        evento = EventoLog(NivelLog.AVISO, mensagem, modulo, dados)
        self._registrar_evento(evento)
    
    def erro(self, mensagem: str, modulo: str = "", dados: Dict = None):
        """Registra log ERRO."""
        evento = EventoLog(NivelLog.ERRO, mensagem, modulo, dados)
        self._registrar_evento(evento)
    
    def critico(self, mensagem: str, modulo: str = "", dados: Dict = None):
        """Registra log CRITICO."""
        evento = EventoLog(NivelLog.CRITICO, mensagem, modulo, dados)
        self._registrar_evento(evento)
    
    def obter_eventos(self, nivel_minimo: int = None, modulo: str = None, limite: int = 100) -> List[Dict]:
        """Obtém eventos com filtros opcionais."""
        with self.lock:
            eventos = list(self.eventos)
        
        # Filtrar
        if nivel_minimo:
            eventos = [e for e in eventos if e.nivel >= nivel_minimo]
        if modulo:
            eventos = [e for e in eventos if modulo in e.modulo]
        
        # Retornar ultimos 'limite' em ordem reversa (mais recentes primeiro)
        return [e.para_dict() for e in reversed(eventos[-limite:])]
    
    def limpar_eventos(self):
        """Limpa buffer de eventos."""
        with self.lock:
            self.eventos.clear()

class Metrica:
    """Representa uma metrica."""
    
    def __init__(self, nome: str, tipo: str = "contador"):
        self.nome = nome
        self.tipo = tipo  # contador, gauge, histograma, temporizador
        self.valores = []
        self.timestamp_inicio = time.time()
        self.lock = threading.Lock()
    
    def registrar(self, valor: float):
        """Registra um valor."""
        with self.lock:
            self.valores.append({
                "valor": valor,
                "timestamp": time.time()
            })
            # Manter ultimos 1000 valores
            if len(self.valores) > 1000:
                self.valores = self.valores[-1000:]
    
    def obter_estatisticas(self) -> Dict:
        """Calcula estatisticas."""
        if not self.valores:
            return {
                "nome": self.nome,
                "tipo": self.tipo,
                "total": 0,
                "media": 0,
                "minima": 0,
                "maxima": 0,
                "count": 0
            }
        
        valores_num = [v["valor"] for v in self.valores]
        total = sum(valores_num)
        media = total / len(valores_num)
        
        return {
            "nome": self.nome,
            "tipo": self.tipo,
            "total": total,
            "media": media,
            "minima": min(valores_num),
            "maxima": max(valores_num),
            "count": len(valores_num),
            "desvio_padrao": self._calcular_desvio_padrao(valores_num, media)
        }
    
    def _calcular_desvio_padrao(self, valores: List[float], media: float) -> float:
        """Calcula desvio padrao."""
        if len(valores) < 2:
            return 0.0
        variancia = sum((v - media) ** 2 for v in valores) / len(valores)
        return variancia ** 0.5

class GerenciadorMetricas:
    """Gerencia metricas do sistema."""
    
    def __init__(self):
        self.metricas: Dict[str, Metrica] = {}
        self.lock = threading.Lock()
    
    def criar_metrica(self, nome: str, tipo: str = "contador") -> Metrica:
        """Cria ou obtém metrica."""
        with self.lock:
            if nome not in self.metricas:
                self.metricas[nome] = Metrica(nome, tipo)
            return self.metricas[nome]
    
    def registrar(self, nome: str, valor: float):
        """Registra valor em metrica."""
        metrica = self.criar_metrica(nome)
        metrica.registrar(valor)
    
    def incrementar(self, nome: str, valor: float = 1):
        """Incrementa contador."""
        self.registrar(nome, valor)
    
    def definir_gauge(self, nome: str, valor: float):
        """Define valor de gauge."""
        self.registrar(nome, valor)
    
    def obter_metricas(self) -> Dict[str, Dict]:
        """Obtém todas as metricas com estatisticas."""
        with self.lock:
            return {
                nome: metrica.obter_estatisticas()
                for nome, metrica in self.metricas.items()
            }
    
    def obter_metrica(self, nome: str) -> Optional[Dict]:
        """Obtém uma metrica especifica."""
        with self.lock:
            if nome in self.metricas:
                return self.metricas[nome].obter_estatisticas()
        return None

class Alerta:
    """Representa um alerta."""
    
    def __init__(self, nome: str, condicao: Callable, severidade: str = "AVISO"):
        self.nome = nome
        self.condicao = condicao  # Callable que retorna bool
        self.severidade = severidade
        self.ativo = False
        self.criado_em = None
        self.contador = 0
    
    def verificar(self, dados: Dict) -> bool:
        """Verifica se alerta deve ser disparado."""
        try:
            resultado = self.condicao(dados)
            if resultado and not self.ativo:
                self.ativo = True
                self.criado_em = datetime.now()
                self.contador = 0
            elif not resultado and self.ativo:
                self.ativo = False
            
            if self.ativo:
                self.contador += 1
            
            return resultado
        except:
            return False
    
    def para_dict(self) -> Dict:
        """Converte para dicionario."""
        return {
            "nome": self.nome,
            "severidade": self.severidade,
            "ativo": self.ativo,
            "contador": self.contador,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None
        }

class GerenciadorAlertas:
    """Gerencia alertas do sistema."""
    
    def __init__(self, logger: LoggerSume = None):
        self.alertas: Dict[str, Alerta] = {}
        self.logger = logger
        self.callbacks_alerta = []
        self.lock = threading.Lock()
    
    def registrar_alerta(self, nome: str, condicao: Callable, severidade: str = "AVISO") -> Alerta:
        """Registra novo alerta."""
        with self.lock:
            alerta = Alerta(nome, condicao, severidade)
            self.alertas[nome] = alerta
            return alerta
    
    def registrar_callback(self, callback: Callable):
        """Registra callback para alertas."""
        self.callbacks_alerta.append(callback)
    
    def verificar_alertas(self, dados: Dict):
        """Verifica todos os alertas."""
        with self.lock:
            alertas_disparados = []
            
            for nome, alerta in self.alertas.items():
                if alerta.verificar(dados):
                    alertas_disparados.append(alerta)
                    
                    if self.logger:
                        self.logger.aviso(
                            f"Alerta ativado: {nome}",
                            "alertas",
                            {"alerta": alerta.para_dict()}
                        )
            
            # Chamar callbacks
            for callback in self.callbacks_alerta:
                for alerta in alertas_disparados:
                    try:
                        callback(alerta)
                    except:
                        pass
    
    def obter_alertas(self) -> Dict[str, Dict]:
        """Obtém status de todos os alertas."""
        with self.lock:
            return {
                nome: alerta.para_dict()
                for nome, alerta in self.alertas.items()
            }
    
    def obter_alertas_ativos(self) -> List[Dict]:
        """Obtém apenas alertas ativos."""
        with self.lock:
            return [
                alerta.para_dict()
                for alerta in self.alertas.values()
                if alerta.ativo
            ]

class ColecionadorMetricasAuto:
    """Coleciona automaticamente metricas do sistema."""
    
    def __init__(self, metricas: GerenciadorMetricas, intervalo: float = 5.0):
        self.metricas = metricas
        self.intervalo = intervalo
        self.ativo = False
        self.thread = None
        self.lock = threading.Lock()
    
    def iniciar(self):
        """Inicia coleta automatica."""
        if self.ativo:
            return
        
        self.ativo = True
        self.thread = threading.Thread(target=self._colecionar, daemon=True)
        self.thread.start()
    
    def parar(self):
        """Para coleta automatica."""
        self.ativo = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _colecionar(self):
        """Thread de coleta."""
        while self.ativo:
            try:
                # Coletar metricas de sistema
                import psutil
                
                # CPU
                cpu = psutil.cpu_percent(interval=0.1)
                self.metricas.definir_gauge("cpu_uso_percent", cpu)
                
                # Memoria
                mem = psutil.virtual_memory()
                self.metricas.definir_gauge("memoria_uso_percent", mem.percent)
                self.metricas.definir_gauge("memoria_usada_mb", mem.used / (1024 * 1024))
                
                # Disco
                disco = psutil.disk_usage('/')
                self.metricas.definir_gauge("disco_uso_percent", disco.percent)
                
                # Processos
                self.metricas.definir_gauge("processos_ativos", len(psutil.pids()))
                
            except:
                pass  # psutil pode nao estar disponivel
            
            time.sleep(self.intervalo)

# Logger global
logger_global = LoggerSume("Sumé")
metricas_global = GerenciadorMetricas()
alertas_global = GerenciadorAlertas(logger_global)

def obter_logger() -> LoggerSume:
    """Obtém logger global."""
    return logger_global

def obter_metricas() -> GerenciadorMetricas:
    """Obtém gerenciador de metricas."""
    return metricas_global

def obter_alertas() -> GerenciadorAlertas:
    """Obtém gerenciador de alertas."""
    return alertas_global
