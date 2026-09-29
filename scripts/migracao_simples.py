#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple migration script to consolidate notes in the Obsidian vault.
Groups notes by normalized title (lowercase, no accents, spaces/hyphens/underscores equal).
For each group, picks the note with the longest original title as canonical,
merges aliases, tags, links, and bodies, then deletes duplicates.
"""

import os
import sys
import re

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modulos.vault import salvar, ler, apagar, listar
from utils.nome_utils import normalizar_nome
from utils.logger import info as log_info, erro as log_erro
from utils import config as cfg


def split_frontmatter(text: str):
    """Split markdown text into frontmatter dict and body.
    Returns (frontmatter_dict, body_string). If no frontmatter, returns ({}, text)."""
    if not text.strip().startswith('---'):
        return {}, text
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1]
    body = parts[2]
    fm = {}
    for line in fm_text.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()
            fm[key] = val
    return fm, body


def parse_list_field(value: str):
    """Parse a frontmatter list-like value.
    Accepts formats like '[item1, item2]' or 'item1, item2' or just 'item'.
    Returns list of strings (stripped)."""
    if not value:
        return []
    v = value.strip()
    # If it looks like a Python list
    if v.startswith('[') and v.endswith(']'):
        try:
            import ast
            lst = ast.literal_eval(v)
            if isinstance(lst, list):
                return [str(x).strip() for x in lst if str(x).strip()]
        except Exception:
            pass
    # Otherwise split by commas
    return [x.strip() for x in v.split(',') if x.strip()]


def main():
    log_info("migracao_simples", "Iniciando migração simples de consolidação...")
    vault_path = cfg.get("caminho_obsidian")
    if not vault_path:
        vault_path = "dados/vault"
    if not os.path.isdir(vault_path):
        log_erro("migracao_simples", f"Vault path not found: {vault_path}")
        return

    # Get all notes via listar
    notas_info = listar()
    if not notas_info:
        log_info("migracao_simples", "Nenhuma nota encontrada.")
        return

    # Build list of note data
    notas = []  # each dict: arquivo, caminho, titulo, frontmatter, corpo, aliases, tags, links
    for info in notas_info:
        caminho = info['caminho']
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                texto = f.read()
        except Exception as e:
            log_erro("migracao_simples", f"Erro ao ler {info['titulo']}: {e}")
            continue
        fm, corpo = split_frontmatter(texto)
        titulo = fm.get('titulo', info['titulo'])
        aliases = parse_list_field(fm.get('aliases', ''))
        tags = parse_list_field(fm.get('tags', ''))
        links = parse_list_field(fm.get('links', ''))
        notas.append({
            'arquivo': os.path.basename(caminho),
            'caminho': caminho,
            'titulo': titulo,
            'frontmatter': fm,
            'corpo': corpo,
            'aliases': aliases,
            'tags': tags,
            'links': links,
        })

    # Group by normalized title
    grupos = {}  # norm_titulo -> list of indices
    for idx, nota in enumerate(notas):
        norm = normalizar_nome(nota['titulo'])
        grupos.setdefault(norm, []).append(idx)

    total_grupos = len(grupos)
    total_antigas = len(notas)
    total_novas = 0
    removidas = 0

    for norm, indices in grupos.items():
        if len(indices) == 1:
            total_novas += 1
            continue
        # Choose canonical: note with longest original title (more specific)
        canon_idx = max(indices, key=lambda i: len(notas[i]['titulo']))
        canon = notas[canon_idx]
        titulo_canonico = canon['titulo']

        # Merge metadata
        aliases_set = set(canon['aliases'])
        tags_set = set(canon['tags'])
        links_set = set(canon['links'])
        corpo_merged = canon['corpo']

        for idx in indices:
            if idx == canon_idx:
                continue
            nota = notas[idx]
            # Add this note's title as alias if different
            if nota['titulo'] != titulo_canonico:
                aliases_set.add(nota['titulo'])
            # Merge aliases, tags, links
            aliases_set.update(nota['aliases'])
            tags_set.update(nota['tags'])
            links_set.update(nota['links'])
            # Merge bodies
            if nota['corpo'].strip():
                corpo_merged += "\n\n---\n\n" + nota['corpo']

        # Convert to lists
        aliases_list = sorted(aliases_set)
        tags_list = sorted(tags_set)
        links_list = sorted(links_set)

        # Write canonical note
        try:
            salvar(
                titulo=titulo_canonico,
                corpo=corpo_merged,
                tags=tags_list,
                links=links_list,
                aliases=aliases_list
            )
            log_info("migracao_simples", f"Nota canônica atualizada: {titulo_canonico}")
        except Exception as e:
            log_erro("migracao_simples", f"Erro ao salvar {titulo_canonico}: {e}")
            continue

        # Delete other notes in group
        for idx in indices:
            if idx == canon_idx:
                continue
            nota = notas[idx]
            try:
                apagar(nota['titulo'])
                log_info("migracao_simples", f"Nota removida: {nota['titulo']}")
                removidas += 1
            except Exception as e:
                log_erro("migracao_simples", f"Erro ao remover {nota['titulo']}: {e}")

        total_novas += 1

    log_info("migracao_simples", f"Migração concluída. "
                   f"Grupos: {total_grupos}, Notas antes: {total_antigas}, "
                   f"Notas depois: {total_novas}, Removidas: {removidas}")


if __name__ == '__main__':
    main()