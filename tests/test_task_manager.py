import pytest
from modules.task_manager import TaskManager

def test_initialization():
    """Testuje, czy TaskManager jest tworzony z pustą listą zadań."""
    tm = TaskManager()
    assert tm.list_tasks() == "Brak zadań."

def test_add_task():
    """Testuje, czy można dodać pojedyncze zadanie."""
    tm = TaskManager()
    task_description = "Nauczyć się pisać testy w pytest"
    response = tm.add_task(task_description)
    
    assert response == f"Dodano zadanie: {task_description}"
    # Sprawdzamy, czy zadanie faktycznie jest na liście
    assert task_description in tm.list_tasks()

def test_add_multiple_tasks():
    """Testuje, czy można dodać wiele zadań i czy są poprawnie listowane."""
    tm = TaskManager()
    task1 = "Zadanie 1"
    task2 = "Zadanie 2"
    
    tm.add_task(task1)
    tm.add_task(task2)
    
    listed_tasks = tm.list_tasks()
    assert "1. Zadanie 1" in listed_tasks
    assert "2. Zadanie 2" in listed_tasks

def test_list_tasks_format():
    """Testuje, czy format listowania zadań jest poprawny."""
    tm = TaskManager()
    tm.add_task("Zrobić zakupy")
    
    expected_output = "Lista zadań:\n1. Zrobić zakupy"
    assert tm.list_tasks() == expected_output 