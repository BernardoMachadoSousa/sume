"""
Busca por arquivos no computador.
"""

import os
from typing import List, Dict, Any
from utils import config as cfg
from . import ranker, semantic

def _get_search_paths() -> List[str]:
    """
    Retorna a lista de pastas onde a busca deve ser realizada.
    Suporta caminhos absolutos e relativos ao home do usuário.
    """
    pastas_config = cfg.get("pastas_busca", [])
    if not pastas_config:
        pastas_config = ["Documents", "Desktop", "Downloads", "Pictures"]
    
    home = os.path.expanduser("~")
    paths = []
    for pasta in pastas_config:
        if os.path.isabs(pasta):
            caminho = pasta
        else:
            caminho = os.path.join(home, pasta)
        
        if os.path.exists(caminho):
            paths.append(caminho)
    
    return paths

def _get_file_extensions() -> List[str]:
    """
    Retorna a lista de extensões de arquivo a serem consideradas na busca.
    """
    extensoes = cfg.get("extensoes_busca", [])
    if not extensoes:
        # Padrão: extensões comuns de documentos, imagens, código, etc.
        extensoes = [
            ".txt", ".md", ".pdf", ".docx", ".xlsx", ".pptx",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp",
            ".zip", ".rar", ".7z",
            ".py", ".js", ".ts", ".html", ".css",
            ".json", ".csv", ".xml", ".yaml", ".yml"
        ]
    return extensoes

def _should_index_file(filepath: str, extensoes: List[str]) -> bool:
    """
    Determina se um arquivo deve ser indexado com base na extensão.
    """
    _, ext = os.path.splitext(filepath)
    return ext.lower() in extensoes

def buscar(termo: str) -> List[Dict[str, Any]]:
    """
    Busca por `termo` nos arquivos indexados do computador.
    Retorna uma lista de dicionários com chaves: 'nome', 'caminho', 'trecho'.
    """
    if not termo or not termo.strip():
        return []
    
    termo_lower = termo.lower()
    resultados = []
    
    # Obtém configurações de busca
    paths = _get_search_paths()
    extensoes = _get_file_extensions()
    
    # Percorre todas as pastas configuradas
    for base_path in paths:
        for root, dirs, files in os.walk(base_path):
            # Pula diretórios ocultos e de sistema (opcional)
            dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('$')]
            
            for file in files:
                filepath = os.path.join(root, file)
                
                # Verifica se o arquivo deve ser indexado
                if not _should_index_file(filepath, extensoes):
                    continue
                
                # Tenta ler o arquivo como texto (pula binários)
                try:
                    # Tenta diferentes encodings comuns
                    content = None
                    for encoding in ['utf-8', 'latin-1', 'cp1252']:
                        try:
                            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if content is None:
                        continue  # Não conseguiu ler como texto
                    
                    # Busca simples por termo (case-insensitive)
                    if termo_lower in content.lower():
                        # Extrai um trecho ao redor do primeiro occurrence
                        idx = content.lower().find(termo_lower)
                        start = max(0, idx - 150)
                        end = min(len(content), idx + len(termo) + 150)
                        trecho = content[start:end]
                        # Adiciona elipses se cortado
                        if start > 0:
                            trecho = "..." + trecho
                        if end < len(content):
                            trecho = trecho + "..."
                        
                        resultados.append({
                            "nome": file,
                            "caminho": filepath,
                            "trecho": trecho
                        })
                
                except (OSError, IOError):
                    # Pula arquivos que não podem ser lidos (permissão, etc.)
                    continue
    
    # Classifica os resultados por relevância
    if resultados:
        resultados = ranker.rank_results(resultados, termo)
        resultados = semantic.enriquecer_com_embeddings(resultados, termo)
        resultados = semantic.combinar_scores(resultados, peso_tfidf=0.6)
    
    return resultados


def buscar_por_nome(termo: str, limite: int = 10) -> List[Dict[str, Any]]:
    if not termo or not termo.strip():
        return []

    termo_lower = termo.lower().strip()
    extensoes = _get_file_extensions()
    resultados = []

    for base_path in _get_search_paths():
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('$')]
            for file in files:
                if not _should_index_file(os.path.join(root, file), extensoes):
                    continue
                nome_lower = file.lower()
                nome_sem_ext, _ = os.path.splitext(nome_lower)
                if termo_lower == nome_lower or termo_lower == nome_sem_ext:
                    score = 1.0
                elif nome_sem_ext.startswith(termo_lower) or nome_lower.startswith(termo_lower):
                    score = 0.9
                elif termo_lower in nome_sem_ext:
                    score = 0.8
                elif termo_lower in nome_lower:
                    score = 0.7
                elif all(p in nome_lower for p in termo_lower.split()):
                    score = 0.55
                else:
                    continue
                resultados.append({
                    "nome": file,
                    "caminho": os.path.join(root, file),
                    "score": score,
                })

    resultados.sort(key=lambda r: (-r["score"], len(r["nome"])))
    return resultados[:limite]
