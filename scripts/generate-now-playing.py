#!/usr/bin/env python3
from __future__ import annotations

import base64
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "now-playing.svg"
DEFAULT_AUTH_PATH = ROOT / ".secrets" / "ytmusic-auth.json"


def load_auth():
    from ytmusicapi import YTMusic
    auth_path = os.getenv("YTMUSIC_AUTH_FILE", str(DEFAULT_AUTH_PATH))
    auth_b64 = os.getenv("YTMUSIC_AUTH_JSON_BASE64", "").strip()

    if auth_b64:
        decoded = base64.b64decode(auth_b64).decode("utf-8")
        parsed = json.loads(decoded)
        Path(auth_path).parent.mkdir(parents=True, exist_ok=True)
        Path(auth_path).write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")

    if not Path(auth_path).exists():
        raise FileNotFoundError("Authentication file not found")

    return YTMusic(auth_path)


def fetch_recent_tracks(client) -> list[dict[str, Any]]:
    items = client.get_history()
    if not isinstance(items, list):
        return []
    return items


def select_latest_music_item(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in items:
        if not isinstance(item, dict):
            continue
        video_type = str(item.get("videoType", "")).lower()
        if video_type in {"song", "music_video"}:
            return item
        artists = item.get("artists") or []
        if isinstance(artists, list) and artists:
            return item
    return None


def truncate_text(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def escape_svg_text(text: str, max_len: int) -> str:
    return html.escape(truncate_text(text or "-", max_len), quote=True)


def normalize_track(item: dict[str, Any] | None) -> dict[str, str]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if not item:
        return {
            "title": "No recent YouTube Music history",
            "artist": "Waiting for next drive mode track...",
            "album": "YouTube Music history sync",
            "time": now,
        }

    title = str(item.get("title") or "Unknown Track")

    artists = item.get("artists") or []
    if isinstance(artists, list):
        artist_text = ", ".join(str(a.get("name", "")) for a in artists if isinstance(a, dict) and a.get("name"))
    else:
        artist_text = ""

    album_obj = item.get("album")
    if isinstance(album_obj, dict):
        album = str(album_obj.get("name") or "")
    else:
        album = ""

    played_at = str(item.get("played") or item.get("feedbackTokens", {}).get("add", "") or now)

    return {
        "title": title,
        "artist": artist_text or "Unknown Artist",
        "album": album or "Unknown Album",
        "time": played_at,
    }


def render_svg(track: dict[str, str]) -> str:
    title = escape_svg_text(track["title"], 48)
    artist = escape_svg_text(track["artist"], 40)
    album = escape_svg_text(track["album"], 40)
    played = escape_svg_text(track["time"], 42)
    updated = escape_svg_text(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), 42)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="320" viewBox="0 0 1200 320" role="img" aria-label="Now Playing from YouTube Music">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#05070f"/>
      <stop offset="55%" stop-color="#0d1430"/>
      <stop offset="100%" stop-color="#1b0f2f"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="320" rx="24" fill="url(#bg)"/>
  <rect x="24" y="24" width="1152" height="272" rx="18" fill="none" stroke="#334155"/>
  <rect x="38" y="38" width="10" height="244" rx="5" fill="#ef4444" opacity="0.9"/>
  <text x="72" y="72" fill="#93c5fd" font-family="Segoe UI,Arial,sans-serif" font-size="18" letter-spacing="2">NOW PLAYING</text>
  <text x="72" y="98" fill="#fca5a5" font-family="Segoe UI,Arial,sans-serif" font-size="14">YouTube Music History</text>
  <text x="72" y="148" fill="#f8fafc" font-family="Segoe UI,Arial,sans-serif" font-size="34" font-weight="700">{title}</text>
  <text x="72" y="184" fill="#cbd5e1" font-family="Segoe UI,Arial,sans-serif" font-size="24">{artist}</text>
  <text x="72" y="214" fill="#a5b4fc" font-family="Segoe UI,Arial,sans-serif" font-size="18">Album: {album}</text>
  <text x="72" y="242" fill="#94a3b8" font-family="Segoe UI,Arial,sans-serif" font-size="16">History time: {played}</text>
  <text x="72" y="268" fill="#64748b" font-family="Segoe UI,Arial,sans-serif" font-size="14">Updated by GitHub Actions: {updated}</text>
  <polyline points="760,220 790,190 820,210 850,150 880,168 910,120 940,136 970,110 1000,142 1030,86 1060,132 1090,112" fill="none" stroke="#60a5fa" stroke-width="3"/>
  <rect x="748" y="236" width="356" height="14" rx="7" fill="#1e293b"/>
  <rect x="748" y="236" width="214" height="14" rx="7" fill="#8b5cf6"/>
  <rect x="748" y="260" width="356" height="4" rx="2" fill="#ef4444" opacity="0.8"/>
</svg>
'''


def write_svg(content: str) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")


def main() -> int:
    previous = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
    try:
        client = load_auth()
        items = fetch_recent_tracks(client)
        latest = select_latest_music_item(items)
        track = normalize_track(latest)
        write_svg(render_svg(track))
        print("now-playing.svg updated")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"now-playing update skipped: {exc.__class__.__name__}")
        if previous:
            print("kept previous now-playing.svg")
            return 0
        fallback = normalize_track(None)
        write_svg(render_svg(fallback))
        print("fallback now-playing.svg generated")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
