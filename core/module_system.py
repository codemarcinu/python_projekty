"""
System modułów dla aplikacji AI.

Ten moduł zapewnia mechanizm dynamicznego ładowania i zarządzania modułami
rozszerzającymi funkcjonalność aplikacji.
"""

from typing import Dict, Callable, Any, List, Union, Type
import importlib
import importlib.util
import os
import functools
from functools import wraps
import inspect
import sys
from core.tool_models import BaseTool

# Słownik przechowujący zarejestrowane narzędzia
_tools: Dict[str, Union[Callable, BaseTool]] = {}

def tool(func: Callable) -> Callable:
    """
    Dekorator do rejestrowania funkcji jako narzędzia, który poprawnie
    zachowuje metadane funkcji (w tym jej sygnaturę i argumenty).
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)
    
    _tools[func.__name__] = wrapper
    return wrapper

def register_tool(tool_instance: BaseTool) -> None:
    """
    Rejestruje instancję narzędzia w systemie.
    
    Args:
        tool_instance (BaseTool): Instancja narzędzia do zarejestrowania.
    """
    _tools[tool_instance.name] = tool_instance

def get_tool(name: str) -> Union[Callable, BaseTool]:
    """
    Zwraca narzędzie na podstawie jego nazwy.
    
    Args:
        name (str): Nazwa narzędzia do pobrania.
        
    Returns:
        Union[Callable, BaseTool]: Funkcja lub instancja narzędzia.
        
    Raises:
        KeyError: Jeśli narzędzie o podanej nazwie nie istnieje.
    """
    if name not in _tools:
        raise KeyError(f"Narzędzie '{name}' nie zostało znalezione")
    return _tools[name]

def get_available_tools() -> List[str]:
    """
    Zwraca listę nazw wszystkich dostępnych narzędzi.
    
    Returns:
        List[str]: Lista nazw zarejestrowanych narzędzi.
    """
    return list(_tools.keys())

def get_tool_descriptions() -> Dict[str, str]:
    """
    Zwraca słownik zawierający nazwy i opisy wszystkich dostępnych narzędzi.
    
    Returns:
        Dict[str, str]: Słownik {nazwa_narzędzia: opis_narzędzia}
    """
    descriptions = {}
    for name, tool in _tools.items():
        if isinstance(tool, BaseTool):
            descriptions[name] = tool.description
        else:
            # Dla funkcji używamy docstringa jako opisu
            descriptions[name] = tool.__doc__.strip() if tool.__doc__ else "No description available."
    return descriptions

def get_registered_tools() -> Dict[str, Union[Callable, BaseTool]]:
    """
    Zwraca słownik wszystkich zarejestrowanych narzędzi.
    
    Returns:
        Dict[str, Union[Callable, BaseTool]]: Słownik {nazwa_narzędzia: narzędzie}
    """
    return _tools.copy()

def load_modules(module_dir: str) -> None:
    """
    Dynamicznie ładuje wszystkie moduły .py z podanego katalogu.
    
    Args:
        module_dir (str): Ścieżka do katalogu zawierającego moduły.
        
    Raises:
        ImportError: Jeśli wystąpi błąd podczas importowania modułu.
        FileNotFoundError: Jeśli katalog modułów nie istnieje.
    """
    if not os.path.exists(module_dir):
        raise FileNotFoundError(f"Katalog modułów '{module_dir}' nie istnieje")
    
    # Dodaj katalog modułów do sys.path jeśli nie jest już dodany
    if module_dir not in sys.path:
        sys.path.append(module_dir)
    
    for filename in os.listdir(module_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]
            try:
                # Użyj importlib.util do ładowania modułu
                module_path = os.path.join(module_dir, filename)
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec is None:
                    raise ImportError(f"Nie można utworzyć specyfikacji dla modułu {module_name}")
                
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Szukamy klas dziedziczących po BaseTool
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        hasattr(obj, 'name') and 
                        hasattr(obj, 'description') and 
                        hasattr(obj, 'execute') and
                        obj != BaseTool):
                        # Tworzymy instancję i rejestrujemy narzędzie
                        tool_instance = obj()
                        register_tool(tool_instance)
                        print(f"Zarejestrowano narzędzie: {tool_instance.name}")
                
            except Exception as e:
                print(f"Błąd podczas ładowania modułu {module_name}: {str(e)}")
                raise
