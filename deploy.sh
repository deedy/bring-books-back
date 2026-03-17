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

echo "==> [Step 1/7] Converting new PNGs to WebP..."
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

echo "==> [Step 2/7] Ensuring JSON references use .webp..."
if grep -rq '\.png"' "$DATA_DIR"/*.json "$DATA_DIR"/books/*/meta.json "$DATA_DIR"/books/*/annotations.json 2>/dev/null; then
  find "$DATA_DIR" -name "*.json" -exec sed -i '' 's/\.png"/.webp"/g' {} +
  echo "  Updated JSON references"
else
  echo "  Already up to date"
fi

echo "==> [Step 3/7] Rebuilding search index..."
npm --prefix web run search:index
echo "  Search index rebuilt"

SYNC_PID=""
if [ -f "$MARKER" ] && [ -z "$(find "$IMG_DIR" -newer "$MARKER" -name '*.webp' -print -quit)" ]; then
  echo "==> [Step 4/7] Skipping GCS sync (no image changes)"
else
  echo "==> [Step 4/7] Syncing images to GCS (background)..."
  (gcloud storage rsync -r "$IMG_DIR" "${BUCKET}/data/images" \
    --cache-control='public, max-age=2592000' \
    --project="${PROJECT_ID}" \
    --delete-unmatched-destination-objects \
    --quiet && touch "$MARKER") &
  SYNC_PID=$!
fi

AUDIO_SYNC_PID=""
AUDIO_DIRS=$(find data -maxdepth 2 -type d -name "audio" 2>/dev/null || true)
if [ -n "$AUDIO_DIRS" ]; then
  echo "==> [Step 5/7] Syncing audio files to GCS & copying manifests (background)..."
  (
    for audio_dir in $AUDIO_DIRS; do
      book_id=$(basename "$(dirname "$audio_dir")")
      # Sync .mp3 files to GCS
      gcloud storage rsync "$audio_dir" "${BUCKET}/data/audio/${book_id}" \
        --exclude='(?!.*/ch-[0-9]+-[0-9]+\.mp3$).*' \
        --cache-control='public, max-age=2592000' \
        --project="${PROJECT_ID}" \
        --quiet
      # Copy manifest.json to web public directory
      if [ -f "${audio_dir}/manifest.json" ]; then
        mkdir -p "web/public/data/books/${book_id}"
        cp "${audio_dir}/manifest.json" "web/public/data/books/${book_id}/audio_manifest.json"
        echo "  Copied manifest for ${book_id}"
      fi
    done
  ) &
  AUDIO_SYNC_PID=$!
else
  echo "==> [Step 5/7] Skipping audio sync (no audio directories)"
fi

echo "==> [Step 6/7] Packaging server image via Cloud Build..."
step_time
gcloud builds submit web/ \
  --tag "${IMAGE}" \
  --quiet &
BUILD_PID=$!

if [ -n "$SYNC_PID" ]; then
  wait "$SYNC_PID" || { echo "ERROR: GCS image sync failed"; exit 1; }
  echo "  GCS image sync done"
fi
if [ -n "$AUDIO_SYNC_PID" ]; then
  wait "$AUDIO_SYNC_PID" || { echo "ERROR: GCS audio sync failed"; exit 1; }
  echo "  GCS audio sync done"
fi
wait "$BUILD_PID" || { echo "ERROR: Cloud Build failed"; exit 1; }
echo "  Build done"
step_time

echo "==> [Step 7/7] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 20 \
  --quiet

URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format "value(status.url)")

TOTAL=$(( $(date +%s) - START_TIME ))
echo ""
echo "==> Deployed successfully in ${TOTAL}s!"
echo "    URL: ${URL}"
