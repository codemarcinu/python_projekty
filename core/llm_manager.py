"""
Moduł zarządzający komunikacją z lokalnym modelem językowym.

Ten moduł odpowiada za wysyłanie zapytań do lokalnego modelu LLM
za pomocą biblioteki ollama i odbieranie odpowiedzi.
"""

from typing import List, Dict, Any, Sequence, cast
import ollama
from .config_manager import settings


class LLMManager:
    """Klasa zarządzająca interakcją z lokalnym modelem LLM poprzez Ollama."""

    def __init__(self) -> None:
        """Inicjalizuje menedżera LLM."""
        self.model = settings.LLM_MODEL

    def generate_response(self, history: List[Dict[str, str]]) -> str:
        """Generuje odpowiedź na podstawie historii konwersacji.
        
        Args:
            history (List[Dict[str, str]]): Lista słowników zawierających historię konwersacji,
                gdzie każdy słownik ma klucze 'role' i 'content'
        
        Returns:
            str: Wygenerowana odpowiedź modelu
        """
        try:
            # Konwertujemy historię do formatu akceptowanego przez ollama
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
            # type: ignore - ollama ma własne typy, które nie są w pełni kompatybilne z typami Pythona
            response = ollama.chat(
                model=self.model,
                messages=messages  # type: ignore
            )
            return cast(Dict[str, Any], response)['message']['content']
        except Exception as e:
            return f"Wystąpił błąd podczas generowania odpowiedzi: {str(e)}"
