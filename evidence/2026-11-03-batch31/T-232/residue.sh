#!/bin/zsh
# List live processes whose argv or environment mentions a fixture directory (ps -E shows the environment of our own processes).
# Usage: residue.sh /private/tmp/<fixture-prefix>
/bin/ps -axE -ww -o pid=,ppid=,command= | grep -F -- "$1" | grep -v -F -- 'residue.sh' | grep -v grep | cut -c1-200
