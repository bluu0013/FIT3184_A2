"""Model registry: loads weights and class list from a config file, reloads when it changes.

The config can be a local path or gs://bucket/path.json. Swapping to a new model means editing
that file (new weights path, version and classes), not redeploying code.
Owner: Member B.
"""
import json
import os
import tempfile
import threading
import time

REFRESH_SECONDS = int(os.environ.get("MODEL_REFRESH_SECONDS", "60"))


def fetch(uri):
    """Return a local path for a local path, gs:// URI, or a bare Ultralytics weight name."""
    if not uri.startswith("gs://"):
        return uri
    from google.cloud import storage

    bucket, _, blob = uri[5:].partition("/")
    local = os.path.join(tempfile.gettempdir(), "ecoguard", bucket, blob)
    os.makedirs(os.path.dirname(local), exist_ok=True)
    storage.Client().bucket(bucket).blob(blob).download_to_filename(local)
    return local


def read_config(uri):
    path = fetch(uri)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class LoadedModel:
    def __init__(self, config):
        self.config = config
        self.version = config["model_version"]
        self.threshold = float(config.get("confidence", 0.35))
        self.label_map = config.get("label_map", {})
        self._model = self._load(config)

    @staticmethod
    def _load(config):
        weights = fetch(config["weights"])
        kind = config.get("type", "yolo")
        if kind == "yolo_world":
            from ultralytics import YOLOWorld

            model = YOLOWorld(weights)
            model.set_classes(config["classes"])
            return model
        if kind == "yolo":
            from ultralytics import YOLO

            return YOLO(weights)
        raise ValueError(f"unknown model type: {kind}")

    def predict(self, image):
        """image: numpy BGR array. Returns [{label, confidence, bbox}]."""
        result = self._model.predict(image, conf=0.05, verbose=False)[0]
        names = result.names
        out = []
        for box in result.boxes:
            out.append(
                {
                    "label": names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": [round(float(v), 1) for v in box.xyxy[0].tolist()],
                }
            )
        return out


class ModelRegistry:
    def __init__(self, config_uri):
        self.config_uri = config_uri
        self._lock = threading.Lock()
        self._model = None
        self._checked = 0.0

    def get(self):
        now = time.time()
        with self._lock:
            if self._model is None or now - self._checked > REFRESH_SECONDS:
                self._checked = now
                config = read_config(self.config_uri)
                fingerprint = (config["model_version"], config["weights"])
                current = self._model and (self._model.version, self._model.config["weights"])
                if self._model is None or fingerprint != current:
                    self._model = LoadedModel(config)
            return self._model
