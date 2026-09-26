"""
Cliente de sincronizacao em nuvem com versionamento e resolucao de conflitos.
Permite backup automatico de notas e dados com encriptacao.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from plugins.encriptacao import EncriptadorAES, EnvelopeEncriptado
import threading
import time

class VersaoArquivo:
    """Representa uma versao de arquivo no historico."""
    
    def __init__(self, conteudo: str, timestamp: str = None, usuario: str = "local", dispositivo: str = "pc"):
        self.conteudo = conteudo
        self.timestamp = timestamp or datetime.now().isoformat()
        self.usuario = usuario
        self.dispositivo = dispositivo
        self.hash = hashlib.sha256(conteudo.encode()).hexdigest()
    
    def para_dict(self) -> Dict:
        """Converte para dicionario."""
        return {
            "conteudo": self.conteudo,
            "timestamp": self.timestamp,
            "usuario": self.usuario,
            "dispositivo": self.dispositivo,
            "hash": self.hash
        }

class ArquivoSincronizado:
    """Arquivo com historico de versoes e metadados."""
    
    def __init__(self, caminho: str, nome: str):
        self.caminho = caminho
        self.nome = nome
        self.versoes: List[VersaoArquivo] = []
        self.ultima_sincronizacao = None
        self.em_conflito = False
        self.resolucao = None
    
    def adicionar_versao(self, versao: VersaoArquivo):
        """Adiciona versao ao historico."""
        self.versoes.append(versao)
        self.ultima_sincronizacao = datetime.now().isoformat()
    
    def obter_versao_atual(self) -> Optional[VersaoArquivo]:
        """Retorna versao mais recente."""
        return self.versoes[-1] if self.versoes else None
    
    def para_dict(self) -> Dict:
        """Converte para dicionario."""
        return {
            "caminho": self.caminho,
            "nome": self.nome,
            "versoes": [v.para_dict() for v in self.versoes],
            "ultima_sincronizacao": self.ultima_sincronizacao,
            "em_conflito": self.em_conflito,
            "resolucao": self.resolucao
        }

class ClienteSincronizacao:
    """Cliente de sincronizacao com nuvem."""
    
    def __init__(self, chave_mestra: bytes, senha: str, url_servidor: str = "http://localhost:5000"):
        self.chave_mestra = chave_mestra
        self.senha = senha
        self.url_servidor = url_servidor
        self.encriptador = EncriptadorAES(chave_mestra)
        self.arquivos_sincronizados: Dict[str, ArquivoSincronizado] = {}
        self.sincronizando = False
        self.ultima_sincronizacao = None
    
    def registrar_arquivo(self, caminho: str, nome: str = None) -> ArquivoSincronizado:
        """Registra arquivo para sincronizacao."""
        nome = nome or os.path.basename(caminho)
        arquivo = ArquivoSincronizado(caminho, nome)
        self.arquivos_sincronizados[nome] = arquivo
        return arquivo
    
    def sincronizar_arquivo_local(self, nome: str) -> bool:
        """Sincroniza arquivo local para memoria."""
        if nome not in self.arquivos_sincronizados:
            return False
        
        arquivo = self.arquivos_sincronizados[nome]
        
        try:
            with open(arquivo.caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            versao = VersaoArquivo(conteudo)
            arquivo.adicionar_versao(versao)
            return True
        except:
            return False
    
    def sincronizar_para_nuvem(self, nome: str) -> Tuple[bool, str]:
        """Sincroniza arquivo para nuvem."""
        if nome not in self.arquivos_sincronizados:
            return False, "Arquivo nao registrado"
        
        arquivo = self.arquivos_sincronizados[nome]
        versao_atual = arquivo.obter_versao_atual()
        
        if not versao_atual:
            return False, "Nenhuma versao disponivel"
        
        try:
            # Encriptar dados
            dados = arquivo.para_dict()
            import hashlib
            chave_hmac = hashlib.sha256(self.senha.encode()).digest()
            envelope_criador = EnvelopeEncriptado(self.encriptador, chave_hmac)
            envelope = envelope_criador.criar_envelope(dados)
            
            # Enviar para nuvem (simulado)
            payload = {
                "arquivo": nome,
                "timestamp": datetime.now().isoformat(),
                "envelope": envelope
            }
            
            # Aqui seria uma chamada HTTP real
            # response = requests.post(f"{self.url_servidor}/sync", json=payload)
            # if response.status_code == 200:
            #     arquivo.ultima_sincronizacao = datetime.now().isoformat()
            #     return True, "Sincronizado com sucesso"
            
            # Por enquanto, simular sucesso
            arquivo.ultima_sincronizacao = datetime.now().isoformat()
            return True, "Sincronizado com sucesso (simulado)"
        
        except Exception as e:
            return False, f"Erro na sincronizacao: {str(e)}"
    
    def sincronizar_da_nuvem(self, nome: str, envelope_json: str) -> Tuple[bool, str]:
        """Sincroniza arquivo da nuvem para local."""
        if nome not in self.arquivos_sincronizados:
            return False, "Arquivo nao registrado"
        
        try:
            import hashlib
            chave_hmac = hashlib.sha256(self.senha.encode()).digest()
            envelope_criador = EnvelopeEncriptado(self.encriptador, chave_hmac)
            dados = envelope_criador.abrir_envelope(envelope_json)
            
            arquivo = self.arquivos_sincronizados[nome]
            
            # Detectar conflito
            versao_local = arquivo.obter_versao_atual()
            versao_remota = VersaoArquivo(
                dados["dados"]["versoes"][-1]["conteudo"],
                dados["dados"]["versoes"][-1]["timestamp"],
                dados["dados"]["versoes"][-1]["usuario"],
                dados["dados"]["versoes"][-1]["dispositivo"]
            )
            
            if versao_local and versao_local.hash != versao_remota.hash:
                arquivo.em_conflito = True
                return False, "Conflito detectado entre versoes"
            
            # Sem conflito, adicionar versao remota
            arquivo.adicionar_versao(versao_remota)
            return True, "Sincronizado da nuvem com sucesso"
        
        except Exception as e:
            return False, f"Erro ao sincronizar da nuvem: {str(e)}"
    
    def resolver_conflito(self, nome: str, usar_versao: str = "local") -> bool:
        """Resolve conflito escolhendo qual versao manter."""
        if nome not in self.arquivos_sincronizados:
            return False
        
        arquivo = self.arquivos_sincronizados[nome]
        
        if not arquivo.em_conflito:
            return False
        
        arquivo.em_conflito = False
        arquivo.resolucao = {
            "estrategia": usar_versao,
            "timestamp": datetime.now().isoformat()
        }
        
        return True
    
    def sincronizar_automatico(self, intervalo_segundos: int = 300):
        """Sincroniza automaticamente em intervalo."""
        def thread_sincronizacao():
            while self.sincronizando:
                self.sincronizar_tudo()
                time.sleep(intervalo_segundos)
        
        self.sincronizando = True
        thread = threading.Thread(target=thread_sincronizacao, daemon=True)
        thread.start()
    
    def parar_sincronizacao_automatica(self):
        """Para sincronizacao automatica."""
        self.sincronizando = False
    
    def sincronizar_tudo(self) -> Dict[str, Tuple[bool, str]]:
        """Sincroniza todos os arquivos registrados."""
        resultados = {}
        
        for nome in self.arquivos_sincronizados:
            # Sincronizar local primeiro
            self.sincronizar_arquivo_local(nome)
            
            # Depois para nuvem
            sucesso, msg = self.sincronizar_para_nuvem(nome)
            resultados[nome] = (sucesso, msg)
        
        self.ultima_sincronizacao = datetime.now().isoformat()
        return resultados
    
    def obter_status(self) -> Dict:
        """Retorna status da sincronizacao."""
        arquivos_com_conflito = sum(
            1 for a in self.arquivos_sincronizados.values() if a.em_conflito
        )
        
        return {
            "total_arquivos": len(self.arquivos_sincronizados),
            "arquivos_com_conflito": arquivos_com_conflito,
            "ultima_sincronizacao": self.ultima_sincronizacao,
            "sincronizando": self.sincronizando
        }

class RepositorioLocal:
    """Repositorio local de sincronizacao."""
    
    def __init__(self, diretorio: str = None):
        self.diretorio = diretorio or os.path.expanduser("~/.sume/sync")
        self.arquivo_indice = os.path.join(self.diretorio, "indice.json")
        self.indice = {}
        self.carregar_indice()
    
    def carregar_indice(self):
        """Carrega indice de sincronizacao."""
        if os.path.exists(self.arquivo_indice):
            try:
                with open(self.arquivo_indice, 'r', encoding='utf-8') as f:
                    self.indice = json.load(f)
            except:
                self.indice = {}
    
    def salvar_indice(self):
        """Salva indice de sincronizacao."""
        os.makedirs(self.diretorio, exist_ok=True)
        with open(self.arquivo_indice, 'w', encoding='utf-8') as f:
            json.dump(self.indice, f, ensure_ascii=False, indent=2)
    
    def registrar_arquivo(self, nome: str, hash_local: str, timestamp: str):
        """Registra arquivo no indice."""
        self.indice[nome] = {
            "hash_local": hash_local,
            "timestamp": timestamp,
            "sincronizado": False
        }
        self.salvar_indice()
    
    def marcar_sincronizado(self, nome: str):
        """Marca arquivo como sincronizado."""
        if nome in self.indice:
            self.indice[nome]["sincronizado"] = True
            self.salvar_indice()
    
    def obter_status_arquivo(self, nome: str) -> Optional[Dict]:
        """Obtém status de arquivo."""
        return self.indice.get(nome)
    
    def listar_pendentes(self) -> List[str]:
        """Lista arquivos pendentes de sincronizacao."""
        return [
            nome for nome, dados in self.indice.items()
            if not dados.get("sincronizado", False)
        ]

# Cliente global
cliente_sincronizacao_global = None

def inicializar_cliente(chave_mestra: bytes, senha: str) -> ClienteSincronizacao:
    """Helper para inicializar cliente de sincronizacao."""
    global cliente_sincronizacao_global
    cliente_sincronizacao_global = ClienteSincronizacao(chave_mestra, senha)
    return cliente_sincronizacao_global

def obter_cliente() -> Optional[ClienteSincronizacao]:
    """Helper para obter cliente global."""
    return cliente_sincronizacao_global
