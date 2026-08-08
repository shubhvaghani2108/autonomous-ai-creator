import sys
from pathlib import Path

# Add project root to sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.database import topic_already_processed, save_topic


def is_topic_known(agent_id, topic):
    """
    Check whether a topic has already been processed by the agent.
    Prints memory logs and returns True if known, False otherwise.
    """
    if not agent_id or not topic:
        return False

    title = topic.get("title", "").strip()
    url = topic.get("url", "").strip() if topic.get("url") else None

    known = topic_already_processed(agent_id=agent_id, title=title, url=url)

    if known:
        print(f"[MEMORY] Known topic skipped: {title}")
    else:
        print(f"[MEMORY] New topic: {title}")

    return known


def remember_topic(agent_id, topic, decision, score, reason):
    """
    Record an evaluated topic decision into persistent database memory.
    """
    title = topic.get("title", "").strip()
    url = topic.get("url", "").strip() if topic.get("url") else ""
    summary = topic.get("summary", "").strip()

    return save_topic(
        agent_id=agent_id,
        title=title,
        url=url,
        summary=summary,
        decision=decision,
        score=score,
        reason=reason
    )
