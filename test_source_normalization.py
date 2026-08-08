import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from agent.writer import normalize_source_url
from database.database import initialize_database, create_agent, save_post, get_posts

print("--- Testing Source URL Normalization ---")

# Test 1: Direct function tests
markdown_url_1 = "[https://example.com](https://example.com)"
normalized_1 = normalize_source_url(markdown_url_1)
print(f"Input:  {markdown_url_1}")
print(f"Output: {normalized_1}")
assert normalized_1 == "https://example.com", f"Expected 'https://example.com', got '{normalized_1}'"

markdown_url_2 = "[Microsoft Security Article](https://www.microsoft.com/en-us/security/blog/2026/08/04/advance-zero-trust/)"
normalized_2 = normalize_source_url(markdown_url_2)
print(f"Input:  {markdown_url_2}")
print(f"Output: {normalized_2}")
assert normalized_2 == "https://www.microsoft.com/en-us/security/blog/2026/08/04/advance-zero-trust/", f"Expected plain URL, got '{normalized_2}'"

raw_plain_url = "https://blog.google/technology/ai/rss/"
normalized_3 = normalize_source_url(raw_plain_url)
assert normalized_3 == raw_plain_url, "Plain URL should remain unchanged"

# Test 2: Database saving and retrieval with Markdown URL input
initialize_database()
test_agent_id = create_agent("URLNormalizationTestAgent", "AI Security")

save_post(
    agent_id=test_agent_id,
    text="Test post text",
    rationale="Test rationale",
    sources=["[https://example.com](https://example.com)", "[Microsoft](https://www.microsoft.com/feed)"]
)

retrieved_posts = get_posts(test_agent_id)
assert len(retrieved_posts) == 1, "Should retrieve 1 post"
retrieved_sources = retrieved_posts[0]["sources"]

print("Retrieved Sources from DB:", retrieved_sources)
assert retrieved_sources == [
    "https://example.com",
    "https://www.microsoft.com/feed"
], f"Unexpected DB sources: {retrieved_sources}"

print("\n==============================================")
print("SOURCE NORMALIZATION TEST PASSED SUCCESSFULLY!")
print("==============================================")
