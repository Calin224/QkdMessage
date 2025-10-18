# Flask WebSocket Server

A modern Flask application with WebSocket support using Flask-SocketIO.

## Features

- Real-time WebSocket communication
- Room-based messaging
- Broadcast messaging
- Connection management
- Modern web interface
- RESTful API endpoints
- Configurable settings

## Project Structure

```
QkdMessage/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration settings
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   └── message.py           # Message model
│   ├── routes/                  # HTTP routes
│   │   ├── __init__.py
│   │   └── routes.py            # Main routes
│   ├── websocket/               # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── handlers.py          # WebSocket event handlers
│   │   └── connection_manager.py # Connection management
│   └── templates/               # HTML templates
│       ├── base.html            # Base template
│       └── index.html           # Main page
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /home/stephan/Desktop/QkdMessage
   ```

2. **Activate your virtual environment:**
   ```bash
   source bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Running the Server

1. **Start the Flask WebSocket server:**
   ```bash
   python run.py
   ```

2. **Access the application:**
   - Web interface: http://localhost:5000
   - API status: http://localhost:5000/api/status
   - Health check: http://localhost:5000/api/health

## Usage

### Web Interface
- Open http://localhost:5000 in your browser
- Enter a username and room name (optional)
- Start chatting in real-time!

### WebSocket Events

**Client to Server:**
- `connect` - Client connects
- `disconnect` - Client disconnects
- `join_room` - Join a specific room
- `leave_room` - Leave current room
- `send_message` - Send message to room
- `broadcast` - Send message to all clients
- `get_connections` - Get connection count

**Server to Client:**
- `status` - Status messages
- `new_message` - New message in room
- `broadcast_message` - Broadcast message
- `room_joined` - Confirmation of joining room
- `room_left` - Confirmation of leaving room
- `connections_count` - Current connection count
- `error` - Error messages

### API Endpoints

- `GET /` - Main web interface
- `GET /api/status` - Server status
- `GET /api/health` - Health check

## Configuration

Edit `.env` file to configure:
- `SECRET_KEY` - Flask secret key
- `DEBUG` - Debug mode (True/False)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 5000)
- `DATABASE_URL` - Database connection (optional)
- `REDIS_URL` - Redis connection (optional)

## Development

### Adding New WebSocket Events

1. Add event handler in `app/websocket/handlers.py`
2. Update client-side JavaScript in `app/templates/index.html`
3. Test the new functionality

### Adding New Routes

1. Add route in `app/routes/routes.py`
2. Import and register in `app/routes/__init__.py`
3. Add corresponding template if needed

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Use a production WSGI server like Gunicorn
3. Configure Redis for message queue
4. Set up proper logging
5. Use environment variables for sensitive data

## Dependencies

- **Flask** - Web framework
- **Flask-SocketIO** - WebSocket support
- **python-socketio** - Socket.IO client/server
- **python-engineio** - Engine.IO client/server
- **python-dotenv** - Environment variable loading
- **eventlet** - Async networking library
- **redis** - Redis client (optional)

## License

This project is open source and available under the MIT License.
