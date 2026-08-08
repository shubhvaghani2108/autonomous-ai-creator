import re
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone


DB_PATH = Path(__file__).parent.parent / "data" / "agent.db"


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


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT,
            summary TEXT,
            discovered_at TEXT NOT NULL,
            decision TEXT,
            score INTEGER,
            reason TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            topic_id INTEGER,
            created_at TEXT NOT NULL,
            text TEXT NOT NULL,
            rationale TEXT NOT NULL,
            sources TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def create_agent(name, domain):

    agent_id = str(uuid.uuid4())

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO agents
        (id, name, domain, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        agent_id,
        name,
        domain,
        utc_now()
    ))

    connection.commit()
    connection.close()

    return agent_id


def agent_exists(agent_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM agents
        WHERE id = ?
    """, (agent_id,))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def topic_already_processed(agent_id, title, url=None):
    """
    Check whether this topic has already been processed.
    We check both URL and normalized title.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # First check exact URL
    if url:
        clean_url = normalize_source_url(url)
        cursor.execute("""
            SELECT id
            FROM topics
            WHERE agent_id = ?
            AND (url = ? OR url = ?)
            LIMIT 1
        """, (agent_id, url, clean_url))

        if cursor.fetchone():
            connection.close()
            return True

    # Normalize title for comparison
    normalized_title = " ".join(
        title.lower().strip().split()
    )

    cursor.execute("""
        SELECT title
        FROM topics
        WHERE agent_id = ?
    """, (agent_id,))

    rows = cursor.fetchall()

    connection.close()

    for row in rows:

        existing_title = " ".join(
            row["title"].lower().strip().split()
        )

        if existing_title == normalized_title:
            return True

    return False


def save_topic(
    agent_id,
    title,
    url,
    summary,
    decision,
    score,
    reason
):
    clean_url = normalize_source_url(url) if url else url

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO topics (
            agent_id,
            title,
            url,
            summary,
            discovered_at,
            decision,
            score,
            reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        agent_id,
        title,
        clean_url,
        summary,
        utc_now(),
        decision,
        score,
        reason
    ))

    topic_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return topic_id


def save_post(agent_id, text, rationale, sources, topic_id=None):

    post_id = str(uuid.uuid4())

    clean_sources = []
    if isinstance(sources, list):
        for s in sources:
            norm = normalize_source_url(s)
            if norm and norm not in clean_sources:
                clean_sources.append(norm)
    elif isinstance(sources, str):
        norm = normalize_source_url(sources)
        if norm:
            clean_sources.append(norm)

    sources_str = "|||".join(clean_sources)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO posts
        (id, agent_id, topic_id, created_at, text, rationale, sources)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        post_id,
        agent_id,
        topic_id,
        utc_now(),
        text,
        rationale,
        sources_str
    ))

    connection.commit()
    connection.close()

    return post_id


def get_posts(agent_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            created_at,
            text,
            rationale,
            sources
        FROM posts
        WHERE agent_id = ?
        ORDER BY created_at DESC
    """, (agent_id,))

    rows = cursor.fetchall()

    connection.close()

    posts = []

    for row in rows:

        raw_sources = row["sources"].split("|||") if row["sources"] else []
        clean_sources = []
        for s in raw_sources:
            norm = normalize_source_url(s)
            if norm and norm not in clean_sources:
                clean_sources.append(norm)

        posts.append({
            "id": row["id"],
            "createdAt": row["created_at"],
            "text": row["text"],
            "rationale": row["rationale"],
            "sources": clean_sources
        })

    return posts


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
