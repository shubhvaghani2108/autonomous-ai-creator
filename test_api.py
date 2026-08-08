
from app import create_app
from agent.persona import get_persona

app = create_app()
client = app.test_client()

persona = get_persona()

# Test /api/agent/init
init_res = client.post("/api/agent/init", json={"persona": persona})
print("Init status:", init_res.status_code)
print("Init json:", init_res.get_json())
agent_id = init_res.get_json().get("agentId")

# Test /api/agent/feed
feed_res = client.get(f"/api/agent/feed?agentId={agent_id}")
print("Feed status:", feed_res.status_code)
print("Feed json:", feed_res.get_json())
