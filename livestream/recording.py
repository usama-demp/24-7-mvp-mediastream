import json
import logging
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import boto3
import psycopg2
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

FFMPEG_EXE = os.getenv("FFMPEG_EXE", "ffmpeg").strip()
YTDLP_EXE = os.getenv("YTDLP_EXE", "yt-dlp").strip()

DEFAULT_BASE_DIR = r"D:\livestream" if os.name == "nt" else "/mnt/d/livestream"
BASE_DIR = Path(os.getenv("RECORDER_BASE_DIR", DEFAULT_BASE_DIR).strip()).resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = BASE_DIR / "recorder.log"

CHUNK_SECONDS = int(os.getenv("CHUNK_SECONDS", "600"))
MAIN_LOOP_SLEEP = int(os.getenv("MAIN_LOOP_SLEEP", "20"))
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "90"))
SEARCH_RESULTS_TO_CHECK = int(os.getenv("SEARCH_RESULTS_TO_CHECK", "5"))
FFMPEG_STOP_TIMEOUT = int(os.getenv("FFMPEG_STOP_TIMEOUT", "10"))
MAX_STDERR_CHARS = int(os.getenv("MAX_STDERR_CHARS", "2000"))
MAX_RESOLVE_RETRIES = int(os.getenv("MAX_RESOLVE_RETRIES", "3"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "2"))
PRUNE_INTERVAL_SECONDS = int(os.getenv("PRUNE_INTERVAL_SECONDS", "1800"))
UPLOAD_SCAN_INTERVAL_SECONDS = int(os.getenv("UPLOAD_SCAN_INTERVAL_SECONDS", "30"))
UPLOAD_MIN_FILE_AGE_SECONDS = int(os.getenv("UPLOAD_MIN_FILE_AGE_SECONDS", "90"))
PROGRESS_BAR_WIDTH = int(os.getenv("PROGRESS_BAR_WIDTH", "28"))

STALL_GRACE_SECONDS = int(os.getenv("STALL_GRACE_SECONDS", str(CHUNK_SECONDS + 240)))
CHANNEL_REENABLE_SECONDS = int(os.getenv("CHANNEL_REENABLE_SECONDS", "1800"))

OBS_ACCESS_KEY = os.getenv("OBS_ACCESS_KEY", "").strip()
OBS_SECRET_KEY = os.getenv("OBS_SECRET_KEY", "").strip()
OBS_BUCKET = os.getenv("OBS_BUCKET", "").strip()
OBS_ENDPOINT = os.getenv("OBS_ENDPOINT", "").strip()
OBS_PREFIX = os.getenv("OBS_PREFIX", "foreign_news_24x7").strip("/")

OBS_MULTIPART_THRESHOLD_MB = int(os.getenv("OBS_MULTIPART_THRESHOLD_MB", "64"))
OBS_MULTIPART_CHUNKSIZE_MB = int(os.getenv("OBS_MULTIPART_CHUNKSIZE_MB", "16"))
OBS_MAX_CONCURRENCY = int(os.getenv("OBS_MAX_CONCURRENCY", "1"))

PGHOST = os.getenv("PGHOST", "").strip()
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "").strip()
PGUSER = os.getenv("PGUSER", "").strip()
PGPASSWORD = os.getenv("PGPASSWORD", "").strip()
PG_TABLE = os.getenv("PG_TABLE", "news_recordings").strip()

YTDLP_JS_RUNTIMES = os.getenv("YTDLP_JS_RUNTIMES", "").strip()
YTDLP_COOKIES_FILE = os.getenv("YTDLP_COOKIES_FILE", "").strip()
YTDLP_COOKIES_FROM_BROWSER = os.getenv("YTDLP_COOKIES_FROM_BROWSER", "").strip()

VIDEO_PRESET = os.getenv("VIDEO_PRESET", "veryfast").strip()
VIDEO_CRF = os.getenv("VIDEO_CRF", "20").strip()
AUDIO_BITRATE = os.getenv("AUDIO_BITRATE", "160k").strip()
AUDIO_SAMPLE_RATE = os.getenv("AUDIO_SAMPLE_RATE", "48000").strip()
AUDIO_CHANNELS = os.getenv("AUDIO_CHANNELS", "2").strip()
VIDEO_MAXRATE = os.getenv("VIDEO_MAXRATE", "5M").strip()
VIDEO_BUFSIZE = os.getenv("VIDEO_BUFSIZE", "10M").strip()
RECORD_EXT = os.getenv("RECORD_EXT", ".ts").strip() or ".ts"
RECORD_MIME = os.getenv("RECORD_MIME", "video/mp2t").strip() or "video/mp2t"

UPLOADING_SUFFIX = ".uploading"
UPLOADED_SUFFIX = ".uploaded"

CHANNELS = [
    {"name": "TRT World", "search_query": "TRT World live", "channel_live_url": None, "allowed_terms": ["trt world"], "blocked_terms": ["news18", "india"], "enabled": True},
    {"name": "DW English", "search_query": "DW News live", "channel_live_url": None, "allowed_terms": ["dw", "dw news", "deutsche welle"], "blocked_terms": ["news18", "india", "arabia"], "enabled": True},
    {"name": "Al Jazeera English", "search_query": "Al Jazeera English live", "channel_live_url": None, "allowed_terms": ["al jazeera english"], "blocked_terms": ["arabic", "mubasher", "news18", "india"], "enabled": True},
    {"name": "Sky News", "search_query": "Sky News live", "channel_live_url": None, "allowed_terms": ["sky news", "skynews"], "blocked_terms": ["news18", "india", "pakistan", "cnn"], "enabled": True},
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)

STOP_REQUESTED = False

def handle_shutdown(signum, frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True
    logging.info("Received signal %s. Shutdown requested.", signum)

signal.signal(signal.SIGINT, handle_shutdown)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, handle_shutdown)

def truncate(text: str, limit: int = MAX_STDERR_CHARS) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"

def safe_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[-\s]+", "_", name)
    return name

def normalize_for_match(s: Optional[str]) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def contains_any(text: str, terms: List[str]) -> bool:
    text_n = normalize_for_match(text)
    return any(normalize_for_match(t) in text_n for t in terms if t)

def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def yt_dlp_base_args() -> List[str]:
    args = [sys.executable, "-m", "yt_dlp"]
    args += [
        "--remote-components", "ejs:github",
        "--extractor-args", "youtube:player_client=web",
        "--add-headers", "User-Agent:Mozilla/5.0",
        "--geo-bypass",
        "--no-check-certificates",
    ]
    if YTDLP_JS_RUNTIMES:
        args += ["--js-runtimes", YTDLP_JS_RUNTIMES]
    if YTDLP_COOKIES_FILE:
        args += ["--cookies", YTDLP_COOKIES_FILE]
    elif YTDLP_COOKIES_FROM_BROWSER:
        args += ["--cookies-from-browser", YTDLP_COOKIES_FROM_BROWSER]
    return args

def ensure_tools():
    run([FFMPEG_EXE, "-version"])
    yt = run(yt_dlp_base_args() + ["--version"])
    logging.info("ffmpeg detected successfully.")
    logging.info("yt-dlp version: %s", yt.stdout.strip())

def ensure_obs_config():
    missing = []
    if not OBS_ACCESS_KEY:
        missing.append("OBS_ACCESS_KEY")
    if not OBS_SECRET_KEY:
        missing.append("OBS_SECRET_KEY")
    if not OBS_BUCKET:
        missing.append("OBS_BUCKET")
    if not OBS_ENDPOINT:
        missing.append("OBS_ENDPOINT")
    if missing:
        raise RuntimeError(f"Missing OBS environment variables: {', '.join(missing)}")

def ensure_pg_config():
    missing = []
    if not PGHOST:
        missing.append("PGHOST")
    if not PGDATABASE:
        missing.append("PGDATABASE")
    if not PGUSER:
        missing.append("PGUSER")
    if not PGPASSWORD:
        missing.append("PGPASSWORD")
    if missing:
        raise RuntimeError(f"Missing Postgres environment variables: {', '.join(missing)}")

def build_output_pattern(channel_dir: Path, folder_name: str) -> Path:
    day_folder = datetime.now().strftime("%Y-%m-%d")
    out_dir = channel_dir / day_folder
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{folder_name}_%Y%m%d_%H%M%S{RECORD_EXT}"

def prune_old_recordings(base_dir: Path, retention_days: int):
    cutoff = datetime.now().date() - timedelta(days=retention_days - 1)
    for channel_dir in base_dir.iterdir():
        if not channel_dir.is_dir():
            continue
        for day_dir in channel_dir.iterdir():
            if not day_dir.is_dir():
                continue
            try:
                folder_date = datetime.strptime(day_dir.name, "%Y-%m-%d").date()
            except ValueError:
                continue
            if folder_date < cutoff:
                logging.info("Deleting old folder: %s", day_dir)
                shutil.rmtree(day_dir, ignore_errors=True)

def render_progress(current: int, total: int, cycle_no: int, channel_name: str):
    total = max(total, 1)
    ratio = current / total
    filled = int(PROGRESS_BAR_WIDTH * ratio)
    bar = "█" * filled + "-" * (PROGRESS_BAR_WIDTH - filled)
    msg = f"\rCycle {cycle_no} [{bar}] {current}/{total} | {channel_name[:40]:40}"
    sys.stdout.write(msg)
    sys.stdout.flush()
    if current == total:
        sys.stdout.write("\n")
        sys.stdout.flush()

def is_file_ready(path: Path, min_age_seconds: int = UPLOAD_MIN_FILE_AGE_SECONDS) -> bool:
    if not path.is_file():
        return False
    age = time.time() - path.stat().st_mtime
    return age >= min_age_seconds

def build_obs_key(local_file: Path) -> str:
    relative_path = local_file.relative_to(BASE_DIR).as_posix()
    return f"{OBS_PREFIX}/{relative_path}" if OBS_PREFIX else relative_path

def sidecar_path_for(file_path: Path, suffix: str) -> Path:
    return file_path.with_name(file_path.name + suffix)

def build_http_url(bucket: str, object_key: str) -> str:
    endpoint = OBS_ENDPOINT.rstrip("/")
    return f"{endpoint}/{bucket}/{object_key}"

def parse_recording_time_from_filename(file_path: Path) -> Tuple[datetime, datetime]:
    m = re.search(r"_(\d{8})_(\d{6})(?:\.[^.]+)$", file_path.name)
    if not m:
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        return file_mtime - timedelta(seconds=CHUNK_SECONDS), file_mtime
    dt = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y%m%d %H%M%S")
    return dt, dt + timedelta(seconds=CHUNK_SECONDS)

TRANSFER_CONFIG = TransferConfig(
    multipart_threshold=OBS_MULTIPART_THRESHOLD_MB * 1024 * 1024,
    multipart_chunksize=OBS_MULTIPART_CHUNKSIZE_MB * 1024 * 1024,
    max_concurrency=OBS_MAX_CONCURRENCY,
    use_threads=True,
)

S3_CLIENT = boto3.client(
    "s3",
    aws_access_key_id=OBS_ACCESS_KEY,
    aws_secret_access_key=OBS_SECRET_KEY,
    endpoint_url=OBS_ENDPOINT,
    use_ssl=OBS_ENDPOINT.startswith("https://"),
    verify=False if OBS_ENDPOINT.startswith("http://") else True,
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
        retries={"max_attempts": 10, "mode": "standard"},
    ),
)

def verify_obs_access():
    S3_CLIENT.head_bucket(Bucket=OBS_BUCKET)
    logging.info("OBS bucket access verified: %s", OBS_BUCKET)

def upload_file_to_obs(local_path: str, object_key: str):
    S3_CLIENT.upload_file(
        Filename=local_path,
        Bucket=OBS_BUCKET,
        Key=object_key,
        Config=TRANSFER_CONFIG,
        ExtraArgs={"ContentType": RECORD_MIME},
    )

def get_pg_connection():
    return psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
        cursor_factory=RealDictCursor,
    )

def create_table_if_not_exists():
    sql = f"""
    CREATE TABLE IF NOT EXISTS {PG_TABLE} (
        id BIGSERIAL PRIMARY KEY,
        channel_name TEXT NOT NULL,
        folder_name TEXT NOT NULL,
        recorded_from TIMESTAMP NOT NULL,
        recorded_to TIMESTAMP NOT NULL,
        local_file_name TEXT NOT NULL,
        bucket_name TEXT NOT NULL,
        object_key TEXT NOT NULL UNIQUE,
        s3_url TEXT NOT NULL,
        http_url TEXT,
        watch_url TEXT,
        direct_url TEXT,
        file_size_bytes BIGINT,
        upload_time TIMESTAMP NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_{PG_TABLE}_channel_name ON {PG_TABLE}(channel_name);
    CREATE INDEX IF NOT EXISTS idx_{PG_TABLE}_recorded_from ON {PG_TABLE}(recorded_from);
    CREATE INDEX IF NOT EXISTS idx_{PG_TABLE}_recorded_to ON {PG_TABLE}(recorded_to);
    """
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

def metadata_exists(object_key: str) -> bool:
    sql = f"SELECT 1 FROM {PG_TABLE} WHERE object_key = %s LIMIT 1"
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (object_key,))
            row = cur.fetchone()
            return row is not None

def insert_metadata(record: Dict):
    sql = f"""
    INSERT INTO {PG_TABLE} (
        channel_name,
        folder_name,
        recorded_from,
        recorded_to,
        local_file_name,
        bucket_name,
        object_key,
        s3_url,
        http_url,
        watch_url,
        direct_url,
        file_size_bytes,
        upload_time
    )
    VALUES (
        %(channel_name)s,
        %(folder_name)s,
        %(recorded_from)s,
        %(recorded_to)s,
        %(local_file_name)s,
        %(bucket_name)s,
        %(object_key)s,
        %(s3_url)s,
        %(http_url)s,
        %(watch_url)s,
        %(direct_url)s,
        %(file_size_bytes)s,
        %(upload_time)s
    )
    ON CONFLICT (object_key) DO NOTHING
    """
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, record)
        conn.commit()

@dataclass
class ChannelState:
    name: str
    search_query: str
    channel_live_url: Optional[str] = None
    allowed_terms: List[str] = field(default_factory=list)
    blocked_terms: List[str] = field(default_factory=list)
    enabled: bool = True
    folder_name: str = field(init=False)
    channel_dir: Path = field(init=False)
    process: Optional[subprocess.Popen] = field(default=None, init=False)
    last_start_attempt: float = field(default=0.0, init=False)
    last_error: str = field(default="", init=False)
    last_watch_url: Optional[str] = field(default=None, init=False)
    last_direct_url: Optional[str] = field(default=None, init=False)
    resolve_fail_count: int = field(default=0, init=False)
    disabled_due_to_error: bool = field(default=False, init=False)
    disabled_at: float = field(default=0.0, init=False)
    last_segment_time: float = field(default=0.0, init=False)
    last_seen_segment_file: Optional[str] = field(default=None, init=False)
    force_reacquire: bool = field(default=False, init=False)

    def __post_init__(self):
        self.folder_name = safe_name(self.name)
        self.channel_dir = BASE_DIR / self.folder_name
        self.channel_dir.mkdir(parents=True, exist_ok=True)

    def can_retry(self) -> bool:
        return (time.time() - self.last_start_attempt) >= RETRY_DELAY_SECONDS

STATE_BY_FOLDER_NAME: Dict[str, ChannelState] = {}

def score_entry(entry: dict, state: ChannelState) -> int:
    title = normalize_for_match(entry.get("title"))
    uploader = normalize_for_match(entry.get("uploader"))
    channel = normalize_for_match(entry.get("channel"))
    description = normalize_for_match(entry.get("description"))
    combined = " ".join([title, uploader, channel, description])
    live_status = entry.get("live_status")
    is_live = entry.get("is_live")
    if not (is_live or live_status == "is_live"):
        return -999999
    if state.blocked_terms and contains_any(combined, state.blocked_terms):
        return -999999
    if state.allowed_terms and not contains_any(combined, state.allowed_terms):
        return -999999
    score = 1000
    expected = normalize_for_match(state.name)
    if expected in title:
        score += 25
    if expected in uploader:
        score += 35
    if expected in channel:
        score += 35
    for term in state.allowed_terms:
        t = normalize_for_match(term)
        if t in title:
            score += 20
        if t in uploader:
            score += 35
        if t in channel:
            score += 35
    if "live" in title:
        score += 10
    if "news" in title:
        score += 5
    if "official" in uploader or "official" in channel:
        score += 5
    return score

def search_youtube_live_watch_url(state: ChannelState) -> str:
    cp = run(
        yt_dlp_base_args() + ["--dump-single-json", f"ytsearch{SEARCH_RESULTS_TO_CHECK}:{state.search_query}"],
        check=False,
    )
    if cp.returncode != 0 or not cp.stdout.strip():
        raise RuntimeError(cp.stderr.strip() or f"No search results returned for: {state.search_query}")
    data = json.loads(cp.stdout)
    entries = data.get("entries") or []
    candidates: List[Tuple[int, str, str, str]] = []
    for entry in entries:
        if not entry:
            continue
        webpage_url = entry.get("webpage_url")
        if not webpage_url:
            continue
        score = score_entry(entry, state)
        if score < 0:
            continue
        candidates.append((score, webpage_url, entry.get("uploader") or "", entry.get("title") or ""))
    if not candidates:
        raise RuntimeError(f"No valid live result found for search: {state.search_query}")
    candidates.sort(key=lambda x: x[0], reverse=True)
    best = candidates[0]
    logging.info("[%s] Best match score=%s uploader=%s title=%s", state.name, best[0], best[2], best[3])
    return best[1]

def try_channel_live_url(channel_live_url: str) -> str:
    cp = run(yt_dlp_base_args() + ["--dump-single-json", channel_live_url], check=False)
    if cp.returncode != 0 or not cp.stdout.strip():
        raise RuntimeError(cp.stderr.strip() or f"Failed to open {channel_live_url}")
    data = json.loads(cp.stdout)
    webpage_url = data.get("webpage_url") or data.get("original_url")
    live_status = data.get("live_status")
    is_live = data.get("is_live")
    if not webpage_url:
        raise RuntimeError(f"No webpage_url from {channel_live_url}")
    if not (is_live or live_status == "is_live"):
        raise RuntimeError(f"{channel_live_url} is not currently live")
    return webpage_url

def resolve_live_watch_url(state: ChannelState) -> str:
    errors = []
    if state.channel_live_url:
        try:
            watch_url = try_channel_live_url(state.channel_live_url)
            logging.info("[%s] Resolved via channel_live_url: %s", state.name, watch_url)
            return watch_url
        except Exception as e:
            errors.append(f"/live failed: {e}")
    try:
        watch_url = search_youtube_live_watch_url(state)
        logging.info("[%s] Resolved via search: %s", state.name, watch_url)
        return watch_url
    except Exception as e:
        errors.append(f"search failed: {e}")
    raise RuntimeError(" | ".join(errors))

def get_direct_stream_urls(watch_url: str) -> List[str]:
    format_candidates = [
        "b[protocol=m3u8]/b",
        "best[protocol=m3u8]/best",
        "best",
    ]

    errors = []

    for fmt in format_candidates:
        cmd = yt_dlp_base_args() + ["-f", fmt, "-g", watch_url]
        cp = run(cmd, check=False)

        lines = [line.strip() for line in cp.stdout.splitlines() if line.strip()]
        if lines:
            logging.info("Resolved direct stream URL for %s using format: %s", watch_url, fmt)
            return lines

        err = cp.stderr.strip() or f"No direct stream URL found using format {fmt}"
        errors.append(f"{fmt}: {err}")
        logging.warning("Direct stream resolution failed for %s using format %s", watch_url, fmt)

    raise RuntimeError(
        "Could not resolve direct stream from: "
        f"{watch_url}\n" + "\n".join(errors)
    )

def resolve_ingest_urls(state: ChannelState) -> Tuple[str, List[str]]:
    watch_url = resolve_live_watch_url(state)
    direct_urls = get_direct_stream_urls(watch_url)
    state.last_watch_url = watch_url
    state.last_direct_url = " | ".join(direct_urls)
    return watch_url, direct_urls

def newest_segment_file(state: ChannelState) -> Optional[Path]:
    files = list(state.channel_dir.rglob(f"*{RECORD_EXT}"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)

def refresh_segment_heartbeat(state: ChannelState):
    latest = newest_segment_file(state)
    if not latest:
        return
    latest_path = str(latest)
    latest_mtime = latest.stat().st_mtime
    if state.last_seen_segment_file != latest_path or latest_mtime > state.last_segment_time:
        state.last_seen_segment_file = latest_path
        state.last_segment_time = latest_mtime

def start_recording(state: ChannelState):
    state.last_start_attempt = time.time()
    logging.info("[%s] Searching current live stream...", state.name)
    watch_url, direct_urls = resolve_ingest_urls(state)
    out_pattern = build_output_pattern(state.channel_dir, state.folder_name)
    input_url = direct_urls[0]

    cmd = [
        FFMPEG_EXE,
        "-hide_banner",
        "-loglevel", "error",
        "-nostdin",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_on_network_error", "1",
        "-reconnect_on_http_error", "4xx,5xx",
        "-reconnect_delay_max", "10",
        "-rw_timeout", "15000000",
        "-thread_queue_size", "4096",
        "-fflags", "+discardcorrupt",
        "-analyzeduration", "20M",
        "-probesize", "20M",
        "-i", input_url,
        "-map", "0:v:0?",
        "-map", "0:a:0?",
        "-c", "copy",
        "-dn",
        "-sn",
        "-f", "segment",
        "-segment_time", str(CHUNK_SECONDS),
        "-reset_timestamps", "1",
        "-strftime", "1",
        "-segment_format", "mpegts",
        str(out_pattern),
    ]

    logging.info("[%s] Watch URL: %s", state.name, watch_url)
    logging.info("[%s] Direct stream URLs resolved: %s", state.name, len(direct_urls))
    logging.info("[%s] Saving to local spool: %s", state.name, out_pattern.parent)

    state.process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    state.resolve_fail_count = 0
    state.disabled_due_to_error = False
    state.disabled_at = 0.0
    state.force_reacquire = False
    state.last_segment_time = time.time()

def stop_recording(state: ChannelState):
    if state.process and state.process.poll() is None:
        logging.info("[%s] Stopping process...", state.name)
        state.process.terminate()
        try:
            state.process.wait(timeout=FFMPEG_STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            state.process.kill()
    state.process = None

def force_restart_channel(state: ChannelState, reason: str):
    logging.warning("[%s] Force restart triggered: %s", state.name, reason)
    stop_recording(state)
    state.force_reacquire = True
    state.last_start_attempt = 0

def process_is_running(state: ChannelState) -> bool:
    return state.process is not None and state.process.poll() is None

def check_process(state: ChannelState):
    if not state.process:
        return
    rc = state.process.poll()
    if rc is None:
        return
    stderr_text = ""
    try:
        _, stderr_text = state.process.communicate(timeout=2)
    except Exception:
        pass
    state.process = None
    msg = f"Recording stopped unexpectedly. Exit code: {rc}"
    if stderr_text.strip():
        msg += f"\n\nffmpeg error:\n{truncate(stderr_text)}"
    logging.error("[%s] %s", state.name, msg)

def check_stream_stall(state: ChannelState):
    if not process_is_running(state):
        return
    refresh_segment_heartbeat(state)
    if state.last_segment_time <= 0:
        return
    idle_for = time.time() - state.last_segment_time
    if idle_for >= STALL_GRACE_SECONDS:
        force_restart_channel(state, f"no new segment for {int(idle_for)} seconds")

def maybe_reenable_channel(state: ChannelState):
    if not state.disabled_due_to_error:
        return
    if (time.time() - state.disabled_at) >= CHANNEL_REENABLE_SECONDS:
        logging.info("[%s] Re-enabling channel after cooldown.", state.name)
        state.disabled_due_to_error = False
        state.resolve_fail_count = 0
        state.last_start_attempt = 0

def try_start_if_needed(state: ChannelState):
    if not state.enabled:
        return
    maybe_reenable_channel(state)
    if state.disabled_due_to_error:
        return
    if process_is_running(state):
        return
    if not state.can_retry():
        return
    try:
        start_recording(state)
        logging.info("[%s] Recording started successfully.", state.name)
    except Exception as e:
        state.process = None
        state.resolve_fail_count += 1
        state.last_error = truncate(str(e))
        logging.error(
            "[%s] Could not start recording. Attempt %s/%s\n%s",
            state.name,
            state.resolve_fail_count,
            MAX_RESOLVE_RETRIES,
            state.last_error,
        )
        if state.resolve_fail_count >= MAX_RESOLVE_RETRIES:
            state.disabled_due_to_error = True
            state.disabled_at = time.time()
            logging.error(
                "[%s] Temporarily disabling channel after %s failed attempts. Will retry after cooldown.",
                state.name,
                MAX_RESOLVE_RETRIES,
            )

def upload_completed_chunks(base_dir: Path):
    uploaded_count = 0
    failed_count = 0

    for folder_name, state in STATE_BY_FOLDER_NAME.items():
        if not state.channel_dir.exists():
            continue

        for rec_file in sorted(state.channel_dir.rglob(f"*{RECORD_EXT}")):
            if not rec_file.is_file():
                continue

            uploaded_marker = sidecar_path_for(rec_file, UPLOADED_SUFFIX)
            uploading_marker = sidecar_path_for(rec_file, UPLOADING_SUFFIX)

            if uploaded_marker.exists() or uploading_marker.exists():
                continue

            if not is_file_ready(rec_file, min_age_seconds=UPLOAD_MIN_FILE_AGE_SECONDS):
                continue

            object_key = build_obs_key(rec_file)

            if metadata_exists(object_key):
                logging.info("Metadata already exists for object_key=%s, cleaning local file if present.", object_key)
                uploaded_marker.touch(exist_ok=True)
                try:
                    rec_file.unlink(missing_ok=True)
                except Exception:
                    pass
                continue

            recorded_from, recorded_to = parse_recording_time_from_filename(rec_file)
            file_size_bytes = rec_file.stat().st_size
            s3_url = f"s3://{OBS_BUCKET}/{object_key}"
            http_url = build_http_url(OBS_BUCKET, object_key)

            try:
                uploading_marker.touch(exist_ok=False)
                logging.info("Uploading to OBS: %s -> %s", rec_file, s3_url)
                upload_file_to_obs(str(rec_file), object_key)

                record = {
                    "channel_name": state.name,
                    "folder_name": folder_name,
                    "recorded_from": recorded_from,
                    "recorded_to": recorded_to,
                    "local_file_name": rec_file.name,
                    "bucket_name": OBS_BUCKET,
                    "object_key": object_key,
                    "s3_url": s3_url,
                    "http_url": http_url,
                    "watch_url": state.last_watch_url,
                    "direct_url": state.last_direct_url,
                    "file_size_bytes": file_size_bytes,
                    "upload_time": datetime.now(),
                }

                insert_metadata(record)
                uploaded_marker.touch(exist_ok=True)
                rec_file.unlink(missing_ok=True)
                uploading_marker.unlink(missing_ok=True)
                logging.info("Uploaded successfully, metadata saved, local file removed: %s", rec_file)
                uploaded_count += 1

            except Exception as e:
                logging.error("Upload/metadata failed for %s: %s", rec_file, truncate(str(e)))
                uploading_marker.unlink(missing_ok=True)
                failed_count += 1

    if uploaded_count or failed_count:
        logging.info("Upload scan complete | uploaded=%s | failed=%s", uploaded_count, failed_count)

def cleanup_uploaded_markers(base_dir: Path):
    for marker in base_dir.rglob(f"*{UPLOADED_SUFFIX}"):
        try:
            original_file = Path(str(marker)[:-len(UPLOADED_SUFFIX)])
            if not original_file.exists():
                marker.unlink(missing_ok=True)
        except Exception:
            pass

def main():
    ensure_tools()
    ensure_obs_config()
    ensure_pg_config()
    verify_obs_access()
    create_table_if_not_exists()

    states = [
        ChannelState(
            name=ch["name"],
            search_query=ch["search_query"],
            channel_live_url=ch.get("channel_live_url"),
            allowed_terms=ch.get("allowed_terms", []),
            blocked_terms=ch.get("blocked_terms", []),
            enabled=ch.get("enabled", True),
        )
        for ch in CHANNELS
        if ch.get("enabled", True)
    ]

    if not states:
        logging.warning("No enabled channels found.")
        return

    for s in states:
        STATE_BY_FOLDER_NAME[s.folder_name] = s

    logging.info("====================================================")
    logging.info("24/7 NEWS RECORDER + OBS + POSTGRES STARTED")
    logging.info("Host: %s", platform.node())
    logging.info("Channels: %d", len(states))
    logging.info("Chunk length: %s seconds", CHUNK_SECONDS)
    logging.info("Stall grace: %s seconds", STALL_GRACE_SECONDS)
    logging.info("Channel re-enable cooldown: %s seconds", CHANNEL_REENABLE_SECONDS)
    logging.info("Retention: last %d days", RETENTION_DAYS)
    logging.info("Base spool folder: %s", BASE_DIR)
    logging.info("OBS endpoint: %s", OBS_ENDPOINT)
    logging.info("OBS bucket: %s", OBS_BUCKET)
    logging.info("OBS prefix: %s", OBS_PREFIX)
    logging.info("Postgres host: %s", PGHOST)
    logging.info("Postgres db: %s", PGDATABASE)
    logging.info("Postgres table: %s", PG_TABLE)
    logging.info("yt-dlp js runtimes: %s", YTDLP_JS_RUNTIMES or "none")
    logging.info("yt-dlp cookies file: %s", YTDLP_COOKIES_FILE or "none")
    logging.info("Output format: %s", RECORD_EXT)
    logging.info("====================================================")

    cycle_no = 0
    last_prune_time = 0.0
    last_upload_scan = 0.0

    try:
        while not STOP_REQUESTED:
            cycle_no += 1
            total = len(states)

            for idx, state in enumerate(states, start=1):
                if STOP_REQUESTED:
                    break
                render_progress(idx, total, cycle_no, state.name)
                check_process(state)
                check_stream_stall(state)
                try_start_if_needed(state)

            now = time.time()

            if now - last_upload_scan >= UPLOAD_SCAN_INTERVAL_SECONDS:
                upload_completed_chunks(BASE_DIR)
                cleanup_uploaded_markers(BASE_DIR)
                last_upload_scan = now

            if now - last_prune_time >= PRUNE_INTERVAL_SECONDS:
                prune_old_recordings(BASE_DIR, RETENTION_DAYS)
                last_prune_time = now

            active_count = sum(1 for s in states if process_is_running(s))
            skipped_count = sum(1 for s in states if s.disabled_due_to_error)

            logging.info(
                "Cycle %s complete | active=%s | skipped=%s | base=%s",
                cycle_no,
                active_count,
                skipped_count,
                BASE_DIR,
            )

            slept = 0
            while slept < MAIN_LOOP_SLEEP and not STOP_REQUESTED:
                time.sleep(1)
                slept += 1

    finally:
        logging.info("Stopping all channels...")
        for state in states:
            stop_recording(state)

        logging.info("Running final upload scan before exit...")
        try:
            upload_completed_chunks(BASE_DIR)
        except Exception as e:
            logging.error("Final upload scan failed: %s", truncate(str(e)))

        logging.info("Stopped cleanly.")

if __name__ == "__main__":
    main()