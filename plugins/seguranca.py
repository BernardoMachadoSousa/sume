"""
Modulo de seguranca: sanitizacao, validacao e protecao contra ataques.
Implementa defesas contra XSS, injection, e outras vulnerabilidades.
"""

import re
import html
from typing import Any, List, Dict, Optional
import unicodedata

class SanitizadorHTML:
    """Sanitiza strings para prevenir XSS attacks."""
    
    def __init__(self):
        self.tags_perigosas = [
            'script', 'iframe', 'object', 'embed', 'applet', 'meta',
            'link', 'style', 'form', 'input', 'button', 'select',
            'textarea', 'frame', 'frameset', 'noframe', 'noscript'
        ]
        self.attrs_perigosos = [
            'onload', 'onerror', 'onclick', 'onmouseover', 'onkeydown',
            'onkeyup', 'onmouseout', 'onchange', 'onfocus', 'onblur',
            'ondblclick', 'onsubmit', 'onreset', 'onselect'
        ]
    
    def sanitizar(self, texto: str) -> str:
        """Remove tags e atributos perigosos."""
        if not isinstance(texto, str):
            return ""
        
        # Escape HTML entities
        texto = html.escape(texto)
        
        # Remove tags de script
        for tag in self.tags_perigosas:
            padrao = rf'<{tag}[^>]*>.*?</{tag}>|<{tag}[^>]*/?>'
            texto = re.sub(padrao, '', texto, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove atributos perigosos
        for attr in self.attrs_perigosos:
            padrao = rf'\s+{attr}\s*=\s*["\']?[^"\'>\s]*["\']?'
            texto = re.sub(padrao, '', texto, flags=re.IGNORECASE)
        
        return texto
    
    def limpar_texto(self, texto: str, max_tamanho: int = 10000) -> str:
        """Limpa e normaliza texto."""
        if not isinstance(texto, str):
            return ""
        
        # Remove caracteres de controle
        texto = ''.join(c for c in texto if unicodedata.category(c)[0] != 'C' or c == '\n')
        
        # Remove espacos em excesso
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        # Limita tamanho
        if len(texto) > max_tamanho:
            texto = texto[:max_tamanho]
        
        return texto

class ValidadorComando:
    """Valida comandos de entrada."""
    
    def __init__(self):
        self.tamanho_minimo = 1
        self.tamanho_maximo = 5000
        self.padrao_valido = re.compile(r'^[\w\s\.,\!\?\'\"\-\(\)\:][\w\s\.,\!\?\'\"\-\(\)\:]*$', re.UNICODE)
    
    def validar(self, comando: str) -> tuple[bool, str]:
        """Valida comando e retorna (valido, mensagem)."""
        if not isinstance(comando, str):
            return False, "Comando deve ser uma string"
        
        comando = comando.strip()
        
        if len(comando) < self.tamanho_minimo:
            return False, "Comando muito curto"
        
        if len(comando) > self.tamanho_maximo:
            return False, "Comando muito longo"
        
        # Valida caracteres permitidos
        if not self.padrao_valido.match(comando):
            return False, "Comando contém caracteres inválidos"
        
        return True, "Válido"
    
    def detectar_injection(self, comando: str) -> bool:
        """Detecta possíveis tentativas de injection."""
        padroes_suspeitos = [
            r"(\$\{.*?\})",
            r"(\$\(.*?\))",
            r"(`.*?`)",
            r"(\|\s*[a-z]+)",
            r"(&&\s*[a-z]+)",
            r"(;\s*[a-z]+)",
        ]
        
        for padrao in padroes_suspeitos:
            if re.search(padrao, comando, re.IGNORECASE):
                return True
        
        return False

class RateLimiter:
    """Implementa rate limiting para prevenir abuso."""
    
    def __init__(self, max_requisicoes: int = 100, janela_segundos: int = 60):
        self.max_requisicoes = max_requisicoes
        self.janela_segundos = janela_segundos
        self.requisicoes = {}
    
    def pode_processar(self, chave: str) -> bool:
        """Verifica se a requisição deve ser processada."""
        import time
        
        agora = time.time()
        
        if chave not in self.requisicoes:
            self.requisicoes[chave] = []
        
        # Remove requisições antigas
        self.requisicoes[chave] = [
            timestamp for timestamp in self.requisicoes[chave]
            if agora - timestamp < self.janela_segundos
        ]
        
        if len(self.requisicoes[chave]) < self.max_requisicoes:
            self.requisicoes[chave].append(agora)
            return True
        
        return False
    
    def requisicoes_restantes(self, chave: str) -> int:
        """Retorna numero de requisições restantes."""
        import time
        
        agora = time.time()
        
        if chave not in self.requisicoes:
            return self.max_requisicoes
        
        self.requisicoes[chave] = [
            timestamp for timestamp in self.requisicoes[chave]
            if agora - timestamp < self.janela_segundos
        ]
        
        return self.max_requisicoes - len(self.requisicoes[chave])

class ValidadorCaminho:
    """Valida caminhos de arquivo para prevenir path traversal."""
    
    @staticmethod
    def validar_caminho(caminho: str, raiz_permitida: str = None) -> bool:
        """Valida se caminho eh seguro."""
        import os
        
        if not isinstance(caminho, str):
            return False
        
        # Remove null bytes
        if '\0' in caminho:
            return False
        
        # Detecta path traversal ANTES da normalizacao
        if '..' in caminho:
            return False
        
        # Normaliza caminho
        try:
            caminho_normalizado = os.path.normpath(caminho)
        except:
            return False
        
        # Verifica raiz permitida se especificada
        if raiz_permitida:
            try:
                raiz_abs = os.path.abspath(raiz_permitida)
                caminho_abs = os.path.abspath(caminho_normalizado)
                
                if not caminho_abs.startswith(raiz_abs):
                    return False
            except:
                return False
        
        return True

class CSRFToken:
    """Gera e valida tokens CSRF."""
    
    def __init__(self):
        self.tokens = {}
    
    def gerar_token(self, sessao_id: str) -> str:
        """Gera novo token CSRF."""
        import secrets
        
        token = secrets.token_urlsafe(32)
        self.tokens[sessao_id] = token
        return token
    
    def validar_token(self, sessao_id: str, token: str) -> bool:
        """Valida token CSRF."""
        if sessao_id not in self.tokens:
            return False
        
        return self.tokens[sessao_id] == token

sanitizador = SanitizadorHTML()
validador_comando = ValidadorComando()
rate_limiter = RateLimiter(max_requisicoes=100, janela_segundos=60)
validador_caminho = ValidadorCaminho()
csrf_token = CSRFToken()

def sanitizar(texto: str) -> str:
    """Helper para sanitizar texto."""
    return sanitizador.sanitizar(texto)

def limpar_texto(texto: str) -> str:
    """Helper para limpar texto."""
    return sanitizador.limpar_texto(texto)

def validar_comando(comando: str) -> tuple[bool, str]:
    """Helper para validar comando."""
    return validador_comando.validar(comando)

def detectar_injection(comando: str) -> bool:
    """Helper para detectar injection."""
    return validador_comando.detectar_injection(comando)

def pode_processar(chave: str) -> bool:
    """Helper para rate limiting."""
    return rate_limiter.pode_processar(chave)

def validar_caminho_arquivo(caminho: str, raiz: str = None) -> bool:
    """Helper para validar caminho."""
    return ValidadorCaminho.validar_caminho(caminho, raiz)
