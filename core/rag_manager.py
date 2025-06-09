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
import asyncio

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

logger = logging.getLogger(__name__)

class RAGError(Exception):
    """Base exception for RAG-related errors."""
    pass

class RAGManager:
    """Klasa zarządzająca systemem RAG (Retrieval-Augmented Generation).
    
    Odpowiada za zarządzanie wektorowym magazynem dokumentów, tworzenie i ładowanie
    indeksów FAISS oraz integrację z modelami embeddingów.
    
    Attributes:
        config: Konfiguracja RAG
        embeddings: Model do tworzenia wektorów (embeddings)
        index_path: Ścieżka do przechowywania indeksu wektorowego
        vector_store: Magazyn wektorowy FAISS
    """
    
    def __init__(self, config):
        """Inicjalizuje menedżera RAG.
        
        Args:
            config: Konfiguracja RAG zawierająca ustawienia dla embeddingów i indeksu.
            
        Raises:
            RAGError: Jeśli inicjalizacja się nie powiedzie.
        """
        try:
            self.config = config
            
            # Inicjalizacja modelu embeddingów z konfiguracji
            self.embeddings = OllamaEmbeddings(
                base_url=config.base_url,
                model=config.embedding_model
            )
            
            # Konfiguracja ścieżek
            self.index_path = config.index_path
            self.vector_db_path = config.vector_db_path
            self.upload_dir = config.upload_dir
            
            # Utwórz wymagane katalogi
            self._ensure_directories()
            
            # Inicjalizacja text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap
            )
            
            # Inicjalizacja magazynu wektorowego
            self.vector_store = self._load_or_create_index()
            
            logger.info("RAG Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG Manager: {e}")
            raise RAGError(f"Failed to initialize RAG Manager: {e}")
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        try:
            self.index_path.mkdir(parents=True, exist_ok=True)
            self.vector_db_path.mkdir(parents=True, exist_ok=True)
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Required directories created/verified")
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise RAGError(f"Failed to create required directories: {e}")
    
    def _load_or_create_index(self):
        """Ładuje istniejący indeks lub tworzy nowy."""
        try:
            if self.index_path.exists() and any(self.index_path.iterdir()):
                return FAISS.load_local(
                    str(self.index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                return self._create_empty_index()
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return self._create_empty_index()
            
    def _create_empty_index(self):
        """Tworzy pusty indeks."""
        try:
            # Dodaj przykładowy tekst zamiast pustej listy
            return FAISS.from_texts(
                ["Witaj w bazie wiedzy!"],
                self.embeddings
            )
        except Exception as e:
            logger.error(f"Error creating empty index: {e}")
            raise RAGError(f"Failed to create empty index: {e}")
    
    def _get_loader(self, file_path: str):
        """Zwraca odpowiedni loader dla typu pliku."""
        try:
            ext = Path(file_path).suffix.lower()
            if ext == '.pdf':
                return PyPDFLoader(file_path)
            elif ext in ['.txt', '.md']:
                return TextLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            logger.error(f"Error getting document loader: {e}")
            raise RAGError(f"Failed to get document loader: {e}")
            
    async def add_document(self, file_path: str) -> bool:
        """Dodaje dokument do bazy wiedzy.
        
        Args:
            file_path: Ścieżka do pliku do dodania.
            
        Returns:
            bool: True jeśli dokument został dodany pomyślnie, False w przeciwnym razie.
        """
        try:
            loader = self._get_loader(file_path)
            documents = loader.load()
            
            splits = self.text_splitter.split_documents(documents)
            
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(splits, self.embeddings)
            else:
                self.vector_store.add_documents(splits)
                
            self.vector_store.save_local(str(self.index_path))
            logger.info(f"Successfully added document: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document {file_path}: {e}")
            return False
    
    def get_retriever(self) -> Optional[BaseRetriever]:
        """Zwraca retriever do wyszukiwania dokumentów w bazie wektorowej."""
        if self.vector_store is None:
            return None
        return self.vector_store.as_retriever(
            search_kwargs={"k": self.config.max_results}
        )

    async def query(self, query: str) -> str:
        """Wyszukuje odpowiedź na pytanie w bazie wektorowej."""
        if self.vector_store is None:
            raise RAGError("Vector store not initialized. Add documents first.")
        
        try:
            # Wyszukanie podobnych dokumentów
            docs = self.vector_store.similarity_search(
                query, 
                k=self.config.max_results
            )
            
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
            response = await self.config.llm_model.generate(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise RAGError(f"Failed to process query: {e}")

    def list_documents(self) -> List[Dict[str, Any]]:
        """Zwraca listę dokumentów w bazie."""
        try:
            if self.vector_store is None:
                return []
                
            docs = self.vector_store.similarity_search("", k=1000)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
            
    async def delete_document(self, filename_to_delete: str) -> bool:
        """Usuwa dokument z bazy wektorowej."""
        try:
            if self.vector_store is None:
                return False
                
            # Pobierz wszystkie dokumenty
            docs = self.vector_store.similarity_search("", k=1000)
            
            # Filtruj dokumenty
            docs_to_keep = [
                doc for doc in docs 
                if doc.metadata.get("source_filename") != filename_to_delete
            ]
            
            if len(docs_to_keep) == len(docs):
                logger.warning(f"Document {filename_to_delete} not found in database")
                return False
                
            # Twórz nowy indeks
            new_store = FAISS.from_documents(
                documents=docs_to_keep,
                embedding=self.embeddings
            )
            
            # Zastąp stary indeks
            self.vector_store = new_store
            self.vector_store.save_local(str(self.index_path))
            
            logger.info(f"Successfully deleted document: {filename_to_delete}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
            
    def init_empty_index(self) -> None:
        """Tworzy pusty indeks FAISS."""
        try:
            if self.index_path.exists() and any(self.index_path.iterdir()):
                logger.info("FAISS index already exists")
                return
            logger.info("Creating empty FAISS index...")
            # Dodaj przykładowy tekst zamiast pustej listy
            self.vector_store = FAISS.from_texts(["Witaj w bazie wiedzy!"], self.embeddings)
            self.vector_store.save_local(str(self.index_path))
            logger.info(f"Empty FAISS index created at {self.index_path}")
        except Exception as e:
            logger.error(f"Error initializing empty index: {e}")
            raise RAGError(f"Failed to initialize empty index: {e}")

    def get_document_count(self) -> int:
        """Zwraca liczbę dokumentów w bazie."""
        try:
            if self.vector_store is None:
                return 0
                
            docs = self.vector_store.similarity_search("", k=1000)
            return len(docs)
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0

    async def search(self, query: str, k: Optional[int] = None) -> List[Document]:
        """Wyszukuje podobne dokumenty."""
        try:
            if self.vector_store is None:
                return []
                
            k = k or self.config.max_results
            return self.vector_store.similarity_search(query, k=k)
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return [] 