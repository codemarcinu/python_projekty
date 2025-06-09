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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
    from interfaces.web_ui import app as web_app
    console.print(f"[bold blue]Starting web server at http://{host}:{port}[/bold blue]")
    uvicorn.run(
        "interfaces.web_ui:app",
        host=host,
        port=port,
        reload=reload
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
    app()
