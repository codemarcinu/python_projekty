# AI Assistant API

Nowoczesny asystent AI wykorzystujący lokalne modele LLM, zbudowany w Python z FastAPI i Svelte.

## 🚀 Funkcje

- 💬 Interaktywny chat z AI
- 🔍 Wyszukiwanie semantyczne z RAG
- 📚 Obsługa dokumentów i kontekstu
- 🔐 Uwierzytelnianie i autoryzacja
- 🌐 Interfejs WebSocket do komunikacji w czasie rzeczywistym
- 📊 Monitorowanie i logowanie
- 🧪 Testy jednostkowe i integracyjne

## 🛠️ Technologie

### Backend
- Python 3.9+
- FastAPI
- Pydantic
- LangChain
- FAISS
- Sentence Transformers
- Ollama

### Frontend
- Svelte
- TypeScript
- TailwindCSS
- WebSocket

## 📋 Wymagania

- Python 3.9+
- Node.js 16+
- Ollama (lokalnie lub zdalnie)
- 8GB+ RAM (zalecane)
- GPU (opcjonalnie, dla lepszej wydajności)

## 🚀 Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/yourusername/ai-assistant.git
cd ai-assistant
```

2. Utwórz i aktywuj środowisko wirtualne:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
.\venv\Scripts\activate  # Windows
```

3. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

4. Skonfiguruj zmienne środowiskowe:
```bash
cp .env.example .env
# Edytuj .env zgodnie z potrzebami
```

5. Uruchom skrypt instalacyjny:
```bash
./setup.sh
```

## 🏃‍♂️ Uruchomienie

1. Uruchom backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Uruchom frontend (w osobnym terminalu):
```bash
cd frontend
npm install
npm run dev
```

3. Otwórz przeglądarkę:
```
http://localhost:8000
```

## 📚 Dokumentacja API

Dostępne endpointy:

- `GET /` - Strona główna
- `GET /api/health` - Sprawdzenie stanu API
- `GET /api/models` - Lista dostępnych modeli AI
- `POST /api/chat` - Endpoint do wysyłania wiadomości
- `WS /ws/{client_id}` - WebSocket do komunikacji w czasie rzeczywistym

Pełna dokumentacja API dostępna pod adresem:
```
http://localhost:8000/docs
```

## 🧪 Testy

```bash
# Uruchom wszystkie testy
pytest

# Uruchom testy z pokryciem
pytest --cov=.

# Uruchom konkretny test
pytest tests/test_specific.py
```

## 📁 Struktura Projektu

```
project/
├── core/                 # Rdzeń aplikacji
│   ├── ai_engine.py     # Główna logika AI
│   ├── llm_manager.py   # Zarządzanie modelami
│   ├── rag_manager.py   # Retrieval-Augmented Generation
│   └── conversation.py  # Obsługa rozmów
├── interfaces/          # Interfejsy użytkownika
│   ├── web_ui.py       # FastAPI web interface
│   ├── cli.py          # Command line interface
│   └── api.py          # REST API endpoints
├── config/             # Konfiguracja
├── utils/              # Narzędzia pomocnicze
├── static/             # Pliki statyczne (CSS, JS)
├── tests/              # Testy
└── frontend/           # Frontend Svelte
```

## 🔧 Konfiguracja

Główne ustawienia w pliku `.env`:

```env
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=300

# Models
PRIMARY_MODEL=gemma3:12b
DOCUMENT_MODEL=SpeakLeash/bielik-11b-v2.3-instruct:Q6_K

# RAG Settings
EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5
TRUST_REMOTE_CODE=true

# Limits
MAX_FILE_SIZE=52428800  # 50MB
MAX_CONVERSATION_LENGTH=100
REQUEST_TIMEOUT=30

# Paths
UPLOAD_DIR=./uploads
FAISS_INDEX_PATH=./data/faiss_index
```

## 🤝 Współpraca

1. Fork projektu
2. Utwórz branch dla nowej funkcji (`git checkout -b feature/amazing-feature`)
3. Commit zmian (`git commit -m 'Add amazing feature'`)
4. Push do brancha (`git push origin feature/amazing-feature`)
5. Otwórz Pull Request

## 📝 Licencja

Ten projekt jest udostępniany na licencji MIT. Szczegóły w pliku [LICENSE](LICENSE).

## 🙏 Podziękowania

- [Ollama](https://github.com/ollama/ollama) za świetne narzędzie do lokalnych modeli LLM
- [LangChain](https://github.com/langchain-ai/langchain) za framework do aplikacji AI
- [FastAPI](https://github.com/tiangolo/fastapi) za nowoczesny framework webowy
- [Svelte](https://github.com/sveltejs/svelte) za świetny framework frontendowy 