"""Query logic shared by the search Lambda and the Lex fulfilment Lambda."""
from datetime import datetime, timedelta, timezone

from . import db, storage, tags as taglib


def present(item, expires=3600):
    """Public shape of a record: presigned URLs instead of keys."""
    thumb_key = item.get("thumb_key")
    return {
        "file_id": item["file_id"],
        "type": item.get("type"),
        "url": storage.presign_get(item["s3_key"], expires),
        "thumb_url": storage.presign_get(thumb_key, expires) if thumb_key else None,
        "tags": item.get("tags", {}),
        "created_at": item.get("created_at"),
    }


def day_range(day):
    """(since, until) ISO strings covering one UTC day given as YYYY-MM-DD."""
    try:
        start = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError) as exc:
        raise ValueError("date must be YYYY-MM-DD") from exc
    return start.isoformat(), (start + timedelta(days=1)).isoformat()


def find_by_tags(required, since=None, until=None, limit=200):
    items = [i for i in db.scan_ready(since, until) if taglib.matches(i.get("tags"), required)]
    items.sort(key=lambda i: i.get("created_at", ""), reverse=True)
    return [present(i) for i in items[:limit]]


def find_lost_pet(species, extra_tags=(), days=30, limit=50):
    """Files holding every species tag, ranked by matched extra tags (colour, breed), then newest."""
    days = max(1, min(int(days), 365))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    required = {s: 1 for s in species}
    ranked = []
    for item in db.scan_ready(since=since):
        tags = item.get("tags") or {}
        if not taglib.matches(tags, required):
            continue
        score = sum(1 for t in extra_tags if t in tags)
        ranked.append((score, item.get("created_at", ""), item))
    ranked.sort(key=lambda r: (r[0], r[1]), reverse=True)
    return [present(r[2]) for r in ranked[:limit]]
