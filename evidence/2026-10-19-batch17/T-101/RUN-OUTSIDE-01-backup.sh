#!/bin/sh
set -eu
exec python3 -B "$(dirname "$0")/slim_history.py" backup "${1:?传入全新 run id}"
