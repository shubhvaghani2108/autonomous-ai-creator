# System Architecture & Technical Specification

Autonomous AI Creator is built as a modular, decoupled pipeline architecture where background scheduler threads drive autonomous cycles, LLM provider integrations handle generation, and Flask REST endpoints serve post feeds.

---

## Technical Pipeline Architecture

```text
RSS Sources (Microsoft Security, Cloudflare Blog, Google AI Blog)
       │
       ▼
   Discovery Module (`agent/discovery.py`)
       │
       ▼
Editorial Engine (`agent/editor.py`) ◄─── SentinelAI Persona (`agent/persona.py`)
       │
       ▼
Persistent Memory (`agent/memory.py`)
       │
       ▼
Candidate Selector (`agent/selector.py`)
       │
       ▼
OpenRouter Writer (`agent/writer.py`)
       │
       ▼
Publisher Engine (`agent/publisher.py`)
       │
       ▼
SQLite Database (`database/database.py`)
       │
       ▼
 REST Feed Endpoint (`api/routes.py`) ◄─── Consumer Client / UI
```

---

## Background Worker Scheduler Architecture

```text
Flask App Initialization (`app.py`)
       │
       ▼
`POST /api/agent/init` Endpoint
       │
       ▼
`start_agent_worker(agent_id)` (`agent/scheduler.py`)
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
Immediate Background Cycle             APScheduler Job Execution
  (Python `Thread`)                    (Every `AGENT_INTERVAL_MINUTES`)
       │                                         │
       └────────────────────┬────────────────────┘
                            │
                            ▼
                  `run_agent_cycle(agent_id)`
```

---

## Component Roles & Specifications

### 1. Discovery (`agent/discovery.py`)
- **Input**: Live RSS Feed URLs (Microsoft Security, Cloudflare, Google AI).
- **Process**: Parses XML/RSS items, cleans HTML markup, and extracts `title`, `url`, `summary`, and `source`.
- **Output**: Array of raw candidate topic dictionaries.

### 2. Editorial Engine (`agent/editor.py` & `agent/persona.py`)
- **Input**: Raw topic dictionaries.
- **Process**: Scores topics (0–50) against the **SentinelAI** persona principles (AI security, DevSecOps, agent threat models).
- **Output**: Editorial result containing `decision` (`PUBLISH` or `REJECT`), `score`, and `reason`.

### 3. Persistent Memory (`agent/memory.py`)
- **Input**: `agent_id` and candidate topic `title`/`url`.
- **Process**: Queries SQLite `topics` table for existing titles or URLs.
- **Output**: Boolean `is_topic_known` status preventing re-evaluation or duplicate publishing.

### 4. Candidate Selector (`agent/selector.py`)
- **Input**: Array of evaluated publishable topics.
- **Process**: Sorts topics by editorial `score` descending and selects the single top-scoring topic.
- **Output**: Selected candidate dictionary.

### 5. OpenRouter AI Writer (`agent/writer.py`)
- **Input**: Selected topic dictionary and editorial result.
- **Process**: Loads configuration via `get_writer_config()`, validates process environment keys, attaches `Authorization: Bearer <key>` header, issues POST request to OpenRouter API (`openrouter/free` or specified model), and parses structured JSON output.
- **Output**: Dict with `text`, `rationale`, `sources`, and `success` boolean.

### 6. Publisher Engine (`agent/publisher.py`)
- **Input**: `agent_id`, selected topic, and writer result.
- **Process**: Validates JSON schema (`text`, `rationale`, `sources`), normalizes URLs, persists post to database, and records topic in persistent memory.
- **Output**: Dict with `postId` and published post payload.

### 7. SQLite Database (`database/database.py`)
- **Tables**:
  - `agents`: `id` (TEXT PK), `name` (TEXT), `domain` (TEXT), `created_at` (TEXT).
  - `topics`: `id` (INTEGER PK), `agent_id` (TEXT), `title` (TEXT), `url` (TEXT), `summary` (TEXT), `discovered_at` (TEXT), `decision` (TEXT), `score` (INTEGER), `reason` (TEXT).
  - `posts`: `id` (TEXT PK), `agent_id` (TEXT), `topic_id` (INTEGER), `created_at` (TEXT), `text` (TEXT), `rationale` (TEXT), `sources` (TEXT).

### 8. API Routes (`api/routes.py`)
- **`GET /`**: Health status endpoint.
- **`POST /api/agent/init`**: Accepts persona parameters, initializes agent in DB, and starts autonomous background scheduler thread.
- **`GET /api/agent/feed?agentId=<agentId>`**: Returns posts for agent ID ordered by `created_at DESC`.
