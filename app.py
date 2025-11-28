"""Main Flask application for LLM Analysis Quiz endpoint."""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import threading
from datetime import datetime

from config import Config
from quiz_solver import QuizSolver

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

Config.validate()
os.makedirs(Config.TEMP_DIR, exist_ok=True)
quiz_solver = QuizSolver()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/quiz', methods=['POST'])
def handle_quiz():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        required_fields = ['email', 'secret', 'url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        if data['email'] != Config.EMAIL:
            return jsonify({'error': 'Invalid email'}), 403
        
        if data['secret'] != Config.SECRET_KEY:
            return jsonify({'error': 'Invalid secret'}), 403
        
        logger.info(f"Authenticated request for URL: {data['url']}")
        
        quiz_url = data['url']
        thread = threading.Thread(
            target=quiz_solver.solve_quiz_chain,
            args=(quiz_url, data['email'], data['secret'])
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'received',
            'message': 'Quiz processing started',
            'url': quiz_url
        }), 200
        
    except Exception as e:
        logger.error(f"Error handling quiz request: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'name': 'LLM Analysis Quiz API',
        'version': '1.0.0',
        'endpoints': {'POST /quiz': 'Main quiz endpoint', 'GET /health': 'Health check'}
    }), 200

if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', Config.PORT))
    app.run(host=Config.HOST, port=port, debug=Config.DEBUG)
