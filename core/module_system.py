"""
System modułów dla aplikacji AI.

Ten moduł zapewnia mechanizm dynamicznego ładowania i zarządzania modułami
rozszerzającymi funkcjonalność aplikacji.
"""

from typing import Dict, Callable, Any, List
import importlib
import os
import functools
from functools import wraps

# Słownik przechowujący zarejestrowane narzędzia
_tools: Dict[str, Callable] = {}

def tool(func: Callable) -> Callable:
    """
    Dekorator do rejestrowania funkcji jako narzędzia, który poprawnie
    zachowuje metadane funkcji (w tym jej sygnaturę i argumenty).
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Ten "opakowujący" kod jest potrzebny, aby @functools.wraps działał poprawnie.
        # Po prostu wywołuje on oryginalną funkcję z jej argumentami.
        return func(*args, **kwargs)
    
    # Rejestrujemy nową funkcję 'wrapper', która zachowuje metadane oryginału
    _tools[func.__name__] = wrapper
    return wrapper

def get_tool(name: str) -> Callable:
    """Zwraca funkcję narzędzia na podstawie jego nazwy.
    
    Args:
        name (str): Nazwa narzędzia do pobrania.
        
    Returns:
        Callable: Funkcja narzędzia.
        
    Raises:
        KeyError: Jeśli narzędzie o podanej nazwie nie istnieje.
    """
    if name not in _tools:
        raise KeyError(f"Narzędzie '{name}' nie zostało znalezione")
    return _tools[name]

def get_available_tools() -> List[str]:
    """Zwraca listę nazw wszystkich dostępnych narzędzi.
    
    Returns:
        List[str]: Lista nazw zarejestrowanych narzędzi.
    """
    return list(_tools.keys())

def load_modules(module_dir: str) -> None:
    """Dynamicznie ładuje wszystkie moduły .py z podanego katalogu.
    
    Args:
        module_dir (str): Ścieżka do katalogu zawierającego moduły.
        
    Raises:
        ImportError: Jeśli wystąpi błąd podczas importowania modułu.
        FileNotFoundError: Jeśli katalog modułów nie istnieje.
    """
    # Sprawdzenie czy katalog istnieje
    if not os.path.exists(module_dir):
        raise FileNotFoundError(f"Katalog modułów '{module_dir}' nie istnieje")
    
    # Iteracja po wszystkich plikach .py w katalogu
    for filename in os.listdir(module_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]  # Usunięcie rozszerzenia .py
            try:
                # Dynamiczny import modułu
                importlib.import_module(f"{module_dir.replace('/', '.')}.{module_name}")
            except ImportError as e:
                print(f"Błąd podczas ładowania modułu {module_name}: {str(e)}")
                raise
