import sys
import os
import json
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is in sys.path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from agent.persona import get_persona
from agent.writer import generate_post, validate_config, normalize_source_url


print("--- STEP 1: Loading SentinelAI Persona ---")
persona = get_persona()
print("Persona Name:", persona["name"])
print("Domain:", persona["domain"])
assert persona["name"] == "SentinelAI", "Persona name must be SentinelAI"

print("\n--- STEP 2: Loading Gemini Writer Configuration ---")
config = validate_config()
print("Writer Provider:", config["writer_provider"])
print("API Key Configured:", config["api_key_configured"])
print("Model Configured:", config["model_configured"])
print("Model Name:", config["model_name"])

# Verify API key is detected without printing secret string value
api_key_present = config["api_key_configured"]
print("GEMINI_API_KEY Present:", api_key_present)

print("\n--- STEP 3: Creating Test Topic & Editorial Result ---")
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

print("\n--- STEP 4: Calling generate_post() ---")
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

    # Verify source URL is plain URL (not Markdown)
    for src in result["sources"]:
        assert src.startswith("http://") or src.startswith("https://"), f"Source must be absolute URL: {src}"
        assert "[" not in src and "]" not in src, f"Source must be plain URL, got Markdown link: {src}"

    assert test_topic["url"] in result["sources"], "Sources must contain original topic URL"

print("\n===========================================")
print("GEMINI WRITER TEST COMPLETED SUCCESSFULLY!")
print("===========================================")
