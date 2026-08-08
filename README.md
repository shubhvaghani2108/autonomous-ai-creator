# Autonomous AI Creator

An autonomous, self-scheduling AI agent system that continuously monitors live technical and AI security news, editorially evaluates relevance, generates evidence-grounded analysis posts via LLMs (OpenRouter/Gemini), and publishes structured content to an API feed.

---

## Overview

The system runs autonomously in a continuous loop:

1. **Discovers** live technical and security topics from RSS feeds (Microsoft Security, Cloudflare, Google AI).
2. **Evaluates** topics editorially against the **SentinelAI** persona and security relevance threshold.
3. **Remembers** processed topics in persistent memory to prevent duplicate evaluation.
4. **Selects** the single highest-scoring publishable candidate for each cycle.
5. **Generates** concise, evidence-driven analysis posts using an AI writer (OpenRouter LLM).
6. **Publishes** validated posts containing structured text, editorial rationale, and source URLs.
7. **Stores** published posts in SQLite (`data/agent.db`) with UTC timestamps and UUIDv4 primary keys.
8. **Exposes** posts to consumers via a REST API feed (`GET /api/agent/feed?agentId=<agentId>`).
9. **Repeats** automatically on a configurable schedule via APScheduler.

---

## Problem Statement

Technical professionals, AI security researchers, and security operations teams struggle to manually track, filter, and analyze the overwhelming volume of daily security disclosures, AI threat research papers, and vendor updates. Existing content creation systems rely heavily on manual prompt engineering or batch script executions without editorial judgment, duplicate awareness, or structured API distribution.

**Autonomous AI Creator** solves this by implementing an end-to-end autonomous agent pipeline. It continuously scans primary technical RSS feeds, applies domain-specific editorial judgment (SentinelAI persona), avoids redundant content using persistent memory, generates grounded analysis via OpenRouter LLMs, and serves published posts over a REST API feed.

---

## Architecture

```text
RSS Sources (Microsoft, Cloudflare, Google AI)
       │
       ▼
   Discovery (agent/discovery.py)
       │
       ▼
Editorial Engine (agent/editor.py)
       │
       ▼
  Memory Check (agent/memory.py)
       │
       ▼
Best-Topic Selector (agent/selector.py)
       │
       ▼
OpenRouter Writer (agent/writer.py)
       │
       ▼
Publisher Engine (agent/publisher.py)
       │
       ▼
SQLite Database (database/database.py)
       │
       ▼
    Feed API (api/routes.py) ◄─── REST Consumer

───────────────────────────────────────────────
      Background Scheduler (agent/scheduler.py)
                     │
                     ▼
          Autonomous Agent Cycle
```

---

## Features

- **Live RSS Discovery**: Aggregates real-time feeds from primary security and AI engineering blogs.
- **Editorial Scoring**: Evaluates candidate topics (0–50 score) based on technical depth, novelty, and security impact.
- **SentinelAI Persona**: Focuses content on AI security, DevSecOps, and agentic threat models.
- **Persistent Memory**: SQLite-backed deduplication tracking both rejected and published topics.
- **Best-Topic Selection**: Selects only the highest-scoring eligible candidate per cycle.
- **OpenRouter AI Generation**: Leverages OpenRouter API (`openrouter/free` or specified models) with fallback capability.
- **Structured Writer Output**: Guarantees JSON output with validated text, rationale, and normalized source URLs.
- **SQLite Persistence**: Thread-safe database transactions storing posts with ISO 8601 UTC timestamps.
- **REST API Feed**: Endpoints for initializing agents (`POST /api/agent/init`) and retrieving feeds (`GET /api/agent/feed`).
- **Autonomous Scheduler**: APScheduler background thread executing non-blocking agent worker loops.
- **Robust Error Recovery**: Controlled status classifications (`INVALID_OPENROUTER_API_KEY`, `OPENROUTER_QUOTA_OR_RATE_LIMIT`, `OPENROUTER_NETWORK_ERROR`) allowing scheduler recovery without process termination.

---

## Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: Flask 3.1
- **Scheduler**: APScheduler 3.11
- **Database**: SQLite3
- **HTTP Client**: Requests 2.32
- **Environment Management**: python-dotenv 1.0

---

## Installation

1. **Clone the repository**:
   ```bash
   cd e:\autonomous-ai-creator
   ```

2. **Create and activate virtual environment**:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Environment Configuration

Create a `.env` file in the project root (copied from `.env.example`):

```env
AI_WRITER_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openrouter/free
AGENT_INTERVAL_MINUTES=5
```

> **Security Note**: Never commit your actual API keys or `.env` file to Git repository control. `.env` is explicitly ignored by `.gitignore`.

---

## Running the Application

To start the Flask API server:

```powershell
venv\Scripts\python.exe app.py
```

The server listens on `http://127.0.0.1:5001`.

---

## API Endpoints

### 1. Initialize Autonomous Agent Worker
- **Method**: `POST /api/agent/init`
- **Request Body**:
  ```json
  {
    "persona": {
      "name": "SentinelAI",
      "domain": "AI Security"
    }
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "agentId": "c528cf33-54a4-45ab-8106-7b27d66d80cf"
  }
  ```

### 2. Fetch Agent Post Feed
- **Method**: `GET /api/agent/feed?agentId=<agentId>`
- **Response** (`200 OK`):
  ```json
  {
    "posts": [
      {
        "id": "78cbc854-2489-47cf-a503-8ab45c0d6d5f",
        "createdAt": "2026-08-08T20:02:56.123456Z",
        "text": "Microsoft released new Zero Trust guidance for securing AI agents and DevSecOps pipelines...",
        "rationale": "Selected because it provides actionable, vendor-backed guidance on securing AI agents...",
        "sources": [
          "https://www.microsoft.com/en-us/security/blog/2026/08/04/advance-zero-trust-for-ai-new-tools-and-guidance-to-secure-ai-agents-and-devsecops/"
        ]
      }
    ]
  }
  ```

---

## Testing

Run unit diagnostics and live autonomous integration tests:

1. **OpenRouter Configuration Diagnostic**:
   ```powershell
   venv\Scripts\python.exe test_openrouter_config.py
   ```
2. **OpenRouter Writer Isolated Test**:
   ```powershell
   venv\Scripts\python.exe test_openrouter_writer.py
   ```
3. **Publisher & Database Unit Test**:
   ```powershell
   venv\Scripts\python.exe test_publisher.py
   ```
4. **Focused Persistence & Feed Test**:
   ```powershell
   venv\Scripts\python.exe test_focused_publisher.py
   ```
5. **Full Live Autonomous Pipeline Integration Test**:
   ```powershell
   venv\Scripts\python.exe test_live_autonomous.py
   ```

---

## Autonomous Cycle Flow

```text
   Discover (Fetch 30 live RSS topics)
      │
      ▼
   Evaluate (Score each candidate 0-50)
      │
      ▼
   Remember (Record rejected & processed topics in SQLite)
      │
      ▼
   Select (Pick top-scoring un-processed candidate)
      │
      ▼
   Generate (Produce structured post via OpenRouter API)
      │
      ▼
   Publish (Validate schema & normalize URLs)
      │
      ▼
   Persist (Commit to SQLite posts table)
      │
      ▼
   Feed (Expose via GET /api/agent/feed)
```

---

## Security Best Practices

- **Zero Hardcoded Secrets**: All keys are loaded strictly from process environment variables or `.env`.
- **Secret Redaction**: API keys and `Authorization` headers are sanitized and never written to logs or stdout.
- **Git Protection**: `.env`, SQLite databases (`data/*.db`), and `venv/` are excluded by `.gitignore`.
- **Controlled Error Handling**: API authentication errors (HTTP 401/403/429) raise classified errors without crashing background scheduler threads.
- **No Silent Mock Fallback**: When `AI_WRITER_PROVIDER=openrouter` is configured, real OpenRouter API calls are enforced and development mock content is prohibited.

---

## Project Status

- **Status**: **VERIFIED & OPERATIONAL**
- **OpenRouter LLM Integration**: Fully verified with real AI content generation.
- **Autonomous Worker Pipeline**: Multi-cycle autonomous loop tested and verified with dynamic polling.
