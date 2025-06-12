import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from app.core.config import get_settings
from app.api.v1.endpoints import chat
from app.core.rag_manager import RAGManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize components
app = FastAPI(title="AI Assistant API")
config = get_settings()

# Initialize RAG manager
rag_manager = RAGManager(
    model_name=config.rag.embedding_model,
    trust_remote_code=config.rag.trust_remote_code
)

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    try:
        await rag_manager.initialize()
        logger.info("RAG manager initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing RAG manager: {e}")
        raise

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files from frontend
if os.path.exists("frontend/build"):
    app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

# Include routers
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

@app.get("/api/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Fallback for root endpoint
if not os.path.exists("frontend/build"):
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "AI Assistant API", "status": "running", "version": "1.0.0"}

# Error handling middleware
@app.middleware("http")
async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    ) 