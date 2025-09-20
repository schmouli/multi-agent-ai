#!/usr/bin/env bash
set -euo pipefail

# Render Mermaid diagrams to PNG using mermaid-cli via Docker
# Requires Docker. Outputs to docs/images/

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIAGRAMS_DIR="$ROOT_DIR/docs/diagrams"
IMAGES_DIR="$ROOT_DIR/docs/images"

mkdir -p "$IMAGES_DIR"

# Use a pinned mermaid-cli image for reproducibility
IMAGE="minlag/mermaid-cli:10.9.0"

render() {
  local input="$1"
  local output="$2"
  echo "Rendering $input -> $output"
  docker run --rm \
    -v "$DIAGRAMS_DIR":/data \
    -v "$IMAGES_DIR":/out \
    "$IMAGE" \
    -i "/data/$(basename "$input")" \
    -o "/out/$(basename "$output")" \
    -b transparent \
    -w 1600 -H 900
}

render orchestrator_flow.mmd orchestrator-flow.png
render orchestrator_sequence.mmd orchestrator-sequence.png

echo "Done. Images written to $IMAGES_DIR"
