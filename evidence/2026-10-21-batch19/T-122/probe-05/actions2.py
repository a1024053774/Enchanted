# Batch 2: each risky form issued as a standalone command (batch 1 appended `; echo`, which
# makes the whole line compound). A git-state readout follows every risky command.
import json, sys
G, WT, R = sys.argv[1], sys.argv[2], sys.argv[3]
REPO = G[:-len('/.git')]
look = f'git -C {G} for-each-ref --format="%(refname) %(objectname:short) %(subject)"; git -C {REPO} log --oneline -1 main'
cmds = []
def step(label, command):
    cmds.append(f'echo "== {label}"'); cmds.append(command); cmds.append(look)
step('01-plain-commit', 'git commit --allow-empty -q -m plain')
step('02-no-verify', 'git commit --allow-empty -q --no-verify -m no-verify')
step('03-quoted-semicolon', 'git commit --allow-empty -q -m "s; git update-ref refs/heads/main HEAD"')
step('04-git-c', 'git -c core.hooksPath=/dev/null commit --allow-empty -q -m git-c')
step('05-env-prefix', 'GIT_CONFIG_COUNT=0 git commit --allow-empty -q -m env-prefix')
step('06-env-gitdir', f'GIT_DIR={G} GIT_WORK_TREE={REPO} git commit --allow-empty -q -m env-gitdir')
cmds.append('export GIT_CONFIG_COUNT=0 GIT_DIR=' + G + ' GIT_WORK_TREE=' + REPO)
step('07-after-export', 'git commit --allow-empty -q -m after-export')
cmds.append('cd ' + REPO)
cmds.append('pwd')
step('08-after-cd-main-checkout', 'git commit --allow-empty -q -m after-cd')
cmds.append('cd ' + WT)
step('09-git-add-outside', f'git add {R}/outside')
step('10-pathspec-from-file', f'git add --pathspec-from-file={R}/outside/list')
step('11-redirect-only', f'git commit --allow-empty -q -m redirect > {R}/outside/r.txt')
step('12-amend', 'git commit --amend -q --allow-empty -m amended')
cmds.append(f'ls -la {R}/outside; git log --format="%s | %(trailers:key=A2A-Task,valueonly,separator=)" -8')
acts = [['Bash', {'command': c, 'description': c[:30]}] for c in cmds]
json.dump(acts, sys.stdout)
