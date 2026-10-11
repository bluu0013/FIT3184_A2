"""Pure post-processing of detections. No ML or cloud imports so it can be unit tested."""


def counts_from_detections(detections, threshold=0.35, label_map=None):
    """{species: number of detections at or above threshold}.

    label_map renames model labels to platform tags. A label mapped to None is dropped
    (for example COCO's "bird" when we only care about mammals).
    """
    label_map = label_map or {}
    counts = {}
    for det in detections:
        if det["confidence"] < threshold:
            continue
        label = det["label"]
        if label in label_map:
            label = label_map[label]
        if label is None:
            continue
        label = str(label).strip().lower()
        counts[label] = counts.get(label, 0) + 1
    return counts


def merge_max(per_frame_counts):
    """Per species, the highest count seen in any single frame.

    Taking the maximum rather than the sum avoids counting one animal once per sampled frame.
    """
    merged = {}
    for counts in per_frame_counts:
        for label, n in counts.items():
            merged[label] = max(merged.get(label, 0), n)
    return merged


def frame_indices(total_frames, fps, interval_seconds=10):
    """Frame numbers to analyse: the first frame, then one every interval_seconds."""
    if total_frames <= 0:
        return []
    step = max(1, round((fps if fps and fps > 0 else 25.0) * interval_seconds))
    return list(range(0, total_frames, step))
