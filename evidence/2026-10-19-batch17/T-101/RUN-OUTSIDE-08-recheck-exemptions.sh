#!/bin/sh
set -eu
exec python3 -B "$(dirname "$0")/recheck_credential_exemptions.py" "$@"
