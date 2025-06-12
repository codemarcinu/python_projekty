"""
Moduł zarządzania RAG (Retrieval-Augmented Generation).
"""

from typing import List, Optional, Dict, Any
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from pathlib import Path
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class Document(BaseModel):
    """Model dokumentu."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None

class RAGManager:
    """Klasa zarządzająca RAG."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_path: Optional[str] = None
    ):
        self.model = SentenceTransformer(model_name)
        self.index_path = index_path or "./data/faiss_index"
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.documents: Dict[str, Document] = {}
        
    async def initialize(self):
        """Inicjalizuje menedżer RAG."""
        try:
            # Utwórz katalog jeśli nie istnieje
            Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Wczytaj istniejący indeks lub utwórz nowy
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                # Wczytaj dokumenty
                self._load_documents()
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
                
            logger.info("RAG manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG manager: {e}")
            raise
            
    def _load_documents(self):
        """Wczytuje dokumenty z pliku."""
        try:
            docs_path = Path(self.index_path).parent / "documents.json"
            if docs_path.exists():
                with open(docs_path, "r") as f:
                    data = json.load(f)
                    for doc_data in data:
                        doc = Document(**doc_data)
                        self.documents[doc.id] = doc
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            
    def _save_documents(self):
        """Zapisuje dokumenty do pliku."""
        try:
            docs_path = Path(self.index_path).parent / "documents.json"
            with open(docs_path, "w") as f:
                json.dump([doc.dict() for doc in self.documents.values()], f)
        except Exception as e:
            logger.error(f"Error saving documents: {e}")
            
    async def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Dodaje dokument do indeksu."""
        try:
            # Generuj embedding
            embedding = self.model.encode(content)
            
            # Twórz dokument
            doc = Document(
                id=str(len(self.documents)),
                content=content,
                metadata=metadata or {},
                embedding=embedding
            )
            
            # Dodaj do indeksu
            self.index.add(np.array([embedding]))
            self.documents[doc.id] = doc
            
            # Zapisz zmiany
            faiss.write_index(self.index, self.index_path)
            self._save_documents()
            
            return doc
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
            
    async def search(
        self,
        query: str,
        k: int = 5
    ) -> List[Document]:
        """Wyszukuje podobne dokumenty."""
        try:
            # Generuj embedding zapytania
            query_embedding = self.model.encode(query)
            
            # Wyszukaj podobne dokumenty
            distances, indices = self.index.search(
                np.array([query_embedding]),
                k
            )
            
            # Zwróć dokumenty
            results = []
            for idx in indices[0]:
                if idx < len(self.documents):
                    doc_id = str(idx)
                    if doc_id in self.documents:
                        results.append(self.documents[doc_id])
                        
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
            
    async def delete_document(self, doc_id: str) -> bool:
        """Usuwa dokument z indeksu."""
        try:
            if doc_id in self.documents:
                # Usuń z indeksu
                self.index.remove_ids(np.array([int(doc_id)]))
                
                # Usuń z dokumentów
                del self.documents[doc_id]
                
                # Zapisz zmiany
                faiss.write_index(self.index, self.index_path)
                self._save_documents()
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
            
    async def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Document]:
        """Aktualizuje dokument."""
        try:
            if doc_id in self.documents:
                # Generuj nowy embedding
                embedding = self.model.encode(content)
                
                # Aktualizuj dokument
                doc = self.documents[doc_id]
                doc.content = content
                doc.metadata = metadata or doc.metadata
                doc.embedding = embedding
                
                # Aktualizuj indeks
                self.index.remove_ids(np.array([int(doc_id)]))
                self.index.add(np.array([embedding]))
                
                # Zapisz zmiany
                faiss.write_index(self.index, self.index_path)
                self._save_documents()
                
                return doc
            return None
            
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return None 