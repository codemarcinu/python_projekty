"""
Główny plik uruchomieniowy aplikacji.
Uruchamia serwer FastAPI na porcie 8000.
"""

import uvicorn
from interfaces.api import app

if __name__ == "__main__":
    print("Uruchamianie serwera API Asystenta AI...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
