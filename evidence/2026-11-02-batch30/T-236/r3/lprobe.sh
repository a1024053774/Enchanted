#!/bin/sh
for f in /Users/luckye/Documents/Code/VibeGame/README.md /Users/luckye/Documents/Code/a2a/AGENTS.md /private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/3f5514a4-d0d1-44ce-8f38-5ed7424cdfa6/scratchpad/ctl.txt; do
  s=$(date +%s); if /usr/bin/perl -e 'alarm 4; open(F, "<", $ARGV[0]) or die "$!\n"; exit 0' "$f" 2>>/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/3f5514a4-d0d1-44ce-8f38-5ed7424cdfa6/scratchpad/lprobe.err; then r=OK; else r=FAIL; fi; echo "$r $(($(date +%s)-s))s $f" >> /private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/3f5514a4-d0d1-44ce-8f38-5ed7424cdfa6/scratchpad/lprobe.out
done
echo END >> /private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/3f5514a4-d0d1-44ce-8f38-5ed7424cdfa6/scratchpad/lprobe.out
