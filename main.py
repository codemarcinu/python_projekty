"""
Główny moduł aplikacji AI Assistant.
Zawiera punkt wejścia i konfigurację serwera.
"""

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dependency_injector.wiring import inject, Provide

from core.container import Container
from interfaces.web_ui import router as web_router, RateLimitMiddleware
from interfaces.api import router as api_router
from utils.logging import setup_logging

def create_app() -> FastAPI:
    """Tworzy i konfiguruje instancję aplikacji FastAPI."""
    
    # Inicjalizacja kontenera DI
    container = Container()
    
    # Inicjalizacja aplikacji FastAPI
    app = FastAPI(
        title="AI Assistant",
        description="Asystent AI wykorzystujący lokalne modele LLM",
        version="1.0.0"
    )

    # Konfiguracja CORS Middleware
    origins = ["*"]  # Na etapie deweloperskim pozwalamy na wszystkie źródła

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Dodanie Rate Limit Middleware
    app.add_middleware(RateLimitMiddleware)

    # Montowanie plików statycznych
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Podłączenie routerów
    app.include_router(web_router, prefix="/web", tags=["web"])
    app.include_router(api_router, prefix="/api", tags=["api"])
    
    # Przekierowanie ze strony głównej do interfejsu czatu
    @app.get("/")
    async def root():
        return RedirectResponse(url="/web/chat")
    
    # Wire the container to the application
    container.wire(modules=[__name__])
    
    return app

# Tworzymy instancję aplikacji globalnie
app = create_app()

class ConfigManager:
    def load_config(self):
        # Load configuration logic here
        pass

config_manager = ConfigManager()

@app.on_event("startup")
async def startup_event():
    config_manager.load_config()
    logging.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutdown complete.")
