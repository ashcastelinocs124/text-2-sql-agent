#!/usr/bin/env python3
"""
AgentBeats-compatible entrypoint for Sample Purple Agent (SQL Generator).

Starts a Purple Agent server that generates SQL using LLMs.

Usage:
    python entrypoint_purple.py --host 0.0.0.0 --port 8080 --llm gemini
    python entrypoint_purple.py --port 8081 --llm openai --model gpt-4o
"""

import argparse
import os
import sys

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, request, jsonify
from flask_cors import CORS

from a2a.purple_agent import SampleSQLAgent


def create_app(
    llm_provider: str = "gemini",
    model: str = None,
    api_key: str = None,
    card_url: str = None,
    agent_name: str = "Sample SQL Agent",
) -> Flask:
    """Create Flask app for Purple Agent."""
    app = Flask(__name__)
    CORS(app)

    # Initialize SQL Agent
    agent = SampleSQLAgent(
        llm_provider=llm_provider,
        model=model,
        api_key=api_key,
    )

    @app.route("/", methods=["GET"])
    def index():
        """Agent info endpoint."""
        return jsonify({
            "name": agent_name,
            "type": "purple_agent",
            "version": "1.0.0",
            "description": "Purple Agent that generates SQL using LLMs",
            "endpoints": {
                "info": "GET /",
                "health": "GET /health",
                "generate": "POST /generate",
                "agent_card": "GET /.well-known/agent.json",
            },
            "capabilities": {
                "llm_provider": llm_provider,
                "model": model or "default",
            }
        })

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy"})

    @app.route("/.well-known/agent.json", methods=["GET"])
    def agent_card():
        """A2A Agent Card endpoint."""
        return jsonify({
            "name": agent_name,
            "description": f"Purple Agent that generates SQL queries using {llm_provider}",
            "version": "1.0.0",
            "url": card_url or request.host_url.rstrip("/"),
            "capabilities": {
                "streaming": False,
                "pushNotifications": False,
            },
            "skills": [
                {
                    "id": "sql_generation",
                    "name": "SQL Generation",
                    "description": "Generates SQL queries from natural language questions",
                    "inputModes": ["application/json"],
                    "outputModes": ["application/json"],
                }
            ],
            "defaultInputModes": ["application/json"],
            "defaultOutputModes": ["application/json"],
        })

    @app.route("/generate", methods=["POST"])
    def generate():
        """
        Generate SQL from a task.

        Expected request body:
        {
            "task_id": "sqlite_simple_select",
            "question": "Get all customers from New York",
            "schema": {...},
            "dialect": "sqlite"
        }

        Returns:
        {
            "sql": "SELECT * FROM customers WHERE city = 'New York'",
            "reasoning": "...",
            "task_id": "sqlite_simple_select"
        }
        """
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body required"}), 400

        if not data.get("question"):
            return jsonify({"error": "Question required"}), 400

        try:
            # Use synchronous version
            result = agent.handle_task_sync(data)
            return jsonify(result)

        except Exception as e:
            return jsonify({
                "sql": "",
                "error": str(e),
                "task_id": data.get("task_id"),
            }), 500

    # Also support A2A-style message endpoint
    @app.route("/a2a/message", methods=["POST"])
    def a2a_message():
        """
        Handle A2A message format.

        The Green Agent may send messages in A2A format.
        """
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body required"}), 400

        # Extract task from A2A message parts
        parts = data.get("parts", [])
        task_data = {}

        for part in parts:
            if part.get("type") == "data":
                task_data = part.get("data", {})
                break
            elif part.get("type") == "text":
                # Try to parse as task
                task_data = {"question": part.get("text", "")}

        if not task_data:
            task_data = data  # Fallback to whole body

        try:
            result = agent.handle_task_sync(task_data)
            return jsonify({
                "parts": [
                    {
                        "type": "data",
                        "data": result,
                    }
                ]
            })

        except Exception as e:
            return jsonify({
                "parts": [
                    {
                        "type": "data",
                        "data": {
                            "sql": "",
                            "error": str(e),
                        }
                    }
                ]
            }), 500

    return app


def main():
    parser = argparse.ArgumentParser(
        description="Sample Purple Agent (SQL Generator)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind (default: 8080)"
    )
    parser.add_argument(
        "--card-url",
        help="URL for agent card advertisement"
    )
    parser.add_argument(
        "--llm",
        default="gemini",
        choices=["gemini", "openai"],
        help="LLM provider (default: gemini)"
    )
    parser.add_argument(
        "--model",
        help="Model name (optional, uses provider default)"
    )
    parser.add_argument(
        "--api-key",
        help="API key (optional, uses env variable)"
    )
    parser.add_argument(
        "--name",
        default="Sample SQL Agent",
        help="Agent name for identification"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    card_url = args.card_url or f"http://{args.host}:{args.port}"

    print(f"Starting Purple Agent '{args.name}' on {args.host}:{args.port}")
    print(f"LLM: {args.llm}, Model: {args.model or 'default'}")
    print(f"Agent card URL: {card_url}")

    app = create_app(
        llm_provider=args.llm,
        model=args.model,
        api_key=args.api_key,
        card_url=card_url,
        agent_name=args.name,
    )

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
