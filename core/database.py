"""
Moduł zarządzający połączeniem z bazą danych SQLite.
Zapewnia niezawodne połączenie z bazą danych poprzez użycie ścieżek absolutnych.
"""

import sqlite3
import os
from typing import Optional

class DatabaseError(Exception):
    """
    Wyjątek używany do sygnalizowania błędów związanych z bazą danych.
    
    Attributes:
        message (str): Opis błędu
        original_error (Optional[Exception]): Oryginalny wyjątek, jeśli istnieje
    """
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(f"{message} (Original error: {str(original_error)})" if original_error else message)

# --- Definicje na poziomie modułu (globalne), aby mogły być importowane ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DATABASE_FILE = os.path.join(DATA_DIR, 'main.db')

# Flaga zapobiegająca wielokrotnej inicjalizacji
_db_initialized = False

def init_db():
    """
    Inicjalizuje bazę danych. Tworzy katalog i plik bazy danych,
    jeśli nie istnieją, oraz tworzy niezbędne tabele.
    Uruchamia się tylko raz dzięki fladze _db_initialized.
    
    Raises:
        DatabaseError: Jeśli wystąpi błąd podczas inicjalizacji bazy danych.
    """
    global _db_initialized
    if _db_initialized:
        return

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

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
        print("Baza danych została zainicjalizowana pomyślnie.")
        _db_initialized = True
    except sqlite3.Error as e:
        raise DatabaseError("Błąd SQLite podczas inicjalizacji bazy danych", e)
    except OSError as e:
        raise DatabaseError("Błąd systemu operacyjnego podczas inicjalizacji bazy danych", e)
    except Exception as e:
        raise DatabaseError("Nieoczekiwany błąd podczas inicjalizacji bazy danych", e)

def get_db_connection() -> sqlite3.Connection:
    """
    Zwraca połączenie z bazą danych.
    
    Returns:
        sqlite3.Connection: Połączenie z bazą danych.
        
    Raises:
        DatabaseError: Jeśli nie można nawiązać połączenia z bazą danych.
    """
    try:
        return sqlite3.connect(DATABASE_FILE)
    except sqlite3.Error as e:
        raise DatabaseError("Nie można nawiązać połączenia z bazą danych", e) 