import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 180)

def falar(texto: str):
    print("Nexus:", texto)
    engine.say(texto)
    engine.runAndWait()