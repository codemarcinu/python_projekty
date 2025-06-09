# Lokalny Asystent AI

## Opis
Lokalny Asystent AI to nowoczesna, modularna aplikacja działająca w 100% lokalnie na urządzeniu użytkownika. Projekt kładzie szczególny nacisk na prywatność danych, wydajność oraz łatwość rozbudowy o nowe funkcje. Asystent wykorzystuje lokalne modele AI do prowadzenia naturalnych konwersacji i wykonywania zadań bez konieczności korzystania z zewnętrznych usług chmurowych.

## Aktualny Stan Projektu (v0.2)
- ✅ Działający rdzeń konwersacyjny
- ✅ Pamięć kontekstowa (asystent pamięta poprzednie części rozmowy)
- ✅ Dynamiczny system wtyczek (narzędzi)
- ✅ Działający interfejs w linii poleceń (CLI)
- ✅ Podstawowa implementacja API (FastAPI)
- ✅ System konfiguracji z walidacją (Pydantic)
- ✅ Integracja z bazą danych SQLite
- ✅ Podstawowy system zarządzania modelami LLM
- ⏳ Interfejs webowy (w trakcie)
- ⏳ System zdarzeń (w trakcie)

## Stack Technologiczny
- **Język programowania**: Python 3.11+
- **Silnik AI**: Ollama (lokalne modele LLM)
- **Framework CLI**: Typer
- **Walidacja danych**: Pydantic
- **Orkiestracja AI**: LangChain
- **Interfejs API**: FastAPI
- **Baza danych**: SQLite
- **Zarządzanie zależnościami**: Poetry (pyproject.toml)

## Instalacja i Uruchomienie

### Krok 1: Pobranie plików projektu
```bash
git clone [URL_REPOZYTORIUM]
cd [NAZWA_KATALOGU]
```

### Krok 2: Konfiguracja środowiska wirtualnego
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
.\venv\Scripts\activate  # Windows
```

### Krok 3: Instalacja zależności
```bash
pip install -r requirements.txt
```

### Krok 4: Konfiguracja lokalnego LLM
1. Zainstaluj [Ollama](https://ollama.ai/)
2. Pobierz wybrany model (np. llama2):
```bash
ollama pull llama2
```

### Krok 5: Konfiguracja środowiska
1. Skopiuj plik `.env.example` do `.env`:
```bash
cp .env.example .env
```
2. Edytuj plik `.env` i ustaw nazwę modelu:
```
MODEL_NAME=llama2
```

## Sposób Użycia
Aby uruchomić asystenta, wykonaj:
```bash
python interfaces/cli.py
```

Asystent rozpocznie konwersację w trybie interaktywnym. Możesz:
- Zadawać pytania w języku naturalnym
- Prosić o wykonanie zadań
- Zakończyć rozmowę komendą "exit" lub "quit"

## Dostępne Narzędzia (Wtyczki)

### simple_math
- `add`: Dodawanie dwóch liczb
- `multiply`: Mnożenie dwóch liczb

### datetime_tool
- `get_current_datetime`: Zwraca aktualną datę i godzinę

### database_tool
- `query`: Wykonywanie zapytań SQL
- `execute`: Wykonywanie operacji na bazie danych

## Dalszy Rozwój (Roadmap)

### Etap 1: Rozbudowa Zdolności Agentowych (W TRAKCIE)
- ✅ Integracja z bazą danych SQLite
- ⏳ Integracja z API pogody
- ⏳ Wyszukiwarka internetowa
- ⏳ Obsługa kalendarza
- ⏳ System przypomnień

### Etap 2: Implementacja Modułów Aplikacji (W TRAKCIE)
- ⏳ Rozwój modułu `personal_assistant`
  - System zarządzania zadaniami
  - Integracja z bazą danych SQLite
  - System powiadomień
- ⏳ Rozwój modułu `household_manager`
  - Zarządzanie zakupami
  - Obsługa przepisów
  - Integracja OCR

### Etap 3: Stworzenie Interfejsu Webowego (W TRAKCIE)
- ⏳ Implementacja `interfaces/web_ui.py`
- ✅ Podstawowa implementacja `interfaces/api.py`
- ⏳ Panel administracyjny
- ⏳ Dokumentacja API

### Etap 4: Zaawansowana Komunikacja Wewnętrzna (W TRAKCIE)
- ⏳ Implementacja `core/event_bus.py`
- ⏳ System kolejkowania zadań
- ⏳ Mechanizm synchronizacji między modułami
- ⏳ Obsługa zdarzeń asynchronicznych

## Struktura Projektu
```
/
├── core/                    # Rdzeń aplikacji
│   ├── ai_engine.py        # Główny silnik AI
│   ├── llm_manager.py      # Zarządzanie modelami LLM
│   ├── conversation_handler.py # Obsługa konwersacji
│   ├── plugin_system.py    # System wtyczek
│   ├── config_manager.py   # Zarządzanie konfiguracją
│   ├── database.py         # Obsługa bazy danych
│   └── event_bus.py        # System zdarzeń (w trakcie)
├── interfaces/             # Interfejsy aplikacji
│   ├── cli.py             # Interfejs CLI
│   ├── api.py             # API FastAPI
│   └── web_ui.py          # Interfejs webowy (w trakcie)
├── modules/               # Moduły funkcjonalne
├── data/                 # Dane użytkownika i baza SQLite
└── plugins/              # Wtyczki i narzędzia
``` 