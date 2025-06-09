"""
Moduł implementujący API REST dla asystenta AI.
Wykorzystuje FastAPI do obsługi zapytań HTTP.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict

# Importujemy nasz gotowy silnik AI i menedżera konwersacji
from core.ai_engine import AIEngine
from core.conversation_handler import ConversationHandler

# --- Definicja modeli danych (co przyjmujemy i co zwracamy) ---
class ChatRequest(BaseModel):
    prompt: str
    history: List[Dict[str, str]]

class ChatResponse(BaseModel):
    reply: str
    history: List[Dict[str, str]]

# --- Inicjalizacja aplikacji i silnika AI ---
app = FastAPI(title="Lokalny Asystent AI API")

# Montujemy katalog static do obsługi plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

# Tworzymy jedną, globalną instancję silnika, która będzie używana przez wszystkich
# To wydajne, bo wtyczki ładują się tylko raz.
engine = AIEngine()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    """
    Endpoint główny serwujący stronę HTML interfejsu użytkownika.
    """
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Główny endpoint do prowadzenia rozmowy z asystentem AI.
    """
    # Dla każdego zapytania tworzymy nową, tymczasową historię
    # i wypełniamy ją historią przesłaną z frontendu.
    handler = ConversationHandler()
    for message in request.history:
        handler.add_message(role=message['role'], content=message['content'])
    handler.add_message(role="user", content=request.prompt)

    # Przetwarzamy zapytanie przez nasz silnik AI
    response_text = engine.process_turn(handler.get_history())

    # Dodajemy odpowiedź AI do historii
    handler.add_message(role="assistant", content=response_text)

    # Odsyłamy odpowiedź i zaktualizowaną historię
    return ChatResponse(reply=response_text, history=handler.get_history())
