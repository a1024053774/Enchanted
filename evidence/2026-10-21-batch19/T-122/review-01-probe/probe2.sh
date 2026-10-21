#!/bin/zsh
set -u
R=/private/tmp/t122-rv/run2; rm -rf $R; mkdir -p $R/outside $R/sock $R/req
git init -q -b main $R/repo && git -C $R/repo commit -q --allow-empty -m init
git -C $R/repo worktree add -q -b work $R/wt
GITDIR=$(cd $R/repo/.git && pwd -P); WT=$(cd $R/wt && pwd -P); REQ=$(cd $R/req && pwd -P)
python3 -c "
import socket,os
p='$R/sock/s.sock'
s=socket.socket(socket.AF_UNIX);s.bind(p);s.listen(1);s.settimeout(150)
try:
  c,_=s.accept();open('$R/outside/socket-connected','w').write(c.recv(100).decode())
except Exception as e: open('$R/outside/socket-timeout','w').write(str(e))
" &
LP=$!
cat > $WT/checks.sh <<S
echo "== a"; git -C $GITDIR update-ref refs/heads/stolen HEAD; echo "rc=\$?"
echo "== b"; git -C $GITDIR update-ref refs/heads/main HEAD; echo "rc=\$?"
echo "== c"; printf '[core]\n\tfsmonitor = touch $R/outside/fsmonitor-ran\n' >> $GITDIR/config; echo "rc=\$?"
echo "== d"; printf '#!/bin/sh\ntouch $R/outside/hook-ran\n' > $GITDIR/hooks/post-merge; echo "rc=\$?"
echo "== e"; python3 -c "import socket;s=socket.socket(socket.AF_UNIX);s.connect('$R/sock/s.sock');s.send(b'hello');print('connected')"; echo "rc=\$?"
echo "== f"; mkdir -p .claude && echo '{}' > .claude/settings.local.json; echo "rc=\$?"
echo "== g"; echo t > \$TMPDIR/t122rv2.txt; echo "rc=\$? TMPDIR=\$TMPDIR"
echo "== h"; echo t > $GITDIR/worktrees/x-note; echo "rc=\$?"
S
SETTINGS=$(python3 -c "
import json;print(json.dumps({'permissions':{'allow':['Bash','Read','Glob','Grep','Edit(/$WT/**)','Edit(/$REQ/**)']},
 'sandbox':{'enabled':True,'autoAllowBashIfSandboxed':True,'allowUnsandboxedCommands':False,'filesystem':{'allowWrite':['$GITDIR','$REQ']}},
 'fastMode':False}))")
cd $WT
P="Run exactly one Bash command: sh ./checks.sh 2>&1   Then paste its full output verbatim and stop. Do not run anything else."
claude -p --session-id $(uuidgen | tr A-Z a-z) --model claude-haiku-5-5 --effort low --permission-mode dontAsk --setting-sources local --strict-mcp-config --settings "$SETTINGS" --output-format json "$P" > $R/result.json 2> $R/stderr.txt
echo "exit=$?"
kill $LP 2>/dev/null
echo "--- outside"; ls -la $R/outside
echo "--- refs"; git -C $R/repo for-each-ref
echo "--- config tail"; tail -3 $GITDIR/config; ls -la $GITDIR/hooks/post-merge 2>&1; ls $GITDIR/worktrees
ls -la $WT/.claude 2>&1
python3 -c "import json;d=json.load(open('$R/result.json'));print(d.get('result','')[:3000]);print('denials',json.dumps(d.get('permission_denials'))[:2000])"
