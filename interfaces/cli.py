"""
Moduł interfejsu linii poleceń (CLI) aplikacji.

Ten moduł implementuje interfejs użytkownika w formie aplikacji konsolowej
wykorzystującej bibliotekę Typer do obsługi argumentów wiersza poleceń.
"""

import typer
from typing import Optional
from core.conversation_handler import ConversationHandler
from core.llm_manager import LLMManager

# Inicjalizacja aplikacji Typer
app = typer.Typer()


@app.command()
def main() -> None:
    """Główna funkcja interfejsu CLI asystenta AI.
    
    Implementuje pętlę konwersacji, która:
    1. Pobiera wiadomość od użytkownika
    2. Przekazuje ją do modelu AI
    3. Wyświetla odpowiedź
    4. Zachowuje historię konwersacji
    
    Aby zakończyć konwersację, wpisz 'koniec' lub 'wyjdz'.
    """
    # Inicjalizacja komponentów
    llm = LLMManager()
    handler = ConversationHandler()
    
    print("Witaj! Jestem Twoim lokalnym asystentem AI. Aby zakończyć konwersację, wpisz 'koniec' lub 'wyjdz'.")
    
    while True:
        # Pobierz wiadomość od użytkownika
        user_input = input("\nTy: ").strip()
        
        # Sprawdź czy użytkownik chce zakończyć
        if user_input.lower() in ['koniec', 'wyjdz']:
            print("\nDo widzenia!")
            break
        
        # Dodaj wiadomość użytkownika do historii
        handler.add_message('user', user_input)
        
        # Pobierz historię i wygeneruj odpowiedź
        history = handler.get_history()
        response = llm.generate_response(history)
        
        # Wyświetl odpowiedź i dodaj ją do historii
        print(f"\nAsystent: {response}")
        handler.add_message('assistant', response)


if __name__ == "__main__":
    app()
