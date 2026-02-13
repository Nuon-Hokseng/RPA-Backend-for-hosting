#!/usr/bin/env bash
# Render build script – installs Python deps + Playwright browser binaries
set -e

pip install --upgrade pip
pip install -r requirements.txt

# Install only the Chromium binary (no --with-deps; Render's Ubuntu has the system libs)
playwright install chromium