# pyrefly: ignore [missing-import]
import feedparser
from datetime import datetime, timezone


RSS_SOURCES = [
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/"
    },
    {
        "name": "Microsoft Security",
        "url": "https://www.microsoft.com/en-us/security/blog/feed/"
    },
    {
        "name": "Cloudflare Blog",
        "url": "https://blog.cloudflare.com/rss/"
    },
]


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def discover_topics():

    topics = []

    for source in RSS_SOURCES:

        try:

            feed = feedparser.parse(source["url"])

            for entry in feed.entries[:10]:

                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip()

                if not title or not url:
                    continue

                topics.append({
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "source": source["name"],
                    "discoveredAt": utc_now()
                })

        except Exception as error:

            print(
                f"[DISCOVERY ERROR] "
                f"{source['name']}: {error}"
            )

    return topics


if __name__ == "__main__":

    topics = discover_topics()

    print(f"\nDiscovered {len(topics)} topics\n")

    for topic in topics[:10]:

        print("=" * 70)
        print("TITLE:", topic["title"])
        print("URL:", topic["url"])
        print("SOURCE:", topic["source"])
