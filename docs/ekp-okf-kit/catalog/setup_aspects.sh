#!/usr/bin/env bash
# Register (or update) the EKP aspect types in one project/location.
# Run once per environment, and again after gen_aspects.py adds fields.
#   PROJECT=my-proj LOCATION=us-central1 ./catalog/setup_aspects.sh
# Same create-or-update pattern as Google's OKF demo setup.ts.
set -euo pipefail
: "${PROJECT:?set PROJECT}"; : "${LOCATION:?set LOCATION}"
cd "$(dirname "$0")/generated"

for f in ekp-*.json; do
  id="${f%.json}"
  if gcloud dataplex aspect-types describe "$id" --project "$PROJECT" --location "$LOCATION" >/dev/null 2>&1; then
    gcloud dataplex aspect-types update "$id" --project "$PROJECT" --location "$LOCATION" \
      --metadata-template-file-name="$f"
    echo "updated $id"
  else
    gcloud dataplex aspect-types create "$id" --project "$PROJECT" --location "$LOCATION" \
      --metadata-template-file-name="$f"
    echo "created $id"
  fi
done

# Every build pushes into its own entry group in the SAME location, so that
# LookupContext and entry links can span builds.
echo "Aspect types ready. Each build workspace needs catalog.yaml:"
echo "  scope: entryGroup.${PROJECT}.${LOCATION}.<build-entry-group>"
echo "  layout: okf"
echo "If you add a 'publishing:' block, list every ekp-* aspect in it, or kcmd drops them."
