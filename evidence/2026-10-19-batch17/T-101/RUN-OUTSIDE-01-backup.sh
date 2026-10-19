#!/bin/sh
set -eu
exec python3 -B "$(dirname "$0")/slim_history.py" backup "$@"
