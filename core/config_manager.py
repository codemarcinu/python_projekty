"""
Moduł zarządzający konfiguracją aplikacji.

Ten moduł odpowiada za wczytywanie i walidację ustawień aplikacji z pliku .env
oraz zapewnia dostęp do tych ustawień w całej aplikacji.
"""

from typing import Literal
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Klasa przechowująca konfigurację aplikacji.
    
    Wykorzystuje Pydantic do walidacji i wczytywania ustawień z pliku .env.
    Wszystkie pola są opcjonalne i mają zdefiniowane wartości domyślne.
    """
    
    # Konfiguracja dostawcy modelu LLM
    LLM_PROVIDER: Literal["ollama", "vllm"] = "ollama"
    
    # Nazwa modelu LLM do użycia
    # Bielik to polskojęzyczny model o rozmiarze 11B parametrów, 
    # który lepiej radzi sobie z polskimi zapytaniami
    LLM_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
    
    # Klucz API do serwisu pogodowego OpenWeatherMap
    WEATHER_API_KEY: str = ""
    
    # Konfiguracja Pydantic - określa, że ustawienia będą wczytywane z pliku .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Tworzy i zwraca globalną instancję ustawień aplikacji.
    
    Funkcja jest opakowana dekoratorem @lru_cache, co zapewnia,
    że ustawienia będą wczytywane tylko raz i później będą zwracane
    z pamięci podręcznej.
    
    Returns:
        Settings: Instancja klasy Settings z wczytanymi ustawieniami
        
    Example:
        >>> settings = get_settings()
        >>> print(settings.LLM_PROVIDER)
        'ollama'
    """
    return Settings()
