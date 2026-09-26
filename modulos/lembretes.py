"""
Módulo de lembretes do Sumé.
Salva, lista, cancela e verifica alarmes sem dependências externas.
"""
import re
import time
from datetime import datetime, timedelta
from modulos.memoria import guardar, carregar, esquecer, PERMANENTE
from utils.logger import erro as log_erro

_PREFIXO = "lembrete_"


def _chave(ts: float) -> str:
    return f"{_PREFIXO}{int(ts)}"


def _todos() -> list[dict]:
    itens = []
    for chave, valor in (carregar(PERMANENTE) or {}).items():
        if not chave.startswith(_PREFIXO):
            continue
        try:
            ts = float(chave[len(_PREFIXO):])
            itens.append({"chave": chave, "ts": ts, "texto": valor})
        except ValueError:
            pass
    return sorted(itens, key=lambda x: x["ts"])


def _parse_horario(comando: str) -> datetime | None:
    agora = datetime.now()
    c = comando.lower()

    m = re.search(r"daqui\s+(\d+)\s*min", c)
    if m:
        return agora + timedelta(minutes=int(m.group(1)))

    m = re.search(r"daqui\s+(\d+)\s*hora", c)
    if m:
        return agora + timedelta(hours=int(m.group(1)))

    m = re.search(r"(?:às|as)\s+(\d{1,2})(?::|\s*h\s*r?s?)?(\d{2})?", c)
    if m:
        hora = int(m.group(1))
        minuto = int(m.group(2)) if m.group(2) else 0
        alvo = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        if "amanhã" in c or "amanha" in c:
            alvo += timedelta(days=1)
        elif alvo <= agora:
            alvo += timedelta(days=1)
        return alvo

    return None


def _extrair_texto(comando: str) -> str:
    c = comando
    for marcador in ("lembre-me de ", "lembre me de ", "me lembra de ",
                     "me lembre de ", "lembrete de ", "lembrete: "):
        if marcador in c.lower():
            i = c.lower().find(marcador)
            c = c[i + len(marcador):]
            break

    c = re.sub(r"(daqui\s+\d+\s*(min\w*|hora\s*s?))", "", c, flags=re.I)
    c = re.sub(r"(amanhã?\s+)?(às|as)\s+\d{1,2}(?::|\s*h\s*r?s?)?\d{0,2}", "", c, flags=re.I)
    c = re.sub(r"\bamanhã?\b", "", c, flags=re.I)
    return c.strip(" .,:!?") or "lembrete"


def criar(comando: str) -> str:
    alvo = _parse_horario(comando)
    if not alvo:
        return "Não entendi o horário. Tente: 'daqui 30 minutos', 'às 15h', 'amanhã às 9h'."
    texto = _extrair_texto(comando)
    chave = _chave(alvo.timestamp())
    guardar(chave, texto, PERMANENTE)
    hora_fmt = alvo.strftime("%H:%M")
    if alvo.date() == datetime.now().date():
        return f"Anotado! Vou te lembrar de '{texto}' às {hora_fmt}."
    return f"Anotado! Vou te lembrar de '{texto}' amanhã às {hora_fmt}."


def listar() -> str:
    itens = _todos()
    agora = time.time()
    futuros = [i for i in itens if i["ts"] > agora]
    if not futuros:
        return "Nenhum lembrete pendente."
    linhas = []
    for i in futuros:
        dt = datetime.fromtimestamp(i["ts"])
        linhas.append(f"- {dt.strftime('%d/%m %H:%M')}: {i['texto']}")
    return "Lembretes pendentes:\n" + "\n".join(linhas)


def cancelar(trecho: str) -> str:
    itens = _todos()
    agora = time.time()
    futuros = [i for i in itens if i["ts"] > agora]
    alvo = trecho.lower().strip()
    for i in futuros:
        if alvo in i["texto"].lower():
            esquecer(i["chave"])
            return f"Lembrete cancelado: '{i['texto']}'."
    return f"Não encontrei lembrete com '{trecho}'."


def verificar_disparos() -> list[str]:
    """Devolve textos dos lembretes que venceram agora. Apaga do banco."""
    agora = time.time()
    disparados = []
    try:
        for i in _todos():
            if i["ts"] <= agora:
                disparados.append(i["texto"])
                esquecer(i["chave"])
    except Exception as e:
        log_erro("lembretes", str(e))
    return disparados
