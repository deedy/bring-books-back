#!/usr/bin/env bash
# Convert all PNG images to WebP and update JSON references.
# Keeps originals; creates .webp alongside each .png.
set -euo pipefail

IMG_DIR="web/public/data/images"
DATA_DIR="web/public/data"

echo "==> Converting PNGs to WebP..."
count=0
find "$IMG_DIR" -name "*.png" | while read -r png; do
  webp="${png%.png}.webp"
  if [ ! -f "$webp" ]; then
    cwebp -q 80 -quiet "$png" -o "$webp"
    count=$((count + 1))
    printf "  [%s] %s\n" "$count" "$(basename "$webp")"
  fi
done

echo "==> Updating JSON references (.png → .webp)..."
find "$DATA_DIR" -name "*.json" -exec sed -i '' 's/\.png"/.webp"/g' {} +

echo "==> Done! Now upload to GCS:"
echo "    gcloud storage cp -r $IMG_DIR gs://grandoldbooks-assets/data/images \\"
echo "      --cache-control='public, max-age=2592000' --project=grandoldbooks"
