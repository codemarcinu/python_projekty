"""
Moduł implementujący API REST dla asystenta AI.
Wykorzystuje FastAPI do obsługi zapytań HTTP.
"""

from fastapi import FastAPI

# Inicjalizacja aplikacji FastAPI
app = FastAPI(
    title="Asystent AI API",
    description="API dla lokalnego asystenta AI",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Endpoint główny zwracający informację o działaniu API."""
    return {"message": "API Asystenta AI działa!"}
