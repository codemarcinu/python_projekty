import pytest
from app.core.config import settings
import os

def test_settings_initialization():
    assert settings is not None
    assert hasattr(settings, "PROJECT_NAME")
    assert hasattr(settings, "VERSION")
    assert hasattr(settings, "API_V1_STR")
    assert hasattr(settings, "SECRET_KEY")
    assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")
    assert hasattr(settings, "ALGORITHM")
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "OLLAMA_BASE_URL")
    assert hasattr(settings, "OLLAMA_MODEL")

def test_settings_values():
    assert settings.PROJECT_NAME == "Python Projekty"
    assert settings.VERSION == "0.1.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.SECRET_KEY is not None
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings.ALGORITHM == "HS256"
    assert settings.DATABASE_URL is not None
    assert settings.OLLAMA_BASE_URL == "http://localhost:11434"
    assert settings.OLLAMA_MODEL == "llama2"

def test_settings_environment_variables():
    # Test that environment variables are properly loaded
    os.environ["SECRET_KEY"] = "test_secret_key"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["OLLAMA_BASE_URL"] = "http://test:11434"
    os.environ["OLLAMA_MODEL"] = "test_model"
    
    # Reload settings
    from app.core.config import Settings
    test_settings = Settings()
    
    assert test_settings.SECRET_KEY == "test_secret_key"
    assert test_settings.DATABASE_URL == "sqlite:///./test.db"
    assert test_settings.OLLAMA_BASE_URL == "http://test:11434"
    assert test_settings.OLLAMA_MODEL == "test_model"
    
    # Clean up
    del os.environ["SECRET_KEY"]
    del os.environ["DATABASE_URL"]
    del os.environ["OLLAMA_BASE_URL"]
    del os.environ["OLLAMA_MODEL"]

def test_settings_default_values():
    # Test that default values are used when environment variables are not set
    from app.core.config import Settings
    test_settings = Settings()
    
    assert test_settings.PROJECT_NAME == "Python Projekty"
    assert test_settings.VERSION == "0.1.0"
    assert test_settings.API_V1_STR == "/api/v1"
    assert test_settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert test_settings.ALGORITHM == "HS256"
    assert test_settings.OLLAMA_BASE_URL == "http://localhost:11434"
    assert test_settings.OLLAMA_MODEL == "llama2"

def test_settings_validation():
    # Test that validation works properly
    from app.core.config import Settings
    from pydantic import ValidationError
    
    # Test with invalid DATABASE_URL
    with pytest.raises(ValidationError):
        Settings(DATABASE_URL="invalid_url")
    
    # Test with invalid OLLAMA_BASE_URL
    with pytest.raises(ValidationError):
        Settings(OLLAMA_BASE_URL="invalid_url")
    
    # Test with invalid ACCESS_TOKEN_EXPIRE_MINUTES
    with pytest.raises(ValidationError):
        Settings(ACCESS_TOKEN_EXPIRE_MINUTES=-1)
    
    # Test with invalid ALGORITHM
    with pytest.raises(ValidationError):
        Settings(ALGORITHM="invalid_algorithm")

def test_settings_singleton():
    # Test that settings is a singleton
    from app.core.config import Settings
    
    settings1 = Settings()
    settings2 = Settings()
    
    assert settings1 is settings2

def test_settings_immutable():
    # Test that settings is immutable
    with pytest.raises(AttributeError):
        settings.PROJECT_NAME = "New Project Name"
    
    with pytest.raises(AttributeError):
        settings.VERSION = "1.0.0"
    
    with pytest.raises(AttributeError):
        settings.API_V1_STR = "/api/v2"
    
    with pytest.raises(AttributeError):
        settings.SECRET_KEY = "new_secret_key"
    
    with pytest.raises(AttributeError):
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60
    
    with pytest.raises(AttributeError):
        settings.ALGORITHM = "RS256"
    
    with pytest.raises(AttributeError):
        settings.DATABASE_URL = "postgresql://user:pass@localhost/db"
    
    with pytest.raises(AttributeError):
        settings.OLLAMA_BASE_URL = "http://new:11434"
    
    with pytest.raises(AttributeError):
        settings.OLLAMA_MODEL = "new_model" 