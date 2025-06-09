"""
Moduł implementujący narzędzie do wyszukiwania informacji w internecie.

Ten moduł dostarcza funkcjonalność wyszukiwania aktualnych informacji w internecie,
która może być wykorzystana przez asystenta AI do odpowiadania na pytania
wymagające dostępu do najnowszych danych.
"""

from typing import Optional
from core.tool_models import BaseTool
from duckduckgo_search import DDGS


class WebSearchTool(BaseTool):
    """
    Narzędzie do wyszukiwania aktualnych informacji w internecie.
    
    To narzędzie umożliwia asystentowi AI dostęp do aktualnych informacji
    z internetu, takich jak wiadomości, pogoda, wyniki sportowe itp.
    Wykorzystuje API DuckDuckGo do wykonywania wyszukiwań.
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
        
        Tworzy instancję klienta DuckDuckGo Search do wykonywania zapytań.
        """
        self.search_client = DDGS()
    
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
        try:
            # Wykonaj wyszukiwanie i pobierz maksymalnie 4 wyniki
            results = list(self.search_client.text(query, max_results=4))
            
            if not results:
                return "Nie znaleziono żadnych wyników dla podanego zapytania."
            
            # Przetwórz wyniki na czytelny format
            formatted_results = []
            for result in results:
                formatted_result = f"Tytuł: {result['title']}\nOpis: {result['body']}\n"
                formatted_results.append(formatted_result)
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            return f"Wystąpił błąd podczas wyszukiwania: {str(e)}" 