"""EventBridge (S3 Object Created, media/ prefix): make a compressed thumbnail. Owner: Member B.

Uses Pillow. Switch to OpenCV (cv2.resize with INTER_AREA + cv2.imencode quality) if the team
prefers; the spec only requires resize with aspect ratio kept plus compression.
"""
import io
import os

from PIL import Image, ImageOps

from ecoguard_common import db, storage, urls

MAX_EDGE = int(os.environ.get("THUMB_MAX_EDGE", "256"))
QUALITY = int(os.environ.get("THUMB_QUALITY", "70"))


def make_thumbnail(data, max_edge=MAX_EDGE, quality=QUALITY):
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    image.thumbnail((max_edge, max_edge))  # in place, keeps aspect ratio, never upscales
    out = io.BytesIO()
    image.convert("RGB").save(out, "JPEG", quality=quality, optimize=True)
    return out.getvalue()


def handler(event, context):
    key = event["detail"]["object"]["key"]
    file_id = urls.file_id_from_key(key)
    record = db.get_file(file_id)
    if not record or record.get("type") != "image":
        return {"skipped": True}

    thumb = urls.thumb_key(file_id)
    storage.put_bytes(thumb, make_thumbnail(storage.get_bytes(key)), "image/jpeg")
    db.update(file_id, thumb_key=thumb)
    return {"thumb_key": thumb}
