"""
Główny moduł aplikacji AI Assistant.
Zawiera punkt wejścia i konfigurację serwera.
"""

import typer
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from interfaces import web_ui, api

# Initialize FastAPI app
app = FastAPI(
    title="AI Assistant",
    description="Asystent AI wykorzystujący lokalne modele LLM",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(web_ui.router, prefix="/web", tags=["web"])
app.include_router(api.router, prefix="/api", tags=["api"])

# Create Typer app
cli = typer.Typer()

@cli.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False
):
    """
    Uruchamia serwer FastAPI.
    
    Args:
        host: Host do nasłuchiwania
        port: Port do nasłuchiwania
        reload: Czy włączyć auto-reload
    """
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        ws_max_size=1024 * 1024 * 10,  # 10MB
        ws_ping_interval=20.0,
        ws_ping_timeout=20.0
    )

if __name__ == "__main__":
    cli()
