"""
Moduł zarządzania plikami.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import shutil
import os
import logging
from datetime import datetime
import mimetypes
from core.config import get_settings
from pydantic import BaseModel
import json
import asyncio

logger = logging.getLogger(__name__)

class FileInfo(BaseModel):
    """Model informacji o pliku."""
    id: str
    name: str
    path: str
    size: int
    mime_type: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

class FileManager:
    """Klasa zarządzająca plikami."""
    
    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = self.settings.UPLOAD_DIR
        self.max_file_size = self.settings.MAX_FILE_SIZE
        
        # Inicjalizacja katalogu
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Dozwolone typy plików
        self.allowed_types = {
            # Dokumenty
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".rtf": "application/rtf",
            
            # Obrazy
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            
            # Arkusze kalkulacyjne
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".csv": "text/csv",
            
            # Prezentacje
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            
            # Archiwa
            ".zip": "application/zip",
            ".rar": "application/x-rar-compressed",
            ".7z": "application/x-7z-compressed",
            
            # Inne
            ".json": "application/json",
            ".xml": "application/xml",
            ".html": "text/html",
            ".htm": "text/html"
        }
        
    def _get_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """Pobiera informacje o pliku."""
        try:
            if not file_path.exists():
                return None
                
            stats = file_path.stat()
            
            return FileInfo(
                id=str(file_path),
                name=file_path.name,
                path=str(file_path),
                size=stats.st_size,
                mime_type=mimetypes.guess_type(str(file_path))[0] or "application/octet-stream",
                created_at=datetime.fromtimestamp(stats.st_ctime),
                updated_at=datetime.fromtimestamp(stats.st_mtime),
                metadata={}
            )
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None
            
    def is_allowed_file(self, filename: str) -> bool:
        """Sprawdza czy plik jest dozwolony."""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.allowed_types
        
    def get_allowed_types(self) -> Dict[str, str]:
        """Zwraca listę dozwolonych typów plików."""
        return self.allowed_types
        
    async def save_file(
        self,
        file_data: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[FileInfo]:
        """Zapisuje plik."""
        try:
            # Sprawdź rozmiar
            if len(file_data) > self.max_file_size:
                raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size} bytes")
                
            # Sprawdź typ
            if not self.is_allowed_file(filename):
                raise ValueError(f"File type not allowed: {filename}")
                
            # Przygotuj ścieżkę
            file_path = self.upload_dir / filename
            
            # Zapisz plik
            with open(file_path, "wb") as f:
                f.write(file_data)
                
            # Pobierz informacje
            file_info = self._get_file_info(file_path)
            if file_info:
                file_info.metadata = metadata or {}
                
            return file_info
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return None
            
    async def delete_file(self, filename: str) -> bool:
        """Usuwa plik."""
        try:
            file_path = self.upload_dir / filename
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
            
    async def get_file(self, filename: str) -> Optional[bytes]:
        """Pobiera zawartość pliku."""
        try:
            file_path = self.upload_dir / filename
            if file_path.exists():
                with open(file_path, "rb") as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"Error getting file: {e}")
            return None
            
    async def list_files(self) -> List[FileInfo]:
        """Zwraca listę plików."""
        try:
            files = []
            for file_path in self.upload_dir.glob("*"):
                if file_path.is_file():
                    file_info = self._get_file_info(file_path)
                    if file_info:
                        files.append(file_info)
            return files
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
            
    async def update_file_metadata(
        self,
        filename: str,
        metadata: Dict[str, Any]
    ) -> Optional[FileInfo]:
        """Aktualizuje metadane pliku."""
        try:
            file_path = self.upload_dir / filename
            file_info = self._get_file_info(file_path)
            if file_info:
                file_info.metadata.update(metadata)
                return file_info
            return None
        except Exception as e:
            logger.error(f"Error updating file metadata: {e}")
            return None 