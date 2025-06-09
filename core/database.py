"""
Moduł zarządzający połączeniem z bazą danych SQLite.
Zapewnia niezawodne połączenie z bazą danych poprzez użycie ścieżek absolutnych.
"""

import sqlite3
import os

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
    except Exception as e:
        print(f"Błąd podczas inicjalizacji bazy danych: {e}")

def get_db_connection() -> sqlite3.Connection:
    """Zwraca połączenie z bazą danych."""
    return sqlite3.connect(DATABASE_FILE) 