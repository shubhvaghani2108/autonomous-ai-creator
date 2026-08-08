import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database.database import initialize_database, create_agent, save_post, get_posts
from agent.publisher import publish_selected_topic
from app import app

print("==================================================")
print("RUNNING FOCUSED PUBLISHER & DATABASE TEST")
print("==================================================\n")

initialize_database()
test_agent_id = create_agent("FocusedPublisherTestAgent", "AI Security")
print(f"Created Test Agent ID: {test_agent_id}")

# 1. Direct save_post test with required fixed data
post_id = save_post(
    agent_id=test_agent_id,
    text="Autonomous publisher integration test",
    rationale="Testing persistence",
    sources=["https://example.com/test"]
)

print(f"Direct save_post generated UUID: {post_id}")
assert post_id is not None and len(post_id) == 36, "post_id must be a valid UUIDv4 string"

# 2. Verify via get_posts
posts = get_posts(test_agent_id)
print(f"get_posts count: {len(posts)}")
assert len(posts) == 1, "Should find 1 post in DB"
assert posts[0]["id"] == post_id
assert posts[0]["text"] == "Autonomous publisher integration test"
assert posts[0]["rationale"] == "Testing persistence"
assert "https://example.com/test" in posts[0]["sources"]

# 3. Verify Feed API GET /api/agent/feed?agentId=<agent_id>
client = app.test_client()
response = client.get(f"/api/agent/feed?agentId={test_agent_id}")

print(f"Feed API HTTP Status: {response.status_code}")
assert response.status_code == 200, "Feed API must return HTTP 200"

feed_json = response.get_json()
assert "posts" in feed_json, "Feed response must contain 'posts' key"
feed_posts = feed_json["posts"]
assert len(feed_posts) == 1, "Feed posts count should be 1"

feed_post = feed_posts[0]
assert feed_post["id"] == post_id
assert feed_post["text"] == "Autonomous publisher integration test"
assert feed_post["rationale"] == "Testing persistence"
assert "https://example.com/test" in feed_post["sources"]
assert feed_post["createdAt"].endswith("Z"), "Timestamp must end in Z"

print("\n==================================================")
print("FOCUSED PUBLISHER & DATABASE TEST PASSED SUCCESSFULLY!")
print("==================================================")
