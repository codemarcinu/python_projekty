"""
Implementacja szyny zdarzeń (Event Bus) dla systemu komunikacji między modułami.

Ten moduł dostarcza mechanizm publikacji/subskrypcji zdarzeń, który umożliwia
luźne powiązanie między różnymi komponentami systemu. Implementacja jest
bezpieczna wątkowo i wykorzystuje wzorzec Singleton.
"""

from collections import defaultdict
from typing import Any, Callable, Dict, List
import threading
from functools import wraps


def singleton(cls):
    """
    Dekorator implementujący wzorzec Singleton.
    
    Args:
        cls: Klasa do której ma zostać zastosowany wzorzec Singleton.
    
    Returns:
        Callable: Funkcja wrapper zapewniająca pojedynczą instancję klasy.
    """
    instances = {}
    lock = threading.Lock()

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class EventBus:
    """
    Implementacja szyny zdarzeń (Event Bus) z obsługą wielu subskrybentów.
    
    Klasa zapewnia mechanizm publikacji/subskrypcji zdarzeń, który umożliwia
    komunikację między różnymi komponentami systemu. Implementacja jest
    bezpieczna wątkowo i wykorzystuje wzorzec Singleton.
    
    Attributes:
        listeners (Dict[str, List[Callable]]): Słownik przechowujący listy callbacków
            dla poszczególnych typów zdarzeń.
        _lock (threading.Lock): Blokada zapewniająca bezpieczeństwo wątków.
    """
    
    def __init__(self) -> None:
        """
        Inicjalizuje nową instancję EventBus.
        
        Tworzy pusty słownik słuchaczy i inicjalizuje blokadę wątków.
        """
        self.listeners: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Rejestruje nowy callback dla określonego typu zdarzenia.
        
        Args:
            event_type (str): Typ zdarzenia, na które callback ma reagować.
            callback (Callable): Funkcja, która zostanie wywołana przy wystąpieniu zdarzenia.
        
        Raises:
            ValueError: Jeśli callback nie jest callable.
        """
        if not callable(callback):
            raise ValueError("Callback musi być callable")
            
        with self._lock:
            if callback not in self.listeners[event_type]:
                self.listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        Usuwa callback z listy słuchaczy dla określonego typu zdarzenia.
        
        Args:
            event_type (str): Typ zdarzenia.
            callback (Callable): Funkcja do usunięcia z listy słuchaczy.
        """
        with self._lock:
            if event_type in self.listeners and callback in self.listeners[event_type]:
                self.listeners[event_type].remove(callback)
    
    def emit(self, event_type: str, *args: Any, **kwargs: Any) -> None:
        """
        Emituje zdarzenie do wszystkich zarejestrowanych słuchaczy.
        
        Metoda wywołuje wszystkie callbacki zarejestrowane dla danego typu zdarzenia,
        przekazując im dodatkowe argumenty.
        
        Args:
            event_type (str): Typ emitowanego zdarzenia.
            *args: Pozycyjne argumenty przekazywane do callbacków.
            **kwargs: Nazwane argumenty przekazywane do callbacków.
        """
        # Tworzymy kopię listy słuchaczy, aby uniknąć problemów z modyfikacją
        # podczas iteracji
        with self._lock:
            listeners = self.listeners[event_type].copy()
        
        # Wywołujemy callbacki poza blokadą, aby uniknąć deadlocków
        for callback in listeners:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                # Logowanie błędu bez przerywania wykonania innych callbacków
                print(f"Błąd w callbacku dla zdarzenia {event_type}: {str(e)}")
    
    def clear(self, event_type: str | None = None) -> None:
        """
        Czyści wszystkie lub wybrane słuchacze zdarzeń.
        
        Args:
            event_type (str | None, optional): Typ zdarzenia do wyczyszczenia.
                Jeśli None, czyści wszystkie zdarzenia.
        """
        with self._lock:
            if event_type is None:
                self.listeners.clear()
            elif event_type in self.listeners:
                self.listeners[event_type].clear()
