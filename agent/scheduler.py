import os
import sys
import logging
from pathlib import Path
from threading import Thread
from dotenv import load_dotenv

# Ensure project root is in sys.path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Ensure stdout supports UTF-8 on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from database.database import agent_exists
from agent.discovery import discover_topics
from agent.editor import evaluate_topic
from agent.memory import is_topic_known, remember_topic
from agent.publisher import publish_selected_topic

class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

# Configure logger with UTF-8 / safe text handling
logger = logging.getLogger("autonomous_scheduler")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = FlushStreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# In-memory registry of active schedulers per agent
ACTIVE_WORKERS = {}


def safe_text(text):
    """Clean string for safe logging without UnicodeEncodeError on Windows terminals."""
    if not isinstance(text, str):
        text = str(text)
    return text.encode("ascii", "replace").decode("ascii")


def run_agent_cycle(agent_id):
    """
    Executes a single autonomous agent cycle:
    1. Verify agent exists
    2. Discover live topics
    3. Evaluate topics & record rejections in memory
    4. Select highest scoring publishable candidate
    5. Publish at most ONE candidate via publisher
    """
    logger.info(f"[AUTONOMOUS] Cycle START agent={agent_id}")

    if not agent_exists(agent_id):
        logger.error(f"[AUTONOMOUS] Agent {agent_id} does not exist. Stopping worker.")
        stop_agent_worker(agent_id)
        logger.info(f"[AUTONOMOUS] Cycle END agent={agent_id}")
        return

    load_dotenv(root_dir / ".env", override=False)
    from agent.writer import get_writer_provider
    provider = get_writer_provider()
    logger.info(f"[AUTONOMOUS] AI writer provider={provider}")
    if provider == "mock":
        logger.info("[AUTONOMOUS] WARNING: AI_WRITER_MODE=mock. Development content only.")

    try:
        topics = discover_topics()
        logger.info(f"[AUTONOMOUS] Discovered {len(topics)} topics")
        logger.info("[AUTONOMOUS] Discovery complete")

        known_count = 0
        rejected_count = 0
        candidates = []

        for topic in topics:
            title = topic.get("title", "")

            # 1. Persistent memory check
            if is_topic_known(agent_id, topic):
                known_count += 1
                logger.info(f"[AUTONOMOUS] Known topic skipped: {safe_text(title)}")
                continue

            # 2. Editorial evaluation
            eval_result = evaluate_topic(topic)
            decision = eval_result.get("decision")
            score = eval_result.get("score", 0)
            reason = eval_result.get("reason", "")

            # 3. Store rejections in memory to prevent repeated evaluation
            if decision == "REJECT":
                rejected_count += 1
                remember_topic(
                    agent_id=agent_id,
                    topic=topic,
                    decision="REJECT",
                    score=score,
                    reason=reason
                )
                logger.info(f"[AUTONOMOUS] Rejected topic remembered: {safe_text(title)}")
            elif decision == "PUBLISH":
                candidates.append(eval_result)
                logger.info(f"[AUTONOMOUS] Candidate: {safe_text(title)} score={score}")

        publishable_count = len(candidates)
        logger.info(f"[AUTONOMOUS] Known={known_count}")
        logger.info(f"[AUTONOMOUS] Rejected={rejected_count}")
        logger.info(f"[AUTONOMOUS] Publishable={publishable_count}")

        # 4. Select and publish the single best candidate
        if candidates:
            candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
            best_candidate = candidates[0]
            best_topic = best_candidate.get("topic", {})
            best_title = best_topic.get("title", "")

            logger.info(f"[AUTONOMOUS] Selected topic: {safe_text(best_title)}")
            logger.info(f"[AUTONOMOUS] Publishing: {safe_text(best_title)}")

            # 5. Call publisher
            pub_result = publish_selected_topic(agent_id, best_candidate)

            if pub_result.get("success"):
                logger.info(f"[AUTONOMOUS] Published post={pub_result.get('postId')}")
            else:
                logger.error(f"[AUTONOMOUS] Publishing FAILED: {pub_result.get('error')}")
        else:
            logger.info("[AUTONOMOUS] No publishable new topic")

    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"[AUTONOMOUS] Cycle ERROR: {error_type}: {safe_text(str(e))}")

    logger.info(f"[AUTONOMOUS] Cycle END agent={agent_id}")


def start_agent_worker(agent_id):
    """
    Starts an autonomous background scheduler for the given agent_id.
    Prevents duplicate schedulers per agent and runs the first cycle immediately in a background thread.
    """
    if not agent_id:
        return False

    if agent_id in ACTIVE_WORKERS:
        logger.info(f"[AUTONOMOUS] Worker already running for agent {agent_id}")
        return False

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.error("[AUTONOMOUS] APScheduler dependency is missing")
        return False

    load_dotenv(root_dir / ".env", override=False)
    interval_minutes = int(os.getenv("AGENT_INTERVAL_MINUTES", "5"))
    if interval_minutes < 1:
        interval_minutes = 1

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=run_agent_cycle,
        trigger="interval",
        minutes=interval_minutes,
        args=[agent_id],
        id=f"agent_job_{agent_id}",
        max_instances=1,
        coalesce=True
    )

    scheduler.start()
    ACTIVE_WORKERS[agent_id] = scheduler
    logger.info(f"[AUTONOMOUS] Worker started agent={agent_id}")
    logger.info(f"[AUTONOMOUS] Job scheduled interval={interval_minutes} minutes")

    # Run the initial cycle for the agent immediately in a background thread
    from threading import Thread
    first_cycle_thread = Thread(target=run_agent_cycle, args=[agent_id], daemon=True)
    first_cycle_thread.start()

    return True


def stop_agent_worker(agent_id):
    """
    Stops and removes the background worker for the given agent_id.
    """
    if agent_id in ACTIVE_WORKERS:
        scheduler = ACTIVE_WORKERS.pop(agent_id)
        try:
            scheduler.shutdown(wait=False)
            logger.info(f"[AUTONOMOUS] Stopped worker for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"[AUTONOMOUS] Error stopping worker for agent {agent_id}: {safe_text(str(e))}")
    return False
