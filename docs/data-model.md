# Data model

## S3 layout (one private bucket)

| Prefix | Content | Written by |
|---|---|---|
| `media/<sha256>/<safe filename>` | original upload | browser, via presigned PUT |
| `thumbs/<sha256>.jpg` | image thumbnail | `thumbnail` Lambda |

The SHA-256 of the file content is both the S3 key component and the DynamoDB primary key. That
makes deduplication a single conditional write and lets any URL be turned back into a `file_id`
without a lookup. Only the `media/` prefix triggers processing, so writing a thumbnail cannot loop.

## DynamoDB table (`MediaTable`, partition key `file_id`)

| Attribute | Type | Notes |
|---|---|---|
| `file_id` | S | sha256 hex of the content |
| `type` | S | `image` or `video` |
| `filename` | S | sanitised original name |
| `content_type` | S | as declared at upload |
| `size` | N | bytes |
| `owner` | S | Cognito `sub` of the uploader |
| `s3_key` | S | `media/...` |
| `thumb_key` | S | `thumbs/...`, absent for video or before the thumbnail exists |
| `tags` | M | `{species: count}`, counts are integers |
| `status` | S | `pending`, `ready`, `failed`, `rejected` |
| `model_version` | S | from the inference service |
| `created_at` | S | ISO 8601 UTC, lexicographically sortable |
| `processed_at` | S | set when tagging finishes |
| `error` | S | only on `failed` and `rejected` |

Status lifecycle: `upload_init` writes `pending`, then `ingest` verifies the checksum and sets
`ready`. A mismatch deletes the object and sets `rejected`. An inference error sets `failed`
(re-uploading the same file is allowed in both cases).

Queries use a scan with in-Lambda filtering. That is fine for hundreds to low thousands of items and
keeps tag-count logic simple. If the demo dataset grows, add a GSI on `status` + `created_at`.

## Tags

- Lower-case, trimmed, internal whitespace collapsed (`"Feral  Pig"` becomes `"feral pig"`).
- Model tags and manual tags share the same map. A manual add with no count sets the count to 1.
- Model species names come from the `classes` list in the model config, so keep them consistent
  with the Lex `Species` slot values.
