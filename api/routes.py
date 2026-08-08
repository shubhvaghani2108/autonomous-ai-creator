from flask import Blueprint, request, jsonify

from database.database import (
    create_agent,
    agent_exists,
    get_posts
)
from agent.scheduler import start_agent_worker


api = Blueprint("api", __name__)


@api.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "Autonomous AI Creator API is running!"
    }), 200


@api.route("/api/agent/init", methods=["POST"])
def initialize_agent():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "JSON request body is required"
        }), 400

    persona = data.get("persona")

    if not persona:
        return jsonify({
            "error": "persona is required"
        }), 400

    name = persona.get("name")
    domain = persona.get("domain")

    if not name or not domain:
        return jsonify({
            "error": "persona name and domain are required"
        }), 400

    print(f"[API INIT] Creating agent {name} ({domain})", flush=True)
    agent_id = create_agent(
        name=name,
        domain=domain
    )

    print(f"[API INIT] Starting worker for {agent_id}", flush=True)
    res = start_agent_worker(agent_id)
    print(f"[API INIT] start_agent_worker returned {res}", flush=True)

    return jsonify({
        "agentId": agent_id
    }), 200


@api.route("/api/agent/feed", methods=["GET"])
def feed():

    agent_id = request.args.get("agentId")

    if not agent_id:
        return jsonify({
            "error": "agentId is required"
        }), 400

    if not agent_exists(agent_id):
        return jsonify({
            "error": "Agent not found"
        }), 404

    posts = get_posts(agent_id)

    return jsonify({
        "posts": posts
    })