from typing import List, Dict, Any


class ConversationHandler:
    """Klasa odpowiedzialna za zarządzanie historią konwersacji z asystentem AI.
    
    Klasa przechowuje historię wiadomości w formacie zgodnym z wymaganiami modeli LLM,
    gdzie każda wiadomość zawiera rolę nadawcy ('user' lub 'assistant') oraz treść.
    """

    def __init__(self) -> None:
        """Inicjalizuje nową instancję ConversationHandler.
        
        Tworzy pustą listę do przechowywania historii konwersacji.
        """
        self._history: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        """Dodaje nową wiadomość do historii konwersacji.
        
        Args:
            role (str): Rola nadawcy wiadomości ('user' lub 'assistant')
            content (str): Treść wiadomości
        """
        message = {
            'role': role,
            'content': content
        }
        self._history.append(message)

    def get_history(self) -> List[Dict[str, str]]:
        """Zwraca całą historię konwersacji.
        
        Returns:
            List[Dict[str, str]]: Lista słowników zawierających historię wiadomości,
            gdzie każdy słownik ma klucze 'role' i 'content'
        """
        return self._history

    def clear_history(self) -> None:
        """Czyści całą historię konwersacji, resetując ją do stanu początkowego."""
        self._history = []
