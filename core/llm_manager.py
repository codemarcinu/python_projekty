"""
Moduł zarządzający komunikacją z lokalnym modelem językowym.

Ten moduł odpowiada za wysyłanie zapytań do lokalnego modelu LLM
za pomocą biblioteki ollama i odbieranie odpowiedzi.
"""

from typing import List, Dict, Any, cast
import ollama
from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from .config_manager import settings
from core.exceptions import AIEngineError, ConfigError
from collections.abc import Iterator

class OllamaClient:
    """
    Klient do komunikacji z lokalnym serwerem Ollama.

    Konfiguracja modelu i adresu hosta pobierana jest z ustawień aplikacji.
    Weryfikuje połączenie z serwerem podczas inicjalizacji.
    """
    def __init__(self) -> None:
        """
        Inicjalizuje klienta Ollama na podstawie konfiguracji.

        Raises:
            ConfigError: Jeśli brakuje wymaganych ustawień w konfiguracji.
            AIEngineError: Jeśli nie można połączyć się z serwerem Ollama.
        """
        model = getattr(settings, "LLM_MODEL", None)
        host = getattr(settings, "OLLAMA_HOST", None)
        if not isinstance(model, str) or not model:
            raise ConfigError("Brak nazwy modelu LLM w konfiguracji (LLM_MODEL)")
        if not isinstance(host, str) or not host:
            raise ConfigError("Brak adresu hosta Ollama w konfiguracji (OLLAMA_HOST)")
        self.model: str = model
        self.host: str = host
        self.client = ollama.Client(host=self.host)
        try:
            self._verify_connection()
        except Exception as e:
            raise AIEngineError(f"Nie można połączyć się z serwerem Ollama pod adresem {self.host}: {str(e)}")

    def _verify_connection(self) -> None:
        """
        Prywatna metoda sprawdzająca dostępność serwera Ollama.

        Raises:
            Exception: Jeśli nie można uzyskać listy modeli z serwera.
        """
        # Próba pobrania listy modeli jako test połączenia
        self.client.list()

    def generate_response(self, history: List[Dict[str, str]]) -> str:
        """
        Generuje odpowiedź na podstawie historii konwersacji.
        
        Args:
            history (List[Dict[str, str]]): Lista słowników zawierających historię konwersacji,
                gdzie każdy słownik ma klucze 'role' i 'content'
        
        Returns:
            str: Wygenerowana odpowiedź modelu
        """
        try:
            # Konwertujemy historię do formatu akceptowanego przez ollama
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
            # Typ messages jest zgodny z dokumentacją oficjalnego klienta Ollama (list[dict[str, str]])
            response = self.client.chat(
                model=self.model,
                messages=messages  # type: ignore[arg-type]
            )
            # Jeśli response jest iteratorem (stream=True), pobierz pierwszy element
            if isinstance(response, Iterator):
                response = next(response)
            return response['message']['content']
        except Exception as e:
            return f"Wystąpił błąd podczas generowania odpowiedzi: {str(e)}"

    def get_langchain_llm(self) -> Ollama:
        """
        Zwraca instancję LangChain Ollama LLM skonfigurowaną do pracy z lokalnym serwerem.

        Returns:
            Ollama: Skonfigurowana instancja LangChain Ollama LLM
        """
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        return Ollama(
            model=self.model,
            base_url=self.host,
            callback_manager=callback_manager,
            temperature=0.7
        )

# Dla kompatybilności z dotychczasowym kodem
LLMManager = OllamaClient
