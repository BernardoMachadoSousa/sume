"""
Cérebro do Sumé — grafo de conhecimento pessoal no vault.

Cada entidade (pessoa, lugar, data) vira uma nota Markdown no vault.
Os fatos ficam dentro da nota da entidade com links [[wikilink]] para
outras entidades, formando um grafo legível no Obsidian.

Estrutura de uma nota de entidade:
    ---
    titulo: Malu
    tipo: pessoa
    tags: [cerebro, pessoa]
    links: [Bernardo]
    atualizado: ...
    propriedades: {idade: 21}
    relacoes: [{tipo: mora_em, alvo: [[Salvador]], status: atual}]
    ---

    ## Sobre Malu

    - aniversário: [[12 de outubro]]
    - namorada de: [[Bernardo]]

    ## Bernardo sobre Malu
    - "ela é muito fofa"
"""

import os
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from modulos import vault
from modulos.memoria import lembrar, guardar, PERMANENTE
from utils.logger import erro as log_erro, info as log_info
from utils.nome_utils import normalizar_nome, e_pronome_usuario
from modulos.vault import _frontmatter_campo, _frontmatter_objeto
from utils.segredos import detectar_segredo


# ── proveniência, categoria e importância ─────────────────────────────────────

# Pesos base por categoria. A confiança extraída pela IA modula o score final.
_PESO_CATEGORIA = {
    "nome": 1.0,
    "identidade": 0.9,
    "moradia": 0.7,
    "trabalho": 0.7,
    "estudo": 0.65,
    "relacao": 0.8,
    "preferencia": 0.6,
    "saude": 0.85,
    "aniversario": 0.8,
    "contato": 0.9,
    "geral": 0.5,
}


def _categorizar_fato(fato: str) -> str:
    """
    Infere a categoria semântica de um bullet de fato a partir do texto.
    Heurística por palavras-chave (barata, determinística, sem LLM).
    """
    t = (fato or "").lower()
    if not t:
        return "geral"

    if re.search(r"\bnome\b|\bse chama\b|\bchama-se\b", t):
        return "nome"
    if re.search(r"\banivers[aá]rio\b|\bnascid[oa]\b|\bnasceu\b", t):
        return "aniversario"
    if re.search(r"\bmora\b|\bmoradia\b|\b reside\b|\bcidade\b|\bvodouce\b", t):
        return "moradia"
    if re.search(r"\btrabalha\b|\bemprego\b|\bcargo\b|\bprofiss[aã]o\b", t):
        return "trabalho"
    if re.search(r"\bestuda\b|\bestudante\b|\bcurso\b|\bfaculdade\b|\buniversidade\b", t):
        return "estudo"
    if re.search(r"\bnamorad[ao]\b|\bespos[ao]\b|\bamig[ao]\b|\bm[aã]e\b|\bpai\b|\birm[aã]o\b|\bfam[ií]lia\b", t):
        return "relacao"
    if re.search(r"\btelefone\b|\bemail\b|\be-?mail\b|\bcpf\b|\bendere[cç]o\b", t):
        return "contato"
    if re.search(r"\balergia\b|\bdiabet\b|\bmedicamento\b|\brem[eé]dio\b|\bdoen[cç]a\b", t):
        return "saude"
    if re.search(r"\bgosta\b|\bprefere\b|\bcurte\b|\bama\b|\bod(ei|ia)\b|\bfavori", t):
        return "preferencia"
    return "geral"


def _importancia_fato(categoria: str, confianca: float) -> float:
    """
    Calcula a importância (0.0–1.0) de um fato a partir da categoria e da
    confiança da extração. Confiança alta sobe o peso; confiança baixa reduz.
    """
    peso = _PESO_CATEGORIA.get(categoria, _PESO_CATEGORIA["geral"])
    conf = max(0.0, min(1.0, float(confianca or 0.0)))
    # Média entre o peso da categoria e a confiança (evita inflar com conf=1.0)
    return round((peso + conf) / 2, 3)


def _enriquecer_relacao(rel: Dict[str, Any], confianca: float, fonte: str = "conversa") -> Dict[str, Any]:
    """
    Adiciona metadados de proveniência a uma relação, preservando campos
    já existentes (ex.: 'usos' de recalls anteriores).
    """
    cat = rel.get("categoria") or _categorizar_fato(
        f"{rel.get('tipo', '')} {rel.get('alvo', '')}"
    )
    rel.setdefault("categoria", cat)
    rel.setdefault("confianca", round(float(confianca or 0.0), 3))
    rel.setdefault("importancia", _importancia_fato(cat, confianca))
    rel.setdefault("fonte", fonte)
    rel.setdefault("usos", 0)
    return rel


def _recusar_texto_sensivel(texto: str) -> str | None:
    """
    Retorna uma mensagem de recusa se o texto contiver um segredo.
    Caso contrário, retorna None (pode seguir o fluxo normal).
    """
    achado = detectar_segredo(texto)
    if not achado:
        return None
    return (
        f"Não vou guardar isso: parece um {achado}. "
        "Segredos (senhas, tokens, chaves) ficam fora do meu cérebro — "
        "use o cofre ou um gerenciador de senhas pra isso."
    )


# ── utilidades de detecção de contradição e atualização ──────────────────────


def _extrair_relacao_de_bullet(bullet: str) -> Optional[Dict[str, Any]]:
    """
    Extrai uma relação estruturada de um bullet de texto.
    Formatos suportados:
    - "predicado: [[entidade]]"
    - "predicado: valor"
    - "predicado de [[entidade]]" (forma inversa)
    Retorna dict com {predicado, objeto, tipo_objeto} ou None.
    """
    bullet = bullet.strip()
    if not bullet.startswith("- "):
        return None
    bullet = bullet[2:]  # Remove "- "
    
    # Formato: predicado: [[entidade]]
    match = re.match(r"^([^:]+):\s*\[\[([^\]]+)\]\]$", bullet)
    if match:
        predicado, objeto = match.groups()
        return {
            "predicado": predicado.strip(),
            "objeto": objeto.strip(),
            "tipo_objeto": "entidade"
        }
    
    # Formato: predicado: valor
    match = re.match(r"^([^:]+):\s*([^\[\]]+)$", bullet)
    if match:
        predicado, objeto = match.groups()
        objeto = objeto.strip()
        # Tenta determinar se é uma data, número, etc.
        if re.match(r"\d{1,2}\s+de\s+\w+\s+\d{4}", objeto):  # "12 de outubro de 2004"
            tipo_objeto = "data"
        elif re.match(r"\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}", objeto):  # "12/10/2004"
            tipo_objeto = "data"
        elif objeto.isdigit():
            tipo_objeto = "numero"
        else:
            tipo_objeto = "valor"
        return {
            "predicado": predicado.strip(),
            "objeto": objeto,
            "tipo_objeto": tipo_objeto
        }
    
    # Formato: predicado de [[entidade]] (ex: "namorada de [[Bernardo]]")
    match = re.match(r"^(.+)\s+de\s+\[\[([^\]]+)\]\]$", bullet)
    if match:
        predicado, objeto = match.groups()
        # Inverte: se X é Y de Z, então Z tem relação Y com X
        # "Malu é namorada de [[Bernardo]]" => Bernardo tem relação "namorada de" com Malu
        return {
            "predicado": predicado.strip(),
            "objeto": objeto.strip(),
            "tipo_objeto": "entidade",
            "invertido": True
        }
    
    return None


def _eh_mesma_relacao(rel1: Dict[str, Any], rel2: Dict[str, Any]) -> bool:
    """Verifica se duas relações são do mesmo tipo (mesmo sujeito e predicado)."""
    # Compara predicados (normalizando)
    pred1 = rel1.get("predicado", "").lower().strip()
    pred2 = rel2.get("predicado", "").lower().strip()
    
    # Se um é invertido, precisamos ajustar
    if rel1.get("invertido"):
        # rel1 é do formato "A é pred de B" => significa B pred A
        # Para comparar com rel2, precisamos saber o sujeito de cada um
        # Mas como não temos o sujeito aqui, vamos fazer uma comparação simplificada
        pass  # Por agora, ignora o invertido para detecção básica
    
    return pred1 == pred2


def _detectar_contradiccao(rel_nova: Dict[str, Any], rel_existente: Dict[str, Any]) -> bool:
    """
    Detecta se duas relações são contraditórias (mesmo sujeito/predicado, objeto diferente).
    """
    # Primeiro verifica se é a mesma relação (mesmo predicado)
    if not _eh_mesma_relacao(rel_nova, rel_existente):
        return False
    
    # Se for a mesma relação, verifica se o objeto é diferente
    obj_nova = rel_nova.get("objeto", "").lower().strip()
    obj_exist = rel_existente.get("objeto", "").lower().strip()
    
    # Ignora diferenças de formatação menores
    obj_nova_norm = re.sub(r"\s+", " ", obj_nova)
    obj_exist_norm = re.sub(r"\s+", " ", obj_exist)
    
    return obj_nova_norm != obj_exist_norm


def _formatar_relacao_historica(bullet_antigo: str) -> str:
    """
    Converte um bullet atual para indicar que é histórico.
    Ex: "- mora em: [[Salvador]]" -> "- morava em: [[Salvador]] (até 2024)"
    """
    # Tenta melhorar o verbodo para indicar passado
    bullet = bullet_antigo[2:]  # Remove "- "
    
    # Substituições comuns para indicar passado
    substituicoes = [
        (r"mora em", "morava em"),
        (r"estuda", "estudou"),
        (r"trabalha em", "trabalhava em"),
        (r"namora", "namorou"),
        (r"é", "era"),
        (r"possui", "possedia"),
        (r"conhece", "conhecia"),
        (r"gosta de", "gostava de"),
        (r"desenvolve", "desenvolvia"),
        (r"cria", "criava"),
        (r"pertence a", "pertencia a"),
    ]
    
    bullet_modificado = bullet
    for padrao, substituicao in substituicoes:
        if re.search(padrao, bullet, re.IGNORECASE):
            bullet_modificado = re.sub(padrao, substituicao, bullet_modificado, flags=re.IGNORECASE)
            break
    
    # Se nenhuma substituição aconteceu, adiciona "(antes)"
    if bullet_modificado == bullet:
        bullet_modificado = f"{bullet} (antes)"
    
    return f"- {bullet_modificado}"


def _adicionar_relacao_estruturada(titulo: str, relacao: Dict[str, Any], 
                                  data_atual: Optional[str] = None) -> None:
    """
    Adiciona uma relação estruturada ao frontmatter da nota.
    """
    if data_atual is None:
        data_atual = datetime.now().strftime("%Y-%m-%d")
    
    # Prepara a relação para armazenamento
    rel_para_salvar = {
        "tipo": relacao.get("predicado", ""),
        "alvo": relacao.get("objeto", ""),
        "status": "atual",
        "desde": data_atual
    }
    
    # Se for uma relação invertida, ajusta
    if relacao.get("invertido"):
        # "A é pred de B" => B tem relacao pred com A
        # Já está no formato correto se o sujeito e objeto foram trocados na chamada
        pass
    
    # Obtém relações existentes
    notas_existentes = vault.obter_relacoes(titulo) or []
    
    # Verifica se já existe uma relação semelhante para atualizar
    relacao_atualizada = False
    for i, rel_exist in enumerate(notas_existentes):
        if (rel_exist.get("tipo") == rel_para_salvar["tipo"] and 
            rel_exist.get("alvo") == rel_para_salvar["alvo"]):
            # Atualiza a existente
            notas_existentes[i] = rel_para_salvar
            relacao_atualizada = True
            break
    
    if not relacao_atualizada:
        notas_existentes.append(rel_para_salvar)
    
    # Obtém outras propriedades existentes para preservar
    notas = vault.listar()
    propriedades_existentes = []
    tags_existentes = []
    aliases_existentes = []
    links_existentes = []
    
    for nota in notas:
        if nota["titulo"] == titulo:
            propriedades_existentes = nota.get("propriedades", [])
            tags_existentes = nota.get("tags", [])
            aliases_existentes = nota.get("aliases", [])
            links_existentes = nota.get("links", [])
            break
    
    # Salva com as relações atualizadas
    vault.salvar(
        titulo,
        vault.ler(titulo) or "",  # Mantém o corpo atual
        tags=tags_existentes,
        links=links_existentes,
        aliases=aliases_existentes,
        propriedades=propriedades_existentes,
        relacoes=notas_existentes
    )


def _processar_fato_com_detec_contradicao(titulo: str, tipo: str, 
                                        fato_string: str, 
                                        links_extras: List[str] = None,
                                        confianca: float = 0.9,
                                        fonte: str = "conversa") -> None:
    """
    Processa um fato (string) com detecção de contradição e atualização estruturada.
    Mantém o comportamento anterior de adicionar bullets, mas também:
    1. Detecta contradições em relações estruturadas
    2. Atualiza o frontmatter com relações estruturadas
    3. Marca fatos antigos como históricos quando apropriado
    """
    if links_extras is None:
        links_extras = []
    
    # Converte título para canônico (resolve typos)
    titulo = _resolver(titulo)
    
    # Obtém a nota atual COMPLETA (para preservar frontmatter existente)
    nota_atual_completa = vault._ler_raw(titulo) or ""
    if nota_atual_completa is None:
        nota_atual_completa = ""
    
    # Extrai o corpo atual (sem frontmatter) para processamento de bullets
    partes_atuais = nota_atual_completa.split("---", 2)
    corpo_atual = partes_atuais[2].strip() if len(partes_atuais) == 3 else nota_atual_completa.strip()
    
    # Extrai frontmatter existente para saber o que preservar
    frontmatter_existente = partes_atuais[1] if len(partes_atuais) >= 2 else ""
    
    # Extrai tags, links, aliases do frontmatter existente para preservar
    tags_existentes = _frontmatter_campo(frontmatter_existente, "tags")
    links_existentes = _frontmatter_campo(frontmatter_existente, "links")
    aliases_existentes = _frontmatter_campo(frontmatter_existente, "aliases")
    
    # Extrai tipo_entidade existente do frontmatter para preservar
    tipo_existente = None
    for linha in frontmatter_existente.splitlines():
        if linha.startswith("tipo_entidade:"):
            tipo_existente = linha.split(":", 1)[1].strip()
            break
    
    # Extrai propriedades existentes do frontmatter para preservar
    propriedades_existentes = []
    if frontmatter_existente:
        propriedades_existentes = _frontmatter_objeto(frontmatter_existente, "propriedades")
    
    # Prepara as relações estruturadas para atualização
    relacoes_para_salvar = []
    if frontmatter_existente:
        relacoes_para_salvar = _frontmatter_objeto(frontmatter_existente, "relacoes")
    
    # Primeiro, tenta extrair uma relação estruturada do bullet
    relacao_nova = _extrair_relacao_de_bullet(f"- {fato_string}")
    
    # Extrai todas as relações existentes do corpo da nota (bullets) para detecção de contradição
    relacoes_existentes_bullets = []
    linhas = corpo_atual.split("\n")
    for linha in linhas:
        rel = _extrair_relacao_de_bullet(linha)
        if rel:
            relacoes_existentes_bullets.append(rel)
    
    # Se conseguimos extrair uma relação estruturada nova, verificamos contradições
    if relacao_nova and relacao_nova.get("predicado"):
        contradicoes_encontradas = []
        for rel_exist in relacoes_existentes_bullets:
            if _detectar_contradiccao(relacao_nova, rel_exist):
                contradicoes_encontradas.append(rel_exist)
        
        # Se encontrou contradições, marca as antigas como históricas
        if contradicoes_encontradas:
            corpo_modificado = corpo_atual
            for rel_antiga in contradicoes_encontradas:
                # Reconstrói o bullet antigo para modificar
                if rel_antiga.get("tipo_objeto") == "entidade":
                    if rel_antiga.get("invertido"):
                        bullet_antigo = f"- {rel_antiga['predicado']} de [[{rel_antiga['objeto']}]]"
                    else:
                        bullet_antigo = f"- {rel_antiga['predicado']}: [[{rel_antiga['objeto']}]]"
                else:
                    bullet_antigo = f"- {rel_antiga['predicado']}: {rel_antiga['objeto']}"
                
                # Se o bullet existir no corpo, substitui pelo histórico
                if bullet_antigo in corpo_modificado:
                    bullet_historico = _formatar_relacao_historica(bullet_antigo)
                    corpo_modificado = corpo_modificado.replace(bullet_antigo, bullet_historico, 1)
            
            # Atualiza o corpo com os bullets historicizados
            corpo_atual = corpo_modificado
    
    # Agora adiciona o novo bullet (mantém comportamento antigo para compatibilidade)
    novo_bullet = f"- {fato_string}"
    if novo_bullet not in corpo_atual:
        corpo_atual = (corpo_atual + "\n" + novo_bullet).strip() if corpo_atual else novo_bullet
    
    # Extrai links do novo (e antigo) bullet para garantir que sejam salvos
    links_encontrados = re.findall(r"\[\[([^\]]+)\]\]", corpo_atual)
    links_novos = list(links_encontrados)
    for i, link in enumerate(links_novos):
        resolvido = vault.resolver_entidade(link) or link
        links_novos[i] = resolvido
    # Também adiciona os links_extras especificados na chamada (após resolver)
    for link in (links_extras or []):
        resolvido = vault.resolver_entidade(link) or link
        if resolvido not in links_novos:
            links_novos.append(resolvido)
    
    # Adiciona a nova relação estruturada se for válida
    if relacao_nova and relacao_nova.get("predicado"):
        if relacao_nova.get("tipo_objeto") == "entidade":
            objeto_alvo = relacao_nova["objeto"]
            # Verifica se já existe uma relação semelhante para evitar duplicatas
            relacao_existe = False
            for rel_exist in relacoes_para_salvar:
                if (rel_exist.get("tipo") == relacao_nova["predicado"] and 
                    rel_exist.get("alvo") == objeto_alvo and
                    rel_exist.get("invertido", False) == relacao_nova.get("invertido", False)):
                    relacao_existe = True
                    break
            if not relacao_existe:
                relacoes_para_salvar.append(_enriquecer_relacao({
                    "tipo": relacao_nova["predicado"],
                    "alvo": objeto_alvo,
                    "invertido": relacao_nova.get("invertido", False)
                }, confianca, fonte))
    
    # Recusa de segredos: nunca grava credencial no grafo
    recusa = _recusar_texto_sensivel(corpo_atual)
    if recusa:
        log_info("cerebro", f"fato sensível recusado em '{titulo}': {recusa}")
        return

    # Salva a nota, preservando campos não especificados e atualizando apenas o que mudou
    vault.salvar(
        titulo,
        corpo_atual,
        tags=tags_existentes if tags_existentes else None,
        links=links_novos if links_novos else None,
        aliases=aliases_existentes if aliases_existentes else None,
        tipo_entidade=tipo_existente,
        propriedades=propriedades_existentes if propriedades_existentes else None,
        relacoes=relacoes_para_salvar if relacoes_para_salvar else None
    )
    
    # Processa links adicionais (para relações bidirecionais)
    for link in links_extras:
        # Adiciona o link bidirecional na nota vinculada
        nota_link = vault.ler(link) or ""
        if f"[[{titulo}]]" not in nota_link:
            nota_link_completa = vault._ler_raw(link) or ""
            if nota_link_completa:
                partes_link = nota_link_completa.split("---", 2)
                corpo_link = partes_link[2].strip() if len(partes_link) == 3 else nota_link_completa.strip()
                novo_corpo_link = corpo_link + f"\n- [[{titulo}]]" if corpo_link else f"- [[{titulo}]]"
                vault.salvar(link, novo_corpo_link)
            else:
                vault.salvar(link, f"- [[{titulo}]]")


# ── utilidades ───────────────────────────────────────────────────────────────

def _nome_usuario() -> str:
    return lembrar("nome_usuario") or "eu"


def _titulo_entidade(nome: str) -> str:
    return nome.strip().title()


def _ler_entidade(titulo: str) -> str:
    return vault.ler(titulo) or ""


def _salvar_entidade(titulo: str, corpo: str, tipo: str, links: list[str]):
    tags = ["cerebro", tipo]
    vault.salvar(titulo, corpo, tags=tags, links=links)


def _extrair_data(texto: str) -> tuple[str, str, str] | None:
    """
    Tenta extrair dia, mês e ano de uma string que representa uma data.
    Formatos suportados:
      - "12 de outubro de 2004"
      - "12/10/2004"
      - "12-10-2004"
      - "12 outubro 2004"
    Retorna (dia, mes, ano) como strings, ou None se não conseguir.
    """
    import re
    # Normaliza espaços
    texto = texto.strip()
    # Padrao 1: "12 de outubro de 2004"
    padrao1 = r"^(\d{1,2})\s+de\s+([a-zA-ZÀ-ÿ]+)\s+de\s+(\d{4})$"
    m = re.match(padrao1, texto, re.IGNORECASE)
    if m:
        dia, mes, ano = m.groups()
        return (dia, mes, ano)
    # Padrao 2: "12/10/2004" ou "12-10-2004"
    padrao2 = r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$"
    m = re.match(padrao2, texto)
    if m:
        dia, mes, ano = m.groups()
        # Converte mes numero para nome? Vamos manter como numero por enquanto, mas a nota do mes sera o numero.
        # Porém, queremos que o mes seja por extenso para encadear com outras datas do mesmo mes.
        # Vamos tentar converter o numero para nome.
        try:
            mes_num = int(mes)
            if 1 <= mes_num <= 12:
                # Nome dos meses em português
                meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
                mes = meses[mes_num - 1]
            else:
                # Se estiver fora do intervalo, deixamos como numero
                pass
        except ValueError:
            pass
        return (dia, mes, ano)
    # Padrao 3: "12 outubro 2004" (sem "de")
    padrao3 = r"^(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})$"
    m = re.match(padrao3, texto, re.IGNORECASE)
    if m:
        dia, mes, ano = m.groups()
        return (dia, mes, ano)
    return None


def _acrescentar_link_na_nota(titulo: str, link: str) -> None:
    """
    Acrescenta um link [[link]] como bullet na nota com o titulo dado,
    caso ainda nao exista.
    """
    existente = vault.ler(titulo)
    if existente is None:
        # Nota nao existe, cria com o link
        vault.salvar(titulo, f"- [[{link}]]")
    else:
        # Verifica se o link ja esta presente (como [[link]] ou com espacos dentro?)
        # Vamos fazer uma busca simples por [[link]]
        if f"[[{link}]]" not in existente:
            vault.append_to_note(titulo, f"- [[{link}]]")


def _garantir_nos_calendario(dia: str, mes: str, ano: str) -> None:
    """
    Garante que existem notas para o dia, mes e ano, e que elas estao ligadas em cadeia:
      dia -> mes -> ano
    Cada nota recebe um tipo especifico (dia, mes, ano) para possibilitar filtragem futura.
    """
    # Normaliza o mes: remove acentos, deixa minusculo, e substitui hifens/underscores por espacos?
    # Vamos usar a mesma normalizacao de nomes para ter consistencia, mas note que o mes pode ser escrito de varias formas.
    mes_norm = normalizar_nome(mes)
    # No entanto, queremos que a nota do mes tenha um titulo que seja reconhecivel.
    # Se o mes_norm for vazio (ex: mes era "de"), caimos de volta para o mes original lower case.
    if not mes_norm:
        mes_norm = mes.lower()

    # 1. Nota do dia
    titulo_dia = dia
    # Verifica se a nota do dia ja existe e tem o tipo "dia" (pelo menos nas tags)
    # Vamos apenas garantir que ela existe; se nao existir, criamos com tipo "dia" e link para o mes.
    if vault.ler(titulo_dia) is None:
        vault.salvar(titulo_dia, f"- [[{mes_norm}]]", tags=["dia"], links=[mes_norm])
    else:
        # Nota existe, asseguramos que tem o link para o mes
        _acrescentar_link_na_nota(titulo_dia, mes_norm)

    # 2. Nota do mes
    titulo_mes = mes_norm
    if vault.ler(titulo_mes) is None:
        vault.salvar(titulo_mes, f"- [[{ano}]]", tags=["mes"], links=[ano])
    else:
        _acrescentar_link_na_nota(titulo_mes, ano)

    # 3. Nota do ano
    titulo_ano = ano
    if vault.ler(titulo_ano) is None:
        # Nota do ano so precisa existir, sem link obrigatorio
        vault.salvar(titulo_ano, "", tags=["ano"], links=[])
    # Se ja existe, nao precisamos adicionar nada.


def _extrair_links_existentes(corpo: str) -> list[str]:
    return re.findall(r"\[\[([^\]]+)\]\]", corpo)


def _resolver(nome: str) -> str:
    """Título canônico se a nota já existe (inclui typos); senão o nome original."""
    canon = vault.resolver_entidade(nome, nome_usuario=_nome_usuario())
    return canon or nome


def _adicionar_fato(titulo: str, tipo: str, fato: str, links_extras: list[str] | None = None,
                    confianca: float = 0.9, fonte: str = "conversa") -> None:
    """
    Adiciona um bullet de fato na nota da entidade, criando-a se não existir.
    Typos resolvem para a nota canônica e viram alias.

    Agora com detecção de contradição e suporte a relações estruturadas.
    Se o fato adicionar uma relação que já existe com objeto diferente,
    a relação anterior é marcada como histórica (não removida).
    """
    # Se links_extras não for fornecido, inicializa
    if links_extras is None:
        links_extras = []

    # Recusa de segredos antes de qualquer escrita
    recusa = _recusar_texto_sensivel(fato)
    if recusa:
        log_info("cerebro", f"fato sensível recusado: {recusa}")
        return
    
    # Converte título para canônico (resolve typos)
    titulo = _resolver(titulo)
    
    # Nova lógica: processa com detecção de contradição
    _processar_fato_com_detec_contradicao(titulo, tipo, fato, links_extras,
                                          confianca=confianca, fonte=fonte)
    return


# ── inferência de entidade e fato ────────────────────────────────────────────


def _garantir_nota_usuario():
    """Garante que a nota raiz do usuário existe no vault."""
    nome = _nome_usuario()
    titulo = _titulo_entidade(nome)
    existente = vault.resolver_entidade(titulo, nome_usuario=titulo)
    if existente:
        return existente
    if not _ler_entidade(titulo):
        corpo = f"## Sobre {titulo}\n\n- Esta é a nota raiz do usuário no cérebro do Sumé.\n"
        _salvar_entidade(titulo, corpo, "pessoa", [])
        log_info("cerebro", f"nota raiz criada: {titulo}")
    return titulo


# ── inferência de entidade e fato ────────────────────────────────────────────

_PADROES_PESSOA = [
    # "aniversário da Malu é 12/10"
    r"anivers[aá]rio d[ao] (\w+)",
    # "namorada se chama Malu"
    r"(?:namorada|namorado|amigo|amiga|m[aã]e|pai|irm[aã]o|irm[aã]) (?:se chama|chama|[eé]) (\w+)",
    # "sobre a Malu"
    r"sobre (?:a |o )?(\w+)",
    # "da Malu" / "do João"
    r"d[ao] (\w+)",
    # "de Malu"
    r"de (\w+)",
]

_PADROES_FATO = [
    # "aniversário é/foi 12/10/2004" ou "12 de outubro"
    (r"anivers[aá]rio\s+[eéf][oi]{1,2}\s+(.+)",       "aniversário"),
    (r"anivers[aá]rio\s+[eé]\s+(.+)",                  "aniversário"),
    # "aniversário da Malu é 12 de outubro" (possessivo)
    (r"anivers[aá]rio\s+d[ao]\s+[\wà-ú]+\s+[eé]\s+(.+)", "aniversário"),
    (r"nasceu\s+(?:em\s+)?(.+)",                        "data de nascimento"),
    (r"data\s+de\s+nascimento\s+[eé]\s+(.+)",          "data de nascimento"),
    # relações
    (r"[eé]\s+minha\s+namorada",                        "namorada de [[{usuario}]]"),
    (r"[eé]\s+meu\s+namorado",                          "namorado de [[{usuario}]]"),
    (r"[eé]\s+meu\s+amigo",                             "amigo de [[{usuario}]]"),
    (r"[eé]\s+minha\s+amiga",                           "amiga de [[{usuario}]]"),
    (r"[eé]\s+minha\s+m[aã]e",                          "mãe de [[{usuario}]]"),
    (r"[eé]\s+meu\s+pai",                               "pai de [[{usuario}]]"),
    (r"[eé]\s+meu\s+irm[aã]o",                         "irmão de [[{usuario}]]"),
    (r"[eé]\s+minha\s+irm[aã]",                        "irmã de [[{usuario}]]"),
]

_RELACOES_USUARIO = [
    (r"minha\s+namorada\s+[eé]\s+(\w+)",   "namorada", "namorada de [[{usuario}]]"),
    (r"meu\s+namorado\s+[eé]\s+(\w+)",     "namorado", "namorado de [[{usuario}]]"),
    (r"meu\s+amigo\s+[eé]\s+(\w+)",        "pessoa",   "amigo de [[{usuario}]]"),
    (r"minha\s+amiga\s+[eé]\s+(\w+)",      "pessoa",   "amiga de [[{usuario}]]"),
    (r"minha\s+m[aã]e\s+[eé]\s+(\w+)",    "pessoa",   "mãe de [[{usuario}]]"),
    (r"meu\s+pai\s+[eé]\s+(\w+)",          "pessoa",   "pai de [[{usuario}]]"),
    (r"meu\s+irm[aã]o\s+[eé]\s+(\w+)",    "pessoa",   "irmão de [[{usuario}]]"),
    (r"minha\s+irm[aã]\s+[eé]\s+(\w+)",   "pessoa",   "irmã de [[{usuario}]]"),
]


def _inferir_entidade(comando: str) -> tuple[str, str] | None:
    """Retorna (titulo_entidade, tipo) ou None."""
    c = comando.lower()

    # Relações diretas: "minha namorada é Malu"
    for padrao, tipo, _ in _RELACOES_USUARIO:
        m = re.search(padrao, c)
        if m:
            return (_titulo_entidade(m.group(1)), tipo)

    # Padrões genéricos de nome
    for padrao in _PADROES_PESSOA:
        m = re.search(padrao, c)
        if m:
            nome = m.group(1)
            if len(nome) > 2 and nome not in ("que", "ela", "ele", "minha", "meu"):
                return (_titulo_entidade(nome), "pessoa")

    return None


def _inferir_fato(comando: str, entidade: str) -> str | None:
    """Retorna um bullet de fato para a entidade, ou None."""
    c = comando.lower()
    usuario = _titulo_entidade(_nome_usuario())

    for padrao, rotulo in _PADROES_FATO:
        rotulo_final = rotulo.replace("{usuario}", usuario)
        # fatos com valor extraído
        if "{usuario}" not in rotulo:
            m = re.search(padrao, c)
            if m:
                valor = m.group(1).strip(" .!?,")
                return f"{rotulo}: {valor}"
        else:
            # fatos de relação (sem grupo a extrair)
            if re.search(padrao, c):
                return rotulo_final

    # Relações do usuário com a entidade ("minha namorada é X")
    for padrao, _, fato_tpl in _RELACOES_USUARIO:
        m = re.search(padrao, c)
        if m and _titulo_entidade(m.group(1)) == entidade:
            return fato_tpl.replace("{usuario}", usuario)
    
    # Fato livre: retorna o comando como bullet
    return comando


# ── API pública ───────────────────────────────────────────────────────────────

def _salvar_via_regex(comando: str, usuario_titulo: str) -> str | None:
    """
    Fallback: usa padrões regex para extrair entidade e fato do comando.
    Salva o fato na nota da entidade e um link bidirecional na nota do usuário.
    Retorna o título da entidade salva, ou None se não conseguiu inferir.
    """
    res = _inferir_entidade(comando)
    if not res:
        return None
    titulo, tipo = res
    fato = _inferir_fato(comando, titulo)
    if not fato:
        return None
    _adicionar_fato(titulo, tipo, fato, links_extras=[usuario_titulo])
    _adicionar_fato(usuario_titulo, "pessoa", f"[[{titulo}]]", links_extras=[titulo])
    return titulo


def salvar_fato(comando: str) -> str:
    """
    Interpreta o comando via IA ou regex, salva os fatos no vault e
    retorna mensagem de confirmação humana.
    """
    # Guarda de segurança: nada sensível entra no cérebro (texto plano no Obsidian)
    recusa = _recusar_texto_sensivel(comando)
    if recusa:
        log_info("cerebro", f"comando sensível recusado: {recusa}")
        return recusa

    m_nome = re.search(r"(?:meu nome|me chamo)\s+[eé]\s+(.+)", comando, re.IGNORECASE)
    if m_nome:
        nome = m_nome.group(1).strip(" .!?,")
        from modulos.memoria import guardar_nome
        guardar_nome(nome)
        usuario_titulo = _garantir_nota_usuario()
        _adicionar_fato(usuario_titulo, "pessoa", f"nome: {nome}")
        return f"Prazer, {nome}! Vou me lembrar disso."

    usuario_titulo = _garantir_nota_usuario()
    user_canon = vault.resolver_entidade(usuario_titulo, nome_usuario=usuario_titulo) or usuario_titulo
    user_variants = {"usuário", "usuario", "eu", "eu mesmo", "minha pessoa"}

    from modulos.ia_extracao import extrair_grafo
    grafo = extrair_grafo(comando)

    if not grafo or not grafo.get("fatos"):
        entidade = _salvar_via_regex(comando, usuario_titulo)
        if entidade:
            return f"Anotei sobre {entidade}."
        return "Não consegui entender exatamente o que você quer que eu guarde."

    entity_info = {}
    for ent in grafo.get("entidades", []):
        nome = ent["nome"]
        tipo = ent.get("tipo", "coisa")
        aliases = ent.get("aliases", [])
        canon = vault.resolver_entidade(nome, nome_usuario=usuario_titulo) or nome
        entity_info[nome] = (canon, tipo, aliases)

    nome_usuario_norm = normalizar_nome(usuario_titulo)

    def _e_usuario(nome_raw: str, canon: str) -> bool:
        if e_pronome_usuario(nome_raw) or nome_raw.lower() in user_variants:
            return True
        if normalizar_nome(nome_raw) == nome_usuario_norm:
            return True
        if normalizar_nome(canon) == nome_usuario_norm:
            return True
        resolvido = vault.resolver_entidade(nome_raw, nome_usuario=usuario_titulo)
        if resolvido and normalizar_nome(resolvido) == nome_usuario_norm:
            return True
        return False

    for fato in grafo["fatos"]:
        suj_raw = fato["sujeito"]
        obj_raw = fato["objeto"]
        pred = fato["predicado"]
        conf = fato.get("confianca", 0.7) if isinstance(fato.get("confianca", 0.7), (int, float)) else 0.7

        # Recusa de segredos por fato (não grava credencial no grafo)
        if detectar_segredo(f"{pred}: {obj_raw}"):
            continue

        suj_canon, suj_tipo, _ = entity_info.get(suj_raw, (suj_raw, "coisa", []))
        if obj_raw in entity_info:
            obj_canon, obj_tipo, _ = entity_info[obj_raw]
            obj_is_entity = True
        else:
            obj_canon = obj_raw
            obj_tipo = "coisa"
            obj_is_entity = False

        if _e_usuario(suj_raw, suj_canon):
            suj_canon = user_canon
            suj_tipo = "pessoa"
        if _e_usuario(obj_raw, obj_canon):
            obj_canon = user_canon

        if obj_is_entity:
            texto_fato_suj = f"{pred}: [[{obj_canon}]]"
            texto_fato_obj = f"{pred} de [[{suj_canon}]]"
            _adicionar_fato(suj_canon, suj_tipo, texto_fato_suj, links_extras=[obj_canon], confianca=conf)
            _adicionar_fato(obj_canon, obj_tipo, texto_fato_obj, links_extras=[suj_canon], confianca=conf)
        else:
            texto_fato = f"{pred}: {obj_canon}"
            _adicionar_fato(suj_canon, suj_tipo, texto_fato, links_extras=[], confianca=conf)

    for nome, (canon, tipo, aliases) in entity_info.items():
        if vault.ler(canon) is None:
            vault.salvar(canon, "", tags=[tipo], links=[])
        for alias in aliases:
            vault.adicionar_alias(canon, alias)

    from modulos.ia_conversacional import conversar
    resumo_dict = str(grafo)
    prompt = f"Eu acabei de salvar silenciosamente no MEU banco de dados estes fatos: {resumo_dict} baseados nisto que o usuário disse: '{comando}'. Escreva UMA FRASE muito curta e humana dizendo: 'anotado, nome_do_usuario! guardei que X e Y'. IMPORTANTE: NUNCA mostre os parênteses, chaves ou formato de código."
    return conversar(prompt)


def ler_fatos(entidade: str) -> str:
    """Lê os fatos de uma entidade do vault e passa pelo LLM para voz natural."""
    bruto = entidade.replace("?", "").strip()
    if e_pronome_usuario(bruto):
        titulo = _garantir_nota_usuario()
    else:
        titulo = _resolver(_titulo_entidade(bruto))
    corpo = _ler_entidade(titulo)
    if not corpo:
        return f"Não tenho nada anotado sobre {entidade} no meu cérebro."
        
    # Pega o texto Markdown cru e usa IA para apresentar de forma humana
    from modulos.ia_conversacional import conversar
    prompt = f"Baseado ÚNICA E EXCLUSIVAMENTE nas anotações a seguir sobre {titulo}, me responda (em linguagem natural, muito curto, no máximo 2 frases) a pergunta ou resumo sobre a pessoa. Anotações:\n\n{corpo}"
    
    resposta_ia = conversar(prompt)
    if "Desculpe," in resposta_ia and "comunicação" in resposta_ia:
        # fallback caso a IA falhe
        return f"Sobre {titulo}:\n{corpo}"
        
    return resposta_ia


def salvar_fato_sobre(titulo: str, fato: str, tags: list[str] | None = None) -> None:
    """
    Adiciona um bullet de fato livre na nota da entidade (cria a nota se necessário).
    Fatos livres NÃO desencadeiam detecção de contradição, mas criam uma nota se necessário.
    """
    usuario_titulo = _nome_usuario()
    
    # Recusa de segredos: nunca grava credencial como bullet de nota
    recusa = _recusar_texto_sensivel(fato)
    if recusa:
        log_info("cerebro", f"fato livre sensível recusado: {recusa}")
        return

    # Nova lógica: apenas obtém (cria se necessário) e adiciona o fato ao corpo
    caminho = vault.obter_ou_criar_nota(titulo, corpo_inicial=f"- {fato}", tags=tags, nome_usuario=usuario_titulo)
    
    # Adiciona link bidirecional na nota do usuário se o fato não for sobre o próprio usuário
    # `ler` devolve None quando a nota ainda não existe, então o `or ""` é obrigatório aqui.
    if not e_pronome_usuario(titulo):
        nota_usuario = vault.ler(_nome_usuario()) or ""
        if f"[[{titulo}]]" not in nota_usuario:
            novo_corpo_usuario = (nota_usuario + f"\n- [[{titulo}]]").strip() if nota_usuario else f"- [[{titulo}]]"
            vault.salvar(_nome_usuario(), novo_corpo_usuario)
