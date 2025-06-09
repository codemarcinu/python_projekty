from fastapi import FastAPI, Request, Response, status
import time
from typing import Dict, List, Tuple
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimiter:
    """Implementacja mechanizmu rate limiting."""
    
    def __init__(self, rate_limit: int = 10, time_window: int = 60):
        """
        Args:
            rate_limit: Maksymalna liczba requestów w oknie czasowym
            time_window: Okno czasowe w sekundach
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.request_log: Dict[str, List[datetime]] = {}
        self._cleanup_task = None
        self._lock = asyncio.Lock()
    
    async def start_cleanup(self):
        """Uruchamia zadanie czyszczące stare logi requestów."""
        self._cleanup_task = asyncio.create_task(self._cleanup_old_requests())
    
    async def _cleanup_old_requests(self):
        """Okresowo czyści stare requesty."""
        while True:
            await asyncio.sleep(self.time_window)
            async with self._lock:
                current_time = datetime.now()
                for ip, timestamps in list(self.request_log.items()):
                    # Usuń timestampy starsze niż okno czasowe
                    self.request_log[ip] = [
                        ts for ts in timestamps 
                        if current_time - ts < timedelta(seconds=self.time_window)
                    ]
                    # Usuń puste wpisy
                    if not self.request_log[ip]:
                        del self.request_log[ip]
    
    async def is_rate_limited(self, ip: str) -> Tuple[bool, int]:
        """
        Sprawdza czy adres IP przekroczył limit requestów.
        
        Args:
            ip: Adres IP klienta
            
        Returns:
            Tuple[bool, int]: (czy_limitowany, pozostały_czas)
        """
        async with self._lock:
            current_time = datetime.now()
            
            # Dodaj aktualny timestamp do logów
            if ip not in self.request_log:
                self.request_log[ip] = []
            
            # Usuń stare requesty
            self.request_log[ip] = [
                ts for ts in self.request_log[ip] 
                if current_time - ts < timedelta(seconds=self.time_window)
            ]
            
            # Sprawdź limit
            if len(self.request_log[ip]) >= self.rate_limit:
                oldest_request = min(self.request_log[ip])
                reset_time = int((oldest_request + timedelta(seconds=self.time_window) - current_time).total_seconds())
                return True, reset_time
            
            # Dodaj aktualny timestamp
            self.request_log[ip].append(current_time)
            return False, 0

def setup_rate_limiting(app: FastAPI, rate_limiter: RateLimiter):
    """Konfiguruje middleware do ograniczania requestów."""
    
    @app.middleware("http")
    async def rate_limiting_middleware(request: Request, call_next):
        # Pobierz adres IP
        ip = request.client.host if request.client else "unknown"
        
        # Sprawdź limit
        is_limited, reset_time = await rate_limiter.is_rate_limited(ip)
        if is_limited:
            logger.warning(
                f"Rate limit exceeded for IP {ip}",
                extra={
                    "ip": ip,
                    "reset_time": reset_time,
                    "path": request.url.path
                }
            )
            return Response(
                content={"error": "Rate limit exceeded"},
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(reset_time)}
            )
        
        # Kontynuuj request
        return await call_next(request) 