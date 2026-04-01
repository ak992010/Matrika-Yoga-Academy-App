from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "submissions"
DATA_DIR.mkdir(exist_ok=True)
IST_ZONE = ZoneInfo("Asia/Kolkata")

VISITOR_LOG_CSV = "visitor_logs.csv"
VISITOR_LOG_HEADERS = [
    "visited_at",
    "surface",
    "page",
    "path",
    "visitor_type",
    "visitor_name",
    "account_email",
    "ip_masked",
    "browser",
    "device",
    "language",
    "referrer",
]


def visitor_timestamp() -> str:
    return datetime.now(IST_ZONE).strftime("%Y-%m-%d %H:%M:%S IST")


def normalize_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_email(value: object) -> str:
    return normalize_text(value).lower()


def mask_ip_address(ip_address: str) -> str:
    ip_address = normalize_text(ip_address)
    if not ip_address:
        return ""
    if "." in ip_address:
        parts = ip_address.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3] + ["x"])
    if ":" in ip_address:
        parts = [part for part in ip_address.split(":") if part]
        if parts:
            return ":".join(parts[:4]) + ":x:x"
    return "anon-" + hashlib.sha1(ip_address.encode("utf-8")).hexdigest()[:8]


def browser_from_user_agent(user_agent: str) -> str:
    text = normalize_text(user_agent).lower()
    if not text:
        return "Unknown"
    if "edg/" in text or "edge/" in text:
        return "Edge"
    if "opr/" in text or "opera" in text:
        return "Opera"
    if "chrome/" in text and "edg/" not in text:
        return "Chrome"
    if "firefox/" in text:
        return "Firefox"
    if "safari/" in text and "chrome/" not in text:
        return "Safari"
    if "android" in text:
        return "Android Browser"
    return "Other"


def device_from_user_agent(user_agent: str) -> str:
    text = normalize_text(user_agent).lower()
    if not text:
        return "Unknown"
    if "ipad" in text or "tablet" in text:
        return "Tablet"
    if "iphone" in text or ("android" in text and "mobile" in text):
        return "Mobile"
    if "android" in text:
        return "Android"
    if "macintosh" in text or "windows" in text or "linux" in text:
        return "Desktop"
    return "Other"


def language_from_header(accept_language: str) -> str:
    header = normalize_text(accept_language)
    if not header:
        return ""
    first = header.split(",")[0]
    return first.split(";")[0].strip()


def referrer_from_url(referrer: str, own_host: str = "") -> str:
    referrer = normalize_text(referrer)
    if not referrer:
        return "Direct"
    parsed = urlparse(referrer)
    host = normalize_text(parsed.netloc or referrer)
    if own_host and host == own_host:
        return "Internal"
    return host or "Direct"


def append_local_submission_row(csv_name: str, headers: list[str], row: dict[str, object]) -> None:
    file_path = DATA_DIR / csv_name
    existing_rows: list[dict[str, str]] = []
    rewrite_required = False

    if file_path.exists():
        with file_path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            current_headers = reader.fieldnames or []
            existing_rows = list(reader)
        rewrite_required = current_headers != headers

    if rewrite_required:
        with file_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            for existing_row in existing_rows:
                writer.writerow({key: existing_row.get(key, "") for key in headers})
            writer.writerow({key: row.get(key, "") for key in headers})
        return

    with file_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        if not file_path.exists() or file_path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in headers})


def build_visitor_row(
    *,
    surface: str,
    page: str,
    path: str,
    visitor_type: str,
    visitor_name: str = "",
    account_email: str = "",
    ip_address: str = "",
    user_agent: str = "",
    accept_language: str = "",
    referrer: str = "",
    own_host: str = "",
) -> dict[str, str]:
    return {
        "visited_at": visitor_timestamp(),
        "surface": normalize_text(surface),
        "page": normalize_text(page),
        "path": normalize_text(path),
        "visitor_type": normalize_text(visitor_type) or "guest",
        "visitor_name": normalize_text(visitor_name),
        "account_email": normalize_email(account_email),
        "ip_masked": mask_ip_address(ip_address),
        "browser": browser_from_user_agent(user_agent),
        "device": device_from_user_agent(user_agent),
        "language": language_from_header(accept_language),
        "referrer": referrer_from_url(referrer, own_host=own_host),
    }
