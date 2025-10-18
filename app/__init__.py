from flask import Flask
from flask_socketio import SocketIO
from app.config import Config

socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    from app.routes import main_bp
    from app.websocket import ws_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(ws_bp)
    
    return app
