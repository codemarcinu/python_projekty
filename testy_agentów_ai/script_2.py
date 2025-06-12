# Tworzenie szczegółowego planu testów weryfikacji agenta
import pandas as pd

# Szczegółowe testy weryfikacji
verification_tests = [
    {
        "kategoria": "Dynamiczne ładowanie narzędzi",
        "test_id": "DLN-001",
        "opis": "Sprawdzenie wykrywania wszystkich narzędzi z katalogu modules",
        "scenariusz": "Uruchomienie systemu i sprawdzenie czy wszystkie pliki .py z dekoratorem @tool są wykryte",
        "oczekiwany_rezultat": "Wszystkie narzędzia są załadowane i dostępne w get_registered_tools()",
        "priorytet": "Wysoki",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Dynamiczne ładowanie narzędzi", 
        "test_id": "DLN-002",
        "opis": "Test dodania nowego narzędzia bez restartu",
        "scenariusz": "Dodanie nowego pliku .py z narzędziem podczas działania systemu",
        "oczekiwany_rezultat": "Narzędzie jest automatycznie wykryte i dostępne (jeśli zaimplementowane hot-reload)",
        "priorytet": "Średni",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Dynamiczne ładowanie narzędzi",
        "test_id": "DLN-003", 
        "opis": "Obsługa błędnych modułów",
        "scenariusz": "Dodanie pliku .py z błędem składniowym",
        "oczekiwany_rezultat": "System kontynuuje działanie, błędny moduł jest pominięty, error log jest utworzony",
        "priorytet": "Wysoki",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Logika decyzyjna agenta",
        "test_id": "LDA-001",
        "opis": "Wybór odpowiedniego narzędzia na podstawie zapytania",
        "scenariusz": "Zapytanie 'Która jest godzina?' powinno wywołać get_current_datetime",
        "oczekiwany_rezultat": "Agent wybiera i wykonuje get_current_datetime",
        "priorytet": "Wysoki", 
        "status": "Do wykonania"
    },
    {
        "kategoria": "Logika decyzyjna agenta",
        "test_id": "LDA-002",
        "opis": "Test zapytania wymagającego obliczeń",
        "scenariusz": "Zapytanie 'Ile to 5 plus 3?' powinno wywołać funkcję add",
        "oczekiwany_rezultat": "Agent wykonuje add(5, 3) i zwraca wynik 8",
        "priorytet": "Wysoki",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Logika decyzyjna agenta",
        "test_id": "LDA-003",
        "opis": "Fallback gdy żadne narzędzie nie pasuje",
        "scenariusz": "Zapytanie ogólne typu 'Opowiedz mi o historii'",
        "oczekiwany_rezultat": "Agent używa bezpośredniej odpowiedzi LLM bez narzędzi",
        "priorytet": "Średni",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Obsługa argumentów",
        "test_id": "OA-001",
        "opis": "Ekstraktowanie argumentów numerycznych",
        "scenariusz": "Zapytanie 'Pomnóż 4 przez 7'",
        "oczekiwany_rezultat": "Agent ekstraktuje argumenty 4 i 7, wykonuje multiply(4, 7)",
        "priorytet": "Wysoki",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Obsługa argumentów",
        "test_id": "OA-002", 
        "opis": "Obsługa argumentów tekstowych",
        "scenariusz": "Zapytanie 'Dodaj zadanie: kupić mleko'",
        "oczekiwany_rezultat": "Agent ekstraktuje 'kupić mleko' jako opis zadania",
        "priorytet": "Wysoki",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Obsługa błędów",
        "test_id": "OB-001",
        "opis": "Reakcja na awarie narzędzia",
        "scenariusz": "Symulacja błędu w narzędziu (np. brak dostępu do bazy danych w task_manager)",
        "oczekiwany_rezultat": "System zwraca informacyjny komunikat o błędzie, nie crashuje",
        "priorytet": "Wysoki",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Obsługa błędów",
        "test_id": "OB-002",
        "opis": "Test nieprawidłowych argumentów",
        "scenariusz": "Zapytanie 'Pomnóż tekst przez liczbę'",
        "oczekiwany_rezultat": "Agent obsługuje błąd walidacji argumentów gracefully",
        "priorytet": "Średni",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Integracja interfejsów",
        "test_id": "II-001",
        "opis": "Test interfejsu webowego",
        "scenariusz": "Wysłanie zapytania przez web UI i sprawdzenie odpowiedzi",
        "oczekiwany_rezultat": "Interfejs web działa identycznie jak CLI",
        "priorytet": "Średni",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Integracja interfejsów",
        "test_id": "II-002",
        "opis": "Test sesji i zarządzania stanem",
        "scenariusz": "Dodanie zadania, potem wyświetlenie listy zadań w tej samej sesji",
        "oczekiwany_rezultat": "Stan jest zachowany między operacjami",
        "priorytet": "Średni",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Wydajność",
        "test_id": "W-001",
        "opis": "Czas odpowiedzi agenta",
        "scenariusz": "Pomiar czasu odpowiedzi dla podstawowych zapytań",
        "oczekiwany_rezultat": "Odpowiedź w czasie poniżej 5 sekund dla prostych narzędzi",
        "priorytet": "Średni",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Wydajność",
        "test_id": "W-002",
        "opis": "Test obciążenia",
        "scenariusz": "Równoczesne wysłanie wielu zapytań",
        "oczekiwany_rezultat": "System zachowuje stabilność przy obciążeniu",
        "priorytet": "Niski",
        "status": "Do wykonania"
    },
    {
        "kategoria": "Bezpieczeństwo",
        "test_id": "B-001",
        "opis": "Test injection attacks",
        "scenariusz": "Próba wstrzyknięcia kodu przez zapytanie użytkownika",
        "oczekiwany_rezultat": "System odrzuca lub neutralizuje próby injection",
        "priorytet": "Wysoki",
        "status": "Do wykonania"
    }
]

# Utworzenie DataFrame i zapisanie do CSV
df_tests = pd.DataFrame(verification_tests)

# Zapisanie do CSV
df_tests.to_csv('agent_verification_tests.csv', index=False, encoding='utf-8')

print("=== LISTA TESTÓW WERYFIKACJI AGENTA ===")
print(f"Utworzono {len(verification_tests)} testów weryfikacji")
print("\nPodział według kategorii:")
categories = df_tests['kategoria'].value_counts()
for category, count in categories.items():
    print(f"  {category}: {count} testów")

print("\nPodział według priorytetu:")
priorities = df_tests['priorytet'].value_counts()
for priority, count in priorities.items():
    print(f"  {priority}: {count} testów")

print("\nPierwsze 5 testów:")
print(df_tests[['test_id', 'kategoria', 'opis', 'priorytet']].head().to_string(index=False))

print(f"\nPełna lista testów zapisana do pliku: agent_verification_tests.csv")