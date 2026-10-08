"""Retain an isolated wrong gate and run the identical 18-case native suite."""
import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

out=Path(__file__).resolve().parent
fork=out.parents[2].parent/'synara'
name,label=sys.argv[1:]
original=(fork/'packages/a2a-gates/src/core.ts').read_text(encoding='utf-8')
source=original
if name=='done-no-submit':
    needle='''        requireGate(["claimed", "submitted"].includes(task.state), "run_state_changed", task.state);'''
    mutation='''        // Intentional wrong implementation: idle plus a commit impersonates submit.
        if (!live.running && task.state === "claimed") {
          const attempt = this.current(task, run.attempt_id!);
          const commit = await this.git(args.task, attempt.workspace, ["rev-parse", "HEAD"]);
          if (commit !== attempt.base_commit) {
            task.candidate_commit = commit;
            task.state = "submitted";
            attempt.state = "submitted";
            this.save(task, "implicit_done_delivery", { attempt, commit });
          }
        }
'''+needle
    assert source.count(needle)==1
    source=source.replace(needle,mutation,1)
elif name=='ignore-expected-attempt':
    needle='attempt && (!expected || attempt.attempt_id === expected)'
    assert source.count(needle)==1
    source=source.replace(needle,'attempt',1)
    needle='if (args.attempt && !historicalAttempt)'
    assert source.count(needle)==1
    source=source.replace(needle,'if (false && args.attempt && !historicalAttempt)',1)
else:
    raise ValueError(name)
retained=out/'mutants'/label
retained.mkdir(parents=True)
(retained/'core.ts').write_text(source,encoding='utf-8')
shutil.copyfile(fork/'packages/a2a-gates/src/cli.ts',retained/'cli.ts')
(retained/'mutation.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),source.splitlines(True),fromfile='candidate/core.ts',tofile=name+'/core.ts')),encoding='utf-8')
live=Path(tempfile.mkdtemp(prefix='a2a-t037-mutant-'+name+'-',dir='/tmp'))
for path in retained.glob('*.ts'):shutil.copyfile(path,live/path.name)
(live/'node_modules').symlink_to(fork/'packages/a2a-gates/node_modules',target_is_directory=True)
env=dict(os.environ,COOP_SCRIPT=str(out/'native-entry.py'),A2A_MUTANT_CORE=str(live/'core.ts'),A2A_MUTANT_CLI=str(live/'cli.ts'))
(retained/'runtime.json').write_text(json.dumps(dict(runtime=str(live),candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip(),environment={k:env[k] for k in ('COOP_SCRIPT','A2A_MUTANT_CORE','A2A_MUTANT_CLI')}),indent=2)+'\n',encoding='utf-8')
sys.exit(subprocess.call([sys.executable,'-B',str(out/'run-acceptance.py'),label,str(out/'test_run_native_e2e.py')],env=env))
