"""
Moduł zarządzający połączeniem z bazą danych SQLite.
Zapewnia niezawodne połączenie z bazą danych poprzez użycie ścieżek absolutnych.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from .config_manager import get_settings

_db_initialized = False

def init_db() -> None:
    """Inicjalizuje bazę danych SQLite."""
    global _db_initialized
    if _db_initialized:
        return
        
    try:
        db_path = Path(get_settings().DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Tworzenie tabeli konwersacji
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_message TEXT NOT NULL,
                assistant_message TEXT NOT NULL
            )
        """)
        
        # Tworzenie tabeli zadań
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        """)
        
        conn.commit()
        conn.close()
        _db_initialized = True
        print("Baza danych została zainicjalizowana pomyślnie.")
    except Exception as e:
        print(f"Błąd podczas inicjalizacji bazy danych: {e}")
        raise

def get_db_connection() -> sqlite3.Connection:
    """Zwraca połączenie z bazą danych."""
    return sqlite3.connect(str(Path(get_settings().DB_PATH)))

def save_conversation(user_message: str, assistant_message: str) -> None:
    """Zapisuje konwersację do bazy danych."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (user_message, assistant_message) VALUES (?, ?)",
        (user_message, assistant_message)
    )
    conn.commit()
    conn.close()

def get_conversation_history(limit: int = 10) -> list:
    """Pobiera historię konwersacji z bazy danych."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_message, assistant_message FROM conversations ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    history = cursor.fetchall()
    conn.close()
    return history

def add_task(title: str, description: Optional[str] = None) -> int:
    """Dodaje nowe zadanie do bazy danych."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description) VALUES (?, ?)",
        (title, description)
    )
    task_id = cursor.lastrowid
    if task_id is None:
        raise sqlite3.Error("Nie udało się utworzyć nowego zadania")
    conn.commit()
    conn.close()
    return task_id

def get_tasks(status: Optional[str] = None) -> list:
    """Pobiera listę zadań z bazy danych."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status:
        cursor.execute(
            "SELECT id, title, description, status, created_at, completed_at FROM tasks WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
    else:
        cursor.execute(
            "SELECT id, title, description, status, created_at, completed_at FROM tasks ORDER BY created_at DESC"
        )
    
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def update_task_status(task_id: int, status: str) -> None:
    """Aktualizuje status zadania."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status == 'completed':
        cursor.execute(
            "UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, task_id)
        )
    else:
        cursor.execute(
            "UPDATE tasks SET status = ?, completed_at = NULL WHERE id = ?",
            (status, task_id)
        )
    
    conn.commit()
    conn.close() 