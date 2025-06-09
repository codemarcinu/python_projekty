"""
Moduł zarządzający konfiguracją aplikacji.

Ten moduł odpowiada za wczytywanie i walidację ustawień aplikacji z pliku .env
oraz zapewnia dostęp do tych ustawień w całej aplikacji.
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


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
    
    # Ścieżka do bazy danych SQLite
    DB_PATH: str = str(Path("data/main.db"))
    
    # Konfiguracja Pydantic - określa, że ustawienia będą wczytywane z pliku .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Globalna instancja ustawień, którą można importować z innych modułów
settings = Settings()
