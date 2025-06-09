"""
Moduł zarządzający komunikacją z lokalnym modelem językowym.

Ten moduł odpowiada za wysyłanie zapytań do lokalnego modelu LLM
za pomocą biblioteki ollama i odbieranie odpowiedzi.
"""

from typing import List, Dict, Any
import ollama
from .config_manager import Settings, get_settings


class LLMManager:
    """Klasa zarządzająca interakcją z lokalnym modelem LLM poprzez Ollama."""

    def __init__(self) -> None:
        """Inicjalizuje menedżera LLM."""
        self.settings = get_settings()
        self.model = self.settings.LLM_MODEL

    def generate_response(self, history: List[Dict[str, str]]) -> str:
        """Generuje odpowiedź na podstawie historii konwersacji.
        
        Args:
            history (List[Dict[str, str]]): Lista słowników zawierających historię konwersacji,
                gdzie każdy słownik ma klucze 'role' i 'content'
        
        Returns:
            str: Wygenerowana odpowiedź modelu
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=history
            )
            return response['message']['content']
        except Exception as e:
            return f"Wystąpił błąd podczas generowania odpowiedzi: {str(e)}"
