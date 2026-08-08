import sys

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database.database import initialize_database, create_agent
from agent.memory import is_topic_known, remember_topic


# Initialize DB & create test agent
initialize_database()
agent_id = create_agent("MemoryUnitTestAgent", "AI Security")

# 1. Base topic test
topic1 = {
    "title": "New Prompt Injection Vulnerability Discovered",
    "url": "https://example.com/prompt-injection-v1",
    "summary": "Initial report on prompt injection"
}

print("\n--- TEST 1: New topic check ---")
known_before = is_topic_known(agent_id, topic1)
print(f"Result (expected False): {known_before}")
assert known_before is False, "New topic should return False"

print("\n--- TEST 2: Remember topic ---")
remember_topic(
    agent_id=agent_id,
    topic=topic1,
    decision="PUBLISH",
    score=42,
    reason="High AI security relevance"
)

known_after = is_topic_known(agent_id, topic1)
print(f"Result (expected True): {known_after}")
assert known_after is True, "Remembered topic should return True"

# 3. Same URL with a different title
topic2 = {
    "title": "Completely Different Title Here",
    "url": "https://example.com/prompt-injection-v1",
    "summary": "Different summary text"
}

print("\n--- TEST 3: Same URL with different title ---")
known_url = is_topic_known(agent_id, topic2)
print(f"Result (expected True): {known_url}")
assert known_url is True, "Same URL should be detected as known"

# 4. Same title with different whitespace/capitalization
topic3 = {
    "title": "  NEW   PROMPT  INJECTION   vulnerability DISCOVERED  ",
    "url": "https://example.com/different-url-link",
    "summary": "Summary text"
}

print("\n--- TEST 4: Same title with normalized whitespace/capitalization ---")
known_title = is_topic_known(agent_id, topic3)
print(f"Result (expected True): {known_title}")
assert known_title is True, "Normalized title match should be detected as known"

# 5. Completely different topic
topic4 = {
    "title": "Brand New Zero-Day Research on Quantum Cryptography",
    "url": "https://example.com/quantum-crypto-v1",
    "summary": "Quantum research topic"
}

print("\n--- TEST 5: Completely different topic ---")
known_diff = is_topic_known(agent_id, topic4)
print(f"Result (expected False): {known_diff}")
assert known_diff is False, "Completely different topic should return False"

print("\n==========================================")
print("ALL MEMORY UNIT TESTS PASSED SUCCESSFULLY!")
print("==========================================")
