# Inference service (GCP Cloud Run)

FastAPI service that runs the species detector on images and on video frames (one frame every
10 seconds). API shape: [../../../docs/api-contract.md](../../../docs/api-contract.md#inference-service-gcp-internal).

## Deploy

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

gcloud run deploy ecoguard-inference --source . --region australia-southeast1 --memory 4Gi --cpu 2 --timeout 300 --min-instances 1 --allow-unauthenticated --set-env-vars COGNITO_REGION=<aws-region>,COGNITO_USER_POOL_ID=<UserPoolId>,COGNITO_CLIENT_ID=<UserPoolClientId>,INFERENCE_API_KEY=<long random string>
```

Run it from this folder. The command prints the service URL; use it as the `InferenceUrl` stack
parameter on AWS, and use the same random string as `InferenceApiKey`.

`--allow-unauthenticated` is intentional: the caller is a Lambda, not a Google identity, so
authorisation is done in `app/auth.py` (Cognito JWT or shared key). `--min-instances 1` keeps a
container warm so the first request does not exceed API Gateway's 30 s limit; set it back to 0
after the demo to stop paying for it.

## Run locally

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
pip install "git+https://github.com/ultralytics/CLIP.git"
set INFERENCE_API_KEY=dev-key
uvicorn app.main:app --reload --port 8080
```

```bash
curl -X POST http://localhost:8080/detect -H "X-Api-Key: dev-key" -H "Content-Type: application/json" -d "{\"media_type\":\"image\",\"image_base64\":\"<base64>\"}"
```

## Changing the model without code changes

`config/model_config.json` (or the file `MODEL_CONFIG` points to, including `gs://bucket/config.json`):

```json
{
  "model_version": "yolo-world-v2-s-1",
  "type": "yolo_world",
  "weights": "yolov8s-worldv2.pt",
  "classes": ["fox", "feral pig", "cane toad", "rabbit", "cat", "dog"],
  "label_map": {},
  "confidence": 0.35
}
```

- `type`: `yolo` (any Ultralytics weights, labels come from the model) or `yolo_world`
  (open-vocabulary, labels come from `classes`).
- `weights`: an Ultralytics model name, a local path, or `gs://bucket/path.pt`.
- `label_map`: rename or drop model labels, e.g. `{"bird": null, "domestic cat": "cat"}`.
- The service re-reads the config every `MODEL_REFRESH_SECONDS` (default 60) and swaps the model
  when `model_version` or `weights` changes.

**Check accuracy early.** See ADR 5 in [../../../docs/decisions.md](../../../docs/decisions.md): stock
COCO weights do not include fox, feral pig, rabbit or cane toad.
