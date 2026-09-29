# Auto-register intents for file opening
from .file_intent import detectar as detectar_file_intent

# Make available for import
__all__ = ["detectar_file_intent"]