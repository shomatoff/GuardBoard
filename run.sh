#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if (( EUID == 0 )); then
  echo 'GuardBoard must run as a normal user, never root.' >&2
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  echo 'Missing .venv. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt' >&2
  exit 1
fi
exec .venv/bin/python -m backend.main "$@"
