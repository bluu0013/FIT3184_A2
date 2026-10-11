"""Insert fake media records so query and UI work can start before the ML pipeline exists.

Usage:
    python scripts/seed_dummy_data.py --table <TableName output> [--region ap-southeast-2] [--clear]

The records point at keys that do not exist in S3, so presigned URLs resolve to 404s, but every
search, tag edit and Lex flow can be exercised. `--clear` removes only records created by this
script (owner = "seed-script").
"""
import argparse
import hashlib
import random
from datetime import datetime, timedelta, timezone

import boto3

SPECIES = ["fox", "feral pig", "cane toad", "rabbit", "cat", "dog", "deer"]
EXTRA = ["ginger", "black", "juvenile", "labrador"]


def make_item(i, rng):
    file_id = hashlib.sha256(f"seed-{i}".encode()).hexdigest()
    tags = {s: rng.randint(1, 3) for s in rng.sample(SPECIES, rng.randint(1, 3))}
    if "cat" in tags and rng.random() < 0.5:
        tags["ginger"] = 1
    is_video = rng.random() < 0.2
    created = datetime.now(timezone.utc) - timedelta(days=rng.randint(0, 20), hours=rng.randint(0, 23))
    item = {
        "file_id": file_id,
        "type": "video" if is_video else "image",
        "filename": f"seed-{i}.{'mp4' if is_video else 'jpg'}",
        "content_type": "video/mp4" if is_video else "image/jpeg",
        "size": rng.randint(50_000, 5_000_000),
        "owner": "seed-script",
        "s3_key": f"media/{file_id}/seed-{i}.{'mp4' if is_video else 'jpg'}",
        "tags": tags,
        "status": "ready",
        "model_version": "seed",
        "created_at": created.isoformat(),
    }
    if not is_video:
        item["thumb_key"] = f"thumbs/{file_id}.jpg"
    return item


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", required=True)
    parser.add_argument("--region")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    table = boto3.resource("dynamodb", region_name=args.region).Table(args.table)
    rng = random.Random(1234)

    if args.clear:
        from boto3.dynamodb.conditions import Attr

        removed = 0
        kwargs = {"FilterExpression": Attr("owner").eq("seed-script")}
        while True:
            page = table.scan(**kwargs)
            for item in page["Items"]:
                table.delete_item(Key={"file_id": item["file_id"]})
                removed += 1
            if "LastEvaluatedKey" not in page:
                break
            kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]
        print(f"removed {removed} seed records")
        return

    with table.batch_writer() as batch:
        for i in range(args.count):
            batch.put_item(Item=make_item(i, rng))
    print(f"inserted {args.count} seed records into {args.table}")


if __name__ == "__main__":
    main()
