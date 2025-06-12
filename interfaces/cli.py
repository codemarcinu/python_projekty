"""
Command-line interface for the AI Assistant.
Provides a text-based interface for interacting with the AI Assistant.
"""
import asyncio
from pathlib import Path
from typing import Optional
import uuid

import typer
import uvicorn
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from core.container import Container
from utils.logging import setup_logging
from main import app as fastapi_app

from core.ai_engine import get_ai_engine
from core.conversation_handler import get_conversation_manager


# Initialize Typer app
app = typer.Typer(help="AI Assistant CLI")

# Initialize Rich console
console = Console()


@app.command()
def chat(
    conversation_id: Optional[str] = typer.Option(
        None,
        "--conversation",
        "-c",
        help="Conversation ID to continue"
    )
):
    """Start an interactive chat session with the AI Assistant."""
    # Get or create conversation
    conversation_manager = get_conversation_manager()
    if conversation_id:
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            console.print(f"[red]Conversation {conversation_id} not found[/red]")
            return
    else:
        conversation_id_new = str(uuid.uuid4())
        conversation = conversation_manager.create_conversation(conversation_id_new)
    
    # Print welcome message
    console.print("\n[bold blue]AI Assistant CLI[/bold blue]")
    console.print("Type 'exit' or 'quit' to end the session\n")
    
    # Main chat loop
    while True:
        # Get user input
        user_input = Prompt.ask("[bold green]You[/bold green]")
        
        # Check for exit command
        if user_input.lower() in {"exit", "quit"}:
            break
        
        # Process message
        ai_engine = get_ai_engine()
        response = asyncio.run(
            ai_engine.process_message(
                message=user_input
            )
        )
        
        # Print response
        console.print("\n[bold blue]Assistant[/bold blue]")
        console.print(Markdown(response))
        console.print()


@app.command()
def rag(
    query: str = typer.Argument(..., help="Query to process with RAG system"),
    conversation_id: Optional[str] = typer.Option(
        None,
        "--conversation",
        "-c",
        help="Conversation ID to use for context"
    )
):
    """Process a query using the RAG system."""
    # Get conversation if specified
    conversation = None
    if conversation_id:
        conversation_manager = get_conversation_manager()
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            console.print(f"[red]Conversation {conversation_id} not found[/red]")
            return
    
    # Process query
    ai_engine = get_ai_engine()
    if conversation:
        response = asyncio.run(
            ai_engine.process_rag_query(
                query=query
            )
        )
    else:
        response = asyncio.run(
            ai_engine.process_rag_query(
                query=query
            )
        )
    
    # Print response
    console.print("\n[bold blue]RAG Response[/bold blue]")
    console.print(Markdown(response))
    console.print()


@app.command()
def add_doc(
    file_path: Path = typer.Argument(
        ...,
        help="Path to document to add to RAG system",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True
    )
):
    """Add a document to the RAG system."""
    # Validate file type
    allowed_types = {".pdf", ".txt", ".md"}
    if file_path.suffix.lower() not in allowed_types:
        console.print(f"[red]Unsupported file type. Allowed types: {', '.join(allowed_types)}[/red]")
        return
    
    # TODO: Implement document processing
    console.print(f"[yellow]Document processing not yet implemented[/yellow]")


@app.command()
def list_conversations():
    """List all conversations."""
    conversation_manager = get_conversation_manager()
    conversations = conversation_manager.list_conversations()
    
    if not conversations:
        console.print("[yellow]No conversations found[/yellow]")
        return
    
    console.print("\n[bold blue]Conversations[/bold blue]")
    for conv_id, title, updated_at in conversations:
        console.print(f"ID: {conv_id}")
        console.print(f"Title: {title}")
        console.print(f"Last updated: {updated_at}")
        console.print()


@app.command()
def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    log_level: str = "info",
    reload: bool = False
):
    """
    Uruchamia serwer FastAPI z AI Assistant.
    """
    setup_logging()
    console.print(f"[green]Startuję serwer na http://{host}:{port}[/green]")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
        ws_max_size=1024 * 1024 * 10,  # 10MB
        ws_ping_interval=20.0,
        ws_ping_timeout=20.0
    )


if __name__ == "__main__":
    app()
