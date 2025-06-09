"""
Moduł zarządzający systemem RAG (Retrieval-Augmented Generation).

Ten moduł zawiera implementację klasy RAGManager, która odpowiada za:
- Zarządzanie wektorowym magazynem dokumentów
- Tworzenie i ładowanie indeksów FAISS
- Integrację z modelami embeddingów
"""

from pathlib import Path
from typing import Optional, List, Union, Dict, Any
import logging

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

logger = logging.getLogger(__name__)

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
            config: Konfiguracja RAG zawierająca ustawienia dla embeddingów i indeksu.
        """
        self.config = config  # Przechowuj konfigurację jako atrybut klasy
        
        # Inicjalizacja modelu embeddingów z konfiguracji
        self.embeddings = OllamaEmbeddings(
            base_url="http://localhost:11434",  # Domyślny adres Ollama
            model=config.embedding_model
        )
        
        # Ścieżka do przechowywania indeksu wektorowego
        self.index_path = config.index_path
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Inicjalizacja magazynu wektorowego
        self.vector_store = self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Ładuje istniejący indeks lub tworzy nowy."""
        try:
            if self.index_path.exists():
                return FAISS.load_local(
                    str(self.index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                return self._create_empty_index()
        except Exception as e:
            logger.error(f"Błąd podczas ładowania magazynu wektorowego: {e}")
            return self._create_empty_index()
            
    def _create_empty_index(self):
        """Tworzy pusty indeks z przykładowym tekstem."""
        return FAISS.from_texts(
            ["Witaj w bazie wiedzy!"],
            self.embeddings
        )
    
    def _get_loader(self, file_path: str):
        """Zwraca odpowiedni loader dla typu pliku."""
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            return PyPDFLoader(file_path)
        elif ext in ['.txt', '.md']:
            return TextLoader(file_path)
        else:
            raise ValueError(f"Nieobsługiwany typ pliku: {ext}")
            
    def add_document(self, file_path: str) -> bool:
        """Dodaje dokument do bazy wiedzy.
        
        Args:
            file_path: Ścieżka do pliku do dodania.
            
        Returns:
            bool: True jeśli dokument został dodany pomyślnie, False w przeciwnym razie.
        """
        try:
            loader = self._get_loader(file_path)
            documents = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap
            )
            splits = text_splitter.split_documents(documents)
            
            self.vector_store.add_documents(splits)
            self.vector_store.save_local(str(self.index_path))
            return True
        except Exception as e:
            logger.error(f"Błąd podczas dodawania dokumentu: {e}")
            return False
    
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

    def list_documents(self) -> List[Dict[str, Any]]:
        """Zwraca listę dokumentów w bazie.
        
        Returns:
            List[Dict[str, Any]]: Lista dokumentów z ich metadanymi.
        """
        try:
            # Pobierz wszystkie dokumenty z bazy używając similarity_search
            docs = self.vector_store.similarity_search("", k=1000)  # Pobierz maksymalnie 1000 dokumentów
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"Błąd podczas pobierania listy dokumentów: {e}")
            return []
            
    def delete_document(self, filename_to_delete: str) -> bool:
        """Usuwa dokument z bazy wektorowej.
        
        Args:
            filename_to_delete: Nazwa pliku do usunięcia.
            
        Returns:
            bool: True jeśli dokument został usunięty pomyślnie, False w przeciwnym razie.
        """
        try:
            # Pobierz wszystkie dokumenty
            docs = self.vector_store.similarity_search("", k=1000)
            
            # Filtruj dokumenty, które nie są z pliku do usunięcia
            docs_to_keep = [
                doc for doc in docs 
                if doc.metadata.get("source_filename") != filename_to_delete
            ]
            
            if len(docs_to_keep) == len(docs):
                logger.warning(f"Dokument {filename_to_delete} nie został znaleziony w bazie")
                return False
                
            # Twórz nowy indeks z pozostałymi dokumentami
            new_store = FAISS.from_documents(
                documents=docs_to_keep,
                embedding=self.embeddings
            )
            
            # Zastąp stary indeks nowym
            self.vector_store = new_store
            
            # Zapisz zmiany
            self.vector_store.save_local(str(self.index_path))
            logger.info(f"Usunięto dokument {filename_to_delete}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd podczas usuwania dokumentu: {e}")
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
        """Zwraca liczbę dokumentów w bazie.
        
        Returns:
            int: Liczba dokumentów.
        """
        try:
            # Pobierz wszystkie dokumenty z bazy używając similarity_search
            docs = self.vector_store.similarity_search("", k=1000)
            return len(docs)
        except Exception as e:
            logger.error(f"Błąd podczas pobierania liczby dokumentów: {e}")
            return 0

    def search(self, query: str, k: int = 4) -> List[Document]:
        """Wyszukuje podobne dokumenty.
        
        Args:
            query: Zapytanie do wyszukania.
            k: Liczba wyników do zwrócenia.
            
        Returns:
            List[Document]: Lista znalezionych dokumentów.
        """
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Błąd podczas wyszukiwania: {e}")
            return [] 