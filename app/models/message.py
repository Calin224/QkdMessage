from datetime import datetime
from typing import Dict, Any

class Message:
    """Message model for WebSocket communication"""
    
    def __init__(self, content: str, username: str = None, room: str = None, message_type: str = 'text'):
        self.content = content
        self.username = username or 'Anonymous'
        self.room = room
        self.message_type = message_type
        self.timestamp = datetime.utcnow()
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique message ID"""
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'content': self.content,
            'username': self.username,
            'room': self.room,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        message = cls(
            content=data['content'],
            username=data.get('username'),
            room=data.get('room'),
            message_type=data.get('message_type', 'text')
        )
        message.id = data.get('id', message.id)
        if 'timestamp' in data:
            message.timestamp = datetime.fromisoformat(data['timestamp'])
        return message
