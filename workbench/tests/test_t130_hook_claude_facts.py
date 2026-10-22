# -*- coding: utf-8 -*-
"""T-130：提交钩子从 Claude 会话记录读本回合实际的模型与强度。只测钩子的读取函数，夹具是构造的会话记录。

失败方式（先列再写）：
1. 写请求值或 unknown，而不是记录里实际回复的模型与强度（端到端另测）。
2. 最后一行写了一半，被当成事实或让钩子报错。
3. Claude Code 自己写的 `<synthetic>` 回复被当成实际模型。
4. 读了同目录下别的会话的记录。
5. 同一会话 id 有两份记录（不唯一）时任取一份。
6. 记录里的会话 id 与启动时的不符，仍照写。
7. 只认一种强度字段：旧版只有 `effort`、有的只有 `perTurnEffort`；两者不一致时任取一个；都没有时报错而不是 unknown。
8. 记录还不存在时报错，而不是 unknown。
9. 忽略 CLAUDE_CONFIG_DIR，总读 $HOME/.claude。
用法：python3 tests/test_t130_hook_claude_facts.py OUTPUT.json [HOOK_PY]
"""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1])
hook_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'hooks/hook.py'
SESSION, OTHER = '11111111-1111-4111-8111-111111111111', '22222222-2222-4222-8222-222222222222'
report = dict(status='INCOMPLETE', hook=str(hook_path), checks=[])


def assistant(model, session=SESSION, **effort):
    return dict(type='assistant', sessionId=session, message=dict(model=model, role='assistant', content=[]), **effort)


def lines(*entries, tail=''):
    return ''.join(json.dumps(entry) + '\n' for entry in entries) + tail


def facts(files, env_extra=None, config_in_home=False):
    root = Path(tempfile.mkdtemp(prefix='t130-'))
    config = root / ('home/.claude' if config_in_home else 'config')
    for relative, text in files.items():
        path = config / 'projects' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    env = dict(A2A_NATIVE_SESSION=SESSION, HOME=str(root / 'home'))
    if not config_in_home:
        env['CLAUDE_CONFIG_DIR'] = str(config)
    env.update(env_extra or {})
    return hook.latest_turn_facts(env)


def raises(run):
    try:
        run()
    except ValueError:
        return True
    return False


def check(name, condition, detail=None):
    assert condition, f'{name}: {detail}'
    report['checks'].append(name)


try:
    spec = importlib.util.spec_from_file_location('hook_under_test', hook_path)
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    project = '-private-tmp-wt'
    turn = lines(dict(type='user', sessionId=SESSION, promptId='p1'),
                 assistant('claude-sonnet-5-5', effort='medium', perTurnEffort='medium'))
    value = facts({f'{project}/{SESSION}.jsonl': turn})
    check('observed_model_and_effort', value == ('claude-sonnet-5-5', 'medium'), value)
    value = facts({f'{project}/{SESSION}.jsonl': turn + '{"type": "assistant", "sessionId": "' + SESSION + '", "message": {"model": "half'})
    check('half_written_line_skipped', value == ('claude-sonnet-5-5', 'medium'), value)
    value = facts({f'{project}/{SESSION}.jsonl': turn + lines(assistant('<synthetic>'))})
    check('synthetic_reply_skipped', value == ('claude-sonnet-5-5', 'medium'), value)
    value = facts({f'{project}/{SESSION}.jsonl': turn, f'{project}/{OTHER}.jsonl': lines(assistant('claude-opus-5-5', OTHER, effort='max'))})
    check('other_session_ignored', value == ('claude-sonnet-5-5', 'medium'), value)
    check('duplicate_transcript_refused', raises(lambda: facts({f'{project}/{SESSION}.jsonl': turn, f'-elsewhere/{SESSION}.jsonl': turn})))
    check('foreign_session_entry_refused', raises(lambda: facts({f'{project}/{SESSION}.jsonl': lines(assistant('claude-sonnet-5-5', OTHER, effort='low'))})))
    value = facts({f'{project}/{SESSION}.jsonl': lines(assistant('claude-haiku-5-5', effort='low'))})
    check('effort_field_alone', value == ('claude-haiku-5-5', 'low'), value)
    value = facts({f'{project}/{SESSION}.jsonl': lines(assistant('claude-haiku-5-5', perTurnEffort='high'))})
    check('per_turn_effort_field_alone', value == ('claude-haiku-5-5', 'high'), value)
    check('disagreeing_effort_refused', raises(lambda: facts({f'{project}/{SESSION}.jsonl': lines(assistant('claude-haiku-5-5', effort='low', perTurnEffort='high'))})))
    value = facts({f'{project}/{SESSION}.jsonl': lines(assistant('claude-haiku-5-5'))})
    check('no_effort_field_is_unknown', value == ('claude-haiku-5-5', 'unknown'), value)
    value = facts({})
    check('missing_transcript_is_unknown', value == ('unknown', 'unknown'), value)
    value = facts({f'{project}/{SESSION}.jsonl': turn}, config_in_home=True)
    check('home_claude_used_without_config_dir', value == ('claude-sonnet-5-5', 'medium'), value)
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = f'{type(error).__name__}: {error}'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
sys.exit(0 if report['status'] == 'PASS' else 1)
