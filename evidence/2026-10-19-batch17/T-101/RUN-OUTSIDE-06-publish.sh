#!/bin/sh
set -eu
exec python3 -B "$(dirname "$0")/install_publish.py" publish "${1:?传入 run id}"
