#!/bin/zsh
# T-120 probes: can a CLI the user launches in an Enchanted terminal see a2a's instructions
# without writing ~/.claude, ~/.codex or the user's project? Real CLIs, real user login.
# Claude runs use the user's own settings (read only) and --no-session-persistence.
# Codex runs use an isolated CODEX_HOME holding only auth.json, deleted afterwards.
set -u
W=$(mktemp -d /private/tmp/t120-XXXX); P=$W/plugin/enchanted-a2a; SK=$P/skills/a2a-orchestration
mkdir -p $P/.claude-plugin $SK $W/cwd
print '{ "name": "enchanted-a2a", "version": "0.0.1", "description": "probe" }' > $P/.claude-plugin/plugin.json
print -- '---\nname: a2a-orchestration\ndescription: Use when asked to act as a controller in Enchanted.\n---\nThe secret probe word is ZEPHYR-T120.' > $SK/SKILL.md
Q='Do you have a skill named a2a-orchestration? If yes, load it and reply with only the secret probe word it contains. If not, reply NO-SKILL.'
clean=(-u CLAUDECODE -u CLAUDE_CODE_CHILD_SESSION -u CLAUDE_CODE_ENTRYPOINT -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_MESSAGING_SOCKET -u CLAUDE_CODE_MESSAGING_TOKEN -u CLAUDE_CODE_SESSION_ATTENDED -u CLAUDE_PID -u CLAUDE_EFFORT -u CLAUDE_CODE_EXECPATH -u CLAUDE_CODE_PLUGIN_DIRS -u CODEX_THREAD_ID -u CODEX_SANDBOX -u CODEX_SANDBOX_NETWORK_DISABLED)
cd $W/cwd
claude_run() { env $clean "$@" claude -p --no-session-persistence --model claude-haiku-5-5 "$Q" < /dev/null 2>&1 | tail -1; }
print "claude $(claude --version)"
print "C1 env CLAUDE_CODE_PLUGIN_DIRS, user settings on:  $(claude_run CLAUDE_CODE_PLUGIN_DIRS=$P)"
print "C2 env, user settings skipped (--setting-sources): $(env $clean CLAUDE_CODE_PLUGIN_DIRS=$P claude -p --no-session-persistence --setting-sources project,local --model claude-haiku-5-5 "$Q" < /dev/null 2>&1 | tail -1)"
print "C3 flag --plugin-dir, user settings on:          $(env $clean claude -p --no-session-persistence --plugin-dir $P --model claude-haiku-5-5 "$Q" < /dev/null 2>&1 | tail -1)"
H=$W/codex-home; mkdir $H; cp ~/.codex/auth.json $H/
codex_run() { env $clean CODEX_HOME=$H codex exec --skip-git-repo-check -c check_for_update_on_startup=false -m gpt-6.1-sol -c model_reasoning_effort=low "$@" < /dev/null 2>&1 | tail -1; }
print "codex $(codex --version)"
print "X1 -c skills.config path:       $(codex_run -c "skills.config=[{path=\"$SK/SKILL.md\",enabled=true}]" "$Q Do not run commands.")"
print "X2 -c developer_instructions:   $(codex_run -c 'developer_instructions="The secret probe word is ZEPHYR-T120."' 'If your instructions mention a secret probe word, reply with only that word; otherwise reply NONE. Do not run commands.')"
# Z: does a shim directory stay first after the user's real zsh startup files?
mkdir $W/bin $W/zdot; print '#!/bin/sh' > $W/bin/claude; cp $W/bin/claude $W/bin/codex; chmod +x $W/bin/*
print "Z1 PATH prepend only:  $(PATH=$W/bin:$PATH zsh -il -c 'whence claude' </dev/null 2>/dev/null | tail -1)"
for f in zshenv zprofile zlogin; do print -r -- "ZDOTDIR=\$HOME; [[ -f \$HOME/.$f ]] && source \$HOME/.$f; ZDOTDIR=$W/zdot" > $W/zdot/.$f; done
print -r -- "ZDOTDIR=\$HOME; [[ -f \$HOME/.zshrc ]] && source \$HOME/.zshrc; ZDOTDIR=$W/zdot; path=($W/bin \${path:#$W/bin})" > $W/zdot/.zshrc
print "Z2 ZDOTDIR bootstrap:  $(ZDOTDIR=$W/zdot zsh -il -c 'whence claude; print aliases=$(alias | wc -l)' </dev/null 2>/dev/null | tail -2 | tr '\n' ' ')"
rm -rf $W
