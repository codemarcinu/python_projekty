"""
Main entry point for the AI Assistant application.
Handles both CLI and web server modes.
"""
import asyncio
import logging
import uvicorn
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from core.rag_manager import RAGManager
from core.config_manager import get_settings
from core.llm_manager import get_llm_manager, ModelUnavailableError

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Typer app
app = typer.Typer(help="AI Assistant")

# Initialize Rich console
console = Console()


@app.command()
def serve(
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to bind the web server to"
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind the web server to"
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload on code changes"
    )
):
    """Start the web server."""
    llm_manager = get_llm_manager()
    try:
        asyncio.run(llm_manager.validate_ollama_model())
    except ModelUnavailableError as e:
        console.print(f"[bold red]Błąd: {e}[/bold red]")
        raise typer.Exit(code=1)
    from interfaces.web_ui import app as web_app
    console.print(f"[bold blue]Starting web server at http://{host}:{port}[/bold blue]")
    uvicorn.run(
        "interfaces.web_ui:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        ws_max_size=16777216,  # 16MB dla WebSocket
        ws_ping_interval=20,
        ws_ping_timeout=20
    )


@app.command()
def cli():
    """Start the CLI interface."""
    from interfaces.cli import app as cli_app
    cli_app()


@app.command()
def init_vector_db():
    """Inicjalizuje pusty indeks FAISS (baza wiedzy)."""
    console.print("[bold yellow]Inicjalizacja pustego indeksu FAISS...[/bold yellow]")
    config = get_settings().rag
    rag_manager = RAGManager(config)
    rag_manager.init_empty_index()
    console.print("[bold green]Indeks FAISS gotowy![/bold green]")


if __name__ == "__main__":
    try:
        logger.info("Starting AI Assistant server...")
        app()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise
