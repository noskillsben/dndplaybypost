from typing import Dict, Set
from uuid import UUID
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for campaign chat rooms"""
    
    def __init__(self):
        # campaign_id -> set of WebSocket connections
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        # websocket -> user_id mapping for tracking
        self.connection_users: Dict[WebSocket, UUID] = {}
    
    async def connect(self, websocket: WebSocket, campaign_id: UUID, user_id: UUID):
        """Accept a WebSocket connection and add to campaign room"""
        await websocket.accept()
        
        if campaign_id not in self.active_connections:
            self.active_connections[campaign_id] = set()
        
        self.active_connections[campaign_id].add(websocket)
        self.connection_users[websocket] = user_id
        
        logger.info(f"User {user_id} connected to campaign {campaign_id}")
    
    def disconnect(self, websocket: WebSocket, campaign_id: UUID):
        """Remove a WebSocket connection from campaign room"""
        if campaign_id in self.active_connections:
            self.active_connections[campaign_id].discard(websocket)
            
            # Clean up empty campaign rooms
            if not self.active_connections[campaign_id]:
                del self.active_connections[campaign_id]
        
        user_id = self.connection_users.pop(websocket, None)
        logger.info(f"User {user_id} disconnected from campaign {campaign_id}")
    
    async def broadcast(self, campaign_id: UUID, message: dict):
        """Broadcast a message to all connections in a campaign"""
        if campaign_id not in self.active_connections:
            return
        
        # Create a copy to avoid modification during iteration
        connections = self.active_connections[campaign_id].copy()
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                # Remove dead connections
                self.disconnect(connection, campaign_id)
    
    def get_connection_count(self, campaign_id: UUID) -> int:
        """Get number of active connections for a campaign"""
        return len(self.active_connections.get(campaign_id, set()))


# Global connection manager instance
manager = ConnectionManager()
