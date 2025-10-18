import threading
from typing import Set

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.connections: Set[str] = set()
        self.lock = threading.Lock()
    
    def add_connection(self, connection_id: str):
        """Add a new connection"""
        with self.lock:
            self.connections.add(connection_id)
            print(f"Connection added. Total: {len(self.connections)}")
    
    def remove_connection(self, connection_id: str):
        """Remove a connection"""
        with self.lock:
            self.connections.discard(connection_id)
            print(f"Connection removed. Total: {len(self.connections)}")
    
    def get_connection_count(self) -> int:
        """Get current connection count"""
        with self.lock:
            return len(self.connections)
    
    def get_connections(self) -> Set[str]:
        """Get all connection IDs"""
        with self.lock:
            return self.connections.copy()
    
    def is_connected(self, connection_id: str) -> bool:
        """Check if connection exists"""
        with self.lock:
            return connection_id in self.connections
