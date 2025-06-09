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
    
    def __init__(self, config):
        """Inicjalizuje menedżera RAG.
        
        Args:
            config: Menedżer konfiguracji aplikacji, zawierający ustawienia
                          dla modelu embeddingów i innych parametrów RAG.
        """
        self.config = config
        
        # Inicjalizacja modelu embeddingów z konfiguracji
        self.embeddings: Embeddings = OllamaEmbeddings(
            model=config.embedding_model
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
                    embeddings=self.embeddings
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
            
            # Dodanie metadanych o pochodzeniu do każdego fragmentu
            source_filename = file_path.name
            for chunk in chunks:
                if chunk.metadata is None:
                    chunk.metadata = {}
                chunk.metadata["source_filename"] = source_filename
            
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
                self.vector_store.save_local(self.index_path)
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
        response = self.config.llm_model.generate(prompt)
        
        return response 

    def list_documents(self) -> list[str]:
        """Zwraca listę unikalnych nazw dokumentów przechowywanych w bazie wektorowej.
        
        Metoda przeszukuje wszystkie fragmenty dokumentów w bazie wektorowej i wyciąga
        z ich metadanych nazwy plików źródłowych. Zwraca listę unikalnych nazw plików.
        
        Returns:
            list[str]: Lista unikalnych nazw plików przechowywanych w bazie.
                      Jeśli baza jest pusta lub nie istnieje, zwraca pustą listę.
        """
        if self.vector_store is None:
            return []
            
        # Pobranie wszystkich dokumentów z magazynu
        all_docs = self.vector_store.docstore._docs
        
        # Wyciągnięcie unikalnych nazw plików z metadanych
        unique_filenames = set()
        for doc in all_docs.values():
            if doc.metadata and "source_filename" in doc.metadata:
                unique_filenames.add(doc.metadata["source_filename"])
        
        return sorted(list(unique_filenames))

    def delete_document(self, filename_to_delete: str) -> bool:
        """Usuwa dokument i jego wszystkie fragmenty z bazy wektorowej.
        
        Metoda znajduje wszystkie fragmenty dokumentu o podanej nazwie pliku
        i usuwa je z bazy wektorowej. Następnie usuwa również oryginalny plik
        z katalogu uploads.
        
        Args:
            filename_to_delete (str): Nazwa pliku do usunięcia.
            
        Returns:
            bool: True jeśli usunięto jakiekolwiek fragmenty dokumentu,
                 False jeśli dokument nie został znaleziony lub baza jest pusta.
                 
        Raises:
            Exception: W przypadku błędów podczas usuwania pliku lub zapisywania bazy.
        """
        if self.vector_store is None:
            return False
            
        # Lista ID fragmentów do usunięcia
        ids_to_delete = []
        
        # Znajdowanie wszystkich fragmentów dokumentu
        for docstore_id in self.vector_store.index_to_docstore_id.values():
            doc = self.vector_store.docstore._docs.get(docstore_id)
            if doc and doc.metadata and doc.metadata.get("source_filename") == filename_to_delete:
                ids_to_delete.append(docstore_id)
        
        # Jeśli znaleziono fragmenty do usunięcia
        if ids_to_delete:
            # Usunięcie fragmentów z bazy wektorowej
            self.vector_store.delete(ids_to_delete)
            
            # Zapisanie zmian na dysku
            self.vector_store.save_local(self.index_path)
            
            # Usunięcie oryginalnego pliku
            file_path = Path("data/uploads") / filename_to_delete
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                print(f"Ostrzeżenie: Nie udało się usunąć pliku {filename_to_delete}: {e}")
            
            return True
            
        return False 

    def init_empty_index(self) -> None:
        """Tworzy pusty indeks FAISS, jeśli nie istnieje."""
        index_file = self.index_path / "index.faiss"
        if index_file.exists():
            print("Indeks FAISS już istnieje.")
            return
        print("Tworzę pusty indeks FAISS...")
        # Tworzymy pustą bazę wektorową FAISS
        self.vector_store = FAISS.from_texts([], self.embeddings)
        self.vector_store.save_local(str(self.index_path))
        print(f"Pusty indeks FAISS utworzony w {self.index_path}") 

    def get_document_count(self) -> int:
        """Zwraca liczbę unikalnych dokumentów w bazie wektorowej.
        
        Returns:
            int: Liczba unikalnych dokumentów w bazie.
                 Jeśli baza jest pusta lub nie istnieje, zwraca 0.
        """
        return len(self.list_documents()) 