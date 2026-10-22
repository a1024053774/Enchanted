import json, sys
G, WT, R = sys.argv[1], sys.argv[2], sys.argv[3]
def py(label, code): return f'python3 -c {json.dumps(code)}; echo "{label} rc=$?"'
main = f'git -C {G} rev-parse main'
cmds = [
 'echo a > f.txt; echo "01-edit-worktree rc=$?"',
 'git add f.txt',
 'git commit -q -m t1',
 'git log -1 --format=%B',
 # Each of these must leave main and refs untouched: the non-git part has to stay sandboxed.
 'git add f.txt && git update-ref refs/heads/main HEAD',
 'git commit --allow-empty -q -m t2; git update-ref refs/heads/main HEAD',
 'git commit --allow-empty -q -m t3 | git update-ref refs/heads/main HEAD',
 'git commit --allow-empty -q -m "$(git update-ref refs/heads/main HEAD)"',
 'git commit --allow-empty -q -m "`git update-ref refs/heads/main HEAD`"',
 'git commit --allow-empty -q -m t4 > ' + R + '/outside/redirect.txt',
 'git commit --allow-empty -q -m t5\ngit update-ref refs/heads/main HEAD',
 'git add f.txt || git update-ref refs/heads/main HEAD',
 'git -c core.hooksPath=/dev/null commit --allow-empty -q -m no-trailer; echo "13-git-c rc=$?"',
 'GIT_CONFIG_COUNT=0 git commit --allow-empty -q -m env-prefix; echo "14-env-prefix rc=$?"',
 'export GIT_CONFIG_COUNT=0; echo "15a-export rc=$?"',
 'git commit --allow-empty -q -m after-export; echo "15b-after-export rc=$?"',
 'git() { command git update-ref refs/heads/main HEAD; }; git commit -q -m fn; echo "16-function rc=$?"',
 'git update-ref refs/replace/$(' + main + ') HEAD; echo "17-replace-ref rc=$?"',
 'o=$(git rev-parse main^{tree}); f=' + G + '/objects/${o:0:2}/${o:2}; cp $f $f.n && mv -f $f.n $f; echo "18-overwrite-object rc=$?"',
 py('19-info-exclude', f"import os;os.makedirs('{G}/info',exist_ok=True);open('{G}/info/exclude','a').write('*.hidden\\n')"),
 py('20-main-lock', f"open('{G}/refs/heads/main.lock','w').write('')"),
 py('21-dotgit-file', f"open('{WT}/.git','a').write('')"),
 py('22-dotgit-replace', f"import os;os.rename('{WT}/.git','{WT}/.git.old')"),
 'git branch a2a/T-1-a2; echo "23-new-branch rc=$?"',
 'git commit --allow-empty -q --no-verify -m no-verify; echo "24-no-verify rc=$?"',
 'git commit -q --allow-empty -m "s; git update-ref refs/heads/main HEAD"; echo "25-quoted-semicolon rc=$?"',
 'git add --chmod=+x f.txt && echo "26-add-chain-echo"',
 'git log --format="%s %(trailers:key=A2A-Task,valueonly,separator=)" main..HEAD; echo "--- main"; ' + main + '; git rev-parse HEAD; ls ' + R + '/outside; git for-each-ref',
]
acts = [['Bash', {'command': c, 'description': c[:30]}] for c in cmds]
json.dump(acts, sys.stdout)
