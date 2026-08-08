import sys
import os

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent.writer import validate_config


print("--- Testing Configuration & Environment Loading ---")
config = validate_config()

print("AI Writer Mode:", config["writer_mode"])
print("API Key Configured:", config["api_key_configured"])
print("Model Configured:", config["model_configured"])
print("Model Name:", config["model_name"])

# Assertions
assert config["writer_mode"] in ["openai", "mock"], "Writer mode must be 'openai' or 'mock'"
assert config["api_key_configured"] is True, "API key should be detected in environment"
assert config["model_configured"] is True, "Model should be configured in environment"
assert isinstance(config["model_name"], str), "Model name must be a string"

print("\n==============================================")
print("CONFIG VALIDATION TEST COMPLETED SUCCESSFULLY!")
print("==============================================")
