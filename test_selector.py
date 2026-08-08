import sys

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database.database import initialize_database, create_agent
from agent.discovery import discover_topics
from agent.selector import select_best_topic
from agent.memory import remember_topic


initialize_database()
agent_id = create_agent("SelectorUnitTestAgent", "AI Security")

print("--- Step 1: Discovering Live RSS Topics ---")
topics = discover_topics()
print(f"Discovered {len(topics)} topics\n")

print("--- Step 2: Selecting Best Topic (First Run) ---")
best_first = select_best_topic(topics, agent_id=agent_id)

assert best_first is not None, "Expected a publishable topic candidate"
assert "topic" in best_first, "Result must contain topic dictionary"
assert "score" in best_first, "Result must contain score"
assert "decision" in best_first, "Result must contain decision"
assert "reason" in best_first, "Result must contain reason"

print("\nSELECTED FIRST BEST TOPIC:")
print("Title:", best_first["topic"]["title"])
print("Score:", best_first["score"], "/ 50")
print("Decision:", best_first["decision"])
print("Reason:", best_first["reason"])

print("\n--- Step 3: Remembering the First Selected Topic ---")
remember_topic(
    agent_id=agent_id,
    topic=best_first["topic"],
    decision=best_first["decision"],
    score=best_first["score"],
    reason=best_first["reason"]
)

print("\n--- Step 4: Selecting Best Topic Again (Should Skip First Topic) ---")
best_second = select_best_topic(topics, agent_id=agent_id)

assert best_second is not None, "Expected a next best publishable candidate"
assert best_second["topic"]["title"] != best_first["topic"]["title"], "Second selection should not be the already-remembered first topic"

print("\nSELECTED SECOND BEST TOPIC:")
print("Title:", best_second["topic"]["title"])
print("Score:", best_second["score"], "/ 50")
print("Decision:", best_second["decision"])

print("\n============================================")
print("ALL SELECTOR UNIT TESTS PASSED SUCCESSFULLY!")
print("============================================")
