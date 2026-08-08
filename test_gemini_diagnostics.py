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

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# 1. Environment Loading
load_dotenv(root_dir / ".env", override=True)

from agent.writer import validate_config, is_placeholder, normalize_source_url

print("==================================================")
print("SAFE GEMINI DIAGNOSTICS SUITE (test_gemini_diagnostics.py)")
print("==================================================\n")

# 2. Check SDK Installation
sdk_installed = False
sdk_version = "N/A"

try:
    import google.genai as genai
    from google.genai import types
    sdk_installed = True
    try:
        import importlib.metadata
        sdk_version = importlib.metadata.version("google-genai")
    except Exception:
        sdk_version = getattr(genai, "__version__", "Installed (version unknown)")
except ImportError:
    sdk_installed = False

print(f"Gemini SDK installed: {'YES' if sdk_installed else 'NO'}")
print(f"Gemini SDK version: {sdk_version}")

# 3. Check Configuration & Placeholders
config = validate_config()
provider = config["writer_provider"]
api_key = os.getenv("GEMINI_API_KEY", "").strip()
model_name = config["model_name"]

api_key_configured = bool(api_key) and not is_placeholder(api_key)
model_configured = bool(model_name) and not is_placeholder(model_name)

print(f"Provider: {provider}")
print(f"API key configured: {'YES' if api_key_configured else 'NO'}")
print(f"Model configured: {'YES' if model_configured else 'NO'}")
print(f"Model: {model_name}")

# 4. API Request & Classification
api_attempted = False
auth_result = "NOT_ATTEMPTED"
authz_result = "NOT_ATTEMPTED"
final_classification = "UNKNOWN"

if not sdk_installed:
    auth_result = "SDK_MISSING"
    authz_result = "SDK_MISSING"
    final_classification = "SDK_ERROR"
elif not api_key_configured:
    auth_result = "MISSING_OR_PLACEHOLDER_KEY"
    authz_result = "BLOCKED_BEFORE_REQUEST"
    final_classification = "MISSING_OR_PLACEHOLDER_KEY"
elif not model_configured:
    auth_result = "VALID_KEY_PRESENT"
    authz_result = "INVALID_MODEL_CONFIG"
    final_classification = "INVALID_MODEL"
else:
    api_attempted = True
    print("\nAttempting minimal API diagnostic call...")
    try:
        client = genai.Client(api_key=api_key)
        # Attempt minimal generation request
        response = client.models.generate_content(
            model=model_name,
            contents="Ping test for API authorization status.",
            config=types.GenerateContentConfig(
                max_output_tokens=10,
                temperature=0.0
            )
        )
        auth_result = "SUCCESSFUL_AUTHENTICATION"
        authz_result = "AUTHORIZED"
        final_classification = "SUCCESS"
    except Exception as e:
        error_str = str(e)
        error_type = type(e).__name__
        
        # Redact API key safely
        if api_key and api_key in error_str:
            error_str = error_str.replace(api_key, "[REDACTED_API_KEY]")
            
        print(f"\n[DIAGNOSTIC API ERROR DETECTED]")
        print(f"Error Type: {error_type}")
        print(f"Raw Message: {error_str}\n")

        if "403" in error_str and ("Your project has been denied access" in error_str or "PERMISSION_DENIED" in error_str):
            auth_result = "SUCCESSFUL_AUTHENTICATION (Key Accepted)"
            authz_result = "PROJECT_ACCESS_DENIED_BY_GOOGLE"
            final_classification = "EXTERNAL_PROJECT_ACCESS_BLOCK"
        elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            auth_result = "SUCCESSFUL_AUTHENTICATION (Key Accepted)"
            authz_result = "RATE_LIMIT_OR_QUOTA_EXCEEDED"
            final_classification = "RATE_LIMIT_OR_QUOTA_EXCEEDED"
        elif "401" in error_str or "API_KEY_INVALID" in error_str or ("INVALID_ARGUMENT" in error_str and "API key" in error_str):
            auth_result = "INVALID_API_KEY"
            authz_result = "AUTHENTICATION_FAILED"
            final_classification = "INVALID_API_KEY"
        elif "404" in error_str or "NOT_FOUND" in error_str or ("model" in error_str.lower() and "quota" not in error_str.lower()):
            auth_result = "SUCCESSFUL_AUTHENTICATION"
            authz_result = "MODEL_NOT_FOUND_OR_UNSUPPORTED"
            final_classification = "INVALID_MODEL"
        else:
            auth_result = "FAILED"
            authz_result = f"ERROR: {error_type}"
            final_classification = f"UNCLASSIFIED_ERROR ({error_type})"

print("--------------------------------------------------")
print(f"API request attempted: {'YES' if api_attempted else 'NO'}")
print(f"Authentication result: {auth_result}")
print(f"Authorization result: {authz_result}")
print(f"Final classification: {final_classification}")
print("==================================================")
