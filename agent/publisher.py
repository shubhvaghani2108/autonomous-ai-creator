import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from agent.memory import is_topic_known, remember_topic
from agent.writer import generate_post, normalize_source_url
from database.database import save_post


def publish_selected_topic(agent_id, selected_result):
    """
    Complete publishing pipeline:
    1. Verify PUBLISH decision
    2. Check persistent topic memory for duplicates
    3. Generate post using AI Writer
    4. Validate post structure & normalize URLs
    5. Persist post to posts table
    6. Record topic to memory database
    """
    if not agent_id:
        return {
            "success": False,
            "error": "agent_id is required"
        }

    if not selected_result or not isinstance(selected_result, dict):
        return {
            "success": False,
            "error": "selected_result is invalid"
        }

    decision = selected_result.get("decision")
    if decision != "PUBLISH":
        return {
            "success": False,
            "error": f"Topic decision is '{decision}', cannot publish"
        }

    topic = selected_result.get("topic")
    if not topic or not isinstance(topic, dict):
        return {
            "success": False,
            "error": "Topic information missing in selected_result"
        }

    # Duplicate check
    if is_topic_known(agent_id, topic):
        return {
            "success": False,
            "status": "already_processed",
            "error": "Topic has already been processed"
        }

    # Generate post content via Writer (Mock or LLM)
    writer_result = generate_post(topic, selected_result)

    if not writer_result.get("success"):
        return {
            "success": False,
            "error": f"Writer FAILED: {writer_result.get('error', 'Unknown writer error')}"
        }

    import logging
    logger = logging.getLogger("autonomous_scheduler")
    logger.info("[AUTONOMOUS] Writer complete")

    text = writer_result.get("text")
    rationale = writer_result.get("rationale")
    raw_sources = writer_result.get("sources")

    # Output Validation
    if not text or not isinstance(text, str) or not text.strip():
        return {
            "success": False,
            "error": "Validation failed: post text is missing or invalid"
        }

    if not rationale or not isinstance(rationale, str) or not rationale.strip():
        return {
            "success": False,
            "error": "Validation failed: post rationale is missing or invalid"
        }

    if not raw_sources or not isinstance(raw_sources, list) or len(raw_sources) == 0:
        return {
            "success": False,
            "error": "Validation failed: post sources must be a non-empty list"
        }

    # Normalize every source to a plain absolute URL
    sources = []
    for src in raw_sources:
        norm = normalize_source_url(src)
        if norm and norm not in sources:
            sources.append(norm)

    topic_url = normalize_source_url(topic.get("url", ""))
    if topic_url and topic_url not in sources:
        sources.append(topic_url)

    # 1. Save post to database
    post_id = save_post(
        agent_id=agent_id,
        text=text,
        rationale=rationale,
        sources=sources,
        topic_id=None
    )

    # 2. Remember topic decision in memory database
    remember_topic(
        agent_id=agent_id,
        topic=topic,
        decision="PUBLISH",
        score=selected_result.get("score", 0),
        reason=selected_result.get("reason", "")
    )

    logger.info("[AUTONOMOUS] Publisher complete")

    return {
        "success": True,
        "postId": post_id,
        "text": text,
        "rationale": rationale,
        "sources": sources,
        "topic": topic
    }
