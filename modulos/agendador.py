"""
Agendador de rotinas para o Sumé.
Permite agendar tarefas para serem executadas em horários específicos (ex.: rotinas matinal e noturna).
"""

import os
import sys
import logging
from datetime import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Garantir que a raiz do projeto está no path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Importar módulos necessários para as rotinas
from modulos import memoria, diario
from utils.logger import info as log_info, erro as log_erro

# Importar função de clima do plugin
try:
    from plugins.clima.handlers import buscar_clima
except ImportError:
    # Fallback se não conseguir importar
    def buscar_clima(local=""):
        return "Serviço de clima indisponível."

# Configuração do logger
logger = logging.getLogger(__name__)

# Horários padrão (can ser sobrescritos por variáveis de ambiente)
MATINAL_HOUR = int(os.getenv('SUME_MATINAL_HOUR', 7))
MATINAL_MINUTE = int(os.getenv('SUME_MATINAL_MINUTE', 30))
NOTURNA_HOUR = int(os.getenv('SUME_NOTURNA_HOUR', 21))
NOTURNA_MINUTE = int(os.getenv('SUME_NOTURNA_MINUTE', 30))

scheduler = BackgroundScheduler()


def rotina_matinal():
    """
    Rotina executada pela manhã.
    Cumprimenta o usuário, informa o clima e compromissos do dia.
    """
    try:
        log_info("agendador", "Iniciando rotina matinal")
        
        # Cumprimento
        saudacao = "Bom dia! Espero que tenha dormido bem."
        
        # Clima
        try:
            clima_info = buscar_clima("")  # Busca clima local baseado no IP
            if clima_info and "indisponível" not in clima_info.lower():
                saudacao += f" Hoje o clima está: {clima_info}."
            else:
                saudacao += " Não consegui obter informações do clima no momento."
        except Exception as e:
            log_erro("agendador", f"Erro ao obter clima na rotina matinal: {e}")
            saudacao += " Houve um problema ao verificar o clima."
        
        # Compromissos do dia (do vault ou memória)
        # Por enquanto, vamos apenas ler o diário de hoje para ver se há algo importante
        try:
            diario_hoje = diario.ler_diario_hoje()
            if diario_hoje and len(diario_hoje.strip()) > 50:  # Se tiver conteúdo significativo
                saudacao += " Vejo que já tem algumas anotações no seu diário de hoje."
        except Exception as e:
            log_erro("agendador", f"Erro ao ler diário na rotina matinal: {e}")
        
        # Falar a saudacao (usando o módulo de voz)
        from utils.voz import falar
        falar(saudacao)
        
        log_info("agendador", "Rotina matinal concluída")
    except Exception as e:
        log_erro("agendador", f"Erro inesperado na rotina matinal: {e}")


def rotina_noturna():
    """
    Rotina executada à noite.
    Faz um resumo do dia e prepara para o dia seguinte.
    """
    try:
        log_info("agendador", "Iniciando rotina noturna")
        
        # Resumo do dia
        resumo = "Boa noite! Hora de encerrar o dia."
        
        # Ler o diário de hoje para fazer um pequeno resumo
        try:
            diario_hoje = diario.ler_diario_hoje()
            if diario_hoje:
                # Pegamos as primeiras 200 caracteres comoPreview
                preview = diario_hoje[:200].replace('\n', ' ').strip()
                if preview:
                    resumo += f" Hoje você anotou: '{preview}...'"
                else:
                    resumo += " Seu diário de hoje está vazio. Que tal fazer uma rápida anotação antes de dormir?"
            else:
                resumo += " Não encontrei seu diário de hoje. Talvez queira criar uma nota rápida?"
        except Exception as e:
            log_erro("agendador", f"Erro ao ler diário na rotina noturna: {e}")
            resumo += " Não consegui ler seu diário de hoje."
        
        # Sugerir planejamento para amanhã
        resumo += " Lembre-se de verificar seus planos para amanhã."
        
        # Falar o resumo
        from utils.voz import falar
        falar(resumo)
        
        log_info("agendador", "Rotina noturna concluída")
    except Exception as e:
        log_erro("agendador", f"Erro inesperado na rotina noturna: {e}")


def iniciar_agendador():
    """
    Inicia o agendador de tarefas em background.
    """
    try:
        # Agendar rotina matinal
        trigger_matinal = CronTrigger(hour=MATINAL_HOUR, minute=MATINAL_MINUTE)
        scheduler.add_job(rotina_matinal, trigger_matinal, id='rotina_matinal', replace_existing=True)
        log_info("agendador", f"Rotina matinal agendada para {MATINAL_HOUR:02d}:{MATINAL_MINUTE:02d}")
        
        # Agendar rotina noturna
        trigger_noturna = CronTrigger(hour=NOTURNA_HOUR, minute=NOTURNA_MINUTE)
        scheduler.add_job(rotina_noturna, trigger_noturna, id='rotina_noturna', replace_existing=True)
        log_info("agendador", f"Rotina noturna agendada para {NOTURNA_HOUR:02d}:{NOTURNA_MINUTE:02d}")
        
        # Iniciar o scheduler
        scheduler.start()
        log_info("agendador", "Agendador iniciado com sucesso")
    except Exception as e:
        log_erro("agendador", f"Erro ao iniciar agendador: {e}")


def parar_agendador():
    """
    Para o agendador de tarefas.
    """
    try:
        scheduler.shutdown()
        log_info("agendador", "Agendador parado")
    except Exception as e:
        log_erro("agendador", f"Erro ao parar agendador: {e}")


# Se este módulo for executado diretamente, fazer um teste rápido
if __name__ == "__main__":
    # Configurar logging básico para teste
    logging.basicConfig(level=logging.INFO)
    
    print("Iniciando agendador em modo de teste...")
    iniciar_agendador()
    
    try:
        # Manter o script rodando por 1 minuto para ver se as tarefas são agendadas
        import time
        print("Agendador rodando. Pressione Ctrl+C para parar.")
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nParando agendador...")
        parar_agendador()
        print("Agendador parado.")