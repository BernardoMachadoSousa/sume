"""
Módulo de extração semântica via LLM.

Recebe um comando/conversa do usuário e extrai:
- Entidades (nomes de pessoas, lugares, conceitos)
- Relações semânticas entre essas entidades (tipos controlados em utils/tipos_relacao.py)
- Fatos com sujeito, predicado e objeto
- Níveis de confiança

Saída formatada como JSON estruturado, pronto para ser processado por
cerebro.salvar_fato() e armazenado no vault.
"""

import json
import re
import logging
from typing import Any, Dict, List, Optional

from utils.logger import info as log_info, erro as log_erro
from utils.nome_utils import normalizar_nome

log = logging.getLogger(__name__)


# ── Prompt estruturado para LLM ──────────────────────────────────────────────

_PROMPT_EXTRACTION = """
Você é o motor de memória do Sumé. Sua tarefa é analisar o que o usuário disse
e extrair apenas informações relevantes para um grafo de conhecimento pessoal.

Use o formato JSON abaixo e retorne APENAS o JSON (nenhum texto antes ou depois).

Objetivo: Extrair entidades, relações e fatos para construção de um grafo de conhecimento.
Não inclua informações irrelevantes, opiniões, brincadeiras ou perguntas.

ESTRUTURA DE ENTRADA:
- Usuário disse: "{comando}"

ESTRUTURA DE SAÍDA (JSON):
{{
  "entidades": [
    {{
      "nome": "Nome da pessoa/conceito",
      "tipo": "tipo_entidade",
      "aliases": ["alias1", "alias2"]
    }}
  ],
  "fatos": [
    {{
      "sujeito": "Nome da entidade que pratica/possui/sujeito da frase",
      "predicado": "Tipo de relação (usar vocabulário controlado: possui, mora_em, estuda, desenvolve, conhece, gosta_de, e_pai_de, e_mae_de, contradiza, corrige, etc.)",
      "objeto": "Nome da entidade ou valor (pode ser string, número, data)",
      "confianca": 0.0 a 1.0
    }}
  ],
  "atualizacoes": [
    {{
      "tipo": "substituir|adicionar_historico|ignorar",
      "entidade": "Nome da entidade afetada",
      "fato_antigo": "Descrição do fato antigo",
      "fato_novo": "Descrição do fato novo",
      "confianca": 0.0 a 1.0
    }}
  ]
}}

REGRAS CRÍTICAS:
1. Tipos de relação permitidos (vocabulário controlado): possui, pertence_a, mora_em, trabalha_em, estuda, ensina, conhece, gosta_de, desenvolve, cria, e_pai_de, e_mae_de, e_irmao_de, e_irma_de, e_filho_de, e_filha_de, namora, e_marido_de, e_esposa_de, e_noiva_de, igual_a, similar_a, contradiz, corrige, suffixora_a, aconteceu_em, começou_em, termina_em, substitui, depende_de, tem_idade, tem_genero, tem_cor, tem_tamanho, ensina_conceito, aprendeu_de, referencia, contrata, emprega, patrocina, estabelecido_em, localizado_em, origina_de, pertence_a_categoria, tipo_de, influencia, inspirado_por, contem, baseado_em, deriva_de.

2. Se o usuário mencionar uma correção (ex: "mudei para Feira de Santana"), inclua na chave "atualizacoes" com tipo "substituir" ou "adicionar_historico".

3. Se o usuário disser algo irrelevante (tempo, piada, pergunta sem resposta factual), retorne {"entidades": [], "fatos": [], "atualizacoes": []}.

4. Se o usuário usar pronomes (eu, nosso, etc.), resolva para a nota do usuário antes de registrar.

5. confianca deve ser baseado em: Fonte direta (usuário falou) = 0.9, Inferido = 0.5, Contexto existente = 0.7.

6. Retorne sempre JSON válido. Se não conseguir extrair nada significativo, retorne:
   {{"entidades": [], "fatos": [], "atualizacoes": []}}


COMANDOS EXEMPLO:

Entrada: "Meu nome é Bernardo e eu moro em Salvador."
Saída:
{{
  "entidades": [
    {{"nome": "Bernardo", "tipo": "pessoa", "aliases": []}},
    {{"nome": "Salvador", "tipo": "cidade", "aliases": []}}
  ],
  "fatos": [
    {{"sujeito": "Bernardo", "predicado": "mora_em", "objeto": "Salvador", "confianca": 0.9}}
  ],
  "atualizacoes": []
}}

Entrada: "Ana Maria Luísa estuda Biomedicina na UFMG."
Saída:
{{
  "entidades": [
    {{"nome": "Ana Maria Luísa", "tipo": "pessoa", "aliases": []}},
    {{"nome": "Biomedicina", "tipo": "curso", "aliases": []}},
    {{"nome": "UFMG", "tipo": "universidade", "aliases": []}}
  ],
  "fatos": [
    {{"sujeito": "Ana Maria Luísa", "predicado": "estuda", "objeto": "Biomedicina", "confianca": 0.95}},
    {{"sujeito": "Ana Maria Luísa", "predicado": "estuda", "objeto": "UFMG", "confianca": 0.9}}
  ],
  "atualizacoes": []
}}

Agora processe o comando do usuário abaixo e retorne APENAS JSON:
"""


def _resolver_para_usuario(nome: str, nome_usuario_canonico: str) -> str:
    """Se o nome for o usuário ou pronome, retorna o título canônico do usuário."""
    from modulos.vault import resolver_entidade
    from utils.nome_utils import e_pronome_usuario, normalizar_nome
    
    user_norm = normalizar_nome(nome_usuario_canonico)
    nome_norm = normalizar_nome(nome)
    
    if e_pronome_usuario(nome) or nome_norm == user_norm:
        resolvido = resolver_entidade(nome_usuario_canonico, nome_usuario=nome_usuario_canonico)
        if resolvido:
            return resolvido
    return None


def _normalizar_tipo_relacao(tipo: str) -> str:
    """Normaliza o tipo de relação para o vocabulário controlado."""
    tipos_validos = [
        "possui", "pertence_a", "mora_em", "trabalha_em", "estuda", "ensina", 
        "conhece", "gosta_de", "desenvolve", "cria", "e_pai_de", "e_mae_de", 
        "e_irmao_de", "e_irma_de", "e_filho_de", "e_filha_de", "namora", 
        "e_marido_de", "e_esposa_de", "e_noiva_de", "igual_a", "similar_a", 
        "contradiz", "corrige", "sucessora_a", "aconteceu_em", "começou_em", 
        "termina_em", "substitui", "depende_de", "tem_idade", "tem_genero", 
        "tem_cor", "tem_tamanho", "ensina_conceito", "aprendeu_de", "referencia", 
        "contrata", "emprega", "patrocina", "estabelecido_em", "localizado_em", 
        "origina_de", "pertence_a_categoria", "tipo_de", "influencia", 
        "inspirado_por", "contem", "baseado_em", "deriva_de"
    ]
    
    # Se já for válido, retorna como está (já deve estar normalizado)
    if tipo.strip() in tipos_validos:
        return tipo.strip()
    
    # Tentar normalizar (ex: "Mora Em" -> "mora_em")
    tipo_lower = tipo.strip().lower()
    # Remove acentos para comparar
    import unicodedata
    tipo_sem_acentos = unicodedata.normalize("NFKD", tipo_lower).encode("ascii", "ignore").decode("ascii")
    
    # Verificar se algum tipo começado sem acentos
    for t in tipos_validos:
        if t.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u") == tipo_sem_acentos:
            return t
    
    return tipo.strip()


def _mapear_tipo_entidade(nome: str, contexto: str = "") -> str:
    """Tenta inferir o tipo de entidade baseado no nome e contexto."""
    nome_lower = nome.lower()
    
    # Padrões simples
    if any(palavra in nome_lower for palavra in ["salvador", "rio", "cidade", "bahia", "sp", " RJ"]):
        return "cidade"
    if any(palavra in nome_lower for palavra in ["ufmg", "usp", "university", "college", "escola"]):
        return "instituição"
    if any(palavra in nome_lower for palavra in ["direito", "medicina", "engenharia", "direito constitucional"]):
        return "conceito"
    if any(palavra in nome_lower for palavra in ["ana", "maria", "bernardo", "joão", "maria"]):
        # Isso é heurístico; na prática o LLM decide o tipo
        return "pessoa"
    
    return "coisa"


def extrair_grafo(comando: str) -> Optional[Dict[str, Any]]:
    """
    Extrai grafo de conhecimento do comando do usuário usando LLM.
    
    Args:
        comando: A frase ou conversa do usuário
        
    Returns:
        Dict com "entidades", "fatos" e "atualizacoes", ou None se falhar.
    """
    try:
        from modulos.ia_conversacional import conversar
        
        prompt = _PROMPT_EXTRACTION.format(comando=comando)
        
        resposta = conversar(prompt)
        
        # Tentar extrair JSON da resposta
        # O conversar pode retornar texto com formatação, então tentamos encontrar o JSON
        
        # Procurar bloco de código JSON ``` ```json ... ```
        json_match = re.search(r"```json\s*(\{.*\})\s*```", resposta, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Procurar { ... } direto
            json_match = re.search(r"\{(?:[^{}]|(?R))*\}", resposta, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Tentar encontrar o JSON entre as chaves mais externas
                start = resposta.find("{")
                end = resposta.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = resposta[start:end]
                else:
                    log_erro("ia_extracao", f"Não foi possível extrair JSON da resposta: {resposta[:200]}")
                    return None
        
        grafo = json.loads(json_str)
        
        # Validar e normalizar estrutura
        if not isinstance(grafo, dict):
            log_erro("ia_extracao", f"JSON extraído não é dict: {type(grafo)}")
            return None
        
        # Normalizar entidades
        entidades = grafo.get("entidades", [])
        for ent in entidades:
            if "nome" in ent:
                ent["nome"] = ent["nome"].strip()
            if "tipo" not in ent or not ent["tipo"]:
                ent["tipo"] = _mapear_tipo_entidade(ent.get("nome", ""))
            if "aliases" not in ent:
                ent["aliases"] = []
            # Normalizar aliases
            ent["aliases"] = [a.strip() for a in ent.get("aliases", []) if a.strip()]
        
        # Normalizar fatos
        fatos = grafo.get("fatos", [])
        for fato in fatos:
            if "sujeito" in fato:
                fato["sujeito"] = fato["sujeito"].strip()
            if "predicado" in fato:
                fato["predicado"] = _normalizar_tipo_relacao(fato["predicado"])
            if "objeto" in fato:
                fato["objeto"] = fato["objeto"].strip()
            # Garantir confiança
            if "confianca" not in fato or not isinstance(fato.get("confianca"), (int, float)):
                # Baseado no tipo: se envolve usuário direto, 0.9; se inferido, 0.5
                fato["confianca"] = 0.7  # default
        
        # Normalizar atualizações
        atualizacoes = grafo.get("atualizacoes", [])
        for upd in atualizacoes:
            if "tipo" not in upd:
                upd["tipo"] = "ignorar"
            if "entidade" in upd:
                upd["entidade"] = upd["entidade"].strip()
            if "fato_antigo" in upd:
                upd["fato_antigo"] = upd["fato_antigo"].strip()
            if "fato_novo" in upd:
                upd["fato_novo"] = upd["fato_novo"].strip()
        
        grafo["entidades"] = entidades
        grafo["fatos"] = fatos
        grafo["atualizacoes"] = atualizacoes
        
        # Log resumido
        n_ent = len(entidades)
        n_fat = len(fatos)
        n_upd = len(atualizacoes)
        log_info("ia_extracao", f"Extração concluída: {n_ent} entidades, {n_fat} fatos, {n_upd} atualizações")
        
        return grafo
        
    except json.JSONDecodeError as e:
        log_erro("ia_extracao", f"Erro ao decodificar JSON: {e}. Resposta: {resposta[:300]}")
        return None
    except Exception as e:
        log_erro("ia_extracao", f"Erro inesperado em extrair_grafo: {e}")
        return None