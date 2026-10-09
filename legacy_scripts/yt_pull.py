"""
yt_pull.py - pull every public video from a YouTube channel into SQLite.

Setup (once):
  1. Google Cloud Console -> new project -> enable "YouTube Data API v3"
  2. Credentials -> Create API key
  3. pip install requests
  4. export YT_API_KEY="your-key"        (Windows: set YT_API_KEY=your-key)

Run:
  python yt_pull.py @channelhandle
  python yt_pull.py UCxxxxxxxxxxxxxxxxxxxxxx      (or a channel ID)

Safe to re-run: videos are updated, and each run adds a NEW metrics
snapshot, so you can track growth over time.
"""
import os
import sys
import sqlite3
from datetime import datetime, timezone

import requests

API = "https://www.googleapis.com/youtube/v3"
KEY = os.environ.get("YT_API_KEY")
DB_PATH = "kehelmala.db"


def get(endpoint, **params):
    params["key"] = KEY
    r = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS posts (
        platform      TEXT NOT NULL,
        post_id       TEXT NOT NULL,
        channel       TEXT,
        title         TEXT,
        description   TEXT,
        published_at  TEXT,
        duration      TEXT,
        url           TEXT,
        genre         TEXT,          -- fill in later
        PRIMARY KEY (platform, post_id)
    );
    CREATE TABLE IF NOT EXISTS metrics_snapshots (
        platform     TEXT NOT NULL,
        post_id      TEXT NOT NULL,
        captured_at  TEXT NOT NULL,
        views        INTEGER,
        likes        INTEGER,
        comments     INTEGER,
        FOREIGN KEY (platform, post_id) REFERENCES posts (platform, post_id)
    );
    """)


def resolve_channel(ident):
    """Accepts @handle or a UC... channel ID. Returns (channel_id, title, uploads_playlist)."""
    if ident.startswith("UC"):
        data = get("channels", part="snippet,contentDetails", id=ident)
    else:
        data = get("channels", part="snippet,contentDetails", forHandle=ident)
    if not data.get("items"):
        sys.exit(f"Channel not found: {ident}")
    ch = data["items"][0]
    return (
        ch["id"],
        ch["snippet"]["title"],
        ch["contentDetails"]["relatedPlaylists"]["uploads"],
    )


def all_video_ids(uploads_playlist):
    ids, token = [], None
    while True:
        data = get(
            "playlistItems",
            part="contentDetails",
            playlistId=uploads_playlist,
            maxResults=50,
            pageToken=token,
        )
        ids += [i["contentDetails"]["videoId"] for i in data["items"]]
        token = data.get("nextPageToken")
        if not token:
            return ids


def to_int(value):
    # likes/comments can be missing (hidden or disabled) -> store NULL
    return int(value) if value is not None else None


def main():
    if not KEY:
        sys.exit("Set the YT_API_KEY environment variable first.")
    if len(sys.argv) < 2:
        sys.exit("Usage: python yt_pull.py @channelhandle")

    channel_id, channel_title, uploads = resolve_channel(sys.argv[1])
    print(f"Channel: {channel_title}")

    ids = all_video_ids(uploads)
    print(f"Found {len(ids)} videos")

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # videos.list takes up to 50 IDs per call
    for i in range(0, len(ids), 50):
        batch = ids[i : i + 50]
        data = get(
            "videos",
            part="snippet,contentDetails,statistics",
            id=",".join(batch),
        )
        for v in data["items"]:
            s, stats = v["snippet"], v.get("statistics", {})
            conn.execute(
                """INSERT INTO posts
                   (platform, post_id, channel, title, description,
                    published_at, duration, url)
                   VALUES ('youtube', ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(platform, post_id) DO UPDATE SET
                     title=excluded.title, description=excluded.description""",
                (
                    v["id"],
                    channel_title,
                    s["title"],
                    s.get("description", ""),
                    s["publishedAt"],
                    v["contentDetails"]["duration"],
                    f"https://www.youtube.com/watch?v={v['id']}",
                ),
            )
            conn.execute(
                """INSERT INTO metrics_snapshots
                   (platform, post_id, captured_at, views, likes, comments)
                   VALUES ('youtube', ?, ?, ?, ?, ?)""",
                (
                    v["id"],
                    now,
                    to_int(stats.get("viewCount")),
                    to_int(stats.get("likeCount")),
                    to_int(stats.get("commentCount")),
                ),
            )
        conn.commit()
        print(f"  saved {min(i + 50, len(ids))}/{len(ids)}")

    conn.close()
    print(f"Done. Data is in {DB_PATH}")


if __name__ == "__main__":
    main()
