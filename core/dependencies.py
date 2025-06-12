"""
Moduł zarządzania zależnościami.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from core.auth import get_current_user, User
from core.llm_manager import LLMManager
from core.conversation import ConversationManager
from core.rag_manager import RAGManager
from core.file_manager import FileManager
from core.user_manager import UserManager
from core.session_manager import SessionManager
from core.config import get_settings
from core.exceptions import AuthenticationError, AuthorizationError

# Inicjalizacja menedżerów
_llm_manager: Optional[LLMManager] = None
_conversation_manager: Optional[ConversationManager] = None
_rag_manager: Optional[RAGManager] = None
_file_manager: Optional[FileManager] = None
_user_manager: Optional[UserManager] = None
_session_manager: Optional[SessionManager] = None

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_llm_manager() -> LLMManager:
    """Zwraca instancję menedżera LLM."""
    global _llm_manager
    if _llm_manager is None:
        settings = get_settings()
        _llm_manager = LLMManager(ollama_host=settings.OLLAMA_HOST)
        await _llm_manager.initialize()
    return _llm_manager

async def get_conversation_manager() -> ConversationManager:
    """Zwraca instancję menedżera konwersacji."""
    global _conversation_manager
    if _conversation_manager is None:
        llm_manager = await get_llm_manager()
        _conversation_manager = ConversationManager(llm_manager)
    return _conversation_manager

async def get_rag_manager() -> RAGManager:
    """Zwraca instancję menedżera RAG."""
    global _rag_manager
    if _rag_manager is None:
        settings = get_settings()
        _rag_manager = RAGManager(
            model_name=settings.EMBEDDING_MODEL,
            index_path=str(settings.FAISS_INDEX_PATH)
        )
        await _rag_manager.initialize()
    return _rag_manager

async def get_file_manager() -> FileManager:
    """Zwraca instancję menedżera plików."""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager

async def get_user_manager() -> UserManager:
    """Zwraca instancję menedżera użytkowników."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager

async def get_session_manager() -> SessionManager:
    """Zwraca instancję menedżera sesji."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Zwraca aktualnego aktywnego użytkownika."""
    if not current_user.is_active:
        raise AuthenticationError("Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Zwraca aktualnego użytkownika z uprawnieniami admina."""
    if current_user.role != "admin":
        raise AuthorizationError("Admin privileges required")
    return current_user

async def get_current_moderator_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Zwraca aktualnego użytkownika z uprawnieniami moderatora."""
    if current_user.role not in ["admin", "moderator"]:
        raise AuthorizationError("Moderator privileges required")
    return current_user

async def cleanup_managers():
    """Zamyka wszystkie menedżery."""
    global _llm_manager, _rag_manager
    
    if _llm_manager:
        await _llm_manager.close()
        
    if _rag_manager:
        await _rag_manager.close() 