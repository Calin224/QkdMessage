#!/bin/bash

# Flask WebSocket Server Startup Script

echo "Starting Flask WebSocket Server..."

# Check if virtual environment exists
if [ ! -d "bin" ]; then
    echo "Virtual environment not found. Please create one first:"
    echo "python -m venv ."
    echo "source bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source bin/activate

# Check if requirements are installed
if ! python -c "import flask_socketio" 2>/dev/null; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Start the server
echo "Server starting at http://localhost:5000"
python run.py
