"""S3 helpers. The bucket is private; callers get presigned URLs."""
import hashlib
import os

_client = None


def _s3():
    global _client
    if _client is None:
        import boto3

        _client = boto3.client("s3")
    return _client


def bucket():
    return os.environ["MEDIA_BUCKET"]


def presign_get(key, expires=3600):
    return _s3().generate_presigned_url(
        "get_object", Params={"Bucket": bucket(), "Key": key}, ExpiresIn=expires
    )


def presign_put(key, content_type, expires=900):
    return _s3().generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket(), "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def get_bytes(key):
    return _s3().get_object(Bucket=bucket(), Key=key)["Body"].read()


def put_bytes(key, data, content_type):
    _s3().put_object(Bucket=bucket(), Key=key, Body=data, ContentType=content_type)


def sha256_of(key):
    """Stream the object through SHA-256 so large videos do not need to fit in memory."""
    digest = hashlib.sha256()
    body = _s3().get_object(Bucket=bucket(), Key=key)["Body"]
    for chunk in body.iter_chunks(chunk_size=1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def delete_keys(keys):
    keys = [k for k in keys if k]
    if keys:
        _s3().delete_objects(
            Bucket=bucket(), Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True}
        )
