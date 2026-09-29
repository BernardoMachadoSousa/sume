#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migração para consolidar notas duplicadas no vault do Obsidian.
Agrupa notas que se referem à mesma entidade (pessoa, lugar, etc.) com base em
título e aliases, mescla seu conteúdo e remove as notas duplicadas.
"""

import os
import sys
import re
import ast

# Adiciona o diretório raiz do projeto ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modulos.vault import salvar, ler, apagar, listar, resolver_entidade
from utils.nome_utils import normalizar_nome
from utils.logger import info as log_info, erro as log_erro
from utils import config as cfg


def extrair_frontmatter_e_corpo(texto: str):
    """
    Divide o texto de uma nota em frontmatter e corpo.
    Retorna (frontmatter_dict, corpo_string).
    Se não houver frontmatter válido, retorna ({}, texto).
    """
    partes = texto.split('---', 2)
    if len(partes) < 3:
        # Não há frontmatter
        return {}, texto
    frontmatter_text = partes[1]
    corpo = partes[2]
    frontmatter = {}
    for linha in frontmatter_text.splitlines():
        if ':' in linha:
            chave, valor = linha.split(':', 1)
            chave = chave.strip()
            valor = valor.strip()
            frontmatter[chave] = valor
    return frontmatter, corpo


def parse_lista(valor: str):
    """
    Tenta converter uma string em uma lista.
    Aceita formatos como: "[item1, item2]" ou "item1, item2".
    Retorna uma lista de strings.
    """
    if not valor:
        return []
    # Remove espaços extras
    valor = valor.strip()
    # Se estiver entre colchetes, tenta avaliar como lista Python
    if valor.startswith('[') and valor.endswith(']'):
        try:
            lista = ast.literal_eval(valor)
            if isinstance(lista, list):
                # Garante que todos os elementos sejam strings
                return [str(item).strip() for item in lista if str(item).strip()]
        except Exception:
            pass
    # Caso contrário, trata como lista separada por vírgulas
    return [item.strip() for item in valor.split(',') if item.strip()]


def main():
    print("Migration script started")
    log_info("migrar_vault", "Iniciando migração de consolidação de notas...")
    vault_path = cfg.get("caminho_obsidian")
    if not vault_path:
        vault_path = "dados/vault"
    if not os.path.isdir(vault_path):
        log_erro("migrar_vault", f"Caminho do vault não encontrado: {vault_path}")
        return

    # Lista todos os arquivos .md no vault usando a função listar do vault
    notas_info = listar()  # retorna lista de dicts com titulo, tags, caminho
    if not notas_info:
        log_info("migrar_vault", "Nenhuma nota encontrada no vault.")
        return

    # Vamos ler o conteúdo de cada nota
    notas = []  # lista de dicionários com metadados de cada nota
    for info in notas_info:
        caminho = info['caminho']
        titulo = info['titulo']
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                texto = f.read()
        except Exception as e:
            log_erro("migrar_vault", f"Erro ao ler {titulo}: {e}")
            continue

        frontmatter, corpo = extrair_frontmatter_e_corpo(texto)
        # O titulo já vem do frontmatter via listar, mas vamos usar o do frontmatter se existir, caso contrario o do arquivo
        titulo_front = frontmatter.get('titulo', titulo)
        aliases = parse_lista(frontmatter.get('aliases', ''))
        tags = parse_lista(frontmatter.get('tags', ''))
        links = parse_lista(frontmatter.get('links', ''))

        notas.append({
            'arquivo': os.path.basename(caminho),
            'caminho': caminho,
            'titulo': titulo_front,
            'frontmatter': frontmatter,
            'corpo': corpo,
            'aliases': aliases,
            'tags': tags,
            'links': links,
        })

    # Agrupa notas por entidade usando relação de prefixo em títulos normalizados e aliases
    # Vamos construir um grafo onde duas notas estão conectadas se:
    #   - o título normalizado de uma é prefixo do título normalizado da outra (ou vice-versa)
    #   - ou algum alias normalizado de uma é prefixo do título normalizado da outra (ou vice-versa)
    #   - ou o título normalizado de uma é prefixo de algum alias normalizado da outra (ou vice-versa)
    #   - ou algum alias normalizado de uma é prefixo de algum alias normalizado da outra (ou vice-versa)
    # Prefixo significa que a string curta é igual ao início da longa e a longa é estritamente maior.
    n = len(notas)
    # Pré-compute normalized titles and aliases
    norm_titles = [normalizar_nome(nota['titulo']) for nota in notas]
    norm_aliases_list = []
    for nota in notas:
        norm_aliases = [normalizar_nome(a) for a in nota['aliases']]
        norm_aliases_list.append(norm_aliases)
    
    # Construa lista de adjacência
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            connected = False
            # Verifique títulos
            ti, tj = norm_titles[i], norm_titles[j]
            if ti != tj:
                if ti.startswith(tj) or tj.startswith(ti):
                    connected = True
            # Verifique título i vs aliases j
            if not connected:
                for alias_j in norm_aliases_list[j]:
                    if ti.startswith(alias_j) or alias_j.startswith(ti):
                        if ti != alias_j:  # ensure strict prefix
                            connected = True
                            break
            # Verifique título j vs aliases i
            if not connected:
                for alias_i in norm_aliases_list[i]:
                    if tj.startswith(alias_i) or alias_i.startswith(tj):
                        if tj != alias_i:
                            connected = True
                            break
            # Verifique aliases i vs aliases j
            if not connected:
                for alias_i in norm_aliases_list[i]:
                    for alias_j in norm_aliases_list[j]:
                        if alias_i.startswith(alias_j) or alias_j.startswith(alias_i):
                            if alias_i != alias_j:
                                connected = True
                                break
                    if connected:
                        break
            if connected:
                adj[i].add(j)
                adj[j].add(i)
    
    # Encontre componentes conexos
    visited = [False] * n
    grupos = []
    for i in range(n):
        if not visited[i]:
            pilha = [i]
            componente = []
            visited[i] = True
            while pilha:
                no = pilha.pop()
                componente.append(no)
                for vizinho in adj[no]:
                    if not visited[vizinho]:
                        visited[vizinho] = True
                        pilha.append(vizinho)
            grupos.append(componente)
    
    # Processa cada grupo
    total_grupos = len(grupos)
    total_notas_antigas = n
    total_notas_novas = 0
    notas_removidas = 0

    for indice_grupo, indices in enumerate(grupos):
        if len(indices) == 1:
            # Grupo de uma única nota: nada a fazer
            total_notas_novas += 1
            continue

        # Escolhe a nota canônica: aquela com o título mais longo (mais completo)
        indice_canonica = max(indices, key=lambda i: len(notas[i]['titulo']))
        nota_canonica = notas[indice_canonica]
        titulo_canonico = nota_canonica['titulo']

        # Mescla metadados e conteúdo de todas as notas do grupo
        aliases_mesclados = set(nota_canonica['aliases'])
        tags_mesclados = set(nota_canonica['tags'])
        links_mesclados = set(nota_canonica['links'])
        corpo_mesclado = nota_canonica['corpo']

        for indice in indices:
            if indice == indice_canonica:
                continue
            nota = notas[indice]
            # Adiciona o título original como alias (se não for o canônico)
            if nota['titulo'] != titulo_canonico:
                aliases_mesclados.add(nota['titulo'])
            # Adiciona aliases, tags e links
            aliases_mesclados.update(nota['aliases'])
            tags_mesclados.update(nota['tags'])
            links_mesclados.update(nota['links'])
            # Mescla corpos: adiciona um separador e o corpo da nota
            if nota['corpo'].strip():
                corpo_mesclado += "\n\n---\n\n" + nota['corpo']

        # Converte conjuntos para listas ordenadas (para consistência)
        aliases_mesclados = list(aliases_mesclados)
        tags_mesclados = list(tags_mesclados)
        links_mesclados = list(links_mesclados)

        # Salva a nota mesclada (sobrescrevendo a nota canônica)
        try:
            salvar(
                titulo=titulo_canonico,
                corpo=corpo_mesclado,
                tags=tags_mesclados,
                links=links_mesclados,
                aliases=aliases_mesclados
            )
            log_info("migrar_vault", f"Nota canônica atualizada: {titulo_canonico}")
        except Exception as e:
            log_erro("migrar_vault", f"Erro ao salvar nota canônica {titulo_canonico}: {e}")
            continue

        # Remove as outras notas do grupo
        for indice in indices:
            if indice == indice_canonica:
                continue
            nota = notas[indice]
            try:
                apagar(nota['titulo'])
                log_info("migrar_vault", f"Nota removida: {nota['titulo']}")
                notas_removidas += 1
            except Exception as e:
                log_erro("migrar_vault", f"Erro ao remover nota {nota['titulo']}: {e}")

        total_notas_novas += 1

    log_info("migrar_vault", f"Migração concluída. "
                   f"Grupos processados: {total_grupos}, "
                   f"Notas antes: {total_notas_antigas}, "
                   f"Notas depois: {total_notas_novas}, "
                   f"Notas removidas: {notas_removidas}")


if __name__ == '__main__':
    print("Migration script started")
    main()
    print("Migration script finished")