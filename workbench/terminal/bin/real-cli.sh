# Sourced by the claude and codex shims: find the user's own CLI on PATH, skipping this directory.
a2a_real_cli() {
  shim_dir=$(cd "$(dirname "$0")" && pwd -P)
  old_ifs=$IFS; IFS=:
  set -f  # PATH entries are literal directories, never glob patterns.
  for dir in $PATH; do
    [ -n "$dir" ] || continue
    [ "$(cd "$dir" 2>/dev/null && pwd -P)" = "$shim_dir" ] && continue
    if [ -x "$dir/$1" ] && [ ! -d "$dir/$1" ]; then IFS=$old_ifs; set +f; printf '%s\n' "$dir/$1"; return 0; fi
  done
  IFS=$old_ifs; set +f
  printf '%s: command not found\n' "$1" >&2
  return 127
}
