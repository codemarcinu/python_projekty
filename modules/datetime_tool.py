"""
Moduł narzędzia do obsługi daty i czasu.

Ten moduł dostarcza funkcjonalność do sprawdzania aktualnej daty i godziny.
Jest to jedyne wiarygodne źródło informacji o czasie w systemie.
"""

from datetime import datetime
import logging
from core.module_system import tool

logger = logging.getLogger(__name__)

@tool
def get_current_datetime() -> str:
    """
    ZAWSZE używaj tej funkcji, aby uzyskać aktualną datę i godzinę.
    Jest to jedyne wiarygodne źródło informacji o czasie w systemie.
    Użyj jej w odpowiedzi na pytania o:
    - dzisiejszą datę
    - aktualny czas
    - godzinę
    - dzień tygodnia
    - który jest dzień miesiąca
    - który jest rok
    
    NIE odpowiadaj na podstawie swojej wiedzy - ZAWSZE używaj tego narzędzia!
    
    :return: Sformatowany ciąg znaków z aktualną datą i godziną.
    """
    now = datetime.now()
    # Format: Dzień tygodnia, dzień miesiąca rok, godzina:minuta
    formatted_now = now.strftime("%A, %d %B %Y, %H:%M")
    logger.info(f"Wywołuję narzędzie 'get_current_datetime'. Zwracam: {formatted_now}")
    return formatted_now 