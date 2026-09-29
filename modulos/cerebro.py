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

from modulos import vault
from modulos.memoria import lembrar, guardar, PERMANENTE
from utils.logger import erro as log_erro, info as log_info
from utils.nome_utils import normalizar_nome


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
    from utils.nome_utils import normalizar_nome
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


def _adicionar_fato(titulo: str, tipo: str, fato: str, links_extras: list[str] | None = None) -> None:
    """
    Adiciona um bullet de fato na nota da entidade, criando-a se não existir.
    Garante que os links_extras aparecem no frontmatter da nota.
    """
    corpo_atual = vault.ler(titulo) or ""
    novo_bullet = f"- {fato}"
    if novo_bullet in corpo_atual:
        return
    if corpo_atual:
        novo_corpo = corpo_atual + "\n" + novo_bullet
    else:
        novo_corpo = novo_bullet
    todos_links = list(_extrair_links_existentes(novo_corpo))
    for lk in (links_extras or []):
        if lk not in todos_links:
            todos_links.append(lk)
    tags = ["cerebro", tipo]
    vault.salvar(titulo, novo_corpo, tags=tags, links=todos_links)


def _garantir_nota_usuario():
    """Garante que a nota raiz do usuário existe no vault."""
    nome = _nome_usuario()
    titulo = _titulo_entidade(nome)
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

    return None


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
    usuario_titulo = _garantir_nota_usuario()
    user_canon = vault.resolver_entidade(usuario_titulo) or usuario_titulo
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
        canon = vault.resolver_entidade(nome) or nome
        entity_info[nome] = (canon, tipo, aliases)

    nome_usuario_norm = normalizar_nome(usuario_titulo)

    def _e_usuario(nome_raw: str, canon: str) -> bool:
        if nome_raw.lower() in user_variants:
            return True
        if normalizar_nome(nome_raw) == nome_usuario_norm:
            return True
        if normalizar_nome(canon) == nome_usuario_norm:
            return True
        if nome_usuario_norm and normalizar_nome(nome_raw).startswith(nome_usuario_norm):
            return True
        return False

    for fato in grafo["fatos"]:
        suj_raw = fato["sujeito"]
        obj_raw = fato["objeto"]
        pred = fato["predicado"]

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
            _adicionar_fato(suj_canon, suj_tipo, texto_fato_suj, links_extras=[obj_canon])
            _adicionar_fato(obj_canon, obj_tipo, texto_fato_obj, links_extras=[suj_canon])
        else:
            texto_fato = f"{pred}: {obj_canon}"
            _adicionar_fato(suj_canon, suj_tipo, texto_fato, links_extras=[])

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
    titulo = _titulo_entidade(entidade.replace("?", "").strip())
    
    # Suporte a "eu"
    if titulo.lower() in ("eu", "me", "mim"):
        titulo = _titulo_entidade(_nome_usuario())
        
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


def salvar_fato_sobre(entidade: str, fato: str) -> str:
    """Salva um fato livre sobre uma entidade (chamada direta)."""
    usuario_titulo = _garantir_nota_usuario()
    titulo = _titulo_entidade(entidade)
    tipo = "pessoa"
    _adicionar_fato(titulo, tipo, fato, links_extras=[usuario_titulo])
    log_info("cerebro", f"fato livre salvo em [{titulo}]: {fato}")
    return f"Anotei em [[{titulo}]]: {fato}"
