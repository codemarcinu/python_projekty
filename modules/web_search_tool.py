"""
Moduł implementujący narzędzie do wyszukiwania informacji w internecie.

Ten moduł dostarcza funkcjonalność wyszukiwania aktualnych informacji w internecie,
która może być wykorzystana przez asystenta AI do odpowiadania na pytania
wymagające dostępu do najnowszych danych.
"""

import os
from typing import List, Dict, Any
from langchain.tools import BaseTool
from duckduckgo_search import DDGS


class WebSearchTool(BaseTool):
    """
    Narzędzie do wyszukiwania aktualnych informacji w internecie.
    
    To narzędzie umożliwia asystentowi AI dostęp do aktualnych informacji
    z internetu, takich jak wiadomości, pogoda, wyniki sportowe itp.
    Wykorzystuje Google Custom Search API do wykonywania wyszukiwań.
    """
    
    name: str = "web_search"
    description: str = "Wyszukuje informacje w internecie za pomocą DuckDuckGo."

    def _run(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            if not results:
                return "Nie znaleziono wyników."
            return "\n".join([f"{i+1}. {r['title']} - {r['body']}" for i, r in enumerate(results)])
        except Exception as e:
            return f"Błąd wyszukiwania: {str(e)}"

    async def _arun(self, query: str) -> str:
        return self._run(query) 