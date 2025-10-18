#!/usr/bin/env python3
"""
Flask WebSocket Server Entry Point
"""

from app import create_app, socketio
from app.config import Config

if __name__ == '__main__':
    app = create_app(Config)
    
    print("Starting Flask WebSocket Server...")
    print(f"Server will be available at: http://{app.config['HOST']}:{app.config['PORT']}")
    print("Press Ctrl+C to stop the server")
    
    # Run the application with SocketIO
    socketio.run(
        app,
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG'],
        allow_unsafe_werkzeug=True
    )
