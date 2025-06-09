"""
Moduł implementujący API REST dla asystenta AI.
Wykorzystuje FastAPI do obsługi zapytań HTTP oraz WebSocket do komunikacji w czasie rzeczywistym.
"""

import os
import shutil
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, AsyncGenerator, Optional

# Importujemy nasz gotowy silnik AI i menedżera konwersacji
from core.ai_engine import AIEngine
from core.conversation_handler import ConversationHandler
from core.config_manager import ConfigManager

# --- Definicja modeli danych (co przyjmujemy i co zwracamy) ---
class ChatRequest(BaseModel):
    prompt: str
    history: List[Dict[str, str]]

class ChatResponse(BaseModel):
    reply: str
    history: List[Dict[str, str]]

# --- Konfiguracja katalogów ---
UPLOADS_DIR = Path("data/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# --- Inicjalizacja aplikacji i silnika AI ---
app = FastAPI(title="Lokalny Asystent AI API")

# Montujemy katalog static do obsługi plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

# Tworzymy jedną, globalną instancję silnika, która będzie używana przez wszystkich
# To wydajne, bo wtyczki ładują się tylko raz.
config = ConfigManager()
engine = AIEngine(config)

@app.on_event("startup")
async def startup_event():
    """Funkcja wykonywana przy starcie serwera."""
    # Upewniamy się, że katalog uploads istnieje
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Katalog uploads gotowy: {UPLOADS_DIR}")

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket do obsługi komunikacji w czasie rzeczywistym z asystentem AI.
    
    Args:
        websocket (WebSocket): Obiekt połączenia WebSocket.
        
    Obsługuje:
        - Akceptację nowego połączenia
        - Odbieranie wiadomości od klienta
        - Przetwarzanie wiadomości przez silnik AI
        - Strumieniowanie odpowiedzi do klienta
        - Obsługę rozłączenia klienta
    """
    # Akceptujemy nowe połączenie
    await websocket.accept()
    
    # Tworzymy nowy handler konwersacji dla tego połączenia
    handler = ConversationHandler()
    
    try:
        while True:
            # Czekamy na wiadomość od klienta
            message = await websocket.receive_text()
            
            # Dodajemy wiadomość użytkownika do historii
            handler.add_message(role="user", content=message)
            
            # Przetwarzamy zapytanie przez silnik AI i strumieniujemy odpowiedź
            full_response = ""
            async for token in engine.process_turn_stream(handler.get_history()):
                await websocket.send_text(token)
                full_response += token
            
            # Dodajemy pełną odpowiedź do historii
            handler.add_message(role="assistant", content=full_response)
            
    except WebSocketDisconnect:
        # Obsługa rozłączenia klienta
        print("Klient rozłączony")
    except Exception as e:
        # Obsługa innych błędów
        error_message = f"Wystąpił błąd: {str(e)}"
        print(error_message)
        try:
            await websocket.send_text(error_message)
        except:
            pass  # Ignorujemy błędy wysyłania wiadomości o błędzie
        finally:
            await websocket.close()

@app.post("/upload-document/")
async def upload_document(file: UploadFile = File(...)) -> JSONResponse:
    """Endpoint do przesyłania dokumentów do systemu RAG.
    
    Przyjmuje plik, zapisuje go na serwerze i dodaje do bazy wektorowej.
    Wspiera pliki PDF i TXT.
    
    Args:
        file: Przesłany plik (tylko PDF lub TXT)
        
    Returns:
        JSONResponse: Informacja o statusie operacji
        
    Raises:
        HTTPException: W przypadku błędów podczas przetwarzania pliku
    """
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Brak nazwy pliku"
            )
            
        # Sprawdzenie rozszerzenia pliku
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.pdf', '.txt']:
            raise HTTPException(
                status_code=400,
                detail="Nieobsługiwany typ pliku. Wspierane formaty: .pdf, .txt"
            )
        
        # Tworzenie pełnej ścieżki do zapisu pliku
        file_path = UPLOADS_DIR / file.filename
        
        # Zapisanie pliku na dysku
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Dodanie dokumentu do bazy wektorowej
        engine.rag_manager.add_document(str(file_path))
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Plik '{file.filename}' został pomyślnie dodany do bazy wiedzy.",
                "file_path": str(file_path)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # W przypadku innych błędów, usuwamy plik jeśli został zapisany
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Wystąpił błąd podczas przetwarzania pliku: {str(e)}"
        )
