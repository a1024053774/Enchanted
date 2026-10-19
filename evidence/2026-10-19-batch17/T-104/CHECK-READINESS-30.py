"""重放实际延迟片段核对读回同步；不启动 daemon、PTY、Electron 或模型。

失败面：pwd/LOGIN 先到、完成标记只在命令回显里、标记被分块、环境真的
多出变量。执行测试文件的实际解析器和等待 lambda，原精确环境断言不变。
"""
import ast
import base64
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

path='workbench/tests/test_t104_shell_e2e.py'
base='45c127b5af03bfdc50802579bda50b88a98dc2c7'
old=subprocess.check_output(['git','show',base+':'+path],text=True)
new=Path(path).read_text(encoding='utf-8')
archive=Path('/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104/reviewer-02-replay-01/candidate')
run=json.loads((archive/'run.json').read_text(encoding='utf-8'))
entries=[json.loads(line) for line in (archive/'transport.jsonl').read_text(encoding='utf-8').splitlines()]
last=next(row for row in reversed(entries) if row['request']['input']['command']=='pane_output')
prefix=base64.b64decode(last['reply']['data_base64'])
launch=last['request']['input']['launch']
complete_trace=(archive/'state/traces'/launch/'pty.raw').read_bytes()
completion='independent-completion-'+uuid.uuid4().hex
cwd=Path(run['fixture'])/'项目 alpha space'
environment_assert="assert [line for line in lines if line.startswith('A2A_')] == ['A2A_PROJECT=t104-alpha']"
assert old.count(environment_assert)==new.count(environment_assert)==1

def observe(source,data):
    tree=ast.parse(source)
    reader=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='output_lines')
    wait=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='lines' for t in n.targets)
              and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='wait_for')
    context=dict(re=re,cwd=cwd,completion=completion,first=dict(record=dict(id=launch)),
                 request=lambda *args,**kwargs:dict(ok=True,data_base64=base64.b64encode(data).decode('ascii')))
    exec(compile(ast.Module(body=[reader],type_ignores=[]),path,'exec'),context)
    predicate=eval(compile(ast.Expression(body=wait.value.args[0]),path,'eval'),context)
    return bool(predicate()),context['output_lines'](context['first'])

old_ready,_=observe(old,prefix)
new_ready,_=observe(new,prefix)
assert old_ready and not new_ready,'真实延迟前缀必须拒绝旧同步方式并阻止新方式提前返回'
echo=("printf '\\n%s\\n' '"+completion+"'\r\n").encode()
assert not observe(new,echo)[0],'命令回显不能冒充完成标记'
assert not observe(new,complete_trace)[0],'未见完成标记不能结束读回'
assert not observe(new,complete_trace+b'\r\n'+completion[:-1].encode())[0],'分块中的不完整标记不能结束读回'
finished=complete_trace+b'\r\n'+completion.encode()+b'\r\n'
ready,lines=observe(new,finished)
assert ready
exec(compile(environment_assert,path,'exec'),dict(lines=lines))
extra=complete_trace+b'\r\nA2A_UNEXPECTED=independent-sentinel\r\n'+completion.encode()+b'\r\n'
ready,lines=observe(new,extra)
assert ready
try:
    exec(compile(environment_assert,path,'exec'),dict(lines=lines))
except AssertionError:
    rejected=True
else:
    rejected=False
assert rejected,'完整读回后，真实额外变量仍必须被原精确断言拒绝'
report=dict(status='PASS',scope='解析与等待的确定性重放；真实后台连续两次重跑尚未运行',base=base,
            checks=['旧谓词在738字节真实前缀提前满足','新谓词等待env之后的标记','命令回显不算完成',
                    '不完整标记不算完成','完整读回通过原精确断言','额外A2A变量仍被原断言拒绝'],
            candidate_diff=subprocess.check_output(['git','diff','--',path],text=True))
with Path(sys.argv[1]).open('x',encoding='utf-8') as output:
    json.dump(report,output,ensure_ascii=False,indent=2);output.write('\n')
print(json.dumps(report,ensure_ascii=False))
