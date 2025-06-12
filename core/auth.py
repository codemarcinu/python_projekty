"""
Moduł autentykacji i autoryzacji.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
from passlib.context import CryptContext

# Konfiguracja
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Inicjalizacja
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modele
class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = None
    role: str = "user"

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Funkcje pomocnicze
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Weryfikuje hasło."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generuje hash hasła."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Tworzy token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Pobiera aktualnego użytkownika na podstawie tokenu."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Tutaj w prawdziwej aplikacji pobieralibyśmy użytkownika z bazy danych
    # Na potrzeby przykładu zwracamy mockowego użytkownika
    user = User(
        id="1",
        username=token_data.username,
        role="user"
    )
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Sprawdza czy użytkownik jest aktywny."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_permissions(user: User, required_role: str) -> bool:
    """Sprawdza uprawnienia użytkownika."""
    roles = {
        "admin": ["admin", "moderator", "user"],
        "moderator": ["moderator", "user"],
        "user": ["user"]
    }
    return required_role in roles.get(user.role, []) 