"""Search routes. Owner: Member C.

POST /search/tags, /search/thumbnail, /search/by-file, /search/lost-pet
"""
import base64
import binascii

from ecoguard_common import db, inference, responses, search, storage, tags as taglib, urls

MAX_IMAGE_BYTES = 4 * 1024 * 1024  # HTTP API / Lambda payload limit after base64


def _tags(event):
    body = responses.json_body(event)
    required = taglib.normalise_query(body.get("tags"))
    since = until = None
    if body.get("date"):
        since, until = search.day_range(body["date"])
    return {"results": search.find_by_tags(required, since, until)}


def _thumbnail(event):
    body = responses.json_body(event)
    file_id = urls.file_id_from_url(body.get("thumbnail_url"))
    item = db.get_file(file_id)
    if not item or not item.get("s3_key"):
        raise LookupError("no file found for that thumbnail")
    return {"file_id": file_id, "url": storage.presign_get(item["s3_key"])}


def _image_b64(body):
    value = body.get("image_base64")
    if not value:
        return None
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("image_base64 is not valid base64") from exc
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("image is larger than 4 MB")
    return value


def _detect(event, body):
    image = _image_b64(body)
    if not image:
        return {}
    # Forward the caller's token so the secondary cloud can authorise the request itself.
    result = inference.detect(
        image_base64=image, media_type="image", token=responses.bearer_token(event)
    )
    return {k: int(v) for k, v in result.get("counts", {}).items()}


def _by_file(event):
    body = responses.json_body(event)
    if not body.get("image_base64"):
        raise ValueError("image_base64 is required")
    detected = _detect(event, body)
    if not detected:
        return {"detected_tags": {}, "results": []}
    required = {tag: 1 for tag in detected}
    return {"detected_tags": detected, "results": search.find_by_tags(required)}


def _lost_pet(event):
    body = responses.json_body(event)
    detected = _detect(event, body)
    given = taglib.normalise_query(body["tags"]) if body.get("tags") else {}
    if not detected and not given:
        raise ValueError("provide image_base64 and/or tags")
    # Detected species are mandatory. With text only, the first tag is treated as the species.
    if detected:
        species = list(detected)
        extra = list(given)
    else:
        names = list(given)
        species, extra = names[:1], names[1:]
    return {
        "detected_tags": detected,
        "results": search.find_lost_pet(species, extra, body.get("days", 30)),
    }


ROUTES = {
    "POST /search/tags": _tags,
    "POST /search/thumbnail": _thumbnail,
    "POST /search/by-file": _by_file,
    "POST /search/lost-pet": _lost_pet,
}


def handler(event, context):
    fn = ROUTES.get(event.get("routeKey"))
    if fn is None:
        return responses.error(404, "unknown route")
    return responses.run(fn, event)
