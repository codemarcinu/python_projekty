"""
Moduł zawierający podstawowe operacje matematyczne.
"""

from core.module_system import tool

@tool
def add(a: float, b: float) -> float:
    """
    Dodaje dwie liczby.
    
    Args:
        a: Pierwsza liczba
        b: Druga liczba
        
    Returns:
        Suma liczb a i b
    """
    print(f"DEBUG: Wywołuję narzędzie 'add' z argumentami a={a}, b={b}")
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """
    Mnoży przez siebie dwie liczby całkowite.
    Użyj tego narzędzia, gdy użytkownik prosi o pomnożenie dwóch liczb.

    :param a: Pierwsza liczba.
    :param b: Druga liczba.
    :return: Iloczyn liczb a i b.
    """
    print(f"DEBUG: Wywołuję narzędzie 'multiply' z argumentami a={a}, b={b}")
    return a * b

def subtract(a: float, b: float) -> float:
    """
    Odejmuje drugą liczbę od pierwszej.
    
    Args:
        a: Liczba, od której odejmujemy
        b: Liczba, którą odejmujemy
        
    Returns:
        Różnica liczb a i b
    """
    return a - b 