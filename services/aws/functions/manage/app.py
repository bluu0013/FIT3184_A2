"""Bulk tag editing and deletion. Owner: Member C.

POST /tags and POST /files/delete
"""
from ecoguard_common import db, notify, responses, storage, tags as taglib, urls

MAX_URLS = 100


def _resolve(body):
    """Map the request's URLs to file ids. Returns (file_ids, unresolved_urls)."""
    raw = body.get("urls")
    if not isinstance(raw, list) or not raw:
        raise ValueError("urls must be a non-empty list")
    if len(raw) > MAX_URLS:
        raise ValueError(f"at most {MAX_URLS} urls per request")
    ids, bad = [], []
    for url in raw:
        try:
            file_id = urls.file_id_from_url(url)
        except ValueError:
            bad.append(url)
            continue
        if file_id not in ids:
            ids.append(file_id)
    return ids, bad


def _edit_tags(event):
    body = responses.json_body(event)
    operation = body.get("operation")
    tags = taglib.normalise_query(body.get("tags"))
    taglib.apply_tag_edit({}, tags, operation)  # reject a bad operation before touching anything
    ids, not_found = _resolve(body)

    updated = []
    for file_id in ids:
        item = db.get_file(file_id)
        if not item:
            not_found.append(file_id)
            continue
        new_tags = taglib.apply_tag_edit(item.get("tags"), tags, operation)  # validates operation
        if new_tags != (item.get("tags") or {}):
            db.update(file_id, tags=new_tags)
            if operation == 1:
                notify.publish_tags(file_id, new_tags, reason="Tags updated")
        updated.append(file_id)
    return {"updated": updated, "not_found": not_found}


def _delete(event):
    body = responses.json_body(event)
    ids, not_found = _resolve(body)

    deleted = []
    for file_id in ids:
        item = db.get_file(file_id)
        if not item:
            not_found.append(file_id)
            continue
        # Storage first; if this fails the record stays and the call can be retried.
        storage.delete_keys([item.get("s3_key"), item.get("thumb_key")])
        db.delete(file_id)
        deleted.append(file_id)
    return {"deleted": deleted, "not_found": not_found}


ROUTES = {"POST /tags": _edit_tags, "POST /files/delete": _delete}


def handler(event, context):
    fn = ROUTES.get(event.get("routeKey"))
    if fn is None:
        return responses.error(404, "unknown route")
    return responses.run(fn, event)
