#!/bin/sh
set -eu
exec python3 -B "$(dirname "$0")/slim_history.py" plan "${1:?传入 run id}"
