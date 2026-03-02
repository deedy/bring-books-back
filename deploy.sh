#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ──
PROJECT_ID="${GCP_PROJECT_ID:-grandoldbooks}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="bring-books-back"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
BUCKET="gs://grandoldbooks-assets"
IMG_DIR="web/public/data/images"
DATA_DIR="web/public/data"
MARKER=".last_gcs_sync"

echo "==> Deploying ${SERVICE_NAME} to Cloud Run"
echo "    Project: ${PROJECT_ID}"
echo "    Region:  ${REGION}"
echo ""

# Ensure gcloud is pointed at the right project
gcloud config set project "${PROJECT_ID}" --quiet

# ── Step 1: Convert any new PNGs to WebP (parallel) ──
echo "==> Converting new PNGs to WebP..."
TO_CONVERT=$(find "$IMG_DIR" -name "*.png" | while read -r png; do
  webp="${png%.png}.webp"
  [ ! -f "$webp" ] && echo "$png"
done || true)

if [ -n "$TO_CONVERT" ]; then
  converted=$(echo "$TO_CONVERT" | wc -l | tr -d ' ')
  echo "$TO_CONVERT" | xargs -P 8 -I{} sh -c 'cwebp -q 80 -quiet "$1" -o "${1%.png}.webp" && echo "  Converted: $(basename "${1%.png}.webp")"' _ {}
  echo "  ${converted} new images converted"
else
  echo "  0 new images converted"
fi

# ── Step 2: Ensure all JSON refs use .webp ──
echo "==> Ensuring JSON references use .webp..."
if grep -rq '\.png"' "$DATA_DIR"/*.json "$DATA_DIR"/books/*/meta.json "$DATA_DIR"/books/*/chapters.json 2>/dev/null; then
  find "$DATA_DIR" -name "*.json" -exec sed -i '' 's/\.png"/.webp"/g' {} +
  echo "  Updated JSON references"
else
  echo "  Already up to date"
fi

# ── Step 3 & 4: GCS sync and Cloud Build (parallel) ──
SYNC_PID=""
BUILD_PID=""

# Step 3: Sync images to GCS (skip if no changes)
if [ -f "$MARKER" ] && [ -z "$(find "$IMG_DIR" -newer "$MARKER" -name '*.webp' -print -quit)" ]; then
  echo "==> Skipping GCS sync (no image changes since last sync)"
else
  echo "==> Syncing images to GCS..."
  (gcloud storage rsync -r "$IMG_DIR" "${BUCKET}/data/images" \
    --cache-control='public, max-age=2592000' \
    --project="${PROJECT_ID}" \
    --delete-unmatched-destination-objects \
    --quiet && touch "$MARKER") &
  SYNC_PID=$!
fi

# Step 4: Build and push container
echo "==> Building container image..."
gcloud builds submit web/ \
  --tag "${IMAGE}" \
  --quiet &
BUILD_PID=$!

# Wait for both background jobs
if [ -n "$SYNC_PID" ]; then
  wait "$SYNC_PID" || { echo "ERROR: GCS sync failed"; exit 1; }
  echo "  GCS sync done"
fi
wait "$BUILD_PID" || { echo "ERROR: Cloud Build failed"; exit 1; }
echo "  Build done"

# ── Step 5: Deploy to Cloud Run ──
echo "==> Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --quiet

# Print the service URL
URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format "value(status.url)")

echo ""
echo "==> Deployed successfully!"
echo "    URL: ${URL}"
