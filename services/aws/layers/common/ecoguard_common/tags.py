"""Pure tag helpers. No AWS imports."""
import re

_WS = re.compile(r"\s+")


def normalise_tag(tag):
    """Lower-case, trim and collapse whitespace. Raises ValueError for empty or non-string tags."""
    if not isinstance(tag, str):
        raise ValueError("tags must be strings")
    cleaned = _WS.sub(" ", tag.strip().lower())
    if not cleaned:
        raise ValueError("tags must not be empty")
    return cleaned


def _count(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("tag counts must be whole numbers of at least 1")
    return value


def normalise_query(raw):
    """Turn user input into {tag: min_count}.

    Accepts {"fox": 2}, ["fox", "cat"] or "fox". A list or string means a count of 1 each.
    """
    if isinstance(raw, str):
        raw = [raw]
    if isinstance(raw, (list, tuple)):
        out = {normalise_tag(t): 1 for t in raw}
    elif isinstance(raw, dict):
        out = {normalise_tag(k): _count(v) for k, v in raw.items()}
    else:
        raise ValueError("tags must be an object, a list or a string")
    if not out:
        raise ValueError("at least one tag is required")
    return out


def matches(record_tags, required):
    """Logical AND: every required tag is present with at least the required count."""
    record_tags = record_tags or {}
    return all(int(record_tags.get(tag, 0)) >= n for tag, n in required.items())


def apply_tag_edit(current, tags, operation):
    """Return a new tag map after an add (operation 1) or remove (operation 0).

    Adding keeps the larger of the existing and requested count. Removing a tag the record does
    not have is ignored.
    """
    if isinstance(operation, bool) or operation not in (0, 1):
        raise ValueError("operation must be 1 (add) or 0 (remove)")
    result = {k: int(v) for k, v in (current or {}).items()}
    if operation == 1:
        for tag, n in tags.items():
            result[tag] = max(result.get(tag, 0), n)
    else:
        for tag in tags:
            result.pop(tag, None)
    return result
