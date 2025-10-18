from flask import render_template, jsonify, request
from app.routes import main_bp

@main_bp.route('/')
def index():
    """Main page with WebSocket client"""
    return render_template('index.html')

@main_bp.route('/api/status')
def api_status():
    """API endpoint to check server status"""
    return jsonify({
        'status': 'online',
        'message': 'Flask WebSocket server is running'
    })

@main_bp.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': request.environ.get('REQUEST_TIME', 'unknown')
    })
