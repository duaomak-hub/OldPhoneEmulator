#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -c "import flask" 2>/dev/null || pip3 install flask pillow --break-system-packages
if [ $# -eq 0 ]; then
    python3 "$DIR/OldPhoneEmulator.pyz" --web --port 5000
else
    python3 "$DIR/OldPhoneEmulator.pyz" "$@"
fi
