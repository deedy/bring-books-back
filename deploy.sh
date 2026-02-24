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

echo "==> Deploying ${SERVICE_NAME} to Cloud Run"
echo "    Project: ${PROJECT_ID}"
echo "    Region:  ${REGION}"
echo ""

# Ensure gcloud is pointed at the right project
gcloud config set project "${PROJECT_ID}" --quiet

# ── Step 1: Convert any new PNGs to WebP ──
echo "==> Converting new PNGs to WebP..."
converted=0
while IFS= read -r png; do
  webp="${png%.png}.webp"
  if [ ! -f "$webp" ]; then
    cwebp -q 80 -quiet "$png" -o "$webp"
    converted=$((converted + 1))
    echo "  Converted: $(basename "$webp")"
  fi
done < <(find "$IMG_DIR" -name "*.png")
echo "  ${converted} new images converted"

# ── Step 2: Ensure all JSON refs use .webp ──
echo "==> Ensuring JSON references use .webp..."
if grep -rq '\.png"' "$DATA_DIR"/*.json "$DATA_DIR"/books/*/meta.json "$DATA_DIR"/books/*/chapters.json 2>/dev/null; then
  find "$DATA_DIR" -name "*.json" -exec sed -i '' 's/\.png"/.webp"/g' {} +
  echo "  Updated JSON references"
else
  echo "  Already up to date"
fi

# ── Step 3: Sync images to GCS ──
echo "==> Syncing images to GCS..."
gcloud storage rsync -r "$IMG_DIR" "${BUCKET}/data/images" \
  --cache-control='public, max-age=2592000' \
  --project="${PROJECT_ID}" \
  --delete-unmatched-destination-objects \
  --quiet
echo "  Done"

# ── Step 4: Build and push container (images excluded via .dockerignore) ──
echo "==> Building container image..."
gcloud builds submit web/ \
  --tag "${IMAGE}" \
  --quiet

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
