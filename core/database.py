"""
Menedżer bazy danych SQLite dla asystenta AI.
Zapewnia centralne miejsce do zarządzania połączeniem z bazą danych i inicjalizacji schematu.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

# Stała określająca lokalizację pliku bazy danych
DATABASE_FILE: str = "data/main.db"

def init_db() -> None:
    """
    Inicjalizuje bazę danych SQLite, tworząc niezbędne tabele jeśli nie istnieją.
    
    Funkcja:
    1. Tworzy katalog data/ jeśli nie istnieje
    2. Nawiązuje połączenie z bazą danych
    3. Tworzy tabelę tasks jeśli nie istnieje
    4. Zamyka połączenie
    
    Raises:
        sqlite3.Error: W przypadku błędu podczas operacji na bazie danych
    """
    # Upewnij się, że katalog data/ istnieje
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    try:
        # Nawiąż połączenie z bazą danych
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Utwórz tabelę tasks jeśli nie istnieje
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Zatwierdź zmiany i zamknij połączenie
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
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