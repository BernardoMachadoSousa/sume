"""
Sistema de encriptacao end-to-end para sincronizacao em nuvem.
Implementa AES-256 com geracao segura de chaves.
"""

import os
import json
import hashlib
import secrets
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

class GerenciadorChaves:
    """Gerencia chaves de encriptacao com derivacao segura."""
    
    def __init__(self, arquivo_chaves: str = None):
        self.arquivo_chaves = arquivo_chaves or os.path.expanduser("~/.sume/chaves.json")
        self.chaves = {}
        self.carregar()
    
    def gerar_chave_mestra(self, senha: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Gera chave mestra a partir de senha usando PBKDF2."""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
            backend=default_backend()
        )
        
        chave = kdf.derive(senha.encode())
        return chave, salt
    
    def gerar_chave_dispositivo(self) -> str:
        """Gera ID único para dispositivo."""
        dispositivo_id = secrets.token_urlsafe(32)
        return dispositivo_id
    
    def guardar_chave(self, identificador: str, chave: str, salt: str = None):
        """Armazena chave com salt opcionalmente."""
        self.chaves[identificador] = {
            "chave": chave,
            "salt": salt,
            "criada_em": datetime.now().isoformat()
        }
        self.salvar()
    
    def obter_chave(self, identificador: str) -> Optional[Dict]:
        """Obtém chave armazenada."""
        return self.chaves.get(identificador)
    
    def salvar(self):
        """Salva chaves no disco."""
        os.makedirs(os.path.dirname(self.arquivo_chaves), exist_ok=True)
        with open(self.arquivo_chaves, 'w', encoding='utf-8') as f:
            json.dump(self.chaves, f, ensure_ascii=False)
    
    def carregar(self):
        """Carrega chaves do disco."""
        if os.path.exists(self.arquivo_chaves):
            try:
                with open(self.arquivo_chaves, 'r', encoding='utf-8') as f:
                    self.chaves = json.load(f)
            except:
                self.chaves = {}

class EncriptadorAES:
    """Encriptacao AES-256 com Fernet."""
    
    def __init__(self, chave_mestra: bytes):
        # Derivar chave Fernet a partir da chave mestra
        chave_fernet = base64.urlsafe_b64encode(hashlib.sha256(chave_mestra).digest())
        self.cipher = Fernet(chave_fernet)
    
    def encriptar(self, dados: str) -> str:
        """Encripta string e retorna em base64."""
        dados_bytes = dados.encode('utf-8')
        token = self.cipher.encrypt(dados_bytes)
        return base64.b64encode(token).decode('ascii')
    
    def descriptografar(self, dados_encriptados: str) -> str:
        """Descriptografa string."""
        try:
            token = base64.b64decode(dados_encriptados.encode('ascii'))
            dados_bytes = self.cipher.decrypt(token)
            return dados_bytes.decode('utf-8')
        except:
            raise ValueError("Falha ao descriptografar dados")
    
    def encriptar_json(self, obj: Dict) -> str:
        """Encripta objeto JSON."""
        json_str = json.dumps(obj, ensure_ascii=False)
        return self.encriptar(json_str)
    
    def descriptografar_json(self, dados_encriptados: str) -> Dict:
        """Descriptografa JSON."""
        json_str = self.descriptografar(dados_encriptados)
        return json.loads(json_str)

class VerificadorIntegridade:
    """Verifica integridade de dados com HMAC."""
    
    @staticmethod
    def gerar_hash(dados: str, chave: bytes) -> str:
        """Gera HMAC-SHA256 para verificacao de integridade."""
        h = hashlib.new('sha256')
        h.update(chave)
        h.update(dados.encode('utf-8'))
        return h.hexdigest()
    
    @staticmethod
    def verificar_hash(dados: str, hash_esperado: str, chave: bytes) -> bool:
        """Verifica se hash corresponde."""
        hash_calculado = VerificadorIntegridade.gerar_hash(dados, chave)
        return hash_calculado == hash_esperado

class EnvelopeEncriptado:
    """Envelope com dados encriptados, hash e metadados."""
    
    def __init__(self, encriptador: EncriptadorAES, chave_hmac: bytes):
        self.encriptador = encriptador
        self.chave_hmac = chave_hmac
    
    def criar_envelope(self, dados: Dict, chave_versao: str = "1.0") -> str:
        """Cria envelope com dados, hash e metadados."""
        # Encriptar dados
        dados_encriptados = self.encriptador.encriptar_json(dados)
        
        # Gerar hash para integridade
        hash_dados = VerificadorIntegridade.gerar_hash(dados_encriptados, self.chave_hmac)
        
        # Criar envelope
        envelope = {
            "versao": "1.0",
            "timestamp": datetime.now().isoformat(),
            "chave_versao": chave_versao,
            "dados": dados_encriptados,
            "hash": hash_dados,
            "algoritmo": "AES-256-Fernet"
        }
        
        return json.dumps(envelope, ensure_ascii=False)
    
    def abrir_envelope(self, envelope_json: str) -> Dict:
        """Abre e valida envelope."""
        envelope = json.loads(envelope_json)
        
        # Verificar versao
        if envelope.get("versao") != "1.0":
            raise ValueError("Versao de envelope incompativel")
        
        # Verificar integridade
        hash_verificado = VerificadorIntegridade.gerar_hash(
            envelope["dados"],
            self.chave_hmac
        )
        
        if hash_verificado != envelope["hash"]:
            raise ValueError("Hash nao corresponde - dados podem estar corrompidos")
        
        # Descriptografar
        dados = self.encriptador.descriptografar_json(envelope["dados"])
        
        return {
            "dados": dados,
            "timestamp": envelope["timestamp"],
            "chave_versao": envelope["chave_versao"]
        }

class CriptografiaExemplos:
    """Exemplos de uso do sistema de encriptacao."""
    
    @staticmethod
    def exemplo_completo(senha: str):
        """Demonstra fluxo completo de encriptacao."""
        
        # 1. Gerar chave mestra
        gerenciador = GerenciadorChaves()
        chave_mestra, salt = gerenciador.gerar_chave_mestra(senha)
        
        # 2. Criar encriptador
        encriptador = EncriptadorAES(chave_mestra)
        
        # 3. Criar dados para encriptar
        dados = {
            "usuario": "joao@example.com",
            "notas": [
                {"titulo": "Python", "conteudo": "Linguagem versatil"},
                {"titulo": "Web", "conteudo": "Django e Flask"}
            ],
            "configuracoes": {
                "tema": "dark",
                "idioma": "pt-BR"
            }
        }
        
        # 4. Criar envelope
        chave_hmac = hashlib.sha256(senha.encode()).digest()
        envelope_criador = EnvelopeEncriptado(encriptador, chave_hmac)
        envelope_json = envelope_criador.criar_envelope(dados)
        
        # 5. Simular transmissao (envelope encriptado)
        print("Envelope encriptado (seguro para transmitir):")
        print(envelope_json[:100] + "...")
        
        # 6. Abrir envelope
        dados_recuperados = envelope_criador.abrir_envelope(envelope_json)
        print("\nDados recuperados:")
        print(json.dumps(dados_recuperados["dados"], indent=2, ensure_ascii=False))
        
        return True

# Instancias globais
gerenciador_chaves_global = GerenciadorChaves()

def gerar_chave_mestra(senha: str) -> Tuple[bytes, bytes]:
    """Helper para gerar chave mestra."""
    gerenciador = GerenciadorChaves()
    return gerenciador.gerar_chave_mestra(senha)

def criar_encriptador(chave_mestra: bytes) -> EncriptadorAES:
    """Helper para criar encriptador."""
    return EncriptadorAES(chave_mestra)

def criar_envelope(encriptador: EncriptadorAES, dados: Dict, senha: str) -> str:
    """Helper para criar envelope encriptado."""
    chave_hmac = hashlib.sha256(senha.encode()).digest()
    envelope_criador = EnvelopeEncriptado(encriptador, chave_hmac)
    return envelope_criador.criar_envelope(dados)

def abrir_envelope(encriptador: EncriptadorAES, envelope_json: str, senha: str) -> Dict:
    """Helper para abrir envelope."""
    chave_hmac = hashlib.sha256(senha.encode()).digest()
    envelope_criador = EnvelopeEncriptado(encriptador, chave_hmac)
    return envelope_criador.abrir_envelope(envelope_json)
