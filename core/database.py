"""
Moduł zarządzający połączeniem z bazą danych SQLite.
Zapewnia niezawodne połączenie z bazą danych poprzez użycie ścieżek absolutnych.
"""

import sqlite3
import os
from typing import Optional

# --- Nowa, niezawodna metoda lokalizacji bazy danych ---
# Znajdź absolutną ścieżkę do katalogu głównego projektu (jeden poziom wyżej niż 'core')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Zdefiniuj ścieżkę do katalogu 'data'
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
# Zdefiniuj finalną, absolutną ścieżkę do pliku bazy danych
DATABASE_FILE = os.path.join(DATA_DIR, 'main.db')
# --- Koniec nowej metody ---

def init_db() -> None:
    """
    Inicjalizuje bazę danych. Tworzy katalog i plik bazy danych,
    jeśli nie istnieją, oraz tworzy niezbędne tabele.
    
    Raises:
        sqlite3.Error: W przypadku błędu podczas operacji na bazie danych
    """
    try:
        # Upewnij się, że katalog 'data' istnieje
        os.makedirs(DATA_DIR, exist_ok=True)

        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Stwórz tabelę 'tasks', jeśli jeszcze nie istnieje
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'todo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()
        print("Baza danych zainicjalizowana pomyślnie.")
    except Exception as e:
        print(f"Błąd podczas inicjalizacji bazy danych: {e}")
        raise sqlite3.Error(f"Błąd podczas inicjalizacji bazy danych: {e}")

def get_db_connection() -> sqlite3.Connection:
    """
    Tworzy i zwraca nowe połączenie z bazą danych.
    
    Returns:
        sqlite3.Connection: Aktywne połączenie z bazą danych
        
    Raises:
        sqlite3.Error: W przypadku błędu podczas nawiązywania połączenia
    """
    try:
        return sqlite3.connect(DATABASE_FILE)
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Błąd podczas nawiązywania połączenia z bazą danych: {e}") 