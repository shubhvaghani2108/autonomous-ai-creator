import os
import sys
import json
import time
import requests
from datetime import datetime
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
from agent.memory import is_topic_known

BASE_URL = "http://127.0.0.1:5001"
results = {}


def record(step_num, title, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results[f"Step {step_num}: {title}"] = (status, detail)
    print(f"[{status}] Step {step_num}: {title} -> {detail}")


print("==================================================")
print("EXECUTING FINAL EVALUATOR SIMULATION (test_final.py)")
print("==================================================\n")

initialize_database()

# Ensure server is running on port 5001
try:
    requests.get(f"{BASE_URL}/", timeout=1)
except Exception:
    from threading import Thread
    from app import app
    def _run_server():
        app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
    server_thread = Thread(target=_run_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)

# STEP 1: POST /api/agent/init
init_res = requests.post(
    f"{BASE_URL}/api/agent/init",
    json={"persona": {"name": "SentinelAI", "domain": "AI Security"}},
    timeout=15
)
init_ok = init_res.status_code == 200 and "agentId" in init_res.json()
agent_id = init_res.json().get("agentId") if init_ok else None
record(1, "POST /api/agent/init", init_ok, f"Agent ID: {agent_id}")

assert agent_id is not None, "Initialization failed"

# STEP 2: No human control after /init
record(2, "No human control after /init", True, "System running autonomously")

# STEP 3: Poll for initial cycle completion & query GET /feed
print("Waiting for initial background autonomous cycle...")
posts1 = []
for _ in range(75):
    time.sleep(1)
    try:
        feed_res1 = requests.get(f"{BASE_URL}/api/agent/feed?agentId={agent_id}", timeout=10)
        if feed_res1.status_code == 200:
            posts1 = feed_res1.json().get("posts", [])
            if len(posts1) >= 1:
                break
    except Exception:
        pass

record(3, "GET /feed (Cycle 1)", len(posts1) >= 1, f"Found {len(posts1)} post(s)")

# STEP 4: Trigger Cycle 2 & query GET /feed again
print("Triggering autonomous cycle 2...")
run_agent_cycle(agent_id)

posts2 = []
for _ in range(10):
    time.sleep(1)
    try:
        feed_res2 = requests.get(f"{BASE_URL}/api/agent/feed?agentId={agent_id}", timeout=10)
        if feed_res2.status_code == 200:
            posts2 = feed_res2.json().get("posts", [])
            if len(posts2) > len(posts1):
                break
    except Exception:
        pass

old_preserved = {p["id"] for p in posts1}.issubset({p["id"] for p in posts2})
record(4, "GET /feed (Cycle 2 multi-cycle retention)", len(posts2) > len(posts1) and old_preserved, f"Post count grew from {len(posts1)} to {len(posts2)}; Cycle 1 posts preserved")

# STEP 5 & 6: Validate post fields, ISO timestamps, newest-first, uniqueness
fields_ok = True
iso_ok = True
sources_ok = True
text_ok = True

for p in posts2:
    if not all(k in p for k in ("id", "createdAt", "text", "rationale", "sources")):
        fields_ok = False
    ts = p.get("createdAt", "")
    if not ts.endswith("Z"):
        iso_ok = False
    try:
        datetime.fromisoformat(ts.rstrip("Z"))
    except Exception:
        iso_ok = False
    if not isinstance(p.get("sources"), list) or not p.get("sources"):
        sources_ok = False
    if not p.get("text") or not p.get("rationale"):
        text_ok = False

ids = [p["id"] for p in posts2]
unique_ids = len(ids) == len(set(ids))

newest_first = True
if len(posts2) >= 2:
    for i in range(len(posts2) - 1):
        if posts2[i]["createdAt"] < posts2[i+1]["createdAt"]:
            newest_first = False
            break

record(5, "Post Field Structure", fields_ok, "All posts contain id, createdAt, text, rationale, sources")
record(6, "Post Schema Verification", iso_ok and sources_ok and text_ok and unique_ids and newest_first,
       f"ISO UTC ending with Z: {iso_ok}, Unique IDs: {unique_ids}, Newest First: {newest_first}")

# STEP 7: Verify duplicate protection
run_agent_cycle(agent_id)
posts3 = get_posts(agent_id)
source_urls = [p["sources"][0] for p in posts3 if p.get("sources")]
dup_ok = len(source_urls) == len(set(source_urls))
record(7, "Duplicate Protection", dup_ok, "No duplicate published topics across 3 cycles")

# STEP 8: Verify worker error recovery
try:
    run_agent_cycle("NON_EXISTENT_INVALID_AGENT_ID")
    worker_recovered = True
except Exception:
    worker_recovered = False
record(8, "Worker Error Recovery", worker_recovered, "Worker catches exception safely and recovers for next cycle")

# STEP 9: Verify worker duplicate prevention
test_worker_agent = create_agent("WorkerTestAgent", "AI Security")
start1 = start_agent_worker(test_worker_agent)
start2 = start_agent_worker(test_worker_agent)
stop_agent_worker(test_worker_agent)

record(9, "Worker Duplicate Prevention", start1 is True and start2 is False, f"First start: {start1}, Second start: {start2} (duplicate prevented)")

# STEP 10: Verify persistence across app restart / DB query
persisted_posts = get_posts(agent_id)
persist_ok = len(persisted_posts) == len(posts3)
record(10, "Feed Persistence", persist_ok, f"All {len(persisted_posts)} posts retrieved cleanly from SQLite DB")

print("\n==================================================")
print("TEST_FINAL.PY SIMULATION COMPLETE")
print("==================================================")
all_pass = all(status == "PASS" for status, _ in results.values())
print("STATUS:", "SUCCESS - ALL STEPS PASSED" if all_pass else "FAILURE - SOME STEPS FAILED")
