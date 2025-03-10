#!/usr/bin/env bash
cd "$(dirname "$0")"

# Download assets from the server
BOOTSTRAP_CSS="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
BOOTSTRAP_JS="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js"

STATIC_DIR="static"
echo "Downloading assets to $STATIC_DIR..."
mkdir -p "$STATIC_DIR/css"
mkdir -p "$STATIC_DIR/js"

curl -sL "$BOOTSTRAP_CSS" -o "$STATIC_DIR/css/bootstrap.min.css"
curl -sL "$BOOTSTRAP_JS" -o "$STATIC_DIR/js/bootstrap.bundle.min.js"