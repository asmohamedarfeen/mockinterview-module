"""
WebSocket connection manager
Tracks active connections and routes messages to appropriate handlers
"""
from typing import Dict
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
import logging

from app.models.interview import InterviewSession, InterviewState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and session state
    In-memory storage for MVP (Phase 1)
    """
    
    def __init__(self):
        # Map session_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map session_id -> InterviewSession
        self.sessions: Dict[str, InterviewSession] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """
        Register a new WebSocket connection
        Returns True if connection successful, False if session already exists
        """
        try:
            await websocket.accept()
            self.active_connections[session_id] = websocket
            logger.info(f"WebSocket connected: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect WebSocket {session_id}: {e}")
            return False
    
    def disconnect(self, session_id: str):
        """
        Remove WebSocket connection and clean up session
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")
        
        # Optionally keep session data for report generation
        # For now, we'll keep it until explicitly cleaned up
    
    async def send_personal_message(self, message: dict, session_id: str):
        """
        Send message to a specific session
        """
        if session_id not in self.active_connections:
            logger.warning(f"Attempted to send message to non-existent session: {session_id}")
            return
        
        connection = self.active_connections[session_id]
        try:
            await connection.send_json(jsonable_encoder(message))
        except Exception as e:
            logger.error(f"Failed to send message to {session_id}: {e}")
            # Remove broken connection
            self.disconnect(session_id)
    
    async def broadcast(self, message: dict):
        """
        Broadcast message to all active connections
        """
        disconnected = []
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_json(jsonable_encoder(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to {session_id}: {e}")
                disconnected.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected:
            self.disconnect(session_id)
    
    def get_session(self, session_id: str) -> InterviewSession | None:
        """
        Retrieve session by ID
        """
        return self.sessions.get(session_id)
    
    def create_session(self, session: InterviewSession):
        """
        Create or update a session
        """
        self.sessions[session.session_id] = session
        logger.info(f"Session created/updated: {session.session_id}")
    
    def update_session_state(self, session_id: str, state: InterviewState):
        """
        Update session state
        """
        if session_id in self.sessions:
            self.sessions[session_id].state = state
            logger.debug(f"Session {session_id} state updated to {state}")
    
    def is_connected(self, session_id: str) -> bool:
        """
        Check if session has active WebSocket connection
        """
        return session_id in self.active_connections


# Global connection manager instance
manager = ConnectionManager()
