"""Pure helpers for S3 keys and the URLs the API hands out."""
import re
from urllib.parse import unquote, urlparse

_SHA = re.compile(r"^[0-9a-f]{64}$")
_SAFE = re.compile(r"[^A-Za-z0-9._-]")


def is_sha256(value):
    return isinstance(value, str) and bool(_SHA.match(value))


def safe_filename(name):
    base = (name or "").replace("\\", "/").split("/")[-1]
    cleaned = _SAFE.sub("_", base).strip(".") or "upload"
    return cleaned[:100]


def media_key(file_id, filename):
    return f"media/{file_id}/{safe_filename(filename)}"


def thumb_key(file_id):
    return f"thumbs/{file_id}.jpg"


def key_from_url(url):
    """S3 object key from a presigned https URL (virtual-hosted or path style) or an s3:// URL."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("a URL is required")
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https", "s3"):
        raise ValueError("unsupported URL: " + url[:80])
    key = unquote(parsed.path).lstrip("/")
    if not key:
        raise ValueError("URL has no object path")
    return key


def file_id_from_key(key):
    """Find the sha256 in `media/<sha>/<name>` or `thumbs/<sha>.jpg`, wherever it sits in the path."""
    parts = [p for p in key.split("/") if p]
    for i, part in enumerate(parts):
        if part == "media" and i + 2 < len(parts) and is_sha256(parts[i + 1]):
            return parts[i + 1]
        if part == "thumbs" and i + 1 < len(parts):
            stem = parts[i + 1].rsplit(".", 1)[0]
            if is_sha256(stem):
                return stem
    raise ValueError("URL does not point at an EcoGuard media or thumbnail object")


def file_id_from_url(url):
    return file_id_from_key(key_from_url(url))
