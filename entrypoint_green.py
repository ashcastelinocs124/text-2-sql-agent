#!/usr/bin/env python3
"""
AgentBeats-compatible entrypoint for AgentX Green Agent.

Starts the SQL Benchmark Green Agent server that evaluates Purple Agents.

Usage:
    python entrypoint_green.py --host 0.0.0.0 --port 8001
    python entrypoint_green.py --port 8001 --dialect sqlite --scorer-preset strict
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from a2a.green_agent import SQLBenchmarkGreenAgent, AssessmentConfig


def create_app(
    dialect: str = "sqlite",
    scorer_preset: str = "default",
    card_url: str = None,
) -> Flask:
    """Create Flask app for Green Agent."""
    app = Flask(__name__)
    CORS(app)

    # Initialize Green Agent
    agent = SQLBenchmarkGreenAgent(
        dialect=dialect,
        scorer_preset=scorer_preset,
    )

    @app.route("/", methods=["GET"])
    def index():
        """Agent info endpoint."""
        return jsonify({
            "name": "AgentX SQL Benchmark",
            "type": "green_agent",
            "version": "1.0.0",
            "description": "Green Agent for evaluating SQL-generating AI agents",
            "endpoints": {
                "info": "GET /",
                "health": "GET /health",
                "schema": "GET /schema",
                "assess": "POST /assess",
                "agent_card": "GET /.well-known/agent.json",
            },
            "capabilities": {
                "scoring_dimensions": 7,
                "supported_dialects": ["sqlite", "duckdb", "postgresql"],
                "multi_agent": True,
                "streaming": True,
            }
        })

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy"})

    @app.route("/schema", methods=["GET"])
    def schema():
        """Get database schema for Purple Agents."""
        schema_info = agent.get_schema_info()
        return jsonify(schema_info)

    @app.route("/.well-known/agent.json", methods=["GET"])
    def agent_card():
        """A2A Agent Card endpoint."""
        return jsonify({
            "name": "AgentX SQL Benchmark",
            "description": "Green Agent for evaluating SQL-generating AI agents with 7-dimensional scoring",
            "version": "1.0.0",
            "url": card_url or request.host_url.rstrip("/"),
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
            },
            "skills": [
                {
                    "id": "sql_benchmark",
                    "name": "SQL Benchmark Assessment",
                    "description": "Evaluates SQL agents on correctness, efficiency, safety, completeness, semantic accuracy, best practices, and plan quality",
                    "inputModes": ["application/json"],
                    "outputModes": ["application/json"],
                }
            ],
            "defaultInputModes": ["application/json"],
            "defaultOutputModes": ["application/json"],
        })

    @app.route("/assess", methods=["POST"])
    def assess():
        """
        Start an assessment.

        Expected request body:
        {
            "participants": {
                "agent_1": "http://purple-agent-1:8080",
                "agent_2": "http://purple-agent-2:8081"
            },
            "config": {
                "difficulty": ["easy", "medium"],
                "task_count": 10,
                "scorer_preset": "default"
            }
        }
        """
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body required"}), 400

        participants = data.get("participants", {})
        config = data.get("config", {})

        if not participants:
            return jsonify({"error": "No participants specified"}), 400

        # Run assessment synchronously (for simplicity)
        # In production, use async/streaming
        def run_assessment():
            results = []

            async def collect_updates():
                async for update in agent.handle_assessment(participants, config):
                    results.append(update.to_dict())

            asyncio.run(collect_updates())
            return results

        try:
            updates = run_assessment()

            # Find the final artifact
            final_update = updates[-1] if updates else {}
            artifact = final_update.get("artifact")

            return jsonify({
                "status": "completed",
                "updates": updates,
                "artifact": artifact,
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
            }), 500

    @app.route("/assess/stream", methods=["POST"])
    def assess_stream():
        """
        Start an assessment with streaming updates.

        Returns Server-Sent Events (SSE) stream.
        """
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body required"}), 400

        participants = data.get("participants", {})
        config = data.get("config", {})

        if not participants:
            return jsonify({"error": "No participants specified"}), 400

        def generate():
            async def stream_updates():
                async for update in agent.handle_assessment(participants, config):
                    yield f"data: {json.dumps(update.to_dict())}\n\n"

            # Run async generator synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                gen = stream_updates()
                while True:
                    try:
                        update = loop.run_until_complete(gen.__anext__())
                        yield update
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    return app


def main():
    parser = argparse.ArgumentParser(
        description="AgentX SQL Benchmark Green Agent"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind (default: 8001)"
    )
    parser.add_argument(
        "--card-url",
        help="URL for agent card advertisement"
    )
    parser.add_argument(
        "--dialect",
        default="sqlite",
        choices=["sqlite", "duckdb", "postgresql"],
        help="SQL dialect (default: sqlite)"
    )
    parser.add_argument(
        "--scorer-preset",
        default="default",
        choices=["default", "strict", "performance", "quality"],
        help="Scorer preset (default: default)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    card_url = args.card_url or f"http://{args.host}:{args.port}"

    print(f"Starting AgentX Green Agent on {args.host}:{args.port}")
    print(f"Dialect: {args.dialect}, Scorer: {args.scorer_preset}")
    print(f"Agent card URL: {card_url}")

    app = create_app(
        dialect=args.dialect,
        scorer_preset=args.scorer_preset,
        card_url=card_url,
    )

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
