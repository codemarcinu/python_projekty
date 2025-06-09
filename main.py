"""
Main entry point for the AI Assistant application.
Handles both CLI and web server modes.
"""
import asyncio
import uvicorn
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from interfaces.cli import app as cli_app
from interfaces.web_ui import app as web_app


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
    cli_app()


if __name__ == "__main__":
    app()
