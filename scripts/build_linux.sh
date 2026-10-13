#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -x .venv/bin/pyinstaller ]]; then
  echo 'Build environment missing. Run: .venv/bin/pip install -r requirements-build.txt' >&2
  exit 1
fi

.venv/bin/pyinstaller --noconfirm --clean --onedir --name GuardBoard \
  --add-data 'frontend:frontend' --collect-submodules uvicorn backend/main.py
cp README.md LICENSE dist/GuardBoard/
mkdir -p dist/packages
tar -C dist -czf dist/packages/GuardBoard-Linux-x64.tar.gz GuardBoard
(cd dist/packages && sha256sum GuardBoard-Linux-x64.tar.gz > SHA256SUMS)
