import sys

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent.discovery import discover_topics
from agent.editor import evaluate_topic


topics = discover_topics()

print(f"Discovered {len(topics)} topics\n")

for topic in topics:

    result = evaluate_topic(topic)

    print("=" * 80)

    print("TITLE:")
    print(topic["title"])

    print("\nSCORE:")
    print(result["score"], "/ 50")

    print("\nDECISION:")
    print(result["decision"])

    print("\nREASON:")
    print(result["reason"])
