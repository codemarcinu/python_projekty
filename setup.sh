#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up AI Assistant Dashboard...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p uploads
mkdir -p data/vector_store
mkdir -p logs

# Initialize empty FAISS index
echo -e "${YELLOW}Initializing FAISS index...${NC}"
python -c "from core.rag_manager import RAGManager; from core.config_manager import get_settings; RAGManager(get_settings().rag).init_empty_index()"

# Check if Ollama is running
echo -e "${YELLOW}Checking Ollama status...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${RED}Ollama is not running. Please start Ollama first:${NC}"
    echo "1. Install Ollama from https://ollama.ai"
    echo "2. Start Ollama service"
    echo "3. Pull required models:"
    echo "   ollama pull gemma3:12b"
    echo "   ollama pull bielik-11b-v2.3"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOL
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=300

# Models
PRIMARY_MODEL=gemma3:12b
DOCUMENT_MODEL=bielik-11b-v2.3

# Limits
MAX_FILE_SIZE=52428800  # 50MB
MAX_CONVERSATION_LENGTH=100
REQUEST_TIMEOUT=30

# Paths
UPLOAD_DIR=./uploads
FAISS_INDEX_PATH=./data/vector_store
EOL
fi

echo -e "${GREEN}Setup completed!${NC}"
echo -e "To start the dashboard, run:"
echo -e "${YELLOW}python main.py serve${NC}" 