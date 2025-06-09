"""
Moduł zarządzający systemem RAG (Retrieval-Augmented Generation).

Ten moduł zawiera implementację klasy RAGManager, która odpowiada za:
- Zarządzanie wektorowym magazynem dokumentów
- Tworzenie i ładowanie indeksów FAISS
- Integrację z modelami embeddingów
"""

from pathlib import Path
from typing import Optional, List, Union

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

class RAGManager:
    """Klasa zarządzająca systemem RAG (Retrieval-Augmented Generation).
    
    Odpowiada za zarządzanie wektorowym magazynem dokumentów, tworzenie i ładowanie
    indeksów FAISS oraz integrację z modelami embeddingów.
    
    Attributes:
        config_manager: Menedżer konfiguracji aplikacji
        embeddings: Model do tworzenia wektorów (embeddings)
        index_path: Ścieżka do przechowywania indeksu wektorowego
        vector_store: Magazyn wektorowy FAISS
    """
    
    def __init__(self, config_manager) -> None:
        """Inicjalizuje menedżera RAG.
        
        Args:
            config_manager: Menedżer konfiguracji aplikacji, zawierający ustawienia
                          dla modelu embeddingów i innych parametrów RAG.
        """
        self.config_manager = config_manager
        
        # Inicjalizacja modelu embeddingów z konfiguracji
        self.embeddings: Embeddings = OllamaEmbeddings(
            model=config_manager.embedding_model_name
        )
        
        # Ścieżka do przechowywania indeksu wektorowego
        self.index_path = Path("data/vector_store")
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Inicjalizacja magazynu wektorowego
        self.vector_store: Optional[FAISS] = None
        
        # Próba załadowania istniejącego magazynu
        self.load_store()
    
    def load_store(self) -> None:
        """Ładuje istniejący magazyn wektorowy lub przygotowuje nowy.
        
        Metoda sprawdza, czy w zdefiniowanej ścieżce istnieje już zapisany indeks FAISS.
        Jeśli tak, ładuje go do self.vector_store. W przeciwnym razie przygotowuje
        system do utworzenia nowego magazynu przy dodaniu pierwszego dokumentu.
        """
        index_file = self.index_path / "index.faiss"
        
        if index_file.exists():
            try:
                self.vector_store = FAISS.load_local(
                    folder_path=str(self.index_path),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("Załadowano istniejący magazyn wektorowy.")
            except Exception as e:
                print(f"Błąd podczas ładowania magazynu wektorowego: {e}")
                self.vector_store = None
        else:
            print("Magazyn wektorowy nie istnieje. Zostanie utworzony przy dodaniu pierwszego dokumentu.")
            self.vector_store = None

    def add_document(self, file_path: Union[str, Path]) -> None:
        """Dodaje nowy dokument do bazy wektorowej.
        
        Metoda obsługuje cały proces od wczytania pliku po zapisanie go w bazie wektorowej FAISS.
        Wspiera pliki PDF i TXT. Dokument jest dzielony na mniejsze fragmenty, które są
        następnie dodawane do bazy wektorowej.
        
        Args:
            file_path: Ścieżka do pliku, który ma zostać dodany do bazy.
                      Może być stringiem lub obiektem Path.
            
        Raises:
            ValueError: Jeśli typ pliku nie jest wspierany (tylko .pdf i .txt).
            FileNotFoundError: Jeśli plik nie istnieje.
            Exception: W przypadku innych błędów podczas przetwarzania.
        """
        try:
            # Konwersja ścieżki na obiekt Path i sprawdzenie istnienia pliku
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Plik nie istnieje: {file_path}")
            
            print(f"Przetwarzanie pliku: {file_path}")
            
            # Wybór odpowiedniego loadera na podstawie rozszerzenia
            if file_path.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix.lower() == '.txt':
                loader = TextLoader(str(file_path))
            else:
                raise ValueError(f"Nieobsługiwany typ pliku: {file_path.suffix}. Wspierane formaty: .pdf, .txt")
            
            # Ładowanie dokumentu
            documents: List[Document] = loader.load()
            print(f"Zaladowano dokument: {len(documents)} stron/fragmentów")
            
            # Konfiguracja i użycie splittera do podziału na mniejsze fragmenty
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                is_separator_regex=False
            )
            
            chunks = text_splitter.split_documents(documents)
            print(f"Podzielono na {len(chunks)} fragmentów")
            
            # Dodanie dokumentów do bazy wektorowej
            if self.vector_store is None:
                # Tworzenie nowej bazy wektorowej
                print("Tworzenie nowej bazy wektorowej...")
                self.vector_store = FAISS.from_documents(
                    documents=chunks,
                    embedding=self.embeddings
                )
            else:
                # Dodanie do istniejącej bazy
                print("Dodawanie do istniejącej bazy wektorowej...")
                self.vector_store.add_documents(chunks)
            
            # Zapisanie zaktualizowanej bazy na dysku
            if self.vector_store is not None:  # Dodatkowe sprawdzenie dla mypy
                self.vector_store.save_local(
                    folder_path=str(self.index_path),
                    allow_dangerous_deserialization=True
                )
                print("Baza wektorowa zapisana pomyślnie.")
            
        except (ValueError, FileNotFoundError) as e:
            # Przekazanie błędów walidacji i braku pliku
            raise
        except Exception as e:
            # Obsługa innych błędów
            print(f"Wystąpił błąd podczas przetwarzania dokumentu: {e}")
            raise 

    def get_retriever(self) -> Optional[BaseRetriever]:
        """Zwraca retriever do wyszukiwania dokumentów w bazie wektorowej.
        
        Returns:
            Optional[BaseRetriever]: Retriever do wyszukiwania dokumentów lub None,
                                   jeśli baza wektorowa nie istnieje.
        """
        if self.vector_store is None:
            return None
        return self.vector_store.as_retriever()

    def query(self, query: str) -> str:
        """Wyszukuje odpowiedź na pytanie w bazie wektorowej.
        
        Args:
            query (str): Pytanie do zadania.
            
        Returns:
            str: Odpowiedź na pytanie.
            
        Raises:
            ValueError: Jeśli baza wektorowa nie istnieje.
        """
        if self.vector_store is None:
            raise ValueError("Baza wektorowa nie istnieje. Najpierw dodaj dokumenty używając metody add_document.")
        
        # Wyszukanie podobnych dokumentów
        docs = self.vector_store.similarity_search(query, k=3)
        
        # Przygotowanie kontekstu z dokumentów
        context = "\n".join(doc.page_content for doc in docs)
        
        # Przygotowanie promptu dla modelu
        prompt = f"""Odpowiedz na pytanie na podstawie poniższego kontekstu.
        Jeśli nie możesz znaleźć odpowiedzi w kontekście, powiedz o tym.
        
        Kontekst:
        {context}
        
        Pytanie: {query}
        
        Odpowiedź:"""
        
        # Użycie modelu do wygenerowania odpowiedzi
        response = self.config_manager.llm_model.generate(prompt)
        
        return response 