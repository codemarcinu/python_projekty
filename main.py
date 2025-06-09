"""
Główny moduł aplikacji.

Ten moduł zawiera punkt wejścia aplikacji oraz podstawową logikę uruchomieniową.
"""

import typer
import asyncio
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

from core.ai_engine import AIEngine
from core.config_manager import ConfigManager

app = typer.Typer()
console = Console()

@app.command("add-doc")
def add_document(file_path: str) -> None:
    """Dodaje dokument do bazy wektorowej.
    
    Args:
        file_path: Ścieżka do pliku do dodania
    """
    try:
        # Inicjalizacja silnika AI
        config = ConfigManager()
        engine = AIEngine(config)
        
        # Dodanie dokumentu
        engine.rag_manager.add_document(file_path)
        console.print(f"[green]Dokument dodany pomyślnie:[/green] {file_path}")
        
    except Exception as e:
        console.print(f"[red]Wystąpił błąd:[/red] {str(e)}")

@app.command("rag")
def rag_query(query: str) -> None:
    """Zadaje pytanie do dokumentów w bazie wektorowej.
    
    Args:
        query: Pytanie do zadania
    """
    try:
        # Inicjalizacja silnika AI
        config = ConfigManager()
        engine = AIEngine(config)
        
        # Sprawdzenie czy baza wektorowa istnieje
        if engine.rag_manager.vector_store is None:
            console.print("[red]Błąd:[/red] Baza wektorowa nie istnieje. Najpierw dodaj dokumenty używając komendy 'add-doc'.")
            return
        
        # Generowanie i wyświetlanie odpowiedzi
        console.print("\n[bold blue]Odpowiedź:[/bold blue]\n")
        
        async def process_response():
            async for chunk in engine.get_rag_response_stream(query):
                console.print(chunk, end="")
            console.print("\n")
        
        # Uruchomienie asynchronicznej funkcji
        asyncio.run(process_response())
        
    except Exception as e:
        console.print(f"[red]Wystąpił błąd:[/red] {str(e)}")

if __name__ == "__main__":
    app()
