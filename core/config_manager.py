"""
Moduł zarządzający konfiguracją aplikacji.

Ten moduł odpowiada za wczytywanie i walidację ustawień aplikacji z pliku .env
oraz zapewnia dostęp do tych ustawień w całej aplikacji.
"""

from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError
from pathlib import Path
from langchain_community.llms import Ollama


class ConfigError(Exception):
    """
    Wyjątek używany do sygnalizowania błędów związanych z konfiguracją.
    
    Attributes:
        message (str): Opis błędu
        original_error (Optional[Exception]): Oryginalny wyjątek, jeśli istnieje
    """
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(f"{message} (Original error: {str(original_error)})" if original_error else message)


class Settings(BaseSettings):
    """
    Klasa przechowująca konfigurację aplikacji.
    
    Wykorzystuje Pydantic do walidacji i wczytywania ustawień z pliku .env.
    Wszystkie pola są opcjonalne i mają zdefiniowane wartości domyślne.
    """
    
    # Konfiguracja dostawcy modelu LLM
    LLM_PROVIDER: Literal["ollama", "vllm"] = "ollama"
    
    # Adres hosta Ollama (domyślnie localhost)
    OLLAMA_HOST: str = "http://localhost:11434"
    
    # Nazwa modelu LLM do użycia
    # Bielik to polskojęzyczny model o rozmiarze 11B parametrów, 
    # który lepiej radzi sobie z polskimi zapytaniami
    LLM_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
    
    # Nazwa modelu do embeddingów
    EMBEDDING_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
    
    # Klucz API do serwisu pogodowego OpenWeatherMap
    WEATHER_API_KEY: str = ""
    
    # Ścieżka do bazy danych SQLite
    DB_PATH: str = str(Path("data/main.db"))
    
    # Konfiguracja Pydantic - określa, że ustawienia będą wczytywane z pliku .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def embedding_model_name(self) -> str:
        """Zwraca nazwę modelu do embeddingów."""
        return self.EMBEDDING_MODEL
    
    @property
    def llm_model(self) -> Ollama:
        """Zwraca skonfigurowany model LLM."""
        return Ollama(
            base_url=self.OLLAMA_HOST,
            model=self.LLM_MODEL
        )


class ConfigManager:
    """
    Klasa zarządzająca konfiguracją aplikacji.
    
    Zapewnia interfejs do dostępu do ustawień aplikacji oraz metodę do ich wczytywania.
    """
    
    def __init__(self):
        """Inicjalizuje menedżer konfiguracji."""
        self._settings: Optional[Settings] = None
        self.load_settings()
    
    def load_settings(self) -> None:
        """
        Wczytuje i waliduje ustawienia aplikacji.
        
        Raises:
            ConfigError: Jeśli wystąpi błąd podczas wczytywania lub walidacji ustawień.
        """
        try:
            self._settings = Settings()
        except ValidationError as e:
            raise ConfigError("Błąd walidacji ustawień", e)
        except Exception as e:
            raise ConfigError("Nieoczekiwany błąd podczas wczytywania ustawień", e)
    
    @property
    def settings(self) -> Settings:
        """
        Zwraca aktualne ustawienia aplikacji.
        
        Returns:
            Settings: Instancja klasy Settings z wczytanymi ustawieniami.
            
        Raises:
            ConfigError: Jeśli ustawienia nie zostały poprawnie wczytane.
        """
        if self._settings is None:
            self.load_settings()
            if self._settings is None:  # Dodatkowe sprawdzenie po próbie wczytania
                raise ConfigError("Nie udało się wczytać ustawień")
        return self._settings


# Globalna instancja menedżera konfiguracji
config_manager = ConfigManager()
