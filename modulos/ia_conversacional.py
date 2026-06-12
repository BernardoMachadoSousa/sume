import json
import os
import requests

def carregar_chave() -> str:
    caminho = os.path.join(os.path.dirname(__file__), "..", "dados", "configuracoes.json")
    with open(caminho, "r") as f:
        config = json.load(f)
    return config.get("gemini_api_key", "")

def perguntar_ia(mensagem: str, contexto: str = "") -> str:
    chave = carregar_chave()

    if not chave or chave == "COLE_SUA_CHAVE_AQUI":
        return "A chave do Gemini não foi configurada."

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={chave}"

        system_msg = "Você é o Nexus, um assistente pessoal inteligente e amigável. Responda em português, de forma direta. Máximo 3 frases."
        if contexto:
            system_msg += f"\n\nInformações do usuário:\n{contexto}"

        prompt = f"{system_msg}\n\nUsuário: {mensagem}\nNexus:"

        response = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        })

        dados = response.json()

        # Tenta extrair a resposta em qualquer formato
        if "candidates" in dados and len(dados["candidates"]) > 0:
            partes = dados["candidates"][0].get("content", {}).get("parts", [])
            if partes:
                return partes[0].get("text", "Sem resposta.").strip()

        # Se chegou aqui, mostra o erro cru
        return f"Erro na API: {json.dumps(dados, indent=2, ensure_ascii=False)}"

    except Exception as e:
        return f"Erro na IA: {str(e)}"