"""
Główny plik uruchomieniowy aplikacji.
Uruchamia serwer FastAPI na porcie 8000.
"""

import uvicorn
from interfaces.api import app
from core.config_manager import settings

if __name__ == "__main__":
    print("Uruchamianie serwera API Asystenta AI...")
    print(f"🔌 Serwer uruchomiony. Korzystam z modelu: {settings.LLM_MODEL}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
