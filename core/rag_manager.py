"""
Moduł zarządzający systemem RAG (Retrieval-Augmented Generation).

Ten moduł zawiera implementację klasy RAGManager, która odpowiada za:
- Zarządzanie wektorowym magazynem dokumentów
- Tworzenie i ładowanie indeksów FAISS
- Integrację z modelami embeddingów
"""

from pathlib import Path
from typing import Optional

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

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