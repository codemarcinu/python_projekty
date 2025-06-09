import json
import hashlib
from typing import Any, Optional, Callable, TypeVar, Dict, Awaitable, cast
import redis.asyncio as redis
from functools import wraps
import inspect
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Typ dla funkcji, która może być cachowana
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Awaitable[Any]])

class RedisCache:
    """Implementacja cache'owania z użyciem Redis."""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """
        Args:
            redis_url: URL połączenia do Redis
            default_ttl: Domyślny czas życia cache'a w sekundach
        """
        self.redis = redis.from_url(redis_url)
        self.default_ttl = default_ttl
        logger.info(f"Initialized Redis cache with TTL {default_ttl}s")
    
    async def get(self, key: str) -> Optional[str]:
        """Pobiera wartość z cache'a."""
        try:
            value = await self.redis.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            return value
        except Exception as e:
            logger.error(f"Error getting value from cache: {str(e)}")
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Zapisuje wartość do cache'a."""
        try:
            if ttl is None:
                ttl = self.default_ttl
            await self.redis.set(key, value, ex=ttl)
            logger.debug(f"Set cache for key: {key} with TTL {ttl}s")
        except Exception as e:
            logger.error(f"Error setting value in cache: {str(e)}")
    
    async def delete(self, key: str) -> None:
        """Usuwa wartość z cache'a."""
        try:
            await self.redis.delete(key)
            logger.debug(f"Deleted cache for key: {key}")
        except Exception as e:
            logger.error(f"Error deleting value from cache: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        """Sprawdza czy klucz istnieje w cache'u."""
        try:
            exists = bool(await self.redis.exists(key))
            logger.debug(f"Checked existence for key: {key} - {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking key existence in cache: {str(e)}")
            return False
    
    def cached(self, ttl: Optional[int] = None):
        """
        Dekorator do cache'owania wyników funkcji.
        
        Args:
            ttl: Czas życia cache'a w sekundach (opcjonalny)
        """
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Stwórz unikalny klucz cache'a
                cache_key = self._create_cache_key(func, args, kwargs)
                
                # Sprawdź czy wynik jest w cache'u
                cached_result = await self.get(cache_key)
                if cached_result:
                    try:
                        return json.loads(cached_result)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding cached value: {str(e)}")
                        await self.delete(cache_key)
                
                # Wykonaj funkcję
                result = await func(*args, **kwargs)
                
                # Zapisz wynik do cache'a
                try:
                    await self.set(
                        cache_key, 
                        json.dumps(result), 
                        ttl=ttl or self.default_ttl
                    )
                except Exception as e:
                    logger.error(f"Error caching result: {str(e)}")
                
                return result
            return cast(F, wrapper)
        return decorator
    
    def _create_cache_key(self, func: Callable, args: tuple, kwargs: Dict) -> str:
        """
        Tworzy unikalny klucz cache'a dla funkcji i jej argumentów.
        
        Args:
            func: Funkcja do cache'owania
            args: Argumenty pozycyjne
            kwargs: Argumenty nazwane
            
        Returns:
            str: Unikalny klucz cache'a
        """
        # Pobierz nazwy argumentów
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Stwórz klucz na podstawie nazwy funkcji i argumentów
        key_parts = [
            f"{func.__module__}.{func.__name__}",
            json.dumps(bound_args.arguments, sort_keys=True)
        ]
        
        # Utwórz hash
        key = hashlib.md5(json.dumps(key_parts).encode()).hexdigest()
        
        return f"cache:{key}" 