"""Retain every HTTP/hook file before owner-bound fixture shutdown.

Only explicitly enumerated evidence trees enter the archive. Authentication
headers, HOME, credentials and SQLite files never enter the tar input.
"""
import argparse
import ctypes
from contextlib import closing
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import sqlite3
import stat
import subprocess
import tarfile
import time
import traceback
import uuid

from p1_processes import identity_from_ps

ROLES = ('ideation', 'executor')
TABLES = ('dispatch_records', 'orchestration_events', 'events', 'inbox_records',
          'inbox_deliveries', 'relay_requests', 'relay_results', 'user_inputs')
SECRET_NAMES = {'authorization', 'cookie', 'x-api-key', 'api_key', 'apikey', 'access_token', 'accesstoken',
                'refresh_token', 'refreshtoken', 'token', 'capability', 'credential', 'secret', 'password'}
SECRET_KEY = re.compile(rb'"(?:[a-z0-9-]+_)*(?:' + b'|'.join(name.encode() for name in sorted(SECRET_NAMES)) + rb')"\s*:\s*("(?:[^"\\]|\\.)*")', re.I)


def secret_name(key):
    key = key.lower()
    return key in SECRET_NAMES or any(key.endswith('_' + name) for name in SECRET_NAMES)


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_json(path):
    return json.loads(Path(path).read_bytes())


def owned_root(owner):
    root = Path(owner['root'])
    require(root.is_dir() and not root.is_symlink() and root == root.resolve(), 'root_realpath_required')
    require(root.parent == Path('/private/tmp') and root.name.startswith('t078-'), 'owned_scratch_root_required')
    require(owner['scene'] in ('A16', '09C', 'TOPOLOGY_PROBE'), 'scene_required')
    require(bool(owner['source_revision']) and bool(owner['target_binding']), 'source_and_target_binding_required')
    for key in ('task_id', 'attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id', 'workspace', 'launch'):
        require(bool(owner['target_binding'].get(key)), 'target_binding_required:' + key)
    return root


def validate_owner_receipts(owner):
    """Match the owner to original Stage A and both actual B1 manifests."""
    root = owned_root(owner)
    require(owner['scene'] in ('A16', '09C', 'TOPOLOGY_PROBE'), 'operational_scene_required')
    require(re.fullmatch('[0-9a-f]{40}', owner['source_revision']) is not None, 'bound_source_revision_required')
    ready = read_json(Path(owner['stage_a']) / 'readiness.json')
    require(ready['root'] == str(root) and ready['target_binding'] == owner['claim_binding'], 'original_claim_binding_changed')
    claim = ready['target_binding']; target = owner['target_binding']
    for key in ('task_id', 'attempt_id', 'session_id', 'fence', 'spec_rev', 'thread_id', 'workspace'):
        require(target[key] == claim[key], 'original_target_changed:' + key)
    require(target['launch'] == claim['runtime_identity']['launch'], 'original_target_launch_changed')
    processes = owner['processes']
    original = read_json(owner['identity_receipt'])
    require(original['root'] == str(root) and original['processes'] == processes, 'original_process_receipt_changed')
    require(ready['daemon']['pid'] == processes['daemon']['pid'], 'original_daemon_changed')
    require(ready['target_process']['shell_pid'] == processes['target_shell']['pid'] and
            ready['target_process']['leader'] == processes['target_leader']['pid'], 'original_target_PID_changed')
    for role in ROLES:
        api = next(item for item in ready['api_processes'] if item['role'] == role)
        identity = processes[role + '_api']
        require(api['pid'] == identity['pid'] and api['ready'] == read_json(root / 'roles' / role / 'api-ready.json'), 'original_API_ready_changed:' + role)
        require(api['ready']['pid'] == identity['pid'] and api['ready']['role'] == role and api['ready']['stage'] == 'A' and
                api['ready']['protocol'] == 'rev2-raw-c-profile-v1' and api['ready']['model_turns'] == 0, 'original_API_profile_changed:' + role)
        require(shlex.split(identity['command'])[1:] == api['argv'][1:], 'original_API_argv_changed:' + role)
    manifest_roles=ROLES if owner['scene'] in ('A16','09C') else ('ideation',)
    require(set(owner['roles'])==set(manifest_roles),'original_role_set_changed')
    if owner['scene']=='TOPOLOGY_PROBE':
        probe=read_json(owner['probe_record'])
        require(probe['status']=='PREPARED' and probe['root']==str(root) and probe['source_revision']==owner['source_revision'] and
                probe['stage_a']==owner['stage_a'] and probe['original_processes']=={k:processes[k] for k in probe['original_processes']},
                'original_probe_binding_changed')
        inp=read_json(Path(probe['p1'])/'input.json')
        require(inp['root']==str(root) and inp['task']==ready['task'] and inp['preset']=='ideation' and
                inp['launch']==owner['roles']['ideation']['launch'] and inp['session']==owner['roles']['ideation']['session'],
                'original_probe_role_changed')
    for role in manifest_roles:
        binding = owner['roles'][role]; manifest = read_json(binding['manifest'])
        require(binding['launch'] == manifest['launch'] and binding['session'] == manifest['session'] and
                manifest['shell_pid'] == processes[role + '_shell']['pid'] and
                manifest['cli']['pid'] == processes[role + '_cli']['pid'] and
                manifest['cli']['started'] == processes[role + '_cli']['started'], 'original_role_manifest_changed:' + role)
        argv = shlex.split(processes[role + '_cli']['command'])
        require(argv[0] == manifest['cli']['command'] and argv[argv.index('--session-id') + 1] == binding['session'] and
                str(root / 'roles' / role / 'claude-debug.log') in argv, 'original_role_argv_changed:' + role)


def redact(raw, secrets):
    """Replace value spans only. Keep surrounding bytes and record every span."""
    spans = []
    for match in SECRET_KEY.finditer(raw):
        spans.append((match.start(1), match.end(1), b'"[REDACTED]"', 'sensitive_json_field'))
    sensitive = []
    def collect(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if secret_name(key) and isinstance(item, str) and item:
                    sensitive.append(item)
                else: collect(item)
        elif isinstance(value, list):
            for item in value: collect(item)
        elif isinstance(value, str) and value.startswith(('{', '[')):
            try: collect(json.loads(value))
            except ValueError: pass  # Plain business text, not an embedded JSON object.
    try: collect(json.loads(raw))
    except (ValueError, UnicodeDecodeError): pass  # Binary/SSE originals still use the explicit secret inventory.
    for secret in set(secrets + sensitive):
        require(isinstance(secret, str) and len(secret) >= 8, 'invalid_redaction_secret')
        for token in {secret.encode('utf-8'), json.dumps(secret, ensure_ascii=False)[1:-1].encode('utf-8')}:
            start = 0
            while True:
                start = raw.find(token, start)
                if start < 0: break
                spans.append((start, start + len(token), b'[REDACTED]', 'explicit_secret_value'))
                start += len(token)
    merged = []
    for start, end, replacement, reason in sorted(spans):
        if merged and start < merged[-1][1]:
            require(end <= merged[-1][1], 'overlapping_redaction_spans')
            continue
        merged.append((start, end, replacement, reason))
    chunks, mapping, cursor, archived_offset = [], [], 0, 0
    for start, end, replacement, reason in merged:
        chunks += [raw[cursor:start], replacement]
        archived_offset += start - cursor
        mapping.append({'original_start': start, 'original_end': end, 'archived_start': archived_offset,
                        'archived_end': archived_offset + len(replacement), 'reason': reason})
        archived_offset += len(replacement); cursor = end
    chunks.append(raw[cursor:])
    result = b''.join(chunks)
    require(all(secret.encode('utf-8') not in result for secret in secrets), 'secret_redaction_incomplete')
    return result, mapping


def secrets_for(owner):
    path = Path(owner['root']) / 'retention-secrets.json'
    # Even a scene without credentials supplies an explicit empty list.
    require(path.is_file() and not path.is_symlink(), 'explicit_secret_inventory_required')
    value = read_json(path)
    require(isinstance(value, list), 'invalid_secret_inventory')
    return value


def raw_sources(owner):
    root = owned_root(owner); files = {}
    trees = [(f'roles/{role}/{name}', root / 'roles' / role / name)
             for role in ROLES for name in ('http-exchanges', 'hooks')]
    if (root / 'topology-diagnostics').exists():
        trees.append(('topology-diagnostics', root / 'topology-diagnostics'))
    for index, item in enumerate(owner.get('evidence_trees', [])):
        path = Path(item)
        require(path.is_absolute() and path.is_dir() and path == path.resolve(), 'evidence_tree_realpath_required')
        trees.append((f'evidence/{index}', path))
    for logical, tree in trees:
        require(tree.is_dir() and not tree.is_symlink() and tree.resolve() == tree, 'raw_tree_missing:' + str(tree))
        for path in sorted(tree.rglob('*')):
            mode = path.lstat().st_mode
            require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'unsupported_raw_member:' + str(path))
            if stat.S_ISREG(mode):
                require(path.name not in ('auth.json', 'credentials.json', 'operator.json') and
                        not path.name.startswith('state.sqlite3'), 'forbidden_raw_member:' + str(path))
                files[logical + '/' + str(path.relative_to(tree))] = path
    for role in ROLES:
        for name in ('requests.ndjson', 'responses.ndjson'):
            path = root / 'roles' / role / name
            if path.exists():
                require(path.is_file() and not path.is_symlink(), 'invalid_HTTP_log')
                files[f'roles/{role}/{name}'] = path
    target = root / owner['target_bytes']
    require(target.is_relative_to(root) and target.is_file() and target == target.resolve(), 'target_bytes_required')
    files['target/received.bin'] = target
    baseline = root / owner['target_baseline']
    require(baseline.is_relative_to(root) and baseline.is_file() and baseline == baseline.resolve(), 'target_baseline_required')
    files['target/baseline.bin'] = baseline
    return files


def export_live_database(root):
    """One live read transaction; close before returning, never called after stop."""
    database = root / 'state/state.sqlite3'
    require(database.is_file() and database == database.resolve(), 'owned_live_database_required')
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN')
        available = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        result = {table: [dict(row) for row in db.execute('SELECT * FROM ' + table + ' ORDER BY rowid')]
                  for table in TABLES if table in available}
        require('orchestration_events' in result and 'dispatch_records' in result, 'live_event_tables_required')
        db.rollback()
    return result


def capture(owner, staging):
    root = owned_root(owner); staging = Path(staging)
    require(not staging.resolve().is_relative_to(root), 'staging_must_be_outside_root')
    staging.mkdir(parents=True, exist_ok=False)
    secret_values = secrets_for(owner); records = []
    source_files = raw_sources(owner)
    for logical, path in source_files.items():
        raw = path.read_bytes(); clean, mapping = redact(raw, secret_values)
        dest = staging / 'files' / logical; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(clean)
        records.append({'logical': logical, 'source': str(path), 'type': 'file', 'original_bytes': len(raw),
                        'archived_bytes': len(clean), 'redacted': bool(mapping), 'ranges': mapping})
    live = json.dumps(export_live_database(root), ensure_ascii=False, indent=2).encode('utf-8') + b'\n'
    clean, mapping = redact(live, secret_values)
    (staging / 'live-rows.json').write_bytes(clean)
    snapshot = {'schema': 1, 'scene': owner['scene'], 'source_revision': owner['source_revision'],
                'root': str(root), 'target_binding': owner['target_binding'], 'captured_at': time.time(),
                'records': records, 'live_rows_redactions': mapping,
                'scope': 'all enumerated HTTP/hook files, including failures and unfinished traces; live rows before stop'}
    identity = json.dumps({key: owner[key] for key in ('root', 'source', 'source_revision', 'target_binding', 'claim_binding',
        'processes', 'process_graph', 'roles') if key in owner}, ensure_ascii=False).encode()
    clean_identity, identity_maps = redact(identity, secret_values)
    (staging / 'identity-receipts.json').write_bytes(clean_identity)
    snapshot['identity_redactions'] = identity_maps
    save(staging / 'snapshot.json', snapshot)
    assert_stable(owner, staging)
    return snapshot


def assert_stable(owner, staging):
    snapshot = read_json(Path(staging) / 'snapshot.json')
    require(snapshot['root'] == owner['root'] and snapshot['source_revision'] == owner['source_revision'], 'snapshot_owner_mismatch')
    sources = raw_sources(owner); records = snapshot['records']
    require(set(sources) == {item['logical'] for item in records}, 'raw_member_set_changed')
    secrets = secrets_for(owner)
    for item in records:
        raw = sources[item['logical']].read_bytes()
        clean, mapping = redact(raw, secrets)
        require(len(raw) == item['original_bytes'] and mapping == item['ranges'] and
                clean == (Path(staging) / 'files' / item['logical']).read_bytes(), 'raw_bytes_changed:' + item['logical'])


def verify_archive(staging, archive):
    """Compare the entire member set, type and bytes. Never use a checksum."""
    staging = Path(staging)
    expected = {str(path.relative_to(staging)): path for path in staging.rglob('*')}
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers(); actual = {member.name: member for member in members}
        require(len(members) == len(actual) and set(actual) == set(expected), 'archive_member_set_mismatch')
        for name, path in expected.items():
            member = actual[name]
            require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'unsafe_archive_path')
            if path.is_symlink():
                target = os.readlink(path)
                require(path.resolve().is_relative_to(staging.resolve()), 'external_staging_link')
                require(member.issym() and member.linkname == target, 'archive_link_mismatch:' + name)
            elif path.is_dir():
                require(member.isdir(), 'archive_type_mismatch:' + name)
            else:
                require(path.is_file() and member.isfile(), 'archive_type_mismatch:' + name)
                with tar.extractfile(member) as stream:
                    require(stream.read() == path.read_bytes(), 'archive_bytes_mismatch:' + name)
    return list(sorted(expected))


def archive_capture(owner, staging, archive):
    archive = Path(archive)
    require(archive.is_absolute() and not archive.exists(), 'new_archive_path_required')
    require(not archive.resolve().is_relative_to(Path(owner['root'])), 'archive_inside_root')
    archive.parent.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'w:gz') as tar:
        for path in sorted(Path(staging).rglob('*')):
            tar.add(path, arcname=str(path.relative_to(staging)), recursive=False)
    inventory = verify_archive(staging, archive)
    snapshot = read_json(Path(staging) / 'snapshot.json')
    pointers = archive.parent / 'pointers'
    for item in snapshot['records']:
        parts = Path(item['logical']).parts
        role = parts[1] if parts[0] == 'roles' else None
        native = owner.get('roles', {}).get(role, {})
        save(pointers / (item['logical'] + '.archive.json'),
             {**item, 'archive': str(archive), 'member': 'files/' + item['logical'],
              'scene': owner['scene'], 'source_revision': owner['source_revision'],
              'target_binding': owner['target_binding'], 'captured_at': snapshot['captured_at'],
              'byte_readback': 'PASS', 'codec': 'tar+gzip', 'inventory_membership': True,
              'role_launch_native_session': native, 'source_relative_path': item['logical'],
              'record_sequence_or_hook_trace_id': parts[3].split('.')[0] if len(parts) > 3 and role else None,
              'redaction_map_member_if_changed': 'snapshot.json' if item['ranges'] else None})
    receipt = {'status': 'PASS', 'archive': str(archive), 'archive_bytes': archive.stat().st_size,
               'inventory': inventory, 'byte_readback': 'PASS', 'staging': str(Path(staging).resolve()),
               'root': owner['root'], 'scene': owner['scene'], 'source_revision': owner['source_revision']}
    save(archive.parent / 'bundle.archive.json', receipt)
    return receipt


def readback(archive):
    """Recount originals directly from tar; does not use collector summaries."""
    counts = {'Messages_POST': {}, 'hooks': {}, 'roots': {}, 'permission_requests': {},
              'unfinished_http': [], 'unfinished_hooks': []}
    with tarfile.open(archive, 'r:gz') as tar:
        members = {item.name: item for item in tar.getmembers()}
        for role in ROLES:
            base = 'files/roles/' + role + '/http-exchanges/'
            requests = [name for name in members if name.startswith(base) and name.endswith('.request.bin')]
            counts['Messages_POST'][role] = 0
            for name in requests:
                meta_name = name.replace('.request.bin', '.meta.json')
                if meta_name not in members or name.replace('.request.bin', '.response.bin') not in members:
                    counts['unfinished_http'].append(name); continue
                meta = json.load(tar.extractfile(meta_name))
                require(meta.get('method') == 'POST' and isinstance(meta.get('path'), str), 'HTTP_method_path_original_required')
                require(meta['path'].split('?')[0] in ('/v1/messages', '/v1/messages/count_tokens'), 'unexpected_HTTP_path')
                if meta['path'].split('?')[0] == '/v1/messages': counts['Messages_POST'][role] += 1
                if not meta.get('complete'):
                    counts['unfinished_http'].append(name)
            hook_base = 'files/roles/' + role + '/hooks/'
            starts = [name for name in members if name.startswith(hook_base) and name.endswith('/started.json')]
            counts['hooks'][role] = {}
            roots = set(); permissions = []
            for name in starts:
                stdin = name.replace('started.json', 'stdin.bin')
                if stdin not in members:
                    counts['unfinished_hooks'].append(name); continue
                data = json.load(tar.extractfile(stdin)); event = data['hook_event_name']
                counts['hooks'][role][event] = counts['hooks'][role].get(event, 0) + 1
                if name.replace('started.json', 'finished.json') not in members:
                    counts['unfinished_hooks'].append(name)
                if event == 'UserPromptSubmit': roots.add((data.get('session_id'), data.get('prompt_id')))
                if event == 'PermissionRequest': permissions.append({'session_id': data.get('session_id'),
                    'prompt_id': data.get('prompt_id'), 'tool_name': data.get('tool_name'), 'tool_input': data.get('tool_input')})
            counts['roots'][role] = len(roots); counts['permission_requests'][role] = permissions
    return counts


class HttpExchange:
    """Capture request bytes before validation and every attempted wire byte.

    The server passes only method/path/content type. No authentication header
    value crosses this interface. Incomplete writes stay explicitly incomplete.
    """
    def __init__(self, root, sequence, method, path, content_type, body, role):
        self.base = Path(root) / 'http-exchanges'; self.base.mkdir(exist_ok=True)
        self.label = f'{sequence:04d}'
        with (self.base / (self.label + '.request.bin')).open('xb') as stream: stream.write(body)
        self.response = (self.base / (self.label + '.response.bin')).open('xb')
        self.meta = {'sequence': sequence, 'role': role, 'method': method, 'path': path,
                     'request_content_type': content_type, 'request_bytes': len(body), 'started_at': time.time(),
                     'response_bytes': 0, 'wire_bytes_confirmed': 0, 'complete': False}
        self.persist()

    def persist(self):
        target = self.base / (self.label + '.meta.json')
        temporary = self.base / (self.label + '.meta.tmp')
        temporary.write_text(json.dumps(self.meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temporary.replace(target)

    def write(self, stream, payload):
        self.response.write(payload); self.response.flush()
        self.meta['response_bytes'] += len(payload); self.persist()
        stream.write(payload); stream.flush()
        self.meta['wire_bytes_confirmed'] += len(payload); self.persist()

    def finish(self, status, content_type, complete, **fields):
        self.response.close()
        self.meta.update(fields, status=status, response_content_type=content_type,
                         complete=complete, finished_at=time.time())
        self.persist()


class NativeRuntime:
    def __init__(self, owner): self.owner = owner

    def identities(self):
        found = {}
        for label, expected in self.owner['processes'].items():
            pid = expected['pid']
            value = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                                   capture_output=True, text=True, timeout=5, env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'})
            found[label] = identity_from_ps(pid, value.returncode, value.stdout, value.stderr)
        return found

    def topology(self):
        from t078_process_tree import graph_rows, descendants, snapshot
        result = None; second = None
        try:
            result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,tpgid='],
                                    capture_output=True, text=True, timeout=5)
            require(result.returncode == 0 and not result.stderr.strip(), 'process_graph_read_failed')
            graph = graph_rows(result.stdout)
            expected = self.owner['process_graph']
            for label, identity in self.owner['processes'].items():
                require(graph.get(identity['pid']) == expected[label], 'process_graph_changed:' + label)
            actual = descendants(graph, self.owner['processes']['daemon']['pid'])
            managed = {item['pid'] for label, item in self.owner['processes'].items() if not label.endswith('_api')}
            require(managed.issubset(actual), 'managed_process_missing_from_tree')
            parents={self.owner['processes'][role+'_cli']['pid']:role for role in ROLES if role+'_cli' in self.owner['processes']}
            allowed=[];counts={}
            for pid in sorted(actual-managed):
                parent=graph[pid]['ppid'];require(parent in parents,'unexpected_daemon_descendants')
                first=self.helper_identity(pid);require(first is not None,'helper_disappeared')
                require(first['ppid']==parent,'helper_parent_changed')
                argv=shlex.split(first['command']);require(bool(argv) and argv[0]=='caffeinate','unexpected_daemon_descendants')
                path=self.executable_path(pid)
                require(os.path.realpath(path)=='/usr/bin/caffeinate','caffeinate_executable_mismatch')
                # known-bad: ignore-argv
                role=parents[parent];counts[role]=counts.get(role,0)+1
                require(counts[role]<=1,'multiple_caffeinate_for_role')
                parent_probe=subprocess.run(['/bin/ps','-ww','-p',str(parent),'-o','pid=,lstart=,command='],
                    capture_output=True,text=True,timeout=5,env={**os.environ,'LC_ALL':'C','LANG':'C'})
                require(identity_from_ps(parent,parent_probe.returncode,parent_probe.stdout,parent_probe.stderr)==self.owner['processes'][role+'_cli'],
                        'helper_parent_role_identity_changed')
                require(self.helper_identity(pid)==first and self.executable_path(pid)==path,'helper_identity_changed')
                allowed.append({**first,'executable':path,'role':role,'identity_kind':'auxiliary; never a role identity'})
            second=subprocess.run(['/bin/ps','-axo','pid=,ppid=,pgid=,tpgid='],capture_output=True,text=True,timeout=5)
            require(second.returncode==0 and not second.stderr.strip(),'process_graph_recheck_failed')
            again=graph_rows(second.stdout)
            require(descendants(again,self.owner['processes']['daemon']['pid'])==actual and
                    all(again.get(pid)==graph[pid] for pid in actual|{v['pid'] for v in self.owner['processes'].values()}),
                    'owned_process_graph_changed_during_check')
            return allowed
        except Exception as error:
            folder = Path(self.owner['root']) / 'topology-diagnostics' / uuid.uuid4().hex
            if result is None:
                result = subprocess.CompletedProcess(['/bin/ps','-axo','pid=,ppid=,pgid=,tpgid='], -1, '', repr(error))
            snapshot(self.owner, folder, graph_result=result, reason=str(error))
            if second is not None:
                (folder/'recheck.stdout.bin').write_bytes(second.stdout.encode())
                (folder/'recheck.stderr.bin').write_bytes(second.stderr.encode())
            raise

    def helper_identity(self,pid):
        result=subprocess.run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,ppid=,pgid=,tpgid=,lstart=,command='],
            capture_output=True,text=True,timeout=5,env={**os.environ,'LC_ALL':'C','LANG':'C'})
        if result.returncode==1 and not result.stdout.strip():return None
        require(result.returncode==0 and not result.stderr.strip(),'helper_ps_failed')
        cells=result.stdout.strip().split(None,9)
        require(len(cells)==10 and int(cells[0])==pid,'helper_ps_parse_failed')
        return {'pid':pid,'ppid':int(cells[1]),'pgid':int(cells[2]),'tpgid':int(cells[3]),
                'started':' '.join(cells[4:9]),'command':cells[9]}

    def executable_path(self,pid):
        # macOS SDK libproc.h: proc_pidpath; proc_info.h MAXSIZE=4*MAXPATHLEN.
        # Read the kernel's executable path. Never resolve a process name with PATH.
        library=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True)
        function=library.proc_pidpath;function.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32];function.restype=ctypes.c_int
        buffer=ctypes.create_string_buffer(4096)
        size=function(pid,buffer,len(buffer))
        require(size>0,'process_executable_unavailable:'+str(pid)+':'+str(ctypes.get_errno()))
        path=buffer.value.decode('utf-8');require(path.startswith('/'),'absolute_process_executable_required')
        return path

    def wait_helpers_absent(self,helpers,seconds):
        deadline=time.monotonic()+seconds
        while True:
            living=[]
            for expected in helpers:
                current=self.helper_identity(expected['pid'])
                if current is not None:
                    require(current['started']==expected['started'] and current['command']==expected['command'] and
                            self.executable_path(expected['pid'])==expected['executable'],'helper_PID_reused_after_stop')
                    living.append(expected['pid'])
            if not living:return
            require(time.monotonic()<deadline,'auxiliary_exit_unconfirmed');time.sleep(.1)

    def normal_stop(self):
        root = Path(self.owner['root']); source = Path(self.owner['source'])
        env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'ANTHROPIC_', 'CLAUDE_', 'CODEX_'))}
        env['A2A_OPERATOR_CREDENTIAL'] = str(root / 'operator.json')
        result = subprocess.run(['node', str(source / 'workbench/src/gates/cli.ts'), '--state', str(root / 'state'), 'daemon_stop'],
                                cwd=source, env=env, capture_output=True, timeout=30)
        require(result.returncode == 0, 'authenticated_daemon_stop_failed')

    def terminate(self, label): os.kill(self.owner['processes'][label]['pid'], signal.SIGTERM)

    def wait_absent(self, labels, seconds):
        until = time.monotonic() + seconds
        while True:
            observed = self.identities()
            if all(observed[label] is None for label in labels): return
            require(time.monotonic() < until, 'owned_process_exit_unconfirmed')
            time.sleep(.1)


def check_identities(owner, runtime, labels=None):
    expected = owner['processes']; labels = list(expected) if labels is None else labels
    validate_owner_receipts(owner)
    required={'daemon','target_shell','target_leader','ideation_shell','ideation_cli','ideation_api','executor_api'}
    if owner['scene'] in ('A16','09C'):required|={'executor_shell','executor_cli'}
    require(set(expected)==required,'seven_probe_processes_required' if owner['scene']=='TOPOLOGY_PROBE' else 'nine_owned_processes_required')
    require(len({item['pid'] for item in expected.values()}) == len(expected), 'duplicate_owned_PID')
    for _ in range(2):
        actual = runtime.identities()
        for label in labels:
            require(actual.get(label) is not None, 'owned_process_not_alive:' + label)
            require(actual.get(label) == expected[label], 'process_identity_changed:' + label)
    if set(labels) == set(expected):
        helpers=runtime.topology();require(isinstance(helpers,list),'topology_receipt_required');return helpers
    return []


def finish(owner, approval, captured, independent, output, runtime, dry_run=False):
    """No database reads here. Archive and independent readback precede stop."""
    root = owned_root(owner); output = Path(output); output.mkdir(parents=True, exist_ok=False)
    log = {'status': 'BLOCKED', 'signals_sent': [], 'root_removed': False, 'dry_run': dry_run, 'steps': []}
    def step(name):
        log['steps'].append({'name': name, 'at': time.time()})
        (output / 'result.json').write_text(json.dumps(log, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    try:
        require(approval.get('approved_by') == 'executor' and bool(approval.get('approval_ref')), 'signed_cleanup_required')
        for key in ('root', 'scene', 'source_revision', 'target_binding', 'processes'):
            require(approval.get(key) == owner[key], 'cleanup_approval_mismatch:' + key)
        first_helpers=check_identities(owner, runtime); step('OWNERS_VERIFIED')
        if dry_run:
            log['status'] = 'PASS'; step('READ_ONLY_NO_ARCHIVE_STOP_OR_DELETE'); return log
        require(captured['root'] == str(root) and captured['source_revision'] == owner['source_revision'] and
                captured['archive'] == approval['archive'], 'capture_binding_mismatch')
        stage, archive = Path(captured['staging']), Path(captured['archive'])
        require(independent.get('approved_by') == 'executor' and bool(independent.get('approval_ref')) and
                independent.get('archive') == str(archive) and independent.get('counts') == readback(archive),
                'independent_raw_readback_required')
        incomplete = independent['counts']['unfinished_http'] or independent['counts']['unfinished_hooks']
        require(not incomplete or approval.get('retain_failed_scene') is True, 'unfinished_scene_requires_explicit_cleanup_approval')
        require(verify_archive(stage, archive) == captured['inventory'], 'archive_inventory_changed')
        assert_stable(owner, stage); step('ARCHIVE_BYTES_AND_RAW_FILES_VERIFIED_BEFORE_STOP')
        helpers=check_identities(owner, runtime)
        tracked={}
        for helper in first_helpers+helpers:
            old=tracked.get(helper['pid']);require(old is None or old==helper,'auxiliary_identity_changed_before_stop')
            tracked[helper['pid']]=helper
        save(output/'auxiliary-before-stop.json',list(tracked.values()))
        # Each invocation is durable before its side effect. An uncertain
        # shutdown cannot be repeated with another output label.
        journal = archive.parent / 'shutdown-intent.json'
        save(journal, {'root': str(root), 'processes': owner['processes'], 'approval_ref': approval['approval_ref']})
        runtime.normal_stop(); step('DAEMON_STOP_RETURNED')
        apis = ['ideation_api', 'executor_api']
        managed = [key for key in owner['processes'] if key not in apis]
        runtime.wait_absent(managed, 20)
        if tracked:runtime.wait_helpers_absent(list(tracked.values()),3)
        require(not os.path.lexists(root / 'state/control.sock') and not os.path.lexists(root / 'state/daemon.pid'),
                'daemon_socket_or_PID_file_remains')
        for label in apis:
            check_identities(owner, runtime, [label])
            # Log the attempt first; a crash after kill must never resend it.
            log['signals_sent'].append({'pid': owner['processes'][label]['pid'], 'signal': 'SIGTERM'})
            step('SIGTERM_INTENT:' + label); runtime.terminate(label); runtime.wait_absent([label], 3)
        runtime.wait_absent(list(owner['processes']), 1)
        step('ALL_OWNED_PROCESSES_EXITED')
        verify_archive(stage, archive)
        assert_stable(owner, stage)  # Files only; no SQLite, even if DB is gone.
        step('POST_STOP_FILES_VERIFIED')
        require(root == owned_root(owner), 'root_changed_before_delete')
        shutil.rmtree(root)
        log.update(status='PASS', root_removed=True, archive=str(archive), archive_bytes=archive.stat().st_size,
                   post_stop_SQLite_reads=0)
        step('ROOT_REMOVED')
    except Exception as error:
        log.update(error=repr(error), traceback=traceback.format_exc()); step('BLOCKED')
    return log


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['capture', 'readback', 'finish'], required=True)
    parser.add_argument('--owner', type=Path)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--approval', type=Path)
    parser.add_argument('--independent-readback', type=Path)
    parser.add_argument('--capture-result', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.mode == 'readback':
        args.output.mkdir(parents=True, exist_ok=False)
        result = {'archive': str(args.archive.resolve()), 'counts': readback(args.archive), 'approved_by': None, 'approval_ref': None}
        save(args.output / 'readback.json', result)
    else:
        owner = read_json(args.owner)
        validate_owner_receipts(owner)
        if args.mode == 'capture':
            # Do not make an external mount directory on the internal disk.
            require(Path('/Volumes/WD-Elements').is_mount() and args.archive.resolve().is_relative_to(Path('/Volumes/WD-Elements/a2a-evidence')), 'external_archive_volume_required')
            helpers=check_identities(owner, NativeRuntime(owner))
            args.output.mkdir(parents=True, exist_ok=False)
            stage = args.output / 'redacted'
            capture(owner, stage)
            save(stage/'topology-verification.json',{'allowed_helpers':helpers,'owner_process_count':len(owner['processes'])})
            result = archive_capture(owner, stage, args.archive.resolve())
            shutil.copytree(args.archive.parent / 'pointers', args.output / 'archive-pointers')
            save(args.output / 'capture-result.json', result)
        else:
            if args.dry_run:
                result = finish(owner, read_json(args.approval), None, None, args.output, NativeRuntime(owner), True)
            else:
                require(str(args.archive.resolve()) == read_json(args.capture_result)['archive'], 'archive_argument_mismatch')
                result = finish(owner, read_json(args.approval), read_json(args.capture_result),
                                read_json(args.independent_readback), args.output, NativeRuntime(owner))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get('status', 'PASS') == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
