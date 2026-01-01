#!/usr/bin/env python3
"""
Flask backend server for SQL Agent web interface
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from sql_agent import SQLAgent
from sqlalchemy import text
import os

app = Flask(__name__)
CORS(app)

# Initialize SQL Agent
DATABASE_URL = "postgresql://testuser:testpass@localhost:5432/testdb"
agent = SQLAgent(DATABASE_URL)

@app.route('/')
def index():
    """Serve the web interface"""
    return send_file('agent_web.html')

@app.route('/api/execute', methods=['POST'])
def execute_query():
    """Execute SQL query and return results"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        # Debug logging
        print(f"[DEBUG] Received query: '{query}'")
        print(f"[DEBUG] Query length: {len(query)}")
        
        if not query:
            return jsonify({
                'error': 'No query provided'
            }), 400
        
        # Process query through agent
        result = agent.process_query(query, verbose=False)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({
            'error': str(e),
            'overall_status': 'ERROR'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with agent.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     🤖 SQL Agent Web Server Starting                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Server running at: http://localhost:5000
Database: PostgreSQL (testdb)

Press Ctrl+C to stop the server
    """)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
