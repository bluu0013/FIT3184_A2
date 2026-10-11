"""HTTP API (payload v2) request and response helpers."""
import base64
import json


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def ok(body):
    return response(200, body)


def error(status, message):
    return response(status, {"error": message})


def json_body(event):
    raw = event.get("body")
    if not raw:
        return {}
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("body must be valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("body must be a JSON object")
    return data


def claims(event):
    ctx = event.get("requestContext") or {}
    return ((ctx.get("authorizer") or {}).get("jwt") or {}).get("claims") or {}


def bearer_token(event):
    value = (event.get("headers") or {}).get("authorization", "")
    return value[7:] if value.lower().startswith("bearer ") else None


def run(fn, event):
    """Call fn(event) and turn the usual exceptions into HTTP errors.

    ValueError -> 400, LookupError -> 404, ConnectionError (inference or other upstream) -> 502.
    """
    try:
        return ok(fn(event))
    except ValueError as exc:
        return error(400, str(exc))
    except LookupError as exc:
        return error(404, str(exc.args[0]) if exc.args else "not found")
    except ConnectionError as exc:
        return error(502, str(exc))
