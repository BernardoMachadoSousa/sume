"""
Sistema de indexacao incremental para notas e arquivos.
Mantém índice atualizado para acelerar buscas.
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Set
from datetime import datetime

class IndiceNotas:
    """Indice para notas do vault."""
    
    def __init__(self, arquivo_indice: str = None):
        self.arquivo_indice = arquivo_indice or os.path.expanduser("~/.sume/indice_notas.json")
        self.indice = {}
        self.hashes = {}
        self.carregar()
    
    def _gerar_hash_arquivo(self, caminho: str) -> str:
        """Gera hash MD5 do arquivo."""
        try:
            with open(caminho, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def carregar(self):
        """Carrega indice do disco."""
        if os.path.exists(self.arquivo_indice):
            try:
                with open(self.arquivo_indice, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    self.indice = dados.get('indice', {})
                    self.hashes = dados.get('hashes', {})
            except:
                self.indice = {}
                self.hashes = {}
    
    def salvar(self):
        """Salva indice no disco."""
        os.makedirs(os.path.dirname(self.arquivo_indice), exist_ok=True)
        with open(self.arquivo_indice, 'w', encoding='utf-8') as f:
            json.dump({
                'indice': self.indice,
                'hashes': self.hashes,
                'atualizado_em': datetime.now().isoformat()
            }, f, ensure_ascii=False)
    
    def atualizar_nota(self, titulo: str, caminho: str, conteudo: str):
        """Atualiza entrada no indice."""
        chave = hashlib.md5(caminho.encode()).hexdigest()
        novo_hash = self._gerar_hash_arquivo(caminho)
        
        if chave in self.hashes and self.hashes[chave] == novo_hash:
            return False
        
        palavras_chave = self._extrair_palavras_chave(conteudo)
        
        self.indice[chave] = {
            'titulo': titulo,
            'caminho': caminho,
            'palavras_chave': palavras_chave,
            'atualizado_em': datetime.now().isoformat()
        }
        self.hashes[chave] = novo_hash
        
        return True
    
    def remover_nota(self, caminho: str):
        """Remove entrada do indice."""
        chave = hashlib.md5(caminho.encode()).hexdigest()
        
        if chave in self.indice:
            del self.indice[chave]
            del self.hashes[chave]
            return True
        
        return False
    
    def buscar_por_palavra(self, palavra: str) -> List[Dict]:
        """Busca notas que contem a palavra."""
        palavra_lower = palavra.lower()
        resultados = []
        
        for chave, dados in self.indice.items():
            if palavra_lower in dados.get('palavras_chave', []):
                resultados.append(dados)
        
        return resultados
    
    def _extrair_palavras_chave(self, conteudo: str) -> List[str]:
        """Extrai palavras-chave do conteudo."""
        palavras = []
        palavras_comuns = {'o', 'a', 'de', 'para', 'com', 'por', 'que', 'do', 'e', 'é', 'em', 'um', 'uma'}
        
        for palavra in conteudo.lower().split():
            palavra_limpa = ''.join(c for c in palavra if c.isalnum())
            if len(palavra_limpa) > 2 and palavra_limpa not in palavras_comuns:
                if palavra_limpa not in palavras:
                    palavras.append(palavra_limpa)
        
        return palavras[:50]

class IndiceArquivos:
    """Indice para arquivos do computador."""
    
    def __init__(self, arquivo_indice: str = None):
        self.arquivo_indice = arquivo_indice or os.path.expanduser("~/.sume/indice_arquivos.json")
        self.indice = {}
        self.hashes = {}
        self.carregar()
    
    def _gerar_hash_arquivo(self, caminho: str) -> str:
        """Gera hash MD5 do arquivo."""
        try:
            stat = os.stat(caminho)
            hash_base = f"{caminho}:{stat.st_size}:{stat.st_mtime}"
            return hashlib.md5(hash_base.encode()).hexdigest()
        except:
            return ""
    
    def carregar(self):
        """Carrega indice do disco."""
        if os.path.exists(self.arquivo_indice):
            try:
                with open(self.arquivo_indice, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    self.indice = dados.get('indice', {})
                    self.hashes = dados.get('hashes', {})
            except:
                self.indice = {}
                self.hashes = {}
    
    def salvar(self):
        """Salva indice no disco."""
        os.makedirs(os.path.dirname(self.arquivo_indice), exist_ok=True)
        with open(self.arquivo_indice, 'w', encoding='utf-8') as f:
            json.dump({
                'indice': self.indice,
                'hashes': self.hashes,
                'atualizado_em': datetime.now().isoformat()
            }, f, ensure_ascii=False)
    
    def atualizar_arquivo(self, nome: str, caminho: str, tamanho: int = 0, extensao: str = ""):
        """Atualiza entrada no indice."""
        chave = hashlib.md5(caminho.encode()).hexdigest()
        novo_hash = self._gerar_hash_arquivo(caminho)
        
        if chave in self.hashes and self.hashes[chave] == novo_hash:
            return False
        
        self.indice[chave] = {
            'nome': nome,
            'caminho': caminho,
            'extensao': extensao,
            'tamanho': tamanho,
            'atualizado_em': datetime.now().isoformat()
        }
        self.hashes[chave] = novo_hash
        
        return True
    
    def remover_arquivo(self, caminho: str):
        """Remove entrada do indice."""
        chave = hashlib.md5(caminho.encode()).hexdigest()
        
        if chave in self.indice:
            del self.indice[chave]
            del self.hashes[chave]
            return True
        
        return False
    
    def buscar_por_extensao(self, extensao: str) -> List[Dict]:
        """Busca arquivos com extensao especifica."""
        extensao = extensao.lower()
        resultados = []
        
        for chave, dados in self.indice.items():
            if dados.get('extensao', '').lower() == extensao:
                resultados.append(dados)
        
        return resultados
    
    def limpar_invalidos(self) -> int:
        """Remove arquivos que nao existem mais."""
        removidos = 0
        chaves_para_remover = []
        
        for chave, dados in self.indice.items():
            if not os.path.exists(dados.get('caminho', '')):
                chaves_para_remover.append(chave)
        
        for chave in chaves_para_remover:
            del self.indice[chave]
            del self.hashes[chave]
            removidos += 1
        
        return removidos

indice_notas_global = IndiceNotas()
indice_arquivos_global = IndiceArquivos()

def atualizar_indice_notas(titulo: str, caminho: str, conteudo: str) -> bool:
    """Helper para atualizar indice de notas."""
    return indice_notas_global.atualizar_nota(titulo, caminho, conteudo)

def buscar_indice_notas(palavra: str) -> List[Dict]:
    """Helper para buscar no indice de notas."""
    return indice_notas_global.buscar_por_palavra(palavra)

def salvar_indices():
    """Helper para salvar indices."""
    indice_notas_global.salvar()
    indice_arquivos_global.salvar()

def limpar_indice_arquivos():
    """Helper para limpar entradas invalidas."""
    return indice_arquivos_global.limpar_invalidos()
