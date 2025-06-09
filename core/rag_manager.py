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
from core.config_manager import ConfigManager

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
    
    def __init__(self, config: ConfigManager):
        """
        Inicjalizuje menedżera RAG.
        
        Args:
            config: Menedżer konfiguracji
        """
        self.config = config
        self.embedding_model = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.index_path = Path(os.getenv("FAISS_INDEX_PATH", "data/faiss_index"))
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []
    
    async def initialize(self):
        """Inicjalizuje model embeddingów i indeks FAISS."""
        try:
            # Inicjalizacja modelu embeddingów
            self.model = SentenceTransformer(self.embedding_model)
            
            # Inicjalizacja indeksu FAISS
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
            else:
                self.index_path.parent.mkdir(parents=True, exist_ok=True)
                self.index = faiss.IndexFlatL2(384)  # 384 to wymiar wektora dla all-MiniLM-L6-v2
            
            # Wczytanie dokumentów
            self.documents = self._load_documents()
            
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG system: {e}")
            raise
    
    def _load_documents(self) -> List[Dict[str, Any]]:
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
            self.index.add(np.array([embedding], dtype=np.float32))
            
            # Dodanie do listy dokumentów
            self.documents.append({
                "id": file_path,
                "name": Path(file_path).name,
                "path": file_path
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
    
    async def query(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Wyszukuje dokumenty podobne do zapytania.
        
        Args:
            query: Zapytanie
            k: Liczba wyników
            
        Returns:
            List[Dict[str, Any]]: Lista podobnych dokumentów
        """
        try:
            if not self.model or not self.index:
                await self.initialize()
            
            if not self.model or not self.index:
                raise Exception("Failed to initialize RAG system")
            
            # Generowanie embeddingu zapytania
            query_embedding = self.model.encode([query])[0]
            
            # Wyszukiwanie podobnych dokumentów
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32),
                k
            )
            
            # Przygotowanie wyników
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    results.append({
                        "document": doc,
                        "score": float(distances[0][i])
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying RAG system: {e}")
            return []
    
    async def cleanup(self):
        """Zamyka połączenia i zwalnia zasoby."""
        if self.index:
            faiss.write_index(self.index, str(self.index_path))
        self.model = None
        self.index = None

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