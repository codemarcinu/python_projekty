"""
Moduł zarządzania WebSocket.
"""

from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
import asyncio
from datetime import datetime
from core.logger import get_logger

logger = get_logger(__name__)

class ConnectionManager:
    """Klasa zarządzająca połączeniami WebSocket."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.connection_users: Dict[str, str] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str, user_id: str):
        """Nawiązuje połączenie WebSocket."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_users[client_id] = user_id
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(client_id)
        
        logger.info(f"WebSocket connected: {client_id} (user: {user_id})")
        
    async def disconnect(self, client_id: str):
        """Zamyka połączenie WebSocket."""
        if client_id in self.active_connections:
            user_id = self.connection_users.get(client_id)
            if user_id:
                self.user_connections[user_id].discard(client_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
                    
            del self.active_connections[client_id]
            del self.connection_users[client_id]
            
            logger.info(f"WebSocket disconnected: {client_id}")
            
    async def send_message(self, client_id: str, message: Any):
        """Wysyła wiadomość do klienta."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                await self.disconnect(client_id)
                
    async def broadcast(self, message: Any, exclude: Optional[str] = None):
        """Wysyła wiadomość do wszystkich klientów."""
        for client_id in list(self.active_connections.keys()):
            if client_id != exclude:
                await self.send_message(client_id, message)
                
    async def send_to_user(self, user_id: str, message: Any):
        """Wysyła wiadomość do wszystkich połączeń użytkownika."""
        if user_id in self.user_connections:
            for client_id in list(self.user_connections[user_id]):
                await self.send_message(client_id, message)
                
    async def handle_message(self, client_id: str, message: Any):
        """Obsługuje wiadomość od klienta."""
        try:
            # Tutaj można dodać logikę obsługi różnych typów wiadomości
            if isinstance(message, dict):
                message_type = message.get("type")
                
                if message_type == "ping":
                    await self.send_message(client_id, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif message_type == "chat":
                    # Przykład obsługi wiadomości czatu
                    user_id = self.connection_users.get(client_id)
                    if user_id:
                        await self.broadcast({
                            "type": "chat",
                            "user_id": user_id,
                            "message": message.get("content"),
                            "timestamp": datetime.now().isoformat()
                        }, exclude=client_id)
                        
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            
    async def start_listening(self, websocket: WebSocket, client_id: str, user_id: str):
        """Rozpoczyna nasłuchiwanie wiadomości od klienta."""
        await self.connect(websocket, client_id, user_id)
        
        try:
            while True:
                message = await websocket.receive_json()
                await self.handle_message(client_id, message)
                
        except WebSocketDisconnect:
            await self.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error in WebSocket connection {client_id}: {e}")
            await self.disconnect(client_id)
            
    def get_active_connections_count(self) -> int:
        """Zwraca liczbę aktywnych połączeń."""
        return len(self.active_connections)
        
    def get_user_connections_count(self, user_id: str) -> int:
        """Zwraca liczbę połączeń użytkownika."""
        return len(self.user_connections.get(user_id, set()))
        
    def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Zwraca informacje o połączeniu."""
        if client_id in self.active_connections:
            user_id = self.connection_users.get(client_id)
            return {
                "client_id": client_id,
                "user_id": user_id,
                "connected_at": datetime.now().isoformat()
            }
        return None 