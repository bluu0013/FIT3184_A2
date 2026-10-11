"""Fetch and decode images, and sample video frames."""
import base64
import ipaddress
import os
import socket
import tempfile
from urllib.parse import urlparse

import cv2
import numpy as np
import requests

from .aggregate import frame_indices

MAX_BYTES = int(os.environ.get("MAX_MEDIA_BYTES", str(600 * 1024 * 1024)))
FRAME_INTERVAL_SECONDS = int(os.environ.get("FRAME_INTERVAL_SECONDS", "10"))
ALLOWED_SUFFIXES = tuple(
    s.strip() for s in os.environ.get("ALLOWED_URL_SUFFIXES", ".amazonaws.com").split(",") if s.strip()
)


def check_url(url):
    """Only https URLs on an allow-listed host that do not resolve to a private address (SSRF guard)."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not host.endswith(ALLOWED_SUFFIXES):
        raise ValueError("url host is not allowed")
    for info in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP):
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise ValueError("url resolves to a non-public address")


def download(url):
    """Download to a temp file and return its path. Caller deletes it."""
    check_url(url)
    fd, path = tempfile.mkstemp(prefix="ecoguard-")
    size = 0
    try:
        with os.fdopen(fd, "wb") as out, requests.get(url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(1024 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError("media is too large")
                out.write(chunk)
    except Exception:
        os.unlink(path)
        raise
    return path


def decode_base64_image(data):
    raw = base64.b64decode(data, validate=True)
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("could not decode image")
    return image


def read_image(path):
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("could not decode image")
    return image


def sample_frames(path, interval_seconds=FRAME_INTERVAL_SECONDS):
    """Yield (frame_number, BGR image): the first frame, then one every interval_seconds."""
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            raise ValueError("could not open video")
        fps = cap.get(cv2.CAP_PROP_FPS)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for index in frame_indices(total, fps, interval_seconds):
            cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = cap.read()
            if ok:
                yield index, frame
    finally:
        cap.release()
