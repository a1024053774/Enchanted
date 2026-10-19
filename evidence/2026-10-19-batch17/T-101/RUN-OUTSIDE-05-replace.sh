#!/bin/sh
set -eu
exec python3 -B "$(dirname "$0")/install_publish.py" install "${1:?传入 run id}"
