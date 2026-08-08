import sys
from pathlib import Path

# Add project root to sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.editor import evaluate_topic
from agent.memory import is_topic_known


def select_best_topic(topics_or_agent_id, topics_list=None, agent_id=None):
    """
    Evaluate topics, skip already known topics if agent_id is provided,
    and return the best publishable candidate.

    Supports calling conventions:
    - select_best_topic(topics)
    - select_best_topic(topics, agent_id)
    - select_best_topic(agent_id, topics)
    - select_best_topic(topics, agent_id=agent_id)
    """
    if isinstance(topics_or_agent_id, str):
        target_agent_id = topics_or_agent_id
        target_topics = topics_list or []
    else:
        target_topics = topics_or_agent_id or []
        target_agent_id = topics_list if isinstance(topics_list, str) else agent_id

    candidates = []

    for topic in target_topics:
        if target_agent_id and is_topic_known(target_agent_id, topic):
            continue

        result = evaluate_topic(topic)

        if result["decision"] != "PUBLISH":
            continue

        candidates.append(result)

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return candidates[0]
