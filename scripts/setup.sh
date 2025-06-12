#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Setting up development environment...${NC}"

# Create virtual environment for backend
echo -e "${GREEN}Creating Python virtual environment...${NC}"
python -m venv backend/venv
source backend/venv/bin/activate

# Install backend dependencies
echo -e "${GREEN}Installing backend dependencies...${NC}"
cd backend
pip install poetry
poetry install
cd ..

# Install frontend dependencies
echo -e "${GREEN}Installing frontend dependencies...${NC}"
cd frontend
npm install
cd ..

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p backend/uploads
mkdir -p backend/logs

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo -e "${GREEN}Creating .env file...${NC}"
    cat > backend/.env << EOL
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=python_projekty
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
EOL
fi

echo -e "${BLUE}Setup complete!${NC}"
echo -e "To start the development environment:"
echo -e "1. Start Ollama: ollama serve"
echo -e "2. Start backend: cd backend && poetry run uvicorn app.main:app --reload"
echo -e "3. Start frontend: cd frontend && npm run dev" 