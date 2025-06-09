"""
Moduł narzędzia do obsługi daty i czasu.

Ten moduł dostarcza funkcjonalność do sprawdzania aktualnej daty i godziny.
"""

from datetime import datetime
from core.plugin_system import tool


@tool
def get_current_datetime() -> str:
    """
    Zwraca aktualną datę i godzinę.
    Użyj tego narzędzia, gdy użytkownik pyta o czas, datę, który jest dzisiaj dzień, jaka jest godzina itp.
    
    :return: Sformatowany ciąg znaków z aktualną datą i godziną.
    """
    now = datetime.now()
    # Format: Dzień tygodnia, dzień miesiąca rok, godzina:minuta
    formatted_now = now.strftime("%A, %d %B %Y, %H:%M")
    print(f"DEBUG: Wywołuję narzędzie 'get_current_datetime'. Zwracam: {formatted_now}")
    return formatted_now 