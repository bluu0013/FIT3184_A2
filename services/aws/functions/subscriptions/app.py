"""POST /notifications/subscribe: email alerts filtered by species tag. Owner: Member B."""
import re

from ecoguard_common import notify, responses, tags as taglib

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _subscribe(event):
    body = responses.json_body(event)
    tags = list(taglib.normalise_query(body.get("tags")))
    email = body.get("email") or responses.claims(event).get("email")
    if not email or not _EMAIL.match(email):
        raise ValueError("a valid email is required")
    notify.subscribe_email(email, tags)
    return {"status": "pending_confirmation", "email": email, "tags": tags}


def handler(event, context):
    return responses.run(_subscribe, event)
