import os
import sys
import json
import time

# Force mock mode for deterministic unit testing
os.environ["AI_WRITER_PROVIDER"] = "mock"
os.environ["AI_WRITER_MODE"] = "mock"

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database.database import initialize_database, create_agent, get_posts
from agent.scheduler import start_agent_worker, stop_agent_worker, run_agent_cycle


# Initialize database
initialize_database()
agent_id = create_agent("SchedulerUnitTestAgent", "AI Security")

print("--- STEP 1: Running First Autonomous Agent Cycle ---")
run_agent_cycle(agent_id)

posts_cycle1 = get_posts(agent_id)
print(f"Posts after Cycle 1: {len(posts_cycle1)}")
assert len(posts_cycle1) == 1, "Cycle 1 should publish at most 1 post"

first_post = posts_cycle1[0]
print("Published Post Title/ID:", first_post["id"])
print("Text Snippet:", first_post["text"][:100], "...")

print("\n--- STEP 2: Running Second Autonomous Agent Cycle ---")
run_agent_cycle(agent_id)

posts_cycle2 = get_posts(agent_id)
print(f"Posts after Cycle 2: {len(posts_cycle2)}")
assert len(posts_cycle2) == 2, "Cycle 2 should publish the next top candidate"

print("\n--- STEP 3: Testing Worker Start / Stop & Duplicate Worker Prevention ---")
started1 = start_agent_worker(agent_id)
print(f"Worker start 1 (expected True): {started1}")
assert started1 is True, "First worker start should succeed"

started2 = start_agent_worker(agent_id)
print(f"Worker start 2 (expected False): {started2}")
assert started2 is False, "Duplicate worker start should be prevented"

stopped = stop_agent_worker(agent_id)
print(f"Worker stop (expected True): {stopped}")
assert stopped is True, "Worker shutdown should succeed"

print("\n==============================================")
print("ALL SCHEDULER UNIT TESTS PASSED SUCCESSFULLY!")
print("==============================================")
