"""Client for the GCP Cloud Run inference service (see services/gcp/inference)."""
import json
import os
import urllib.error
import urllib.request


class InferenceError(ConnectionError):
    """Raised when the inference service cannot be reached or returns an error."""


def detect(*, url=None, image_base64=None, media_type="image", token=None, timeout=25):
    """Call POST /detect.

    token: the caller's Cognito token to forward (user-initiated requests). When None the shared
    X-Api-Key from the environment is used (S3-triggered ingest has no user token).
    timeout: keep under 30 s for API Gateway paths; ingest may pass a larger value.
    """
    base = os.environ.get("INFERENCE_URL", "").rstrip("/")
    if not base:
        raise InferenceError("INFERENCE_URL is not configured")
    if not (url or image_base64):
        raise ValueError("url or image_base64 is required")

    payload = {"media_type": media_type}
    if url:
        payload["url"] = url
    if image_base64:
        payload["image_base64"] = image_base64

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    elif os.environ.get("INFERENCE_API_KEY"):
        headers["X-Api-Key"] = os.environ["INFERENCE_API_KEY"]

    request = urllib.request.Request(
        base + "/detect", data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise InferenceError(f"inference service returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise InferenceError(f"inference service unreachable: {exc}") from exc
