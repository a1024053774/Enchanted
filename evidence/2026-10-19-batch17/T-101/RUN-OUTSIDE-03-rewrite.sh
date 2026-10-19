#!/bin/sh
set -eu
exec python3 -B "$(dirname "$0")/slim_history.py" rewrite "${1:?主控审查清单后传入 run id}"
