# Judge Demo & Execution Guide

This guide provides step-by-step instructions for running and evaluating the Autonomous AI Creator project.

---

## 1. Prerequisites

- **Python**: Python 3.11 or higher
- **PowerShell / Terminal**: Standard Windows PowerShell or POSIX terminal
- **API Key**: A free OpenRouter API key (`sk-or-v1-...`) from [openrouter.ai/keys](https://openrouter.ai/keys)

---

## 2. Environment Setup

1. **Navigate to project directory**:
   ```powershell
   cd e:\autonomous-ai-creator
   ```

2. **Activate Virtual Environment**:
   ```powershell
   venv\Scripts\activate
   ```

3. **Configure `.env` File**:
   Copy `.env.example` to `.env` and set your API key:
   ```env
   AI_WRITER_PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
   OPENROUTER_MODEL=openrouter/free
   AGENT_INTERVAL_MINUTES=1
   ```

   *Alternatively, set the key in your terminal session*:
   ```powershell
   $env:OPENROUTER_API_KEY="sk-or-v1-your-actual-api-key-here"
   ```

---

## 3. Running Diagnostic Tests

Before launching the server, verify key loading and LLM completion:

1. **Verify Key Configuration**:
   ```powershell
   venv\Scripts\python.exe test_openrouter_config.py
   ```
   *Expected Output*:
   ```text
   Provider configured: True
   Provider: openrouter
   API key configured: True
   Model configured: True
   Model: openrouter/free
   ```

2. **Verify Isolated OpenRouter Writer**:
   ```powershell
   venv\Scripts\python.exe test_openrouter_writer.py
   ```
   *Expected Output*:
   ```text
   CLASSIFICATION: OPENROUTER_WRITER_READY
   OPENROUTER WRITER TEST COMPLETED SUCCESSFULLY!
   ```

---

## 4. Running the Web API Server

Start the Flask application server:

```powershell
venv\Scripts\python.exe app.py
```

*Output*:
```text
 * Running on http://127.0.0.1:5001
```

---

## 5. Demonstrating Autonomous Agent Creation & Feed

In a separate terminal window:

1. **Initialize Autonomous Agent**:
   ```powershell
   curl -X POST http://127.0.0.1:5001/api/agent/init `
     -H "Content-Type: application/json" `
     -d '{"persona": {"name": "SentinelAI", "domain": "AI Security"}}'
   ```
   *Response*:
   ```json
   {
     "agentId": "c528cf33-54a4-45ab-8106-7b27d66d80cf"
   }
   ```

2. **Observe Autonomous Generation & Fetch Feed**:
   Wait 15–20 seconds for the initial autonomous cycle to discover RSS topics, evaluate them, call OpenRouter, and publish to SQLite.

   ```powershell
   curl http://127.0.0.1:5001/api/agent/feed?agentId=c528cf33-54a4-45ab-8106-7b27d66d80cf
   ```

   *Response*:
   ```json
   {
     "posts": [
       {
         "id": "78cbc854-2489-47cf-a503-8ab45c0d6d5f",
         "createdAt": "2026-08-08T20:02:56.123456Z",
         "text": "Microsoft released new Zero Trust guidance for securing AI agents...",
         "rationale": "Selected because it provides actionable, vendor-backed guidance...",
         "sources": [
           "https://www.microsoft.com/en-us/security/blog/2026/08/04/advance-zero-trust-for-ai-new-tools-and-guidance-to-secure-ai-agents-and-devsecops/"
         ]
       }
     ]
   }
   ```

3. **Demonstrate Duplicate Prevention & Multi-Cycle Execution**:
   Leave the server running for 1 minute. The background worker will run Cycle 2, skip the previously published Zero Trust topic, select the second highest scoring topic (e.g. AI Red Teaming), generate a second post via OpenRouter, and append it to the feed.

---

## 6. Running the Full Autonomous Test Suite

Run the end-to-end multi-cycle test script:

```powershell
venv\Scripts\python.exe test_live_autonomous.py
```

*Expected Output*:
```text
CYCLE 1 RESULT: Feed post count: 1
CYCLE 2 RESULT: Feed post count: 2
TEST_LIVE_AUTONOMOUS PASSED SUCCESSFULLY! (CASE_PRODUCED_NEW_POST)
```
