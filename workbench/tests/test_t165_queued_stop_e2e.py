"""T-165：真实 Electron / daemon / PTY / Claude CLI 的确定 Stop 顺序探针。

失败方式（先列再写）：
1. 排队输入的新 Stop 先到，后登记转录时丢失完成事实，worker 留在 busy。
2. 时序未命中、原 submit 被拒或启动失败，却被算成预期红态。
3. 夹具直接修改 pane/数据库或伪造原生 turn，掩盖真实身份检查。
4. 覆盖旧摘要或把脚本化 Messages 冒称供应商模型回合。

期望来自 T-165：先到的 Stop 在原生转录核验后仍须完成同一轮。
复用 T-157 全部断言，不改其期望。只在临时源码副本的 Claude scan
入口加转录可见性屏障：queued UPS 后不读取转录，真实新 Stop 的 signal
请求返回、原生排队记录落盘后放开，经真实 pane_process_info 入口采集，
再用只读 pane_status 观察。没有写 pane 或数据库。
这证明 Stop 早于转录登记，不声称控制了 CLI 的物理磁盘写入时点。
--revision 选择产品源码；--mutant drop-early-stop 在新增缓存点丢弃 Stop。
"""
import argparse
import json
from pathlib import Path
import sys
import time

import test_t157_stop_input_e2e as original
from scripted_claude import Fixture


SCAN_POINT = '      if (!pane.claudeQueuedPrompts?.length) return;'
SCAN_BARRIER = SCAN_POINT + "\n      if (!existsSync(join(this.root, 't165-transcript-visible'))) return;"


def find_early_stop(trace):
    """Correlate global request events with the queued hook's actual launch.

    Request lifecycle events have no task/launch columns; the signal input has
    the launch, and its response is correlated by request id.
    """
    queued = next((e for e in trace if e['type'] == 'claude_prompt_queued'), None)
    if not queued:
        return None
    launch = queued['launch']
    requests = [e for e in trace if e['type'] == 'request_received' and
                e['data']['input'].get('command') == 'signal' and
                e['data']['input'].get('launch') == launch and e['seq'] > queued['seq']]
    for request in requests:
        value = json.loads(request['data']['input']['raw_stdin'])
        if value.get('hook_event_name') != 'Stop' or value.get('prompt_id') == queued['data']['prompt_id']:
            continue
        result = next((e for e in trace if e['type'] == 'request_result' and
                       e['data'].get('command') == 'signal' and e['data'].get('id') == request['data']['id']), None)
        if not result:
            continue
        assert result['data'].get('ok') is True, '新 Stop 请求失败，不是产品完成红态'
        assert not any(e['launch'] == launch and e['type'] == 'turn_start_signal' and
                       e['data'].get('prompt_id') == value['prompt_id'] for e in trace), '时序屏障未成立：新 turn 已登记'
        return dict(stop=value, launch=launch, request_id=request['data']['id'], request_seq=request['seq'],
                    result_seq=result['seq'], queued_seq=queued['seq'])
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--mutant', choices=['drop-early-stop'])
    args, rest = parser.parse_known_args()
    assert not args.summary.exists(), '保留既有摘要'
    inner = args.summary.with_name(args.summary.stem + '-t157.json')
    ordering = {}

    class OrderedFixture(Fixture):
        def __init__(self, *values, **options):
            patches = list(options.pop('patches', ()))
            patches.append(('src/panes.ts', SCAN_POINT, SCAN_BARRIER))
            if args.mutant:
                patches.append(('src/panes.ts', 'pane.claudeEarlyStops.push({ raw, received_at, transfer });',
                                '/* T-165 mutant: discard the authenticated early Stop. */'))
            super().__init__(*values, patches=patches, **options)

        def wait(self, label, predicate, timeout=90):
            if label != 'worker 及门禁反馈回到空闲':
                return super().wait(label, predicate, timeout)

            def early_stop_returned():
                # Task-filtered events omit request_received/request_result.
                trace = self.request('orchestration_events')['events']
                found = find_early_stop(trace)
                if not found:
                    return False
                ordering.update(found)
                ordering['before_release'] = [e for e in trace if e['seq'] >= found['queued_seq'] and
                    (e['launch'] == found['launch'] or e['data'].get('id') == found['request_id'])]
                return True

            super().wait('真实新 Stop 已返回，转录尚未登记', early_stop_returned, 30)

            def native_record_written():
                # Complete native JSONL lines only; the CLI still owns this file.
                lines = Path(ordering['stop']['transcript_path']).read_text(encoding='utf-8').split('\n')[:-1]
                return any(entry.get('type') == 'user' and entry.get('promptId') == ordering['stop']['prompt_id']
                           and entry.get('promptSource') == 'queued'
                           for entry in (json.loads(line) for line in lines if line))

            super().wait('真实 CLI 已写出被屏障遮住的排队转录', native_record_written, 30)
            (self.state / 't165-transcript-visible').write_text('visible\n', encoding='utf-8')
            thread = next(row['thread'] for row in self.request('sidebar_snapshot')['agents']
                          if row['id'] == ordering['launch'])
            observed = self.request('pane_process_info', thread=thread)
            assert observed.get('ok') and observed.get('leader') and not observed.get('failed'), observed
            ordering['process_observation'] = observed
            # Baseline failure must reach the unchanged T-157 assertions, with
            # complete diagnostics, rather than exit only through a wait timeout.
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                value = predicate()
                if value:
                    return value
                assert not self.api.error, self.api.error
                time.sleep(.2)
            ordering['idle_timeout'] = True
            return False

    original.Fixture = OrderedFixture
    sys.argv = [sys.argv[0], '--summary', str(inner), *rest]
    original.main()
    report = json.loads(inner.read_text(encoding='utf-8'))
    trace = report['observed'].get('final_timeline', [])
    stop_id = ordering.get('stop', {}).get('prompt_id')
    starts = [e for e in trace if e['type'] == 'turn_start_signal' and
              e['data'].get('prompt_id') == stop_id and e['data'].get('origin') == 'native-transcript']
    ordered = bool(stop_id and starts and ordering['result_seq'] < starts[0]['seq'])
    report['checks'].append(dict(name='real_stop_before_native_turn_registration', passed=ordered))
    pane = report['observed'].get('final_pane', {})
    report['red_reproduced'] = bool(ordered and not report['errors'] and pane.get('state') == 'busy' and
        pane.get('active') and any(e['type'] == 'stop_not_matched' and e['data'].get('prompt_id') == stop_id for e in trace) and
        any(c['name'] == 'original_stop_submit_accepted' and c['passed'] for c in report['checks']))
    report['ordering'] = ordering
    report['mutant'] = args.mutant
    report['scope'] = 'real CLI/Electron with controlled transcript visibility; no vendor model calls'
    report['status'] = 'PASS' if not report['errors'] and all(c['passed'] for c in report['checks']) else 'INCOMPLETE'
    with args.summary.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=report['status'], red_reproduced=report['red_reproduced'], summary=str(args.summary))))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
