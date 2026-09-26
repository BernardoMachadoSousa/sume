"""
Modulo de exportacao para resultados de busca.
Fornece funcoes para exportar em diferentes formatos (JSON, CSV, texto).
"""

import json
import csv
from typing import Dict, List, Any
from io import StringIO
from datetime import datetime

def exportar_json(resultados: Dict[str, List[Dict]]) -> str:
    """Exporta resultados em formato JSON."""
    return json.dumps(resultados, ensure_ascii=False, indent=2)

def exportar_csv(resultados: Dict[str, List[Dict]]) -> str:
    """Exporta resultados em formato CSV."""
    output = StringIO()
    
    # Processa notas
    if resultados.get("notas"):
        writer = csv.DictWriter(
            output,
            fieldnames=["tipo", "titulo", "trecho", "caminho", "relevancia"],
            extrasaction="ignore"
        )
        writer.writeheader()
        for nota in resultados["notas"]:
            writer.writerow({
                "tipo": "Nota",
                "titulo": nota.get("titulo", ""),
                "trecho": nota.get("trecho", "")[:100],
                "caminho": nota.get("caminho", ""),
                "relevancia": f"{nota.get('relevancia', 0):.2f}"
            })
    
    # Processa arquivos
    if resultados.get("arquivos"):
        writer = csv.DictWriter(
            output,
            fieldnames=["tipo", "nome", "trecho", "caminho", "tamanho", "relevancia"],
            extrasaction="ignore"
        )
        if not resultados.get("notas"):
            writer.writeheader()
        for arq in resultados["arquivos"]:
            writer.writerow({
                "tipo": "Arquivo",
                "nome": arq.get("nome", ""),
                "trecho": arq.get("trecho", "")[:100],
                "caminho": arq.get("caminho", ""),
                "tamanho": f"{arq.get('tamanho', 0)} bytes",
                "relevancia": f"{arq.get('relevancia', 0):.2f}"
            })
    
    return output.getvalue()

def exportar_texto(resultados: Dict[str, List[Dict]], termo_busca: str = "") -> str:
    """Exporta resultados em formato texto legivel."""
    linhas = []
    
    linhas.append("=" * 70)
    linhas.append("RESULTADOS DE BUSCA")
    linhas.append("=" * 70)
    
    if termo_busca:
        linhas.append(f"Termo: {termo_busca}")
    
    linhas.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    linhas.append("")
    
    # Notas
    if resultados.get("notas"):
        linhas.append("NOTAS ENCONTRADAS")
        linhas.append("-" * 70)
        for i, nota in enumerate(resultados["notas"], 1):
            linhas.append(f"\n{i}. {nota.get('titulo', 'Sem titulo')}")
            linhas.append(f"   Relevancia: {nota.get('relevancia', 0):.0%}")
            linhas.append(f"   Caminho: {nota.get('caminho', '')}")
            linhas.append(f"   Trecho: {nota.get('trecho', '')[:150]}")
        linhas.append("")
    
    # Arquivos
    if resultados.get("arquivos"):
        linhas.append("ARQUIVOS ENCONTRADOS")
        linhas.append("-" * 70)
        for i, arq in enumerate(resultados["arquivos"], 1):
            linhas.append(f"\n{i}. {arq.get('nome', 'Sem nome')}")
            linhas.append(f"   Relevancia: {arq.get('relevancia', 0):.0%}")
            linhas.append(f"   Caminho: {arq.get('caminho', '')}")
            linhas.append(f"   Tamanho: {arq.get('tamanho', 0)} bytes")
            linhas.append(f"   Trecho: {arq.get('trecho', '')[:150]}")
        linhas.append("")
    
    linhas.append("=" * 70)
    
    return "\n".join(linhas)

def exportar_markdown(resultados: Dict[str, List[Dict]], termo_busca: str = "") -> str:
    """Exporta resultados em formato Markdown."""
    linhas = []
    
    linhas.append("# Resultados de Busca")
    if termo_busca:
        linhas.append(f"**Termo:** {termo_busca}")
    linhas.append(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    linhas.append("")
    
    # Notas
    if resultados.get("notas"):
        linhas.append("## Notas Encontradas")
        for i, nota in enumerate(resultados["notas"], 1):
            linhas.append(f"### {i}. {nota.get('titulo', 'Sem titulo')}")
            linhas.append(f"- **Relevancia:** {nota.get('relevancia', 0):.0%}")
            linhas.append(f"- **Caminho:** `{nota.get('caminho', '')}`")
            linhas.append(f"- **Trecho:** {nota.get('trecho', '')[:150]}")
            linhas.append("")
    
    # Arquivos
    if resultados.get("arquivos"):
        linhas.append("## Arquivos Encontrados")
        for i, arq in enumerate(resultados["arquivos"], 1):
            linhas.append(f"### {i}. {arq.get('nome', 'Sem nome')}")
            linhas.append(f"- **Relevancia:** {arq.get('relevancia', 0):.0%}")
            linhas.append(f"- **Caminho:** `{arq.get('caminho', '')}`")
            linhas.append(f"- **Tamanho:** {arq.get('tamanho', 0)} bytes")
            linhas.append(f"- **Trecho:** {arq.get('trecho', '')[:150]}")
            linhas.append("")
    
    return "\n".join(linhas)

def salvar_arquivo(conteudo: str, nome_arquivo: str, pasta_destino: str = None) -> str:
    """Salva conteudo exportado em arquivo."""
    import os
    
    if pasta_destino is None:
        pasta_destino = os.path.expanduser("~/Downloads")
    
    os.makedirs(pasta_destino, exist_ok=True)
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    
    with open(caminho_completo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    return caminho_completo
