# API contract

Base URL: `ApiUrl` stack output. All routes are `POST`, JSON in and out, and require
`Authorization: Bearer <Cognito ID token>`. Errors look like `{"error": "message"}` with status
400 (bad input), 404 (not found) or 502 (inference service failed).

A "URL" in any request is one of the URLs returned by this API (presigned S3 URL for a file or a
thumbnail). The server ignores the query string and resolves the object by its path, so a URL that
was returned an hour ago still identifies the file.

A **result** object, used by every search route:

```json
{
  "file_id": "9f2c...64 hex sha256",
  "type": "image",
  "url": "https://...presigned original...",
  "thumb_url": "https://...presigned thumbnail... or null for video",
  "tags": {"fox": 2, "cat": 1},
  "created_at": "2026-10-20T03:14:15+00:00"
}
```

## Upload

### POST /upload/init
Dedup check and presigned upload URL. The browser computes the SHA-256 of the file first.

```json
{"filename": "fox1.jpg", "content_type": "image/jpeg", "sha256": "<64 hex>", "size": 183422}
```
New file:
```json
{"duplicate": false, "file_id": "<sha256>", "upload_url": "https://...", "required_headers": {"Content-Type": "image/jpeg"}}
```
Already stored:
```json
{"duplicate": true, "file_id": "<sha256>", "status": "ready", "url": "https://..."}
```
Then the browser does `PUT upload_url` with the required headers and the file bytes. Processing
(thumbnail, tagging) starts automatically from the S3 event. Poll `/search/tags` or wait for an alert.

## Search

### POST /search/tags
All listed tags must be present with at least the given count (logical AND). A list or a single
string means a count of 1 for each. Optional `date` (`YYYY-MM-DD`, UTC) limits to that day.

```json
{"tags": {"feral pig": 1, "cane toad": 3}}
{"tags": ["cat"]}
```
Response: `{"results": [<result>, ...]}`

### POST /search/thumbnail
```json
{"thumbnail_url": "https://...thumbs/<sha>.jpg?X-Amz-..."}
```
Response: `{"url": "https://...presigned full-size...", "file_id": "<sha>"}`

### POST /search/by-file
Detect tags on the supplied image, then return stored files that contain all of those species.
The image is never written to S3 or DynamoDB. Images only, up to about 4 MB (HTTP API payload limit).

```json
{"image_base64": "<base64 bytes, no data: prefix>"}
```
Response: `{"detected_tags": {"fox": 1}, "results": [<result>, ...]}`

### POST /search/lost-pet
Species comes from `image_base64` (detected) and/or `tags`. Extra tags such as colour or breed are
matched against tags people added manually. Files must contain every species; ranking is by number
of extra tags matched, then newest. `days` (default 30, max 365) limits to recent sightings.

```json
{"image_base64": "<optional>", "tags": ["cat", "ginger"], "days": 14}
```
Response: `{"detected_tags": {"cat": 1}, "results": [<result>, ...]}`

## Manage

### POST /tags
```json
{"urls": ["https://...", "https://..."], "tags": ["fox", "juvenile"], "operation": 1}
```
`operation` is `1` to add and `0` to remove. `tags` may be a list or `{"fox": 2}` (count used when
adding, ignored when removing). Removing a tag a file does not have is ignored.
Response: `{"updated": ["<file_id>", ...], "not_found": ["<url>", ...]}`

### POST /files/delete
```json
{"urls": ["https://...", "https://..."]}
```
Removes the original, the thumbnail and the DynamoDB record.
Response: `{"deleted": ["<file_id>", ...], "not_found": ["<url>", ...]}`

## Notifications

### POST /notifications/subscribe
Email alerts when a file containing any of the tags is added or its tags are updated.
`email` is optional and defaults to the signed-in user's address. SNS emails a confirmation link first.

```json
{"tags": ["fox", "cane toad"], "email": "optional@example.com"}
```
Response: `{"status": "pending_confirmation", "email": "...", "tags": ["fox", "cane toad"]}`

## Chat

### POST /chat
```json
{"text": "Show me all photos of foxes from yesterday", "session_id": "optional"}
```
Response: `{"messages": ["Found 3 files ...\nhttps://..."], "intent": "FindSpecies", "session_id": "..."}`

## Inference service (GCP, internal)

`POST {InferenceUrl}/detect`. Auth is either `Authorization: Bearer <Cognito token>` (user-initiated
calls) or `X-Api-Key` (S3-triggered ingest, where no user token exists).

```json
{"media_type": "image", "url": "https://...presigned..."}
{"media_type": "video", "url": "https://...presigned..."}
{"media_type": "image", "image_base64": "..."}
```
Response:
```json
{
  "counts": {"fox": 2},
  "detections": [{"label": "fox", "confidence": 0.81, "bbox": [x1, y1, x2, y2], "frame": 0}],
  "model_version": "yolo-world-v2-s-1",
  "frames_analysed": 1
}
```
For video `counts` holds the maximum per species seen in any single sampled frame (one frame every
10 seconds), which avoids double counting the same animal across frames.
