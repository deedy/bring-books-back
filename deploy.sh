#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ──
PROJECT_ID="${GCP_PROJECT_ID:-grandoldbooks}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="bring-books-back"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "==> Deploying ${SERVICE_NAME} to Cloud Run"
echo "    Project: ${PROJECT_ID}"
echo "    Region:  ${REGION}"
echo ""

# Ensure gcloud is pointed at the right project
gcloud config set project "${PROJECT_ID}" --quiet

# Build and push the container image using Cloud Build
echo "==> Building container image..."
gcloud builds submit web/ \
  --tag "${IMAGE}" \
  --quiet

# Deploy to Cloud Run
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
