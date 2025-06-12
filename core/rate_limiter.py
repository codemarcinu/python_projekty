"""
Moduł zarządzania rate limitingiem.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import logging
from core.logger import get_logger
from core.exceptions import RateLimitError

logger = get_logger(__name__)

class RateLimiter:
    """Klasa zarządzająca limitami zapytań."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        
        # Słowniki przechowujące liczniki zapytań
        self.minute_requests: Dict[str, list] = {}
        self.hour_requests: Dict[str, list] = {}
        self.day_requests: Dict[str, list] = {}
        
        # Lock do synchronizacji
        self._lock = asyncio.Lock()
        
    async def _cleanup_old_requests(self, client_id: str):
        """Usuwa stare zapytania."""
        now = datetime.now()
        
        # Czyszczenie zapytań z ostatniej minuty
        if client_id in self.minute_requests:
            self.minute_requests[client_id] = [
                ts for ts in self.minute_requests[client_id]
                if now - ts < timedelta(minutes=1)
            ]
            
        # Czyszczenie zapytań z ostatniej godziny
        if client_id in self.hour_requests:
            self.hour_requests[client_id] = [
                ts for ts in self.hour_requests[client_id]
                if now - ts < timedelta(hours=1)
            ]
            
        # Czyszczenie zapytań z ostatniego dnia
        if client_id in self.day_requests:
            self.day_requests[client_id] = [
                ts for ts in self.day_requests[client_id]
                if now - ts < timedelta(days=1)
            ]
            
    async def check_rate_limit(self, client_id: str) -> Tuple[bool, Optional[str]]:
        """Sprawdza limity zapytań.
        
        Args:
            client_id: ID klienta
            
        Returns:
            Tuple[bool, Optional[str]]: (czy_przekroczono_limit, komunikat_błędu)
        """
        async with self._lock:
            now = datetime.now()
            
            # Inicjalizacja list jeśli nie istnieją
            if client_id not in self.minute_requests:
                self.minute_requests[client_id] = []
            if client_id not in self.hour_requests:
                self.hour_requests[client_id] = []
            if client_id not in self.day_requests:
                self.day_requests[client_id] = []
                
            # Czyszczenie starych zapytań
            await self._cleanup_old_requests(client_id)
            
            # Sprawdzanie limitów
            if len(self.minute_requests[client_id]) >= self.requests_per_minute:
                return True, "Rate limit exceeded: too many requests per minute"
                
            if len(self.hour_requests[client_id]) >= self.requests_per_hour:
                return True, "Rate limit exceeded: too many requests per hour"
                
            if len(self.day_requests[client_id]) >= self.requests_per_day:
                return True, "Rate limit exceeded: too many requests per day"
                
            # Dodanie nowego zapytania
            self.minute_requests[client_id].append(now)
            self.hour_requests[client_id].append(now)
            self.day_requests[client_id].append(now)
            
            return False, None
            
    async def get_rate_limit_info(self, client_id: str) -> Dict[str, int]:
        """Zwraca informacje o limitach zapytań."""
        async with self._lock:
            await self._cleanup_old_requests(client_id)
            
            return {
                "minute_requests": len(self.minute_requests.get(client_id, [])),
                "hour_requests": len(self.hour_requests.get(client_id, [])),
                "day_requests": len(self.day_requests.get(client_id, [])),
                "minute_limit": self.requests_per_minute,
                "hour_limit": self.requests_per_hour,
                "day_limit": self.requests_per_day
            }
            
    async def reset_rate_limits(self, client_id: str):
        """Resetuje limity zapytań dla klienta."""
        async with self._lock:
            if client_id in self.minute_requests:
                del self.minute_requests[client_id]
            if client_id in self.hour_requests:
                del self.hour_requests[client_id]
            if client_id in self.day_requests:
                del self.day_requests[client_id]
                
    async def update_limits(
        self,
        requests_per_minute: Optional[int] = None,
        requests_per_hour: Optional[int] = None,
        requests_per_day: Optional[int] = None
    ):
        """Aktualizuje limity zapytań."""
        async with self._lock:
            if requests_per_minute is not None:
                self.requests_per_minute = requests_per_minute
            if requests_per_hour is not None:
                self.requests_per_hour = requests_per_hour
            if requests_per_day is not None:
                self.requests_per_day = requests_per_day
                
    async def cleanup(self):
        """Czyści wszystkie limity."""
        async with self._lock:
            self.minute_requests.clear()
            self.hour_requests.clear()
            self.day_requests.clear() 