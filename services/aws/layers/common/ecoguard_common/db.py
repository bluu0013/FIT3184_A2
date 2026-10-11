"""DynamoDB access for the media table. See docs/data-model.md."""
import os
from datetime import datetime, timezone
from decimal import Decimal

_table_cache = None


def _table():
    global _table_cache
    if _table_cache is None:
        import boto3

        _table_cache = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table_cache


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _clean(value):
    """DynamoDB returns Decimal; convert so json.dumps works."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def get_file(file_id):
    item = _table().get_item(Key={"file_id": file_id}).get("Item")
    return _clean(item) if item else None


def create_pending(item):
    """Create the record only if it does not exist. Returns False when it already does."""
    from botocore.exceptions import ClientError

    try:
        _table().put_item(Item=item, ConditionExpression="attribute_not_exists(file_id)")
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def put(item):
    _table().put_item(Item=item)


def update(file_id, **attrs):
    """SET the given attributes on an existing record."""
    if not attrs:
        return
    names = {f"#k{i}": k for i, k in enumerate(attrs)}
    values = {f":v{i}": v for i, v in enumerate(attrs.values())}
    expr = "SET " + ", ".join(f"#k{i} = :v{i}" for i in range(len(attrs)))
    _table().update_item(
        Key={"file_id": file_id},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def delete(file_id):
    _table().delete_item(Key={"file_id": file_id})


def scan_ready(since=None, until=None):
    """All records with status ready, optionally with created_at in [since, until)."""
    from boto3.dynamodb.conditions import Attr

    cond = Attr("status").eq("ready")
    if since:
        cond = cond & Attr("created_at").gte(since)
    if until:
        cond = cond & Attr("created_at").lt(until)
    kwargs = {"FilterExpression": cond}
    items = []
    while True:
        page = _table().scan(**kwargs)
        items.extend(_clean(i) for i in page.get("Items", []))
        if "LastEvaluatedKey" not in page:
            return items
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]
