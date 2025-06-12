"""
Moduł zarządzania sesjami.
"""

from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import uuid
import logging
from core.config import get_settings

logger = logging.getLogger(__name__)

class Session(BaseModel):
    """Model sesji."""
    id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    data: Dict[str, Any]

class SessionManager:
    """Klasa zarządzająca sesjami."""
    
    def __init__(self):
        self.settings = get_settings()
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = timedelta(minutes=30)
        
    def _create_session(
        self,
        user_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Tworzy nową sesję."""
        now = datetime.now()
        
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=now,
            expires_at=now + self.session_timeout,
            last_activity=now,
            data=data or {}
        )
        
        self.sessions[session.id] = session
        return session
        
    async def create_session(
        self,
        user_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Session]:
        """Tworzy nową sesję."""
        try:
            return self._create_session(user_id, data)
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
            
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Pobiera sesję."""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return None
                
            # Sprawdź czy sesja nie wygasła
            if datetime.now() > session.expires_at:
                await self.delete_session(session_id)
                return None
                
            # Aktualizuj ostatnią aktywność
            session.last_activity = datetime.now()
            session.expires_at = session.last_activity + self.session_timeout
            
            return session
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
            
    async def delete_session(self, session_id: str) -> bool:
        """Usuwa sesję."""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
            
    async def update_session_data(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> Optional[Session]:
        """Aktualizuje dane sesji."""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return None
                
            session.data.update(data)
            session.last_activity = datetime.now()
            session.expires_at = session.last_activity + self.session_timeout
            
            return session
            
        except Exception as e:
            logger.error(f"Error updating session data: {e}")
            return None
            
    async def cleanup_expired_sessions(self) -> int:
        """Usuwa wygasłe sesje."""
        try:
            now = datetime.now()
            expired = [
                session_id for session_id, session in self.sessions.items()
                if now > session.expires_at
            ]
            
            for session_id in expired:
                await self.delete_session(session_id)
                
            return len(expired)
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
            
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Zwraca listę sesji użytkownika."""
        try:
            return [
                session for session in self.sessions.values()
                if session.user_id == user_id
            ]
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
            
    async def delete_user_sessions(self, user_id: str) -> int:
        """Usuwa wszystkie sesje użytkownika."""
        try:
            sessions = await self.get_user_sessions(user_id)
            count = 0
            
            for session in sessions:
                if await self.delete_session(session.id):
                    count += 1
                    
            return count
            
        except Exception as e:
            logger.error(f"Error deleting user sessions: {e}")
            return 0 