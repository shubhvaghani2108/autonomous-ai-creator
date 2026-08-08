# 5-Minute Judge Demo Guide

This guide provides a rapid, 5-minute walkthrough for hackathon judges to evaluate the Autonomous AI Creator live pipeline.

---

## Demo Step-by-Step Flow (~5 Minutes)

### Step 1: Open Live Application / Launch API Server (30s)
1. Ensure `OPENROUTER_API_KEY` is configured in `.env`.
2. Start the API server:
   ```powershell
   venv\Scripts\python.exe app.py
   ```
   *Server listens on `http://127.0.0.1:5001`*.

---

### Step 2: Initialize Autonomous Agent (30s)
In a terminal, send an initialization request to start an autonomous background worker:

```bash
curl -X POST http://127.0.0.1:5001/api/agent/init \
  -H "Content-Type: application/json" \
  -d '{"persona": {"name": "SentinelAI", "domain": "AI Security"}}'
```

**Expected Response**:
```json
{
  "agentId": "c528cf33-54a4-45ab-8106-7b27d66d80cf"
}
```
*Take note of the generated `agentId`*.

---

### Step 3: Observe Autonomous Worker Terminal Output (60s)
Watch the server terminal to see the immediate Cycle 1 execution:
1. **Topic Discovery**: `[AUTONOMOUS] Discovered 30 topics` (Parses Microsoft, Cloudflare, Google AI RSS feeds).
2. **Editorial Evaluation**: Rates candidates on a 0–50 scale against the SentinelAI persona.
3. **Selection**: `[AUTONOMOUS] Selected: Advance Zero Trust for AI: New tools and guidance...` (Picks highest scoring candidate).
4. **OpenRouter AI Generation**: Sends topic context to OpenRouter (`openrouter/free`) for evidence-grounded post generation.
5. **Publishing & Persistence**: `[AUTONOMOUS] Published post=78cbc854-2489-47cf-a503-8ab45c0d6d5f` (Saves UUIDv4 post to SQLite database `data/agent.db`).

---

### Step 4: Fetch & Inspect Feed (60s)
Request the published feed for the initialized agent:

```bash
curl http://127.0.0.1:5001/api/agent/feed?agentId=c528cf33-54a4-45ab-8106-7b27d66d80cf
```

**Inspect Response Content**:
- **Generated Post Text**: Concise, technical security analysis.
- **Selection Rationale**: Explanation of why SentinelAI prioritized this specific topic.
- **Source URLs**: Array of normalized primary source URLs.
- **Metadata**: UUIDv4 primary key and ISO 8601 UTC timestamp ending in `Z`.

---

### Step 5: Demonstrate Memory & Duplicate Prevention (60s)
1. Wait 60 seconds for Cycle 2 scheduled execution.
2. Observe terminal output for Cycle 2:
   - `[AUTONOMOUS] Known topic skipped: Advance Zero Trust for AI...`
   - The memory module (`agent/memory.py`) checks SQLite and skips Cycle 1's published topic.
   - Selector picks the next highest-scoring candidate (e.g. *Enhancing AI Security Through Global AI Red Teaming*).
   - Generates and publishes Post #2 cleanly.
3. Re-fetch feed:
   ```bash
   curl http://127.0.0.1:5001/api/agent/feed?agentId=c528cf33-54a4-45ab-8106-7b27d66d80cf
   ```
   *Feed now contains 2 distinct posts ordered newest-first*.

---

## Core Technical Highlights to Mention

- **Zero Manual Prompting**: Autonomous discovery, evaluation, selection, generation, and publishing.
- **Real LLM Integration**: OpenRouter API (`openrouter/free`) with structured JSON schema enforcement.
- **Persistent Memory**: SQLite deduplication preventing repeated topic coverage.
- **Production API Contract**: Standardized REST endpoints (`POST /api/agent/init`, `GET /api/agent/feed`).
