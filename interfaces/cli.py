"""
Moduł interfejsu linii poleceń (CLI) aplikacji.

Ten moduł implementuje interfejs użytkownika w formie aplikacji konsolowej
wykorzystującej bibliotekę Typer do obsługi argumentów wiersza poleceń.
"""

import typer
from typing import Optional
from core.conversation_handler import ConversationHandler
from core.ai_engine import AIEngine
from core.database import init_db

# Inicjalizacja aplikacji Typer
app = typer.Typer()


@app.command()
def main() -> None:
    """Główna funkcja interfejsu CLI asystenta AI.
    
    Implementuje pętlę konwersacji, która:
    1. Inicjalizuje bazę danych
    2. Pobiera wiadomość od użytkownika
    3. Przekazuje ją do silnika AI
    4. Wyświetla odpowiedź
    5. Zachowuje historię konwersacji
    
    Aby zakończyć konwersację, wpisz 'koniec' lub 'wyjdz'.
    """
    # Inicjalizacja bazy danych
    try:
        init_db()
        print("Baza danych zainicjalizowana pomyślnie.")
    except Exception as e:
        print(f"Błąd podczas inicjalizacji bazy danych: {e}")
        return
    
    # Inicjalizacja komponentów
    handler = ConversationHandler()
    engine = AIEngine()
    
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
        
        # Przetwórz turę konwersacji przez silnik AI
        final_response = engine.process_turn(handler.get_history())
        
        # Wyświetl odpowiedź i dodaj ją do historii
        print(f"\nAsystent: {final_response}")
        handler.add_message('assistant', final_response)


if __name__ == "__main__":
    app()
