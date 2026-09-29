"""
Módulo dedicado a extração de dados estruturados com LLMs.
Bate no Groq pedindo retorno em JSON puro.
"""

import os
import json
import requests
from utils.logger import erro as log_erro
from utils import config as cfg
from modulos.ia_conversacional import MODELO_NUVEM_PADRAO, URL_GROQ, _credencial_groq

def extrair_grafo(comando: str) -> dict:
    """
    Usa LLM para converter uma frase natural num schema JSON de entidades e fatos.
    O LLM infere entidades, tipos, relações e fatos soltos.
    
    Retorna sempre um dict no formato:
    {
      "entidades": [{"nome": "Malu", "tipo": "pessoa"}],
      "fatos": [{"sujeito": "Malu", "predicado": "namorada de", "objeto": "Bernardo"}]
    }
    Se falhar, retorna {"entidades": [], "fatos": []}.
    """
    chave = _credencial_groq()
    
    system_prompt = """
Você é um extrator de grafos de conhecimento de classe mundial. Você pega uma declaração em linguagem natural do usuário ("Bernardo") e a formata em um JSON estrito.
Tipos de entidade permitidos: pessoa, lugar, animal, coisa, organizacao. NÃO crie entidade do tipo 'data'; datas devem aparecer apenas como valores de fatos (ex: "nasceu em 12 de outubro de 2004").
Tipos de relações de família devem apontar para 'Bernardo'. Por exemplo "minha namorada é a Malu" = {"sujeito": "Malu", "predicado": "namorada de", "objeto": "Bernardo"}.

Cada entidade deve ter os campos:
- "nome": string (o nome canônico ou mais completo da entidade)
- "tipo": string (um dos tipos permitidos)
- "aliases" (opcional): lista de strings que são apelidos, variações ou pronomes que se referem à mesma entidade (ex: para "Bernardo Jonas", pode incluir ["Bernardo", "Eu"] se o contexto indicar).

RETORNE APENAS O JSON, NENHUM OUTRO TEXTO E NENHUMA EXPLICAÇÃO. O formato de saída obrigatório é exatamente este formato:
{
  "entidades": [{"nome": "string", "tipo": "string", "aliases": ["string", ...] }],
  "fatos": [{"sujeito": "string", "predicado": "string", "objeto": "string"}]
}
Seja generoso: mesmo apelidos, fatos triviais ou deduções lógicas do texto devem ser registrados.
Exemplo: "O nome da minha namorada é Maria Luiza, mas chamo ela de Malu e ela nasceu em 12/10/2004."
Retorna:
{
  "entidades": [
    {"nome": "Bernardo Jonas", "tipo": "pessoa", "aliases": ["Eu"]},
    {"nome": "Maria Luiza", "tipo": "pessoa", "aliases": ["Malu", "Maria"]}
  ],
  "fatos": [
    {"sujeito": "Maria Luiza", "predicado": "namorada de", "objeto": "Bernardo Jonas"},
    {"sujeito": "Bernardo Jonas", "predicado": "namorado de", "objeto": "Maria Luiza"},
    {"sujeito": "Maria Luiza", "predicado": "nasceu em", "objeto": "12 de outubro de 2004"}
  ]
}
"""

    if not chave:
        # Fallback local via Ollama (usando phi3:mini sem estrutura JSON garantida da API, fazemos o parse hard)
        import ollama
        try:
            r = ollama.chat(model="phi3:mini", messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"O usuário 'Bernardo' disse:\n{comando}"}
            ])
            texto_sujo = r["message"]["content"].strip()
            
            # Limpeza boba
            import re
            m = re.search(r"\{.*\}", texto_sujo, re.DOTALL)
            if m:
                texto_sujo = m.group(0)
            
            return json.loads(texto_sujo)
        except Exception as e:
            log_erro("ia_extracao", f"Erro no extrator (fallback ollama): {e}")
            return {"entidades": [], "fatos": []}

    try:
        r = requests.post(
            URL_GROQ,
            headers={
                "Authorization": f"Bearer {chave}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"O usuário 'Bernardo' disse:\n{comando}"}
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            },
            timeout=15
        )
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"].strip()
        
        # fallback caso modelo ignore response_format nalgum edge case
        if texto.startswith("```json"):
            texto = texto.split("```json")[-1].split("```")[0].strip()
            
        dados = json.loads(texto)
        return dados
    except Exception as e:
        log_erro("ia_extracao", f"Erro no extrator de grafo LLM: {e}")
        print(f"DEBUG ERRO EXTRACAO: {e}")  # Adicionei pro debug
        return {"entidades": [], "fatos": []}
