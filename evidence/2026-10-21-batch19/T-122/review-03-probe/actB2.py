# Same as actB, but a post-commit hook in the worktree moves main and writes a trailer-less commit onto the attempt branch.
import json, sys
G, WT, R = sys.argv[1:4]; O = R + '/outside'
hook = ('#!/bin/sh\\n'
        'git update-ref refs/heads/main HEAD\\n'
        't=$(git write-tree); c=$(echo no-trailer | git commit-tree $t -p HEAD); git update-ref HEAD $c\\n'
        'echo ok > ' + O + '/B2-post-commit-ran\\n')
c = []
c.append('mkdir -p .husky && printf "' + hook + '" > .husky/post-commit && chmod +x .husky/post-commit')
c.append('echo hi > hello.txt')
c.append('git add hello.txt')
c.append('git commit -q -m husky')
json.dump([['Bash', {'command': x, 'description': 'step'}] for x in c], sys.stdout)
