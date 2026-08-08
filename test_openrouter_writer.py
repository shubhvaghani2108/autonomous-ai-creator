import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path and load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env", override=False)

from agent.persona import get_persona
from agent.writer import generate_post, validate_config, normalize_source_url


print("==================================================")
print("TESTING OPENROUTER WRITER (test_openrouter_writer.py)")
print("==================================================\n")

print("--- STEP 1: Loading SentinelAI Persona ---")
persona = get_persona()
print("Persona Name:", persona["name"])
print("Domain:", persona["domain"])
assert persona["name"] == "SentinelAI", "Persona name must be SentinelAI"

print("\n--- STEP 2: Loading OpenRouter Writer Configuration ---")
config = validate_config()
print("Writer Provider:", config["writer_provider"])
print("API Key Configured:", config["api_key_configured"])
print("Model Configured:", config["model_configured"])
print("Model Name:", config["model_name"])

assert config["writer_provider"] == "openrouter", f"Expected provider 'openrouter', got '{config['writer_provider']}'"
assert config["model_configured"] is True, "OPENROUTER_MODEL must be configured"

if not config["api_key_configured"]:
    print("\n--------------------------------------------------")
    print("[CONFIGURATION ALERT: OPENROUTER_API_KEY MISSING OR PLACEHOLDER]")
    print("OPENROUTER_API_KEY is not configured with a valid real key.")
    print("To generate live posts via OpenRouter:")
    print("1. Create a free API key at: https://openrouter.ai/keys")
    print("2. Add OPENROUTER_API_KEY=sk-or-v1-... into your .env file")
    print("   or set $env:OPENROUTER_API_KEY=\"sk-or-v1-...\" in PowerShell")
    print("--------------------------------------------------\n")

print("--- STEP 3: Creating Test Topic & Editorial Result ---")
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

print("\n--- STEP 4: Calling generate_post() via OpenRouter ---")
result = generate_post(test_topic, editorial_result)

if not result.get("success"):
    print("\n[WRITER ERROR RESPONSE]")
    print("Error:", result.get("error"))
    
    # Classify error if key is configured but API returned error
    err_str = result.get("error", "")
    if "401" in err_str or "UNAUTHORIZED" in err_str.upper() or "INVALID" in err_str.upper() and "KEY" in err_str.upper():
        print("\nCLASSIFICATION: INVALID_OPENROUTER_API_KEY")
    elif "429" in err_str or "RATE_LIMIT" in err_str.upper() or "QUOTA" in err_str.upper():
        print("\nCLASSIFICATION: OPENROUTER_QUOTA_OR_RATE_LIMIT")
    else:
        print("\nCLASSIFICATION: OPENROUTER_API_ERROR")
    sys.exit(1)
else:
    print("\n--- GENERATED POST ---")
    print(result.get("text"))

    print("\n--- RATIONALE ---")
    print(result.get("rationale"))

    print("\n--- SOURCES ---")
    print(result.get("sources"))

    # Assertions on successful OpenRouter response
    assert "text" in result and result["text"], "Result must contain non-empty text"
    assert "rationale" in result and result["rationale"], "Result must contain non-empty rationale"
    assert "sources" in result and isinstance(result["sources"], list), "Result must contain sources list"

    # Verify source URL is plain URL (not Markdown)
    for src in result["sources"]:
        assert src.startswith("http://") or src.startswith("https://"), f"Source must be absolute URL: {src}"
        assert "[" not in src and "]" not in src, f"Source must be plain URL, got Markdown link: {src}"

    assert test_topic["url"] in result["sources"], "Sources must contain original topic URL"

    print("\nCLASSIFICATION: OPENROUTER_WRITER_READY")

print("\n==============================================")
print("OPENROUTER WRITER TEST COMPLETED SUCCESSFULLY!")
print("==============================================")
