#!/bin/bash
# Underrail Save Editor - Launch Script (Unix/Linux/macOS)
#
# Usage:
#   ./run.sh           - Start the interactive console
#   ./run.sh view      - View save file data
#   ./run.sh edit      - Edit save file
#
# The script will look for Python 3 in the following order:
#   1. python3
#   2. python

set -e

# Find the script's directory (where 'use' folder should be)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Check Python version
PY_VERSION=$($PYTHON -c "import sys; print(sys.version_info.major)")
if [ "$PY_VERSION" -lt 3 ]; then
    echo "Error: Python 3 is required, but Python $PY_VERSION was found."
    exit 1
fi

# Run the main screen module
cd "$SCRIPT_DIR"
exec $PYTHON -m use.main_screen "$@"
