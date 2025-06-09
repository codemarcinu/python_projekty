"""
Moduł interfejsu linii poleceń (CLI) aplikacji.

Ten moduł implementuje interfejs użytkownika w formie aplikacji konsolowej
wykorzystującej bibliotekę Typer do obsługi argumentów wiersza poleceń.
"""

import typer
from rich.console import Console
from core.ai_engine import AIEngine
from core.conversation_handler import ConversationHandler
from core.database import init_db
from core.config_manager import settings

# Inicjalizacja aplikacji Typer
app = typer.Typer()
console = Console()


@app.command()
def main():
    """
    Uruchamia główną pętlę interaktywnego czatu z asystentem AI.
    """
    # Inicjalizuj bazę danych TYLKO RAZ przy starcie.
    init_db()
    
    # Wyświetl informację o używanym modelu
    console.print(f"🔌 Korzystam z modelu: [bold green]{settings.LLM_MODEL}[/bold green]")

    engine = AIEngine()
    handler = ConversationHandler()

    console.print("[bold cyan]Witaj! Jestem Twoim lokalnym asystentem AI.[/bold cyan]")
    console.print("Aby zakończyć konwersację, wpisz 'koniec' lub 'wyjdz'.")

    while True:
        prompt = console.input("[bold green]Ty: [/bold green]")

        if prompt.lower() in ["koniec", "wyjdz", "exit"]:
            console.print("[bold cyan]Do widzenia![/bold cyan]")
            break

        handler.add_message(role="user", content=prompt)

        console.print("[yellow]Asystent myśli...[/yellow]", end="\r")
        final_response = engine.process_turn(handler.get_history())
        console.print(" " * 20, end="\r") # Wyczyść "Asystent myśli..."

        console.print(f"[bold blue]Asystent:[/bold blue] {final_response}")
        handler.add_message(role="assistant", content=final_response)


if __name__ == "__main__":
    app()
