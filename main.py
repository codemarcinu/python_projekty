"""
Główny plik uruchomieniowy aplikacji.

Ten moduł zawiera główną logikę uruchomieniową aplikacji oraz definicje komend CLI.
"""

import typer
from pathlib import Path
import uvicorn
from core.config_manager import config_manager
from core.ai_engine import AIEngine
from interfaces.api import app

# Inicjalizacja aplikacji Typer
cli = typer.Typer()

# Inicjalizacja silnika AI
engine = AIEngine(config_manager.settings)

@cli.command()
def add_doc(file_path: str):
    """
    Dodaje dokument do bazy wiedzy.
    
    Args:
        file_path (str): Ścieżka do pliku do dodania
    """
    try:
        path = Path(file_path)
        if not path.exists():
            print(f"Błąd: Plik {file_path} nie istnieje")
            return
        
        engine.rag_manager.add_document(path)
        print(f"Dokument {file_path} został dodany do bazy wiedzy")
    except Exception as e:
        print(f"Błąd podczas dodawania dokumentu: {e}")

@cli.command()
def rag(query: str):
    """
    Zadaje pytanie do bazy wiedzy.
    
    Args:
        query (str): Pytanie do zadania
    """
    try:
        response = engine.rag_manager.query(query)
        print(f"Odpowiedź: {response}")
    except Exception as e:
        print(f"Błąd podczas przetwarzania zapytania: {e}")

@cli.command()
def serve(host: str = "127.0.0.1", port: int = 8000):
    """
    Uruchamia serwer FastAPI.
    
    Args:
        host (str): Adres hosta
        port (int): Port serwera
    """
    print(f"Uruchamianie serwera na {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    cli()
