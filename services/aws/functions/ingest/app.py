"""EventBridge (S3 Object Created, media/ prefix): verify, tag and index a file. Owner: Member B."""
from ecoguard_common import db, inference, notify, storage, urls


def handler(event, context):
    key = event["detail"]["object"]["key"]
    file_id = urls.file_id_from_key(key)
    record = db.get_file(file_id)
    if record is None:
        print(f"no record for {file_id}; ignoring {key}")
        return {"skipped": True}

    # Never trust the checksum the browser declared.
    if storage.sha256_of(key) != file_id:
        storage.delete_keys([key])
        db.update(file_id, status="rejected", error="checksum mismatch")
        return {"rejected": True}

    try:
        result = inference.detect(
            url=storage.presign_get(key, 3600),
            media_type=record.get("type", "image"),
            timeout=280,  # cold ML container plus up to a few minutes of video
        )
    except inference.InferenceError as exc:
        db.update(file_id, status="failed", error=str(exc)[:500])
        raise

    tags = {name: int(n) for name, n in result.get("counts", {}).items()}
    db.update(
        file_id,
        tags=tags,
        status="ready",
        model_version=result.get("model_version", "unknown"),
        processed_at=db.now_iso(),
    )
    notify.publish_tags(file_id, tags)
    return {"file_id": file_id, "tags": tags}
