from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect
from app.websocket import ws_bp
from app.websocket.connection_manager import ConnectionManager
from app import socketio
import json

# Initialize connection manager
connection_manager = ConnectionManager()

@ws_bp.route('/socket.io/')
def socketio_route():
    """WebSocket route handler"""
    pass

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    connection_manager.add_connection(request.sid)
    emit('status', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')
    connection_manager.remove_connection(request.sid)

@socketio.on('join_room')
def handle_join_room(data):
    """Handle client joining a room"""
    room = data.get('room')
    if room:
        join_room(room)
        emit('status', {'message': f'Joined room: {room}'})
        emit('room_joined', {'room': room}, room=room)

@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle client leaving a room"""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('status', {'message': f'Left room: {room}'})
        emit('room_left', {'room': room}, room=room)

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming messages"""
    room = data.get('room')
    message = data.get('message')
    username = data.get('username', 'Anonymous')
    
    if room and message:
        emit('new_message', {
            'username': username,
            'message': message,
            'timestamp': data.get('timestamp')
        }, room=room)
    else:
        emit('error', {'message': 'Invalid message format'})

@socketio.on('broadcast')
def handle_broadcast(data):
    """Handle broadcast messages to all connected clients"""
    message = data.get('message')
    if message:
        emit('broadcast_message', {
            'message': message,
            'timestamp': data.get('timestamp')
        }, broadcast=True)

@socketio.on('get_connections')
def handle_get_connections():
    """Send current connection count to client"""
    emit('connections_count', {
        'count': connection_manager.get_connection_count()
    })
