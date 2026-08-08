import os
import sys
import json

# Force mock mode for deterministic unit testing without consuming API credits
os.environ["AI_WRITER_PROVIDER"] = "mock"
os.environ["AI_WRITER_MODE"] = "mock"

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database.database import initialize_database, create_agent, get_posts
from agent.publisher import publish_selected_topic


# 1. Initialize database & test agent
initialize_database()
agent_id = create_agent("PublisherUnitTestAgent", "AI Security")

print("--- STEP 1: Constructing Publishable Topic & Selection Result ---")
test_topic = {
    "title": "Advance Zero Trust for AI: New tools and guidance to secure AI agents and DevSecOps",
    "url": "https://www.microsoft.com/en-us/security/blog/2026/08/04/advance-zero-trust-for-ai-new-tools-and-guidance-to-secure-ai-agents-and-devsecops/",
    "summary": "Microsoft introduced Zero Trust guidelines for AI agents and DevSecOps integration.",
    "source": "Microsoft Security"
}

selected_result = {
    "topic": test_topic,
    "score": 43,
    "decision": "PUBLISH",
    "reason": "Strong fit for SentinelAI. The topic has meaningful AI relevance and sufficient technical or security significance."
}

print("Topic Title:", test_topic["title"])
print("Decision:", selected_result["decision"])

print("\n--- STEP 2: Publishing Topic via publish_selected_topic() ---")
pub_result = publish_selected_topic(agent_id, selected_result)

print("Publish Result:")
print(json.dumps(pub_result, indent=2))

assert pub_result.get("success") is True, "Publishing should succeed"
assert "postId" in pub_result and pub_result["postId"], "postId must be returned"
assert "text" in pub_result and pub_result["text"], "text must be returned"
assert "rationale" in pub_result and pub_result["rationale"], "rationale must be returned"
assert "sources" in pub_result and test_topic["url"] in pub_result["sources"], "sources must contain topic URL"

print("\n--- STEP 3: Verifying Saved Post via get_posts() ---")
posts_before = get_posts(agent_id)
print(f"Total posts found in database: {len(posts_before)}")
assert len(posts_before) == 1, "Database should contain exactly 1 post"
assert posts_before[0]["id"] == pub_result["postId"], "Saved post ID should match returned postId"

print("\n--- STEP 4: Attempting Duplicate Publishing for Same Topic ---")
dup_result = publish_selected_topic(agent_id, selected_result)

print("Duplicate Publish Result:")
print(json.dumps(dup_result, indent=2))

assert dup_result.get("success") is False, "Duplicate publish attempt should fail"
assert dup_result.get("status") == "already_processed", "Status must be 'already_processed'"

print("\n--- STEP 5: Verifying No Duplicate Post Was Created ---")
posts_after = get_posts(agent_id)
print(f"Total posts found in database after duplicate attempt: {len(posts_after)}")
assert len(posts_after) == 1, "Database should still contain exactly 1 post"

print("\n==============================================")
print("ALL PUBLISHER UNIT TESTS PASSED SUCCESSFULLY!")
print("==============================================")
