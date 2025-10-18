import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # WebSocket configuration
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # Database configuration (if needed)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    
    # Redis configuration (for SocketIO message queue)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
