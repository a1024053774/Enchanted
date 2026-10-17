#!/bin/sh
set -eu
# Only the failed in-process socket test from this session. No vendor CLI.
pid=74270
expected='workbench/tests/test_t078_empty_declaration_entry.ts evidence/2026-10-11-batch13/T-078/main-concurrency-red-09a3'
command=$(/bin/ps -p "$pid" -o command=) || exit 0
case "$command" in
  *"$expected") kill -TERM "$pid" ;;
  *) echo 'BLOCKED: probe PID was reused; no signal sent' >&2; exit 1 ;;
esac
