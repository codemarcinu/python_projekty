# Instrukcja dla Agenta AI: Autonomiczna Refaktoryzacja Projektu

## Kontekst

Projekt `codemarcinu/python_projekty` wymaga refaktoryzacji, aby jego wygląd i struktura odpowiadały projektowi `open-webui/open-webui`. Obecny projekt to prosty asystent AI z interfejsem sieciowym opartym na tradycyjnym podejściu (HTML/CSS/JS), podczas gdy docelowy projekt wykorzystuje nowoczesne technologie (SvelteKit, TypeScript, Tailwind CSS).

## Instrukcja Wykonawcza

Jako agent AI przeprowadź autonomiczną refaktoryzację projektu `codemarcinu/python_projekty` zgodnie z poniższymi wytycznymi, wykonując następujące etapy:

### 1. Analiza i Przygotowanie

1. Sklonuj oba repozytoria:
   ```
   git clone https://github.com/codemarcinu/python_projekty.git
   git clone https://github.com/open-webui/open-webui.git
   ```

2. Utwórz nową gałąź w projekcie `python_projekty` do refaktoryzacji:
   ```
   cd python_projekty
   git checkout -b refactor-to-svelte
   ```

3. Przeanalizuj strukturę projektu `open-webui` i zidentyfikuj kluczowe elementy do zaimplementowania w `python_projekty`.

### 2. Reorganizacja Struktury Projektu

1. Zainicjalizuj projekt SvelteKit w nowym katalogu tymczasowym:
   ```
   mkdir temp-svelte
   cd temp-svelte
   npm create svelte@latest .
   ```
   Wybierz TypeScript, ESLint, Prettier i skonfiguruj SvelteKit jako aplikację.

2. Zainstaluj niezbędne zależności:
   ```
   npm install
   npm install -D tailwindcss postcss autoprefixer
   npm install -D svelte-preprocess
   npx tailwindcss init -p
   ```

3. Skonfiguruj Tailwind CSS na podstawie projektu `open-webui`:
   - Skopiuj ustawienia kolorów, komponentów i wariantów
   - Skonfiguruj dark mode

4. Utwórz nową strukturę katalogów w projekcie `python_projekty`:
   ```
   mkdir -p src/lib/{components/{layout,chat,common,dashboard},stores,utils,apis}
   mkdir -p src/routes/{auth,error,(app)}
   ```

### 3. Implementacja Komponentów Frontend

1. Przenieś istniejącą logikę HTML/CSS do komponentów Svelte:
   - Przekształć `templates/dashboard.html` na komponenty Svelte w `src/lib/components/dashboard/`
   - Przekształć `templates/chat.html` na komponenty Svelte w `src/lib/components/chat/`

2. Zaimplementuj layout główny aplikacji (`src/routes/(app)/+layout.svelte`):
   - Dodaj responsywny sidebar z funkcją zwijania
   - Zaimplementuj menu nawigacyjne
   - Dodaj obsługę dark/light mode

3. Zaimplementuj składniki UI wzorowane na `open-webui`:
   - Przyciski, pola formularzy, karty
   - Komponenty dla czatu, wiadomości, dropzone dla plików
   - Modalne okna ustawień i pomocy

4. Zaimplementuj store'y Svelte (`src/lib/stores/`):
   - Stan czatu i wiadomości
   - Informacje o użytkowniku i ustawienia
   - Dane modeli AI i dokumentów

### 4. Integracja Backend

1. Zachowaj istniejący kod backendu w folderach:
   - `core/`
   - `config/`
   - `modules/`
   - `utils/`

2. Zmodyfikuj punkty końcowe API w FastAPI:
   - Zaktualizuj trasy API do pracy z komponentami Svelte
   - Dodaj obsługę sesji użytkowników i RBAC
   - Zaktualizuj kontrakt API aby pasował do nowego frontendu

3. Zaimplementuj obsługę WebSocket dla komunikacji w czasie rzeczywistym:
   - Dodaj obsługę czatu w czasie rzeczywistym
   - Zaimplementuj powiadomienia o stanie systemu

### 5. Zmiany w UI/UX

1. Zastąp obecny design interfejsem wzorowanym na `open-webui`:
   - Nowoczesny, minimalistyczny wygląd
   - Pełna responsywność
   - Wsparcie dla dark/light mode
   - Animacje i przejścia

2. Zaimplementuj zaawansowane funkcje UI:
   - Formatowanie Markdown w czacie
   - Podświetlanie składni kodu
   - Drag-and-drop dla dokumentów
   - Dynamiczne menu i nawigacja

### 6. Kompilacja i Testowanie

1. Skonfiguruj build system:
   ```
   npm run build
   ```

2. Zaktualizuj `main.py` aby obsługiwał nowy frontend:
   - Skonfiguruj serwowanie statycznych plików z katalogu build
   - Zaktualizuj trasy API

3. Przeprowadź testy funkcjonalne:
   - Sprawdź poprawność działania czatu
   - Przetestuj responsywność interfejsu
   - Zweryfikuj integracje backendu

### 7. Finalizacja

1. Oczyść kod, usuń nieużywane pliki:
   ```
   git rm -r templates/
   git rm -r static/
   ```

2. Zaktualizuj dokumentację:
   - Uaktualnij README.md
   - Dodaj informacje o nowej architekturze
   - Zaktualizuj instrukcje instalacji

3. Zatwierdź zmiany:
   ```
   git add .
   git commit -m "Refaktoryzacja do architektury SvelteKit i Tailwind CSS"
   ```

## Szczegółowe Wytyczne Implementacyjne

### Sidebar i Nawigacja

Zaimplementuj komponent Sidebar wzorowany na `open-webui` z następującymi cechami:
- Możliwość zwijania/rozwijania
- Zapisywanie stanu w localStorage
- Dynamiczne menu zależne od uprawnień użytkownika
- Wskaźniki aktywnego modelu

### Chat Interface

Zbuduj zaawansowany interfejs czatu:
- Obsługa Markdown i formatowania
- Podświetlanie składni dla bloków kodu
- Kopiowanie wiadomości i kodu
- Wskaźniki pisania

### System Zarządzania Dokumentami

Utwórz zaawansowany interfejs dla dokumentów RAG:
- Drag-and-drop upload
- Podgląd dokumentów
- Status przetwarzania
- Filtrowanie i wyszukiwanie

### Komponenty UI

Zaimplementuj podstawowe komponenty UI z `open-webui`:
- Buttony z wariantami (primary, secondary, ghost)
- Input fields z walidacją
- Select menus i dropdowny
- Toast notifications
- Modal dialogs
- Toggle switches

### Theme Switcher

Zaimplementuj system zmiany motywu:
- Automatyczne wykrywanie preferencji systemowych
- Przełącznik dark/light mode
- Zapisywanie preferencji w localStorage

## Zaawansowane Aspekty

### Reaktywność i Stan Aplikacji

Wykorzystaj store'y Svelte do zarządzania stanem aplikacji:
```javascript
// src/lib/stores/chat.js
import { writable } from 'svelte/store';

export const chatStore = writable({
  messages: [],
  loading: false,
  selectedModel: 'default',
  context: []
});

export const sendMessage = async (message) => {
  chatStore.update(state => ({ ...state, loading: true }));
  
  // Komunikacja z API
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  
  const data = await response.json();
  
  chatStore.update(state => ({
    ...state,
    loading: false,
    messages: [...state.messages, 
      { role: 'user', content: message },
      { role: 'assistant', content: data.response }
    ]
  }));
};
```

### Przejścia i Animacje

Zaimplementuj płynne przejścia między widokami i animacje UI:
```svelte
<script>
  import { fade, fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
</script>

<div in:fade={{ duration: 300, delay: 300 }} out:fly={{ y: 20, duration: 300, easing: quintOut }}>
  <!-- Zawartość komponentu -->
</div>
```

### API Wrapper

Stwórz opakowujące funkcje API dla wygodnego wywoływania backendu:
```typescript
// src/lib/apis/chat.ts
export async function sendChatMessage(message: string, model: string) {
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ message, model })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to send message:', error);
    throw error;
  }
}
```

## Wskazówki Realizacyjne

1. **Inkrementalna refaktoryzacja**: Najpierw zbuduj szkielet aplikacji, a następnie dodawaj kolejne funkcje.
2. **Komponentyzacja**: Podziel UI na małe, reużywalne komponenty.
3. **Zachowaj logikę biznesową**: Przenieś istniejącą logikę backendu do nowej struktury.
4. **Stylowanie komponentów**: Używaj Tailwind CSS dla spójnego wyglądu.
5. **Testowanie progresywne**: Testuj każdy komponent podczas rozwijania.

## Konkluzja

Przeprowadzenie tej refaktoryzacji przekształci projekt `python_projekty` w nowoczesną aplikację SPA, która będzie wyglądać i działać podobnie do projektu `open-webui`, zachowując jednocześnie podstawową funkcjonalność asystenta AI. Nowa architektura zapewni lepszą skalowalność, łatwiejsze utrzymanie i lepsze doświadczenie użytkownika.