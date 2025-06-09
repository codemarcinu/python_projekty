"""
Moduł interfejsu linii poleceń (CLI) aplikacji.

Ten moduł implementuje interfejs użytkownika w formie aplikacji konsolowej
wykorzystującej bibliotekę Typer do obsługi argumentów wiersza poleceń.
"""

from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from core.ai_engine import AIEngine
from core.conversation_handler import ConversationHandler
from core.database import init_db, DatabaseError
from core.config_manager import config_manager, ConfigError
from core.exceptions import AIEngineError, ConversationError
import asyncio

# Inicjalizacja aplikacji Typer
app = typer.Typer(
    name="AI Assistant CLI",
    help="Lokalny asystent AI działający w trybie konsolowym",
    add_completion=False
)
console = Console()


def handle_error(error: Exception, context: str) -> None:
    """
    Obsługuje błędy i wyświetla je użytkownikowi w czytelnej formie.

    Args:
        error: Wyjątek, który wystąpił
        context: Kontekst, w którym wystąpił błąd

    Returns:
        None
    """
    error_message = f"[bold red]Błąd podczas {context}:[/bold red]\n{str(error)}"
    console.print(Panel(error_message, title="Błąd", border_style="red"))
    raise typer.Exit(code=1)


@app.command()
def chat(
    prompt: Optional[str] = typer.Argument(
        None,
        help="Pytanie lub polecenie dla asystenta AI"
    )
) -> None:
    """
    Uruchamia interaktywny czat z asystentem AI lub przetwarza pojedyncze polecenie.

    Args:
        prompt: Opcjonalne pytanie lub polecenie dla asystenta. Jeśli nie podano,
                uruchamiany jest tryb interaktywny.

    Returns:
        None

    Raises:
        typer.Exit: W przypadku wystąpienia błędu krytycznego
    """
    try:
        # Inicjalizuj bazę danych TYLKO RAZ przy starcie
        init_db()
    except DatabaseError as e:
        handle_error(e, "inicjalizacji bazy danych")
    
    try:
        # Wyświetl informację o używanym modelu
        console.print(f"🔌 Korzystam z modelu: [bold green]{config_manager.settings.LLM_MODEL}[/bold green]")
    except ConfigError as e:
        handle_error(e, "pobierania konfiguracji")

    try:
        engine = AIEngine(config_manager)
        handler = ConversationHandler()
    except (AIEngineError, ConversationError) as e:
        handle_error(e, "inicjalizacji silnika AI")

    # Jeśli podano prompt, przetwórz go i zakończ
    if prompt:
        try:
            handler.add_message(role="user", content=prompt)
            console.print("[yellow]Asystent myśli...[/yellow]", end="\r")
            final_response = engine.process_turn(handler.get_history())
            console.print(" " * 20, end="\r")  # Wyczyść "Asystent myśli..."
            console.print(f"[bold blue]Asystent:[/bold blue] {final_response}")
            handler.add_message(role="assistant", content=final_response)
        except (AIEngineError, ConversationError) as e:
            handle_error(e, "przetwarzania polecenia")
        return

    # Tryb interaktywny
    console.print("[bold cyan]Witaj! Jestem Twoim lokalnym asystentem AI.[/bold cyan]")
    console.print("Aby zakończyć konwersację, wpisz 'koniec' lub 'wyjdz'.")

    while True:
        try:
            user_input = console.input("[bold green]Ty: [/bold green]")

            if user_input.lower() in ["koniec", "wyjdz", "exit"]:
                console.print("[bold cyan]Do widzenia![/bold cyan]")
                break

            handler.add_message(role="user", content=user_input)

            console.print("[yellow]Asystent myśli...[/yellow]", end="\r")
            final_response = engine.process_turn(handler.get_history())
            console.print(" " * 20, end="\r")  # Wyczyść "Asystent myśli..."

            console.print(f"[bold blue]Asystent:[/bold blue] {final_response}")
            handler.add_message(role="assistant", content=final_response)
        except (AIEngineError, ConversationError) as e:
            console.print(Panel(
                f"[bold red]Wystąpił błąd podczas przetwarzania odpowiedzi:[/bold red]\n{str(e)}",
                title="Błąd",
                border_style="red"
            ))
            console.print("[yellow]Możesz kontynuować konwersację...[/yellow]")


@app.command("rag")
async def rag_query(query: str) -> None:
    """Zadaje pytanie do dokumentów w bazie wektorowej.
    
    Args:
        query: Pytanie do zadania
    """
    try:
        # Inicjalizacja silnika AI
        engine = AIEngine(config_manager)
        
        # Sprawdzenie czy baza wektorowa istnieje
        if engine.rag_manager.vector_store is None:
            console.print("[red]Błąd:[/red] Baza wektorowa nie istnieje. Najpierw dodaj dokumenty używając komendy 'add-doc'.")
            return
        
        # Generowanie i wyświetlanie odpowiedzi
        console.print("\n[bold blue]Odpowiedź:[/bold blue]\n")
        async for chunk in engine.get_rag_response_stream(query):
            console.print(chunk, end="")
        console.print("\n")
        
    except Exception as e:
        console.print(f"[red]Wystąpił błąd:[/red] {str(e)}")


if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        handle_error(e, "uruchamiania aplikacji")
