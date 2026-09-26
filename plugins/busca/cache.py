"""
Sistema de cache LRU para otimizar resultados de busca.
Reduz tempo de processamento ao reutilizar resultados recentes.
"""

from collections import OrderedDict
from typing import Dict, List, Any, Optional
import hashlib
import time

class CacheLRU:
    """Cache LRU (Least Recently Used) para armazenar resultados de busca."""
    
    def __init__(self, tamanho_maximo: int = 100, ttl_segundos: int = 3600):
        self.tamanho_maximo = tamanho_maximo
        self.ttl_segundos = ttl_segundos
        self.cache = OrderedDict()
        self.timestamps = {}
        self.acessos = {}
    
    def _gerar_chave(self, termo: str, tipo: str = None, filtros: Dict = None) -> str:
        """Gera chave de cache baseada no termo de busca e filtros."""
        chave_base = f"{termo}:{tipo or 'todos'}"
        
        if filtros:
            chave_base += f":{str(sorted(filtros.items()))}"
        
        return hashlib.md5(chave_base.encode()).hexdigest()
    
    def _limpar_expirados(self):
        """Remove itens expirados do cache."""
        agora = time.time()
        chaves_expiradas = [
            chave for chave, timestamp in self.timestamps.items()
            if agora - timestamp > self.ttl_segundos
        ]
        
        for chave in chaves_expiradas:
            del self.cache[chave]
            del self.timestamps[chave]
            del self.acessos[chave]
    
    def obter(self, termo: str, tipo: str = None, filtros: Dict = None) -> Optional[Dict]:
        """Obtém resultado do cache se disponível."""
        self._limpar_expirados()
        
        chave = self._gerar_chave(termo, tipo, filtros)
        
        if chave not in self.cache:
            return None
        
        self.acessos[chave] = self.acessos.get(chave, 0) + 1
        self.cache.move_to_end(chave)
        
        return self.cache[chave]
    
    def guardar(self, termo: str, resultado: Dict, tipo: str = None, filtros: Dict = None):
        """Armazena resultado no cache."""
        chave = self._gerar_chave(termo, tipo, filtros)
        
        if chave in self.cache:
            self.cache.move_to_end(chave)
        elif len(self.cache) >= self.tamanho_maximo:
            chave_removida = next(iter(self.cache))
            del self.cache[chave_removida]
            del self.timestamps[chave_removida]
            del self.acessos[chave_removida]
        
        self.cache[chave] = resultado
        self.timestamps[chave] = time.time()
        self.acessos[chave] = 0
    
    def limpar(self):
        """Limpa todo o cache."""
        self.cache.clear()
        self.timestamps.clear()
        self.acessos.clear()
    
    def tamanho(self) -> int:
        """Retorna numero de itens no cache."""
        return len(self.cache)
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatisticas do cache."""
        total_acessos = sum(self.acessos.values())
        
        return {
            "itens_armazenados": len(self.cache),
            "tamanho_maximo": self.tamanho_maximo,
            "total_acessos": total_acessos,
            "taxa_ocupacao": len(self.cache) / self.tamanho_maximo if self.tamanho_maximo > 0 else 0
        }

cache_global = CacheLRU(tamanho_maximo=100, ttl_segundos=3600)

def obter_cache(termo: str, tipo: str = None, filtros: Dict = None) -> Optional[Dict]:
    """Funcao helper para obter do cache global."""
    return cache_global.obter(termo, tipo, filtros)

def guardar_cache(termo: str, resultado: Dict, tipo: str = None, filtros: Dict = None):
    """Funcao helper para guardar no cache global."""
    cache_global.guardar(termo, resultado, tipo, filtros)

def limpar_cache():
    """Funcao helper para limpar cache global."""
    cache_global.limpar()

def stats_cache() -> Dict[str, Any]:
    """Funcao helper para obter estatisticas do cache."""
    return cache_global.estatisticas()
