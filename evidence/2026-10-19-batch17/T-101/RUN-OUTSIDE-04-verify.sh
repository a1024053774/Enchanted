#!/bin/sh
set -eu
exec python3 -B "$(dirname "$0")/slim_history.py" verify "${1:?候选审查并提交后传入 run id}"
