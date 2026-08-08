import sys
from pathlib import Path

# Add project root to sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.persona import get_persona


AI_SECURITY_KEYWORDS = [
    "ai security",
    "llm security",
    "ai agent security",
    "secure ai",
    "securing ai",
    "ai red teaming",
    "ai red team",
    "prompt injection",
    "prompt attack",
    "llm attack",
    "llm vulnerability",
    "ai vulnerability",
    "ai threat",
    "agent security",
    "agentic security",
    "agentic ai",
    "autonomous agent",
    "ai safety",
    "model security",
    "machine learning security",
]


SECURITY_KEYWORDS = [
    "security",
    "cybersecurity",
    "vulnerability",
    "attack",
    "threat",
    "malware",
    "ransomware",
    "credential theft",
    "zero trust",
    "supply chain",
    "privacy",
    "authentication",
    "authorization",
    "red team",
    "defensive",
]


TECHNICAL_KEYWORDS = [
    "api",
    "agent",
    "llm",
    "model",
    "mcp",
    "protocol",
    "framework",
    "architecture",
    "runtime",
    "developer",
    "research",
    "infrastructure",
    "devsecops",
    "red teaming",
]


LOW_VALUE_KEYWORDS = [
    "dinner party",
    "real world",
    "celebrating",
    "galaxy unpacked",
    "course",
    "funding",
    "ambassadors",
    "vibe coding",
]


def keyword_matches(content, keywords):
    return [
        keyword
        for keyword in keywords
        if keyword in content
    ]


def evaluate_topic(topic):

    persona = get_persona()

    title = topic.get("title", "")
    summary = topic.get("summary", "")

    content = f"{title} {summary}".lower()

    # ---------------------------------------
    # AI relevance
    # ---------------------------------------

    ai_terms = [
        "ai",
        "artificial intelligence",
        "llm",
        "large language model",
        "machine learning",
        "gemini",
        "agent",
        "agents",
        "mcp",
        "model",
        "generative ai",
        "genai",
    ]

    ai_matches = keyword_matches(content, ai_terms)

    if len(ai_matches) >= 3:
        ai_score = 10
    elif len(ai_matches) >= 2:
        ai_score = 8
    elif len(ai_matches) >= 1:
        ai_score = 6
    else:
        ai_score = 0

    # ---------------------------------------
    # AI Security relevance
    # ---------------------------------------

    ai_security_matches = keyword_matches(
        content,
        AI_SECURITY_KEYWORDS
    )

    security_matches = keyword_matches(
        content,
        SECURITY_KEYWORDS
    )

    if len(ai_security_matches) >= 2:
        security_score = 10
    elif len(ai_security_matches) == 1:
        security_score = 9
    elif len(security_matches) >= 3 and ai_matches:
        security_score = 8
    elif len(security_matches) >= 2 and ai_matches:
        security_score = 7
    elif len(security_matches) >= 1 and ai_matches:
        security_score = 6
    else:
        security_score = 0

    # ---------------------------------------
    # Technical depth
    # ---------------------------------------

    technical_matches = keyword_matches(
        content,
        TECHNICAL_KEYWORDS
    )

    if len(technical_matches) >= 4:
        technical_score = 10
    elif len(technical_matches) >= 3:
        technical_score = 9
    elif len(technical_matches) >= 2:
        technical_score = 8
    elif len(technical_matches) >= 1:
        technical_score = 6
    else:
        technical_score = 2

    # ---------------------------------------
    # Novelty
    # ---------------------------------------

    novelty_keywords = [
        "new",
        "introducing",
        "introduces",
        "launch",
        "launched",
        "release",
        "released",
        "announcing",
        "announced",
        "expanding",
        "research",
        "discovered",
        "update",
        "latest",
        "next generation",
    ]

    novelty_matches = keyword_matches(
        content,
        novelty_keywords
    )

    if len(novelty_matches) >= 2:
        novelty_score = 10
    elif len(novelty_matches) == 1:
        novelty_score = 8
    else:
        novelty_score = 6

    # ---------------------------------------
    # Persona fit
    # ---------------------------------------

    persona_interests = [
        interest.lower()
        for interest in persona["interests"]
    ]

    persona_matches = [
        interest
        for interest in persona_interests
        if interest in content
    ]

    if len(persona_matches) >= 3:
        persona_score = 10
    elif len(persona_matches) >= 2:
        persona_score = 9
    elif len(persona_matches) >= 1:
        persona_score = 8
    elif ai_matches:
        persona_score = 6
    else:
        persona_score = 2

    # ---------------------------------------
    # Total
    # ---------------------------------------

    total_score = (
        ai_score
        + security_score
        + technical_score
        + novelty_score
        + persona_score
    )

    # ---------------------------------------
    # Low-value override
    # ---------------------------------------

    low_value_matches = keyword_matches(
        content,
        LOW_VALUE_KEYWORDS
    )

    if low_value_matches and not ai_security_matches:
        decision = "REJECT"
        reason = (
            "Low editorial value for SentinelAI. "
            "The topic does not provide sufficient "
            "AI security or technical significance."
        )

    elif ai_score < 6:
        decision = "REJECT"
        reason = (
            "Rejected because the topic does not "
            "have sufficient AI relevance."
        )

    elif total_score >= 30:
        decision = "PUBLISH"

        reason = (
            "Strong fit for SentinelAI. "
            "The topic has meaningful AI relevance "
            "and sufficient technical or security significance."
        )

    else:
        decision = "REJECT"

        reason = (
            "The topic is related to AI but does not "
            "meet SentinelAI's current editorial threshold."
        )

    return {
        "topic": topic,
        "score": total_score,
        "decision": decision,
        "reason": reason,
        "details": {
            "ai_relevance": ai_score,
            "security_relevance": security_score,
            "technical_depth": technical_score,
            "novelty": novelty_score,
            "persona_fit": persona_score,
            "ai_matches": ai_matches,
            "security_matches": security_matches,
            "ai_security_matches": ai_security_matches,
            "technical_matches": technical_matches,
        }
    }


if __name__ == "__main__":

    test_topic = {
        "title": (
            "Enhancing AI security through "
            "global AI red teaming"
        ),
        "summary": (
            "New research explores AI security "
            "and red teaming techniques."
        ),
        "url": "https://example.com",
        "source": "Security Research"
    }

    result = evaluate_topic(test_topic)

    print("\nEDITORIAL DECISION")
    print("==================")

    print("\nTitle:")
    print(result["topic"]["title"])

    print("\nScore:")
    print(result["score"], "/ 50")

    print("\nDecision:")
    print(result["decision"])

    print("\nReason:")
    print(result["reason"])

    print("\nScore Breakdown:")

    for key, value in result["details"].items():
        print(f"{key}: {value}")
