import sys
import json

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent.persona import get_persona
from agent.writer import generate_post


print("--- STEP 1: Loading SentinelAI Persona ---")
persona = get_persona()
print("Persona Name:", persona["name"])
print("Domain:", persona["domain"])

print("\n--- STEP 2: Creating Test Topic & Editorial Result ---")
test_topic = {
    "title": "Advance Zero Trust for AI: New tools and guidance to secure AI agents and DevSecOps",
    "url": "https://www.microsoft.com/en-us/security/blog/2026/08/04/advance-zero-trust-for-ai-new-tools-and-guidance-to-secure-ai-agents-and-devsecops/",
    "summary": "Microsoft introduced Zero Trust guidelines for AI agents and DevSecOps integration.",
    "source": "Microsoft Security"
}

editorial_result = {
    "score": 43,
    "decision": "PUBLISH",
    "reason": "Strong fit for SentinelAI. The topic has meaningful AI relevance and sufficient technical or security significance."
}

print("Test Topic Title:", test_topic["title"])
print("Editorial Score:", editorial_result["score"], "/ 50")

print("\n--- STEP 3: Calling generate_post() ---")
result = generate_post(test_topic, editorial_result)

if not result.get("success"):
    print("\n[WRITER CONTROLLED RESPONSE]")
    print("Error:", result.get("error"))
else:
    print("\n--- GENERATED POST ---")
    print(result.get("text"))

    print("\n--- RATIONALE ---")
    print(result.get("rationale"))

    print("\n--- SOURCES ---")
    print(result.get("sources"))

    # Assertions on successful response
    assert "text" in result and result["text"], "Result must contain non-empty text"
    assert "rationale" in result and result["rationale"], "Result must contain non-empty rationale"
    assert "sources" in result and isinstance(result["sources"], list), "Result must contain sources list"
    assert test_topic["url"] in result["sources"], "Sources must contain original topic URL"

print("\n===========================================")
print("WRITER TEST COMPLETED SUCCESSFULLY!")
print("===========================================")
