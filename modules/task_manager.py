"""
Moduł do zarządzania zadaniami w asystencie AI.
Zapewnia funkcjonalność dodawania, wyświetlania, oznaczania jako wykonane i usuwania zadań w bazie danych.
"""

import sqlite3
from typing import List, Tuple
from core.module_system import tool
from core.database import DATABASE_FILE, get_db_connection

class TaskManager:
    """Klasa zarządzająca listą zadań."""
    
    def __init__(self):
        """Inicjalizuje pustą listę zadań."""
        self.tasks = []
    
    def add_task(self, task_description: str) -> str:
        """Dodaje nowe zadanie do listy.
        
        Args:
            task_description: Opis zadania do dodania
            
        Returns:
            str: Potwierdzenie dodania zadania
        """
        self.tasks.append(task_description)
        return f"Dodano zadanie: {task_description}"
    
    def list_tasks(self) -> str:
        """Zwraca sformatowaną listę wszystkich zadań.
        
        Returns:
            str: Sformatowana lista zadań lub informacja o braku zadań
        """
        if not self.tasks:
            return "Brak zadań."
            
        task_list = "Lista zadań:\n"
        for i, task in enumerate(self.tasks, 1):
            task_list += f"{i}. {task}\n"
        return task_list.rstrip()

@tool
def add_task(description: str) -> str:
    """
    Dodaje nowe zadanie do listy zadań do zrobienia.
    Użyj tego narzędzia, gdy użytkownik chce dodać nowe zadanie, zapisać notatkę do zrobienia itp.

    Args:
        description: Opis zadania do dodania.

    Returns:
        str: Komunikat potwierdzający dodanie zadania lub informacja o błędzie.
    """
    print(f"DEBUG: Wywołuję narzędzie 'add_task' z opisem: {description}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (description) VALUES (?)", (description,))
        conn.commit()
        conn.close()
        return f"Pomyślnie dodano zadanie: '{description}'."
    except Exception as e:
        return f"Wystąpił błąd podczas dodawania zadania: {e}"

@tool
def list_tasks(status: str = 'todo') -> str:
    """
    Wyświetla listę zadań o określonym statusie. Domyślnie pokazuje zadania 'do zrobienia' ('todo').
    Użyj, gdy użytkownik pyta "co mam do zrobienia?", "pokaż moje zadania", "jaka jest moja lista zadań?".

    Args:
        status: Status zadań do wyświetlenia (np. 'todo', 'done'). Domyślnie 'todo'.

    Returns:
        str: Sformatowana lista zadań lub informacja o ich braku.
    """
    print(f"DEBUG: Wywołuję narzędzie 'list_tasks' ze statusem: {status}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, description FROM tasks WHERE status = ?", (status,))
        tasks = cursor.fetchall()
        conn.close()

        if not tasks:
            return "Nie masz żadnych zadań do zrobienia."

        task_list_str = f"Twoje zadania (status: {status}):\n"
        for task in tasks:
            task_list_str += f"- [ID: {task[0]}] {task[1]}\n"
        
        return task_list_str
    except Exception as e:
        return f"Wystąpił błąd podczas wyświetlania zadań: {e}"

@tool
def complete_task(task_ids: List[int]) -> str:
    """
    Oznacza zadania jako wykonane.
    Użyj, gdy użytkownik chce oznaczyć zadania jako zakończone.

    Args:
        task_ids: Lista ID zadań do oznaczenia jako wykonane.

    Returns:
        str: Komunikat potwierdzający zmianę statusu lub informacja o błędzie.
    """
    print(f"DEBUG: Wywołuję narzędzie 'complete_task' dla zadań ID: {task_ids}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(task_ids))
        query = f"UPDATE tasks SET status = 'done' WHERE id IN ({placeholders})"
        cursor.execute(query, tuple(task_ids))
        if cursor.rowcount == 0:
            conn.close()
            return f"Nie znaleziono zadań o podanych ID."
        
        conn.commit()
        conn.close()
        return f"Pomyślnie oznaczono {cursor.rowcount} zadań jako wykonane."
    except Exception as e:
        return f"Wystąpił błąd podczas aktualizacji statusu zadań: {e}"

@tool
def delete_task(task_ids: List[int]) -> str:
    """
    Usuwa zadania o podanych ID z bazy danych.
    Użyj, gdy użytkownik chce usunąć zadania z listy.

    Args:
        task_ids: Lista ID zadań do usunięcia.

    Returns:
        str: Komunikat potwierdzający usunięcie lub informacja o błędzie.
    """
    print(f"DEBUG: Wywołuję narzędzie 'delete_task' dla zadań ID: {task_ids}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(task_ids))
        query = f"DELETE FROM tasks WHERE id IN ({placeholders})"
        cursor.execute(query, tuple(task_ids))
        if cursor.rowcount == 0:
            conn.close()
            return f"Nie znaleziono zadań o podanych ID."
        
        conn.commit()
        conn.close()
        return f"Pomyślnie usunięto {cursor.rowcount} zadań."
    except Exception as e:
        return f"Wystąpił błąd podczas usuwania zadań: {e}" 