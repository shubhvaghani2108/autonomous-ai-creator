import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Determine project root cleanly
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env cleanly from project root
load_dotenv(PROJECT_ROOT / ".env", override=False)

from agent.writer import validate_config

print("==================================================")
print("OPENROUTER CONFIGURATION DIAGNOSTIC (test_openrouter_config.py)")
print("==================================================\n")

config = validate_config()

provider_configured = config["writer_provider"] == "openrouter"
api_key_configured = config["api_key_configured"]
model_configured = config["model_configured"]
model_name = config["model_name"]

print(f"Provider configured: {provider_configured}")
print(f"Provider: {config['writer_provider']}")
print(f"API key configured: {api_key_configured}")
print(f"Model configured: {model_configured}")
print(f"Model: {model_name}")
print("\n==================================================")
