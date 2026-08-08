import os
import sys
import re
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is in sys.path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Load .env file without forcing override over explicitly set process environment variables
load_dotenv(root_dir / ".env", override=False)

from agent.persona import get_persona


def normalize_source_url(url_str):
    """
    Extracts plain absolute URL from Markdown link format or cleans raw URL string.
    Examples:
        '[https://example.com](https://example.com)' -> 'https://example.com'
        '[Title](https://example.com/path)' -> 'https://example.com/path'
        '<https://example.com>' -> 'https://example.com'
        'https://example.com' -> 'https://example.com'
    """
    if not url_str or not isinstance(url_str, str):
        return ""

    url_str = url_str.strip()

    md_match = re.match(r'^\[.*?\]\((https?://[^\s\)]+)\)$', url_str, re.IGNORECASE)
    if md_match:
        return md_match.group(1).strip()

    angle_match = re.match(r'^<(https?://[^\s>]+)>$', url_str, re.IGNORECASE)
    if angle_match:
        return angle_match.group(1).strip()

    embedded_match = re.search(r'\((https?://[^\s\)]+)\)', url_str, re.IGNORECASE)
    if embedded_match and url_str.startswith("["):
        return embedded_match.group(1).strip()

    return url_str.strip('\'"<>')


DISALLOWED_PLACEHOLDERS = {
    "your_gemini_api_key",
    "your_supported_gemini_model",
    "your_openrouter_api_key",
    "your_openrouter_model",
    "your_key_here",
    "your_api_key",
    "your_project_id",
    "placeholder",
    "none",
    "null",
    "<your-key>",
    "<your_api_key>",
    "<your-api-key>",
    "sk-or-v1-your-actual-api-key-here",
}


def is_placeholder(val):
    if not val or not isinstance(val, str):
        return True
    clean_val = val.strip().lower()
    if clean_val in DISALLOWED_PLACEHOLDERS:
        return True
    if any(p in clean_val for p in ["your-key", "your_key", "your-api-key", "your_api_key", "your-actual", "your_actual"]):
        return True
    return clean_val.startswith("your_") or clean_val.startswith("your-") or clean_val.startswith("<your")


def get_writer_provider():
    """
    Returns the resolved writer provider ('openrouter', 'gemini', or 'mock').
    Precedence rule:
    1. AI_WRITER_PROVIDER takes precedence if set in environment.
    2. AI_WRITER_MODE is checked ONLY if AI_WRITER_PROVIDER is not set.
    3. Defaults to 'openrouter'.
    """
    provider = os.getenv("AI_WRITER_PROVIDER")
    if provider and provider.strip():
        return provider.strip().lower()

    mode = os.getenv("AI_WRITER_MODE")
    if mode and mode.strip():
        return mode.strip().lower()

    return "openrouter"


def get_writer_config():
    """
    Canonical configuration resolver for AI Writer.
    Reads environment variables first, then falls back to project-root .env.
    Returns status dictionary without exposing sensitive secrets.
    """
    env_path = root_dir / ".env"
    load_dotenv(env_path, override=False)

    provider = get_writer_provider()
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            from dotenv import dotenv_values
            env_dict = dotenv_values(env_path)
            api_key = (env_dict.get("OPENROUTER_API_KEY") or "").strip()
        model_name = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            from dotenv import dotenv_values
            env_dict = dotenv_values(env_path)
            api_key = (env_dict.get("GEMINI_API_KEY") or "").strip()
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            from dotenv import dotenv_values
            env_dict = dotenv_values(env_path)
            api_key = (env_dict.get("OPENAI_API_KEY") or "").strip()
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    elif provider == "mock":
        api_key = "mock"
        model_name = "mock"
    else:
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            from dotenv import dotenv_values
            env_dict = dotenv_values(env_path)
            api_key = (env_dict.get("OPENROUTER_API_KEY") or "").strip()
        model_name = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()

    key_is_placeholder = is_placeholder(api_key) if provider != "mock" else False
    api_key_configured = bool(api_key) and not key_is_placeholder
    model_configured = bool(model_name) and not (is_placeholder(model_name) if provider != "mock" else False)

    return {
        "writer_provider": provider,
        "api_key": api_key,
        "model_name": model_name,
        "api_key_configured": api_key_configured,
        "model_configured": model_configured,
        "is_placeholder": key_is_placeholder
    }


def validate_config():
    """
    Safe configuration validation helper for LLM API (OpenRouter, Gemini, OpenAI, or Mock).
    Returns status dictionary without exposing sensitive secrets.
    """
    cfg = get_writer_config()
    return {
        "writer_provider": cfg["writer_provider"],
        "api_key_configured": cfg["api_key_configured"],
        "model_configured": cfg["model_configured"],
        "model_name": cfg["model_name"]
    }


def _generate_mock_post(topic, editorial_result):
    """
    Generate deterministic development mock post without calling external LLM APIs.
    """
    title = topic.get("title", "").strip()
    raw_url = topic.get("url", "").strip()
    url = normalize_source_url(raw_url)
    summary = topic.get("summary", "").strip()
    source = topic.get("source", "").strip()
    reason = editorial_result.get("reason", "").strip()

    text = (
        f"[DEVELOPMENT MOCK] SentinelAI analysis: {title}. "
        f"{summary} "
        f"This development is relevant because it relates to {source or 'recent AI security updates'}. "
        f"The security implication is worth examining because AI systems and autonomous agents "
        f"increasingly interact with external tools, APIs, and infrastructure."
    )

    rationale = (
        f"Selected because: {reason or 'Strong fit for SentinelAI.'} "
        f"It is relevant now because the development was recently reported by {source or 'primary source'}. "
        f"Prioritized by SentinelAI over generic AI announcements due to its technical relevance."
    )

    sources = [url] if url else ["https://example.com/source"]

    return {
        "success": True,
        "text": text,
        "rationale": rationale,
        "sources": sources
    }


def _generate_openrouter_post(topic, editorial_result):
    cfg = get_writer_config()
    provider = cfg["writer_provider"]
    api_key = cfg["api_key"]
    model_name = cfg["model_name"]

    if not api_key or cfg["is_placeholder"]:
        return {
            "success": False,
            "error": "OPENROUTER_API_KEY is missing or configured with a placeholder value"
        }

    persona = get_persona()
    model_name = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()

    title = topic.get("title", "")
    raw_url = topic.get("url", "")
    url = normalize_source_url(raw_url)
    summary = topic.get("summary", "")
    source = topic.get("source", "")
    reason = editorial_result.get("reason", "")
    score = editorial_result.get("score", 0)

    system_prompt = f"""
You are {persona['name']}, an AI security researcher and technology analyst.
Domain: {persona['domain']}
Mission: {persona['mission']}

EDITORIAL PRINCIPLES:
- Technical significance over hype.
- Security relevance over popularity.
- Evidence over speculation.
- Practical implications over marketing language.
- Primary sources preferred.
- Concise social media style (target 500-900 characters).

OUTPUT REQUIREMENTS:
You must generate structured output in valid JSON format with exactly three keys:
1. "text": The main post text explaining what happened, why it matters, and technical security implications.
2. "rationale": A topic-specific explanation of why SentinelAI selected and prioritized this topic.
3. "sources": A JSON list of string plain URLs containing the provided topic URL: "{url}". Plain URLs only, NOT Markdown links.

Return ONLY valid JSON matching this schema:
{{
    "text": "...",
    "rationale": "...",
    "sources": ["{url}"]
}}
"""

    user_prompt = f"""
TOPIC DETAILS:
Title: {title}
Source: {source}
URL: {url}
Summary: {summary}

EDITORIAL SCORE: {score}/50
SELECTION REASON: {reason}

Generate a concise, technical, grounded post and rationale based on this topic.
Return ONLY valid JSON.
"""

    try:
        import requests

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/autonomous-ai-creator",
            "X-Title": "Autonomous AI Creator"
        }

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.4,
            "response_format": {"type": "json_object"}
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            err_text = response.text
            if api_key and api_key in err_text:
                err_text = err_text.replace(api_key, "[REDACTED_API_KEY]")

            classification = "OPENROUTER_API_ERROR"
            if response.status_code == 401:
                classification = "INVALID_OPENROUTER_API_KEY"
            elif response.status_code == 403:
                classification = "OPENROUTER_ACCESS_DENIED"
            elif response.status_code == 429:
                classification = "OPENROUTER_QUOTA_OR_RATE_LIMIT"

            return {
                "success": False,
                "error": f"OpenRouter API Error [{classification}]: HTTP {response.status_code}: {err_text}"
            }

        res_json = response.json()
        if "choices" not in res_json or not res_json["choices"]:
            return {
                "success": False,
                "error": "OpenRouter API Error: Invalid response structure (no choices returned)"
            }

        content = res_json["choices"][0]["message"]["content"].strip()

        # Clean markdown fences if present
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

        data = json.loads(content)

        text = data.get("text", "").strip()
        rationale = data.get("rationale", "").strip()
        raw_sources = data.get("sources", [])

        if not text or not rationale or not isinstance(raw_sources, list):
            return {
                "success": False,
                "error": "OpenRouter returned incomplete output schema"
            }

        sources = []
        for src in raw_sources:
            norm = normalize_source_url(src)
            if norm and norm not in sources:
                sources.append(norm)

        if url and url not in sources:
            sources.append(url)

        return {
            "success": True,
            "text": text,
            "rationale": rationale,
            "sources": sources
        }

    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__

        if api_key in error_msg:
            error_msg = error_msg.replace(api_key, "[REDACTED_API_KEY]")

        return {
            "success": False,
            "error": f"OpenRouter API Error [OPENROUTER_NETWORK_ERROR]: {error_type}: {error_msg}"
        }


def _generate_gemini_post(topic, editorial_result):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or is_placeholder(api_key):
        return {
            "success": False,
            "error": "GEMINI_API_KEY is missing or configured with a placeholder value"
        }

    persona = get_persona()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    title = topic.get("title", "")
    raw_url = topic.get("url", "")
    url = normalize_source_url(raw_url)
    summary = topic.get("summary", "")
    source = topic.get("source", "")
    reason = editorial_result.get("reason", "")
    score = editorial_result.get("score", 0)

    system_prompt = f"""
You are {persona['name']}, an AI security researcher and technology analyst.
Domain: {persona['domain']}
Mission: {persona['mission']}

EDITORIAL PRINCIPLES:
- Technical significance over hype.
- Security relevance over popularity.
- Evidence over speculation.
- Practical implications over marketing language.
- Primary sources preferred.
- Concise social media style (target 500-900 characters).

OUTPUT REQUIREMENTS:
You must generate structured output in JSON format with exactly three keys:
1. "text": The main post text explaining what happened, why it matters, and technical security implications.
2. "rationale": A topic-specific explanation of why SentinelAI selected and prioritized this topic.
3. "sources": A JSON list of string plain URLs containing the provided topic URL: "{url}". Plain URLs only, NOT Markdown links.

Return ONLY valid JSON matching this schema:
{{
    "text": "...",
    "rationale": "...",
    "sources": ["{url}"]
}}
"""

    user_prompt = f"""
TOPIC DETAILS:
Title: {title}
Source: {source}
URL: {url}
Summary: {summary}

EDITORIAL SCORE: {score}/50
SELECTION REASON: {reason}

Generate a concise, technical, grounded post and rationale based on this topic.
"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.4,
            )
        )

        content = response.text.strip()
        data = json.loads(content)

        text = data.get("text", "").strip()
        rationale = data.get("rationale", "").strip()
        raw_sources = data.get("sources", [])

        if not text or not rationale or not isinstance(raw_sources, list):
            return {
                "success": False,
                "error": "Gemini returned incomplete output schema"
            }

        sources = []
        for src in raw_sources:
            norm = normalize_source_url(src)
            if norm and norm not in sources:
                sources.append(norm)

        if url and url not in sources:
            sources.append(url)

        return {
            "success": True,
            "text": text,
            "rationale": rationale,
            "sources": sources
        }

    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__

        if api_key in error_msg:
            error_msg = error_msg.replace(api_key, "[REDACTED_API_KEY]")

        return {
            "success": False,
            "error": f"Gemini API Error: {error_type}: {error_msg}"
        }


def generate_post(topic, editorial_result):
    """
    Generate a concise, technical, evidence-driven post for SentinelAI.
    Supports AI_WRITER_PROVIDER='openrouter', 'gemini', or 'mock'.
    Returns structured dict with 'text', 'rationale', 'sources', and 'success' status.
    """
    if not editorial_result or editorial_result.get("decision") != "PUBLISH":
        return {
            "success": False,
            "error": "Topic decision is not PUBLISH"
        }

    # Ensure environment variables are loaded
    load_dotenv(root_dir / ".env", override=False)

    provider = get_writer_provider()

    if provider == "mock":
        return _generate_mock_post(topic, editorial_result)
    elif provider == "openrouter":
        return _generate_openrouter_post(topic, editorial_result)
    else:
        return _generate_gemini_post(topic, editorial_result)


if __name__ == "__main__":
    print("Config status:", validate_config())

    test_topic = {
        "title": "Advance Zero Trust for AI: New tools and guidance to secure AI agents and DevSecOps",
        "url": "https://www.microsoft.com/en-us/security/blog/2026/08/04/advance-zero-trust-for-ai-new-tools-and-guidance-to-secure-ai-agents-and-devsecops/",
        "summary": "Microsoft introduces Zero Trust architecture guidelines for AI agents.",
        "source": "Microsoft Security"
    }

    test_result = {
        "score": 43,
        "decision": "PUBLISH",
        "reason": "Strong AI security relevance and technical depth."
    }

    res = generate_post(test_topic, test_result)
    print("Result:", json.dumps(res, indent=2))
