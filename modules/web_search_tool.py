"""
Moduł implementujący narzędzie do wyszukiwania informacji w internecie.

Ten moduł dostarcza funkcjonalność wyszukiwania aktualnych informacji w internecie,
która może być wykorzystana przez asystenta AI do odpowiadania na pytania
wymagające dostępu do najnowszych danych.
"""

import logging
from typing import Optional
from core.tool_models import BaseTool
from core.config_manager import ConfigManager
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class WebSearchTool(BaseTool):
    """
    Narzędzie do wyszukiwania aktualnych informacji w internecie.
    
    To narzędzie umożliwia asystentowi AI dostęp do aktualnych informacji
    z internetu, takich jak wiadomości, pogoda, wyniki sportowe itp.
    Wykorzystuje Google Custom Search API do wykonywania wyszukiwań.
    """
    
    name: str = "web_search"
    description: str = (
        "Narzędzie do wyszukiwania aktualnych informacji w internecie. "
        "Użyj go, gdy potrzebujesz odpowiedzi na pytania o pogodę, "
        "najnowsze wiadomości, wyniki sportowe lub inne dane w czasie rzeczywistym."
    )
    
    def __init__(self) -> None:
        """
        Inicjalizuje narzędzie do wyszukiwania w internecie.
        
        Tworzy instancję klienta Google Custom Search API do wykonywania zapytań.
        """
        try:
            self.api_key = ConfigManager.get_secret('GOOGLE_API_KEY')
            self.cse_id = ConfigManager.get_secret('GOOGLE_CSE_ID')
            self.service = build("customsearch", "v1", developerKey=self.api_key)
            logging.info("Pomyślnie zainicjalizowano WebSearchTool")
        except ValueError as e:
            logging.error(f"Błąd konfiguracji Google Search API: {str(e)}")
            raise ValueError(f"Błąd konfiguracji Google Search API: {str(e)}")
    
    def execute(self, query: str) -> str:
        """
        Wykonuje wyszukiwanie w internecie dla podanego zapytania.
        
        Args:
            query (str): Zapytanie wyszukiwawcze w języku naturalnym.
            
        Returns:
            str: Wyniki wyszukiwania w formie tekstowej, zawierające tytuły
                 i opisy znalezionych stron.
                 
        Raises:
            Exception: W przypadku problemów z połączeniem lub wyszukiwaniem.
        """
        logging.info(f"Wyszukiwanie w internecie frazy: '{query}'")
        
        try:
            # Wykonaj wyszukiwanie i pobierz maksymalnie 4 wyniki
            results = self.service.cse().list(
                q=query,
                cx=self.cse_id,
                num=4
            ).execute()
            
            if 'items' not in results:
                logging.info(f"Nie znaleziono wyników dla frazy: '{query}'")
                return "Nie znaleziono żadnych wyników dla podanego zapytania."
            
            # Przetwórz wyniki na czytelny format
            formatted_results = []
            for result in results['items']:
                formatted_result = f"Tytuł: {result['title']}\nOpis: {result['snippet']}\nLink: {result['link']}\n"
                formatted_results.append(formatted_result)
            
            logging.info(f"Pomyślnie znaleziono {len(results['items'])} wyników dla frazy: '{query}'")
            return "\n\n".join(formatted_results)
            
        except HttpError as e:
            logging.error(f"Błąd HTTP podczas wyszukiwania frazy '{query}': {str(e)}")
            return f"Wystąpił błąd podczas wyszukiwania: {str(e)}"
        except Exception as e:
            logging.error(f"Nieoczekiwany błąd podczas wyszukiwania frazy '{query}': {str(e)}")
            return f"Wystąpił nieoczekiwany błąd: {str(e)}" 