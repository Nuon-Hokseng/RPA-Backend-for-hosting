#!/usr/bin/env bash
# Render build script – installs Python deps + Playwright browser binaries
set -e

pip install --upgrade pip
pip install -r requirements.txt

# Install only Chromium (smallest footprint for Render's free tier)
playwright install --with-deps chromium