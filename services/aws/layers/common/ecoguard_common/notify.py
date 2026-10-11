"""SNS tag alerts. Subscriptions carry a filter policy on the `tags` message attribute."""
import json
import os

_client = None


def _sns():
    global _client
    if _client is None:
        import boto3

        _client = boto3.client("sns")
    return _client


def publish_tags(file_id, tags, reason="New file tagged"):
    """Publish one message whose `tags` attribute lists every species on the file."""
    topic = os.environ.get("ALERTS_TOPIC_ARN")
    species = sorted(tags or [])
    if not topic or not species:
        return
    summary = ", ".join(f"{name} x{tags[name]}" for name in species)
    _sns().publish(
        TopicArn=topic,
        Subject=f"EcoGuard: {', '.join(species)}"[:100],
        Message=f"{reason}\nFile: {file_id}\nDetected: {summary}",
        MessageAttributes={
            "tags": {"DataType": "String.Array", "StringValue": json.dumps(species)}
        },
    )


def subscribe_email(email, tags):
    """Subscribe an email to alerts for any of `tags`. SNS sends a confirmation link first."""
    topic = os.environ["ALERTS_TOPIC_ARN"]
    return _sns().subscribe(
        TopicArn=topic,
        Protocol="email",
        Endpoint=email,
        Attributes={
            "FilterPolicy": json.dumps({"tags": sorted(tags)}),
            "FilterPolicyScope": "MessageAttributes",
        },
        ReturnSubscriptionArn=True,
    )
