import subprocess
import json
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

YTDLP_CMD = "yt-dlp"
executor = ThreadPoolExecutor(max_workers=5)  # adjust if many channels


def run_yt_dlp_search_sync(query: str):
    """Blocking call to yt-dlp (kept for thread executor)"""
    cmd = [YTDLP_CMD, "--dump-single-json", f"ytsearch3:{query} live"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        return data.get("entries", [])
    except Exception as e:
        print(f"[yt-dlp search error] {e}")
        return None


async def run_yt_dlp_search(query: str):
    """Async wrapper around blocking yt-dlp"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, run_yt_dlp_search_sync, query)


def extract_video_id(url: str):
    match = re.search(r"v=([^&]+)", url)
    return match.group(1) if match else None


async def get_live_video_embed(channel_name: str):
    """
    Non-blocking: find live video and return EMBED URL
    """
    entries = await run_yt_dlp_search(channel_name)
    if not entries:
        return None

    for entry in entries:
        if not entry:
            continue

        # Check if live
        is_live = entry.get("is_live")
        live_status = entry.get("live_status")
        if not (is_live or live_status == "is_live"):
            continue

        url = entry.get("webpage_url")
        if not url:
            continue

        video_id = extract_video_id(url)
        if not video_id:
            continue

        return f"https://www.youtube.com/embed/{video_id}?autoplay=1"

    return None