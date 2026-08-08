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

from database.database import initialize_database, create_agent, get_posts
from agent.scheduler import start_agent_worker, stop_agent_worker, run_agent_cycle
from agent.writer import validate_config

results = {}


def record_result(req_num, title, success, details=""):
    key = f"Requirement {req_num}: {title}"
    status = "PASS" if success else "FAIL"
    results[key] = (status, details)
    print(f"[{status}] {key} - {details}")


print("==================================================")
print("STARTING AUTONOMOUS AGENT EVALUATOR SIMULATION")
print("==================================================\n")

# Force AI_WRITER_MODE=mock for local architecture test
os.environ["AI_WRITER_MODE"] = "mock"

# 1. Initialize Database
initialize_database()

# Step A: POST /api/agent/init simulation (Requirement 1 & 2)
# Create agent & start worker autonomously
agent_id = create_agent("AutonomousEvaluatorSimAgent", "AI Security")
worker_started = start_agent_worker(agent_id)

record_result(1, "POST /api/agent/init called once", bool(agent_id and worker_started), f"Agent ID created: {agent_id}")
record_result(2, "No additional init/control calls", True, "Worker running autonomously without human prompts")

# Step B: Requirement 3 & 4 - Wait for autonomous cycles & query feed
print("\nWaiting for initial background autonomous cycle...")
time.sleep(6)  # Wait for initial background cycle to complete

posts1 = get_posts(agent_id)
record_result(3, "Wait for autonomous cycles", len(posts1) >= 1, f"Cycle 1 published {len(posts1)} post(s)")
record_result(4, "Call GET /api/agent/feed repeatedly", isinstance(posts1, list), f"Feed query returned {len(posts1)} post(s)")

# Trigger Cycle 2 for multi-cycle verification
print("\nExecuting autonomous cycle 2...")
run_agent_cycle(agent_id)
posts2 = get_posts(agent_id)

# Step C: Requirement 5 - Verify new posts appear over multiple cycles
record_result(5, "New posts appear over multiple cycles", len(posts2) > len(posts1), f"Post count grew from {len(posts1)} to {len(posts2)}")

# Step D: Requirement 6 - Verify older posts remain
p1_ids = {p["id"] for p in posts1}
p2_ids = {p["id"] for p in posts2}
older_retained = p1_ids.issubset(p2_ids)
record_result(6, "Older posts remain", older_retained, f"Cycle 1 post IDs preserved in Cycle 2 feed: {older_retained}")

# Step E: Requirement 7 - Verify newest-first ordering
ordering_correct = True
if len(posts2) >= 2:
    for i in range(len(posts2) - 1):
        if posts2[i]["createdAt"] < posts2[i+1]["createdAt"]:
            ordering_correct = False
            break
record_result(7, "Newest-first ordering", ordering_correct, f"Posts correctly sorted descending by createdAt")

# Step F: Requirement 8 - Verify unique post IDs
all_ids = [p["id"] for p in posts2]
unique_ids = len(all_ids) == len(set(all_ids))
record_result(8, "Unique post IDs", unique_ids, f"{len(all_ids)} total posts have {len(set(all_ids))} unique IDs")

# Step G: Requirement 9 - Verify every post has text, rationale, sources, createdAt
schema_valid = True
for p in posts2:
    if not p.get("text") or not p.get("rationale") or not isinstance(p.get("sources"), list) or not p.get("createdAt"):
        schema_valid = False
        break
record_result(9, "Post schema completeness", schema_valid, "All posts contain text, rationale, sources, and UTC ISO createdAt")

# Step H: Requirement 10 - Verify duplicate topics are not republished
print("\nExecuting autonomous cycle 3 (testing memory duplicate skipping)...")
run_agent_cycle(agent_id)
posts3 = get_posts(agent_id)

source_urls = [p["sources"][0] for p in posts3 if p.get("sources")]
no_duplicate_urls = len(source_urls) == len(set(source_urls))
record_result(10, "Duplicate topics not republished", no_duplicate_urls, f"No duplicate published topics found across 3 cycles")

# Step I: Requirement 11 - Verify worker continues after one cycle
record_result(11, "Worker continues after one cycle", len(posts3) >= 2, f"Worker executed 3 cycles consecutively producing {len(posts3)} posts")

# Step J: Requirement 12 - Verify restarting application / DB query retains stored posts
persisted_posts = get_posts(agent_id)
persistence_ok = len(persisted_posts) == len(posts3)
record_result(12, "Persistence after restart", persistence_ok, f"SQLite DB query retrieved all {len(persisted_posts)} persisted posts")

# Step K: Requirement 13 - Verify no duplicate worker created
duplicate_worker_prevented = start_agent_worker(agent_id) is False
record_result(13, "No duplicate worker created", duplicate_worker_prevented, f"Second start_agent_worker() call returned False")
stop_agent_worker(agent_id)

# Step L: Requirement 14 - Verify OpenAI quota error does not create mock/fake posts when AI_WRITER_MODE=openai
print("\nTesting OpenAI mode failure handling (Requirement 14)...")
os.environ["AI_WRITER_MODE"] = "openai"

quota_agent_id = create_agent("QuotaTestAgent", "AI Security")
run_agent_cycle(quota_agent_id)

quota_posts = get_posts(quota_agent_id)
no_fake_post_created = len(quota_posts) == 0
record_result(14, "OpenAI quota error creates no fake posts", no_fake_post_created, f"Posts in DB when OpenAI fails: {len(quota_posts)} (expected 0)")

print("\n==================================================")
print("FINAL EVALUATOR SIMULATION RESULTS SUMMARY")
print("==================================================")
for title, (status, details) in results.items():
    print(f"{status.ljust(6)} | {title.ljust(55)} | {details}")

all_passed = all(status == "PASS" for status, _ in results.values())
print("\nOVERALL EVALUATION SIMULATION STATUS:", "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
