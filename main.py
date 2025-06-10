"""
Główny moduł aplikacji AI Assistant.
Zawiera punkt wejścia i konfigurację serwera.
"""

import typer
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dependency_injector.wiring import inject, Provide

from core.container import Container
from interfaces.web_ui import router as web_router
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

# Konfiguracja CLI z Typer
cli = typer.Typer()

@cli.command()
@inject
def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    log_level: str = "info",
    reload: bool = False,
    config_manager = Provide[Container.config_manager],
    llm_manager = Provide[Container.llm_manager],
    ai_engine = Provide[Container.ai_engine],
    rag_manager = Provide[Container.rag_manager]
):
    """
    Uruchamia serwer AI Assistant.
    
    Args:
        host: Host do nasłuchiwania
        port: Port do nasłuchiwania
        log_level: Poziom logowania
        reload: Czy włączyć auto-reload
    """
    setup_logging()
    logging.info("Starting AI Assistant server...")

    @app.on_event("startup")
    def startup_event():
        """Logika uruchamiana przy starcie aplikacji."""
        logging.info("Waiting for application startup.")
        try:
            config_manager.load_config()
            llm_manager.initialize_llm()
            ai_engine.setup_agent()
            rag_manager.initialize()
            logging.info("Application startup complete.")
        except Exception as e:
            logging.error(f"Error during application startup: {e}", exc_info=True)
            # W przyszłości można tu zaimplementować mechanizm, który zatrzyma serwer
    
    @app.on_event("shutdown")
    def shutdown_event():
        """Logika uruchamiana przy zamykaniu aplikacji."""
        logging.info("Waiting for application shutdown.")
        # Tutaj można dodać kod do czyszczenia zasobów, np. zamykanie połączeń
        logging.info("Application shutdown complete.")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
        ws_max_size=1024 * 1024 * 10,  # 10MB
        ws_ping_interval=20.0,
        ws_ping_timeout=20.0
    )

if __name__ == "__main__":
    cli()
