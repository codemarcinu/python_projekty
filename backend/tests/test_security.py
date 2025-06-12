import pytest
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
    get_current_active_user
)
from app.models.user import User
from app.core.config import settings
from datetime import timedelta
import uuid

def test_password_hashing():
    password = "test_password"
    hashed_password = get_password_hash(password)
    
    assert hashed_password != password
    assert verify_password(password, hashed_password)
    assert not verify_password("wrong_password", hashed_password)

def test_access_token_creation():
    user_id = str(uuid.uuid4())
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(minutes=15)
    )
    
    assert access_token is not None
    assert isinstance(access_token, str)
    assert len(access_token) > 0

def test_access_token_expiration():
    user_id = str(uuid.uuid4())
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(microseconds=1)
    )
    
    # Wait for token to expire
    import time
    time.sleep(0.1)
    
    # Test that token is expired
    with pytest.raises(Exception):
        get_current_user(access_token)

def test_get_current_user(db_session):
    # Create a user
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    # Get current user
    current_user = get_current_user(access_token)
    
    assert current_user is not None
    assert current_user.id == user.id
    assert current_user.name == user.name
    assert current_user.email == user.email
    assert current_user.role == user.role

def test_get_current_active_user(db_session):
    # Create an active user
    active_user = User(
        id=str(uuid.uuid4()),
        name="Active User",
        email="active@example.com",
        role="user",
        is_active=True
    )
    db_session.add(active_user)
    
    # Create an inactive user
    inactive_user = User(
        id=str(uuid.uuid4()),
        name="Inactive User",
        email="inactive@example.com",
        role="user",
        is_active=False
    )
    db_session.add(inactive_user)
    db_session.commit()
    
    # Create access tokens
    active_token = create_access_token(data={"sub": active_user.id})
    inactive_token = create_access_token(data={"sub": inactive_user.id})
    
    # Test active user
    current_active_user = get_current_active_user(active_token)
    assert current_active_user is not None
    assert current_active_user.id == active_user.id
    assert current_active_user.is_active is True
    
    # Test inactive user
    with pytest.raises(Exception):
        get_current_active_user(inactive_token)

def test_invalid_token():
    # Test with invalid token
    with pytest.raises(Exception):
        get_current_user("invalid_token")
    
    # Test with expired token
    user_id = str(uuid.uuid4())
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(microseconds=1)
    )
    import time
    time.sleep(0.1)
    with pytest.raises(Exception):
        get_current_user(access_token)
    
    # Test with invalid user ID
    access_token = create_access_token(data={"sub": "invalid_id"})
    with pytest.raises(Exception):
        get_current_user(access_token)

def test_token_payload():
    user_id = str(uuid.uuid4())
    access_token = create_access_token(data={"sub": user_id})
    
    # Test token payload
    from jose import jwt
    payload = jwt.decode(
        access_token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    
    assert payload["sub"] == user_id
    assert "exp" in payload
    assert "iat" in payload

def test_password_complexity():
    # Test password complexity requirements
    from app.core.security import validate_password
    
    # Test too short password
    with pytest.raises(ValueError):
        validate_password("short")
    
    # Test password without numbers
    with pytest.raises(ValueError):
        validate_password("password")
    
    # Test password without special characters
    with pytest.raises(ValueError):
        validate_password("password123")
    
    # Test valid password
    assert validate_password("Password123!") is True

def test_rate_limiting():
    from app.core.security import rate_limit
    
    # Test rate limiting
    @rate_limit(limit=2, period=1)
    def test_function():
        return True
    
    # First call should succeed
    assert test_function() is True
    
    # Second call should succeed
    assert test_function() is True
    
    # Third call should fail
    with pytest.raises(Exception):
        test_function()

def test_cors():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.core.security import configure_cors
    
    app = FastAPI()
    configure_cors(app)
    
    client = TestClient(app)
    
    # Test CORS headers
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

def test_security_headers():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.core.security import configure_security_headers
    
    app = FastAPI()
    configure_security_headers(app)
    
    client = TestClient(app)
    
    # Test security headers
    response = client.get("/")
    
    assert response.status_code == 404  # Because we didn't define any routes
    assert "x-content-type-options" in response.headers
    assert "x-frame-options" in response.headers
    assert "x-xss-protection" in response.headers
    assert "strict-transport-security" in response.headers
    assert "content-security-policy" in response.headers 