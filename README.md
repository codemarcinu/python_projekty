# Modular AI Assistant

A modern, modular AI assistant that runs 100% locally on your device. Built with Python, this application provides both a web interface and a command-line interface for interacting with local language models through Ollama.

## Features

- **100% Local Operation**: All processing happens on your device, ensuring complete privacy
- **Dual Interface**:
  - Modern web interface with real-time chat
  - Powerful command-line interface
- **RAG System**: Add your own documents and ask questions about them
- **Modular Architecture**: Easy to extend with new capabilities
- **Multiple Model Support**: Works with any model available in Ollama

## Prerequisites

- Python 3.11 or newer
- [Ollama](https://ollama.com/) installed and running
- A model downloaded in Ollama (e.g., `ollama pull llama2`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-assistant.git
   cd ai-assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` to configure your settings.

## Usage

### Web Interface

Start the web server:
```bash
python main.py serve
```
Then open your browser to `http://localhost:8000`

### Command Line Interface

Start an interactive chat session:
```bash
python main.py cli
```

Process a RAG query:
```bash
python main.py rag "What is the main topic of my documents?"
```

Add a document to the RAG system:
```bash
python main.py add-doc path/to/your/document.pdf
```

List all conversations:
```bash
python main.py list-conversations
```

## Project Structure

```
/
├── core/                 # Core application components
│   ├── ai_engine.py     # Main AI orchestration
│   ├── llm_manager.py   # LLM interaction
│   ├── conversation_handler.py  # Chat history management
│   └── config_manager.py  # Configuration management
├── interfaces/          # User interfaces
│   ├── web_ui.py       # FastAPI web interface
│   └── cli.py          # Typer CLI interface
├── modules/            # Extensible modules
├── data/              # User data and vector store
├── templates/         # HTML templates
├── static/           # Static web assets
├── main.py           # Application entry point
└── requirements.txt  # Project dependencies
```

## Configuration

The application is configured through environment variables in the `.env` file:

```env
# LLM Settings
LLM_MODEL=llama2
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# RAG Settings
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Web Interface
WEB_HOST=127.0.0.1
WEB_PORT=8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Ollama](https://ollama.com/) for providing the local LLM infrastructure
- [LangChain](https://python.langchain.com/) for AI orchestration
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Typer](https://typer.tiangolo.com/) for the CLI framework 