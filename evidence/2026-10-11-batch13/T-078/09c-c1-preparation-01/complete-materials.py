"""只生成当前 09C 的命令与草稿；不启动角色、不调用 gate/Electron。"""
import json
from pathlib import Path
import shlex

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
SOURCE = BASE.parents[2]
READY = json.loads((BASE / '09c-stage-a-01/readiness.json').read_bytes())
ROOT = Path(READY['root'])
PLAN = ROOT / 'protocol-plan.json'
P1S = {r: BASE / ('09c-c1-b1-' + r + '-p1-01') for r in ['ideation', 'executor']}
DRIVER = SOURCE / 'workbench/tests/t078_09c_driver.py'


def write(path, text):
    assert not path.exists(), path
    path.write_text(text, encoding='utf-8')


def command(argv):
    return shlex.join([str(p) for p in argv]) + '\n'


def c(stage, mode, output, *extra):
    role = 'executor' if stage == 'C-E1' else 'ideation'
    folder = P1S[role] / 'phases' / stage
    return command(['python3', '-B', DRIVER, '--plan', PLAN, '--stage', stage, '--approval',
                    folder / 'approval.json', '--mode', mode, '--output', folder / output, *extra])


def main():
    assert READY['scene'] == '09C'
    for role, p1 in P1S.items():
        # 与 A16 相同的完整原屏/0 POST readiness 核对；由主控签模板后才执行。
        template = json.loads((p1 / 'readiness-template.json').read_bytes())
        template['approval_ref'] = None
        (p1 / 'readiness-template.json').write_text(json.dumps(template, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        original = (BASE / '09b-a16-b1-ideation-p1-01/READINESS-CONFIRM-COMMAND.txt').read_text(encoding='utf-8')
        start = original.index('python3 -B -')
        text = original[start:].replace(str(BASE / '09b-a16-b1-ideation-p1-01'), str(p1))
        text = text.replace('a16-ideation', 'c1-' + role).replace("== 'ideation-s13'", "== '" + role + "-s13'")
        text = text.replace("api = root / 'roles/ideation'", "api = root / 'roles/" + role + "'")
        first = "assert not (p1 / 'readiness.json').exists(), 'Readiness output exists; no overwrite'"
        text = text.replace(first, first + "\nconsent = json.loads((p1 / 'readiness-template.json').read_bytes())\nassert consent['launch'] == inp['launch'] and consent['session'] == inp['session']\nassert consent['confirmed_by'] == 'executor' and consent['readiness'] == 'confirmed' and consent['basis'] and consent['approval_ref']")
        text = text.replace("'approval_ref': '主控 #346 T-078 A-16 ideation 首启读回'", "'approval_ref': consent['approval_ref']")
        text = text.replace("'basis': '主控 #346 逐屏读回 s13：空提示符、manual mode on；本命令复核保存的原屏、0 POST 与无提交事件。'", "'basis': consent['basis']")
        text = text.replace("         'earlier_key_capture_exception': str(p1 / 'c1-" + role + "-s11-Enter/result.json'),\n", '')
        write(p1 / 'READINESS-CONFIRM-COMMAND.txt', '# 主控读完本角色完整 s13 后，填写 readiness-template 的 confirmed_by/readiness/basis/approval_ref，再执行；不 release。\n' + text)

    arm = []
    for role, p1 in P1S.items():
        for folder in sorted((p1 / 'phases').iterdir()):
            stage = folder.name
            write(folder / 'ARM-COMMAND.txt', c(stage, 'arm', 'armed-01'))
            arm.append(c(stage, 'arm', 'armed-01'))
            if stage != 'C-I1':
                write(folder / 'COLLECT-COMMAND.txt', c(stage, 'collect', 'collect-01'))
            if stage == 'C-E1':
                continue
            write(folder / 'OBSERVE-PERMISSION-COMMAND.txt', c(stage, 'observe', 'dispatch-01'))
            # 观察与读屏不发键。后续原屏必须逐字节相等，不接受前缀。
            screen_label = 'c1-ideation-' + stage + '-permission-screen-01'
            read = command(['python3', '-B', SOURCE / 'workbench/tests/run_t078_p1.py', '--materials', p1,
                            '--reuse-stage-a', '--launch-label', 'LAUNCH_LABEL', '--phase', 'screen',
                            '--label', screen_label, '--screen-id', 'ideation-' + stage + '-permission'])
            read += command(['cmp', p1 / screen_label / 'screen.bin', folder / 'dispatch-01/permission-screen.bin'])
            write(folder / 'PERMISSION-SCREEN-CMP-COMMAND.txt', read)
            if stage in ['C-I1', 'C-I2']:
                write(folder / 'PREPARE-PERMISSION-COMMAND.txt', command(['python3', '-B', BASE / 'prepare-a14.py',
                    '--mode', 'permission', '--p1', p1, '--result', folder / 'dispatch-01/result.json',
                    '--output', folder / 'permission-approval-01.json']))
                for check in [True, False]:
                    name = 'PERMISSION-CHECK-COMMAND.txt' if check else 'PERMISSION-ENTER-COMMAND.txt'
                    argv = ['python3', '-B', SOURCE / 'workbench/tests/t078_09b_i1_permission.py',
                        '--materials', p1, '--p1', p1, '--stage', stage, '--stage-a', BASE / '09c-stage-a-01',
                        '--dispatch-result', folder / 'dispatch-01/result.json', '--process-manifest',
                        'LAUNCH_MANIFEST', '--approval', folder / 'permission-approval-01.json',
                        '--output', folder / ('permission-check-01' if check else 'execute-02')]
                    if check: argv.append('--check-only')
                    write(folder / name, command(argv))
    # bind-launch 只会替换 COMMANDS.txt；其他独立文件由下面的文件专用绑定步骤同步。
    write(OUT / 'BIND-COMMAND-REFERENCES.txt', command(['python3', '-B', OUT / 'bind-command-references.py']))
    write(OUT / 'ARM-ALL-COMMANDS.txt', '# 两角色首启/owner/build 完成后，由主控逐份签 phase 批准；五条只 arm，不发送。任一失败即停。\n' + '\n'.join(arm))
    i1 = P1S['ideation'] / 'phases/C-I1'
    write(i1 / 'INITIALIZE-COMMAND.txt', c('C-I1', 'initialize', 'initialized-01'))
    write(i1 / 'START-COMMAND.txt', c('C-I1', 'start', 'start-01'))
    write(OUT / 'CONTINUED-DEMAND-COMMAND.txt', command(['python3', '-B', BASE / 'prepare-rev2-owner.py',
        '--mode', 'demand', '--result', i1 / 'execute-02/settlement.json', '--approval', i1 / 'approval.json',
        '--output', ROOT / 'continued-demand.json']))
    i3 = P1S['ideation'] / 'phases/C-I3'
    slot = 't078-c1-CI3-' + json.loads((P1S['ideation'] / 'input.json').read_bytes())['launch'] + '-execute02'
    build = Path('/Volumes/WD-Elements/a2a-workbench') / slot / 'dist'
    assert not build.parent.exists()
    write(i3 / 'CONDITIONAL-ENTER-COMMAND.txt', c('C-I3', 'permission', 'execute-02', '--build', build))
    review = i3 / 'execute-02-review'
    # 主控先核对实际 template/screen，在不同名字的 draft 上签字；发布时逐字段核对后一次性创建 approved.json。
    publish = f'''# 与 CONDITIONAL-ENTER 进程并行执行；先只把真实模板复制成签字草稿。
python3 -B - <<'PY'
import json
from pathlib import Path
review = Path({str(review)!r})
source = review / 'template.json'
with (review / 'approval-draft.json').open('x', encoding='utf-8') as stream:
    stream.write(source.read_text(encoding='utf-8'))
print('主控核对 template/screen/命令/stop/目标后，只填写 approval-draft.json 的 approved_by=executor 和 approval_ref；未签不得运行下一条。')
PY

# 主控签草稿后原子发布；driver 不读取草稿。任何非签字字段变化均拒绝；不覆盖 approved。
python3 -B - <<'PY'
import json, os
from pathlib import Path
review = Path({str(review)!r})
template = json.loads((review / 'template.json').read_bytes())
signed = json.loads((review / 'approval-draft.json').read_bytes())
assert signed['approved_by'] == 'executor' and signed['approval_ref']
assert {{k:v for k,v in signed.items() if k not in ('approved_by','approval_ref')}} == {{k:v for k,v in template.items() if k not in ('approved_by','approval_ref')}}
pending = review / 'approved-publication.json'
with pending.open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(signed, ensure_ascii=False, indent=2)+'\\n')
    stream.flush(); os.fsync(stream.fileno())
os.link(pending, review / 'approved.json')
PY
'''
    write(i3 / 'REVIEW-AND-PUBLISH-COMMANDS.txt', publish)
    write(OUT / 'GENERATION.json', json.dumps({'status': 'PASS', 'scope': '只生成文件；未调用场景/读屏/按键/HTTP/owner/build',
        'root': str(ROOT), 'source_revision': READY['source_revision'], 'scene_process_starts': 0,
        'signatures_written': False}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
