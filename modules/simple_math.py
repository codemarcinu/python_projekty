from core.module_system import tool

@tool
def add(a: int, b: int) -> int:
    """
    Dodaje dwie liczby całkowite do siebie.
    Użyj tego narzędzia, gdy użytkownik prosi o zsumowanie dwóch liczb.
    
    :param a: Pierwsza liczba do dodania.
    :param b: Druga liczba do dodania.
    :return: Suma liczb a i b.
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