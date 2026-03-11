#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-grandoldbooks}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="bring-books-back"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
BUCKET="gs://grandoldbooks-assets"
IMG_DIR="web/public/data/images"
DATA_DIR="web/public/data"
MARKER=".last_gcs_sync"

START_TIME=$(date +%s)
step_time() { echo "    ⏱ $(( $(date +%s) - START_TIME ))s elapsed"; }

echo "==> Deploying ${SERVICE_NAME} to Cloud Run"
echo "    Project: ${PROJECT_ID}"
echo "    Region:  ${REGION}"
echo ""

gcloud config set project "${PROJECT_ID}" --quiet

echo "==> [Step 1/6] Converting new PNGs to WebP..."
TO_CONVERT=$(find "$IMG_DIR" -name "*.png" | while read -r png; do
  webp="${png%.png}.webp"
  [ ! -f "$webp" ] && echo "$png"
done || true)

if [ -n "$TO_CONVERT" ]; then
  converted=$(echo "$TO_CONVERT" | wc -l | tr -d ' ')
  echo "$TO_CONVERT" | xargs -P 8 -I{} sh -c 'cwebp -q 80 -quiet "$1" -o "${1%.png}.webp" && echo "  Converted: $(basename "${1%.png}.webp")"' _ {}
  echo "  ${converted} new images converted"
else
  echo "  No new images"
fi

echo "==> [Step 2/6] Ensuring JSON references use .webp..."
if grep -rq '\.png"' "$DATA_DIR"/*.json "$DATA_DIR"/books/*/meta.json "$DATA_DIR"/books/*/annotations.json 2>/dev/null; then
  find "$DATA_DIR" -name "*.json" -exec sed -i '' 's/\.png"/.webp"/g' {} +
  echo "  Updated JSON references"
else
  echo "  Already up to date"
fi

echo "==> [Step 3/6] Rebuilding search index..."
npm --prefix web run search:index
echo "  Search index rebuilt"

SYNC_PID=""
if [ -f "$MARKER" ] && [ -z "$(find "$IMG_DIR" -newer "$MARKER" -name '*.webp' -print -quit)" ]; then
  echo "==> [Step 4/6] Skipping GCS sync (no image changes)"
else
  echo "==> [Step 4/6] Syncing images to GCS (background)..."
  (gcloud storage rsync -r "$IMG_DIR" "${BUCKET}/data/images" \
    --cache-control='public, max-age=2592000' \
    --project="${PROJECT_ID}" \
    --delete-unmatched-destination-objects \
    --quiet && touch "$MARKER") &
  SYNC_PID=$!
fi

echo "==> [Step 5/6] Packaging server image via Cloud Build..."
step_time
gcloud builds submit web/ \
  --tag "${IMAGE}" \
  --quiet &
BUILD_PID=$!

if [ -n "$SYNC_PID" ]; then
  wait "$SYNC_PID" || { echo "ERROR: GCS sync failed"; exit 1; }
  echo "  GCS sync done"
fi
wait "$BUILD_PID" || { echo "ERROR: Cloud Build failed"; exit 1; }
echo "  Build done"
step_time

echo "==> [Step 6/6] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --quiet

URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format "value(status.url)")

TOTAL=$(( $(date +%s) - START_TIME ))
echo ""
echo "==> Deployed successfully in ${TOTAL}s!"
echo "    URL: ${URL}"
