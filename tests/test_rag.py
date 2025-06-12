from core.config_manager import get_settings
from core.rag_manager import RAGManager
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def main():
    try:
        # Get settings
        settings = get_settings()
        print("Settings loaded successfully")
        print(f"RAG Settings: {settings.rag}")
        
        # Initialize RAG Manager
        rag_manager = RAGManager(settings.rag)
        print("RAG Manager initialized successfully")
        
        # Initialize empty index
        rag_manager.init_empty_index()
        print("Empty index initialized successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main() 