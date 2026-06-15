import pyttsx3

engine = None

def _get_engine():
    global engine
    try:
        if engine is None:
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
        return engine
    except:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        return engine

def falar(texto: str):
    print("Nexus:", texto)
    eng = _get_engine()
    try:
        eng.say(texto)
        eng.runAndWait()
    except RuntimeError:
        # Se o loop já está rodando, recria a engine
        global engine
        try:
            engine.endLoop()
        except:
            pass
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.say(texto)
        engine.runAndWait()