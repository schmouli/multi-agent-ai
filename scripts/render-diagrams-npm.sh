#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGES_DIR="$ROOT_DIR/docs/images"

mkdir -p "$IMAGES_DIR"

npx --yes mmdc \
  -p "$ROOT_DIR/docs/diagrams/puppeteer-config.json" \
  -i "$ROOT_DIR/docs/diagrams/orchestrator_flow.mmd" \
  -o "$IMAGES_DIR/orchestrator-flow.png" \
  -b transparent -w 1600 -H 900

npx --yes mmdc \
  -p "$ROOT_DIR/docs/diagrams/puppeteer-config.json" \
  -i "$ROOT_DIR/docs/diagrams/orchestrator_sequence.mmd" \
  -o "$IMAGES_DIR/orchestrator-sequence.png" \
  -b transparent -w 1600 -H 900

echo "Done. Images written to $IMAGES_DIR"