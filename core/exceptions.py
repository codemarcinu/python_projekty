"""
Moduł zawierający niestandardowe wyjątki używane w aplikacji.

Ten moduł definiuje wszystkie niestandardowe wyjątki używane w różnych
częściach aplikacji, zapewniając spójną obsługę błędów.
"""

class AIEngineError(Exception):
    """Wyjątek występujący podczas pracy silnika AI."""
    pass


class ConversationError(Exception):
    """Wyjątek występujący podczas obsługi konwersacji."""
    pass


class DatabaseError(Exception):
    """Wyjątek występujący podczas operacji na bazie danych."""
    pass


class ConfigError(Exception):
    """Wyjątek występujący podczas obsługi konfiguracji."""
    pass 