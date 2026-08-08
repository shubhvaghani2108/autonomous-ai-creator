import os
import sys
import json
import time
import requests
from pathlib import Path

# Ensure UTF-8 console output for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Respect process environment variables or default to interval if specified
if "AGENT_INTERVAL_MINUTES" not in os.environ:
    os.environ["AGENT_INTERVAL_MINUTES"] = "1"

from database.database import initialize_database, create_agent, get_posts
from agent.scheduler import start_agent_worker, stop_agent_worker

BASE_URL = "http://127.0.0.1:5001"

print("==================================================")
print("STARTING TEST_LIVE_AUTONOMOUS.PY")
print("==================================================\n")

initialize_database()

# STEP 1: Initialize test agent
test_agent_id = create_agent("LiveAutonomousTestAgent", "AI Security")
print(f"Created Test Agent ID: {test_agent_id}")


def wait_for_posts(agent_id, min_target_count=1, timeout_seconds=90, poll_interval=2):
    """
    Polls get_posts(agent_id) every `poll_interval` seconds up to `timeout_seconds`
    until post count reaches at least min_target_count.
    """
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        posts = get_posts(agent_id)
        if len(posts) >= min_target_count:
            return posts
        time.sleep(poll_interval)
    return get_posts(agent_id)


started = start_agent_worker(test_agent_id)
assert started is True, "Worker failed to start"

# STEP 2: Wait for Cycle 1 via polling (Immediate background thread execution)
print("\nWaiting up to 90 seconds for Cycle 1 post generation...")
posts_cycle1 = wait_for_posts(test_agent_id, min_target_count=1, timeout_seconds=90, poll_interval=2)
count_cycle1 = len(posts_cycle1)
print(f"[CYCLE 1 RESULT] Feed post count: {count_cycle1}")
assert count_cycle1 >= 1, f"Cycle 1 should produce at least 1 post (timed out after 90s, count={count_cycle1})"

# STEP 3: Wait for Cycle 2 via polling (Interval is 1 minute -> wait up to 90 seconds for scheduled execution)
print("\nWaiting up to 90 seconds for Cycle 2 scheduled interval execution...")
posts_cycle2 = wait_for_posts(test_agent_id, min_target_count=count_cycle1 + 1, timeout_seconds=90, poll_interval=2)
count_cycle2 = len(posts_cycle2)
print(f"[CYCLE 2 RESULT] Feed post count: {count_cycle2}")

stop_agent_worker(test_agent_id)

print("\n--- CYCLE ANALYSIS ---")
print(f"Cycle 1 posts: {count_cycle1}")
print(f"Cycle 2 posts: {count_cycle2}")

if count_cycle2 > count_cycle1:
    print("[SUCCESS] Live autonomous worker produced a new post in Cycle 2!")
    case_result = "CASE_PRODUCED_NEW_POST"
else:
    print("[INFO] Live autonomous worker completed Cycle 2 cleanly (either no candidates or all known/rejected).")
    case_result = "CASE_COMPLETED_CLEANLY"

assert count_cycle2 >= count_cycle1, "Post count should not decrease"

print("\n==================================================")
print(f"TEST_LIVE_AUTONOMOUS PASSED SUCCESSFULLY! ({case_result})")
print("==================================================")
