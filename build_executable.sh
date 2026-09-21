#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt
pip install "pyinstaller>=6.0"

mkdir -p executable/V2.0
pyinstaller --noconfirm --clean \
    --distpath executable/V2.0 \
    --workpath build \
    uart_terminal.spec

echo "Built $(pwd)/executable/V2.0/uart_terminal_1_1"
