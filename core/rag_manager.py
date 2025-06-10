"""
Moduł zarządzający systemem RAG (Retrieval-Augmented Generation).

Ten moduł zawiera implementację klasy RAGManager, która odpowiada za:
- Zarządzanie wektorowym magazynem dokumentów
- Tworzenie i ładowanie indeksów FAISS
- Integrację z modelami embeddingów
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever
from core.config_manager import RAGSettings, get_settings

logger = logging.getLogger(__name__)

class RAGError(Exception):
    """Base exception for RAG-related errors."""
    pass

class CustomEmbeddings:
    """Custom embeddings class using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embeddings model.
        
        Args:
            model_name: Name of the sentence-transformers model to use.
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Initialized sentence-transformers model: {model_name}")
        except Exception as e:
            logger.error(f"Error initializing sentence-transformers model: {e}")
            raise RAGError(f"Failed to initialize embeddings model: {e}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents.
        
        Args:
            texts: List of texts to embed.
            
        Returns:
            List of embeddings.
        """
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            raise RAGError(f"Failed to embed documents: {e}")
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a query.
        
        Args:
            text: Text to embed.
            
        Returns:
            Embedding of the text.
        """
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise RAGError(f"Failed to embed query: {e}")

class RAGManager:
    """Menedżer systemu RAG."""
    
    def __init__(self, config: RAGSettings):
        """
        Inicjalizuje menedżera RAG.
        
        Args:
            config: Ustawienia RAG
        """
        self.config = config
        self.settings = get_settings()
        self.embedding_model = self.settings.rag.embedding_model
        self.index_path = self.settings.rag.index_path
        self.upload_dir = self.settings.rag.upload_dir
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []
        self.vector_store = None
    
    async def initialize(self):
        """Inicjalizuje model embeddingów i indeks FAISS."""
        try:
            # Inicjalizacja modelu embeddingów
            self.model = SentenceTransformer(
                self.embedding_model,
                trust_remote_code=True
            )
            
            # Inicjalizacja indeksu FAISS
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
            else:
                self.index_path.parent.mkdir(parents=True, exist_ok=True)
                self.index = faiss.IndexFlatL2(384)  # 384 to wymiar wektora dla all-MiniLM-L6-v2
            
            # Wczytanie dokumentów
            self.documents = await self._load_documents()
            
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG system: {e}")
            raise
    
    async def _load_documents(self) -> List[Dict[str, Any]]:
        """
        Wczytuje dokumenty z katalogu uploads.
        
        Returns:
            List[Dict[str, Any]]: Lista dokumentów
        """
        documents = []
        if self.upload_dir.exists():
            for file_path in self.upload_dir.glob("*"):
                if file_path.is_file():
                    documents.append({
                        "id": str(file_path),
                        "name": file_path.name,
                        "path": str(file_path)
                    })
        return documents
    
    async def add_document(self, file_path: str) -> bool:
        """
        Dodaje dokument do systemu RAG.
        
        Args:
            file_path: Ścieżka do pliku
            
        Returns:
            bool: True jeśli dokument został dodany pomyślnie
        """
        try:
            if not self.model or not self.index:
                await self.initialize()
            
            if not self.model or not self.index:
                raise Exception("Failed to initialize RAG system")
            
            # Wczytanie dokumentu
            with open(file_path, "r") as f:
                content = f.read()
            
            # Generowanie embeddingu
            embedding = self.model.encode([content])[0]
            
            # Dodanie do indeksu
            self.index.add(np.array([embedding], dtype=np.float32).reshape(1, -1))
            
            # Dodanie do listy dokumentów
            self.documents.append({
                "id": file_path,
                "name": Path(file_path).name,
                "path": file_path,
                "content": content
            })
            
            # Zapisanie indeksu
            faiss.write_index(self.index, str(self.index_path))
            
            logger.info(f"Document {file_path} added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document {file_path}: {e}")
            return False
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        Zwraca listę dokumentów w systemie RAG.
        
        Returns:
            List[Dict[str, Any]]: Lista dokumentów
        """
        return self.documents
    
    async def search(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Wyszukuje dokumenty podobne do zapytania.
        
        Args:
            query: Zapytanie
            k: Liczba wyników (opcjonalnie)
            
        Returns:
            List[Document]: Lista podobnych dokumentów
        """
        try:
            if not self.model or not self.index:
                await self.initialize()
            
            if not self.model or not self.index:
                raise Exception("Failed to initialize RAG system")
            
            k = k or self.settings.rag.max_results
            
            # Generowanie embeddingu zapytania
            query_embedding = self.model.encode([query])[0]
            
            # Wyszukiwanie podobnych dokumentów
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32).reshape(1, -1),
                k
            )
            
            # Przygotowanie wyników
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    results.append(Document(
                        page_content=doc["content"],
                        metadata={
                            "source": doc["path"],
                            "score": float(distances[0][i])
                        }
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching RAG system: {e}")
            return []
    
    def get_retriever(self) -> Optional[BaseRetriever]:
        """Zwraca retriever do wyszukiwania dokumentów w bazie wektorowej."""
        if self.vector_store is None:
            return None
        return self.vector_store.as_retriever(
            search_kwargs={"k": self.settings.rag.max_results}
        )
    
    def cleanup(self):
        """Zamyka połączenia i zwalnia zasoby."""
        if self.index:
            faiss.write_index(self.index, str(self.index_path))
        self.model = None
        self.index = None
    
    def delete_document(self, filename_to_delete: str) -> bool:
        """
        Usuwa dokument z systemu RAG.
        
        Args:
            filename_to_delete: Nazwa pliku do usunięcia
            
        Returns:
            bool: True jeśli dokument został usunięty pomyślnie
        """
        try:
            if not self.model or not self.index:
                self.initialize()
            
            if not self.model or not self.index:
                raise Exception("Failed to initialize RAG system")
            
            # Znajdź dokument do usunięcia
            doc_to_delete = None
            doc_index = -1
            for i, doc in enumerate(self.documents):
                if doc["name"] == filename_to_delete:
                    doc_to_delete = doc
                    doc_index = i
                    break
            
            if doc_to_delete is None:
                logger.warning(f"Document {filename_to_delete} not found")
                return False
            
            # Usuń dokument z listy
            self.documents.pop(doc_index)
            
            # Zaktualizuj indeks FAISS
            self.index = faiss.IndexFlatL2(384)  # Reset index
            for doc in self.documents:
                embedding = self.model.encode([doc["content"]])[0]
                self.index.add(np.array([embedding], dtype=np.float32).reshape(1, -1))
            
            # Zapisanie indeksu
            faiss.write_index(self.index, str(self.index_path))
            
            logger.info(f"Document {filename_to_delete} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {filename_to_delete}: {e}")
            return False
    
    def init_empty_index(self) -> None:
        """Inicjalizuje pusty indeks FAISS."""
        try:
            self.index = faiss.IndexFlatL2(384)
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_path))
            logger.info("Empty FAISS index initialized")
        except Exception as e:
            logger.error(f"Error initializing empty index: {e}")
            raise
    
    def get_document_count(self) -> int:
        """
        Zwraca liczbę dokumentów w systemie RAG.
        
        Returns:
            int: Liczba dokumentów
        """
        return len(self.documents) 