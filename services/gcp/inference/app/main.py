"""Aussie EcoGuard inference service (Cloud Run). Owner: Member B."""
import os
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from . import media
from .aggregate import counts_from_detections, merge_max
from .auth import require_auth
from .models import ModelRegistry

app = FastAPI(title="EcoGuard inference")
registry = ModelRegistry(os.environ.get("MODEL_CONFIG", "config/model_config.json"))


class DetectRequest(BaseModel):
    media_type: Literal["image", "video"] = "image"
    url: Optional[str] = None
    image_base64: Optional[str] = None


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/model", dependencies=[Depends(require_auth)])
def model_info():
    model = registry.get()
    return {"model_version": model.version, "type": model.config.get("type"),
            "classes": model.config.get("classes")}


@app.post("/detect")
def detect(req: DetectRequest, _claims: dict = Depends(require_auth)):
    model = registry.get()
    detections, per_frame = [], []
    path = None
    try:
        if req.image_base64:
            frames = [(0, media.decode_base64_image(req.image_base64))]
        elif req.url:
            path = media.download(req.url)
            if req.media_type == "video":
                frames = media.sample_frames(path)
            else:
                frames = [(0, media.read_image(path))]
        else:
            raise HTTPException(status_code=422, detail="url or image_base64 is required")

        analysed = 0
        for index, frame in frames:
            analysed += 1
            found = model.predict(frame)
            per_frame.append(counts_from_detections(found, model.threshold, model.label_map))
            detections.extend({**d, "frame": index} for d in found if d["confidence"] >= model.threshold)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if path:
            os.unlink(path)

    return {
        "counts": merge_max(per_frame),
        "detections": detections,
        "model_version": model.version,
        "frames_analysed": analysed,
    }
