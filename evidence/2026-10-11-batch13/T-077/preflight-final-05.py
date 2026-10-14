#!/usr/bin/env python3
"""Inspect remaining fixture call chains without starting a host or provider."""
import argparse
import ast
import importlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'workbench/tests'))


def inspect_class(cls, names):
    instances = [cls(name) for name in names]
    roots = [*names, '__init__', 'setUp', 'tearDown']
    if hasattr(cls, 'close_fixture'):
        roots.append('close_fixture')
    pending = [(cls, name) for name in roots]
    visited = set()
    checks, findings, expanded = [], [], []
    initialized = set(vars(instances[0]))
    reads = []
    helper_types = {}
    for ancestor in cls.__mro__:
        for function in ancestor.__dict__.values():
            if not inspect.isfunction(function) or ROOT not in Path(inspect.getsourcefile(function)).resolve().parents:
                continue
            for node in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(function)))):
                if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call) or not isinstance(node.value.func, ast.Name):
                    continue
                helper = function.__globals__.get(node.value.func.id)
                if not inspect.isclass(helper) or not helper.__module__ in ('legacy_quality_driver', 'command_evidence'):
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                        helper_types[target.attr] = helper

    def resolve(start, name):
        return next(((owner, owner.__dict__[name]) for owner in cls.__mro__[cls.__mro__.index(start):]
                     if name in owner.__dict__), (None, None))

    while pending:
        start, name = pending.pop()
        owner, function = resolve(start, name)
        if owner is None:
            findings.append({'kind': 'missing_root', 'method': name}); continue
        key = (owner, name)
        if key in visited or not inspect.isfunction(function):
            continue
        visited.add(key)
        filename = Path(inspect.getsourcefile(function)).resolve()
        if ROOT not in filename.parents:
            continue
        source, first = inspect.getsourcelines(function)
        tree = ast.parse(textwrap.dedent(''.join(source)))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
                if isinstance(node.ctx, ast.Store): initialized.add(node.attr)
                elif isinstance(node.ctx, ast.Load): reads.append((node.attr, str(filename.relative_to(ROOT)), first + node.lineno - 1))
            if not isinstance(node, ast.Call): continue
            target_owner = target = None
            receiver = None
            method = None
            helper_call = constructor = False
            if isinstance(node.func, ast.Attribute):
                receiver, method = node.func.value, node.func.attr
                if isinstance(receiver, ast.Name) and receiver.id == 'self':
                    target_owner, target = resolve(cls, method)
                    if target is None:
                        findings.append({'kind': 'missing_method', 'method': method,
                            'caller': owner.__name__ + '.' + name, 'file': str(filename.relative_to(ROOT)),
                            'line': first + node.lineno - 1})
                        continue
                elif (isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Name)
                      and receiver.func.id == 'super' and not receiver.args):
                    position = cls.__mro__.index(owner) + 1
                    if position < len(cls.__mro__):
                        target_owner, target = resolve(cls.__mro__[position], method)
                elif isinstance(receiver, ast.Attribute) and isinstance(receiver.value, ast.Name) and receiver.value.id == 'self' and receiver.attr in helper_types:
                    target_owner = helper_types[receiver.attr]
                    target = getattr(target_owner, method, None)
                    helper_call = True
                    if target is None:
                        findings.append({'kind': 'missing_helper_method', 'method': method,
                                         'helper': target_owner.__name__, 'caller': owner.__name__ + '.' + name})
                else:
                    # Explicit base.method(self, ...) uses the defining module's
                    # actual class object, rather than a guessed class name.
                    value = function.__globals__.get(receiver.id) if isinstance(receiver, ast.Name) else None
                    if isinstance(receiver, ast.Attribute) and isinstance(receiver.value, ast.Name):
                        namespace = function.__globals__.get(receiver.value.id)
                        value = getattr(namespace, receiver.attr, None)
                    if inspect.isclass(value) and value in cls.__mro__ and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == 'self':
                        target_owner, target = resolve(value, method)
            elif isinstance(node.func, ast.Name):
                value = function.__globals__.get(node.func.id)
                if inspect.isclass(value) and value in helper_types.values():
                    target_owner = target = value
                    method = '__init__'; constructor = True
            if target is None or not callable(target): continue
            explicit_base = (not (isinstance(receiver, ast.Name) and receiver.id == 'self')
                             and not isinstance(receiver, ast.Call) and not helper_call)
            positional = [object() for arg in node.args if not isinstance(arg, ast.Starred)]
            if not explicit_base and not constructor: positional.insert(0, instances[0])
            kwargs = {kw.arg: object() for kw in node.keywords if kw.arg is not None}
            unpacked = any(isinstance(arg, ast.Starred) for arg in node.args) or any(kw.arg is None for kw in node.keywords)
            row = {'caller': owner.__name__ + '.' + name, 'method': method,
                   'target': target_owner.__name__, 'file': str(filename.relative_to(ROOT)),
                   'line': first + node.lineno - 1, 'keywords': sorted(kwargs), 'signature': str(inspect.signature(target))}
            try:
                signature = inspect.signature(target)
                if unpacked:
                    signature.bind_partial(*positional, **kwargs)
                    expanded.append(row)
                else:
                    signature.bind(*positional, **kwargs)
                checks.append(row)
            except TypeError as error:
                findings.append({'kind': 'signature_mismatch', **row, 'error': str(error)})
            if not helper_call and not constructor: pending.append((target_owner, method))
            if method == 'addCleanup':
                for arg in node.args:
                    if isinstance(arg, ast.Attribute) and isinstance(arg.value, ast.Name) and arg.value.id == 'self':
                        pending.append((cls, arg.attr))

    missing_data = sorted({(attr, file, line) for attr, file, line in reads
                           if attr not in initialized and not hasattr(instances[0], attr)})
    # TaskCardsCLI.commit reads managed_trailers only for a threaded attempt.
    # QualityCase delegates to this parent only when thread_id is false; its
    # managed branch constructs its own trailers. Retain this conditional edge
    # for explicit inspection, without requiring an unused managed helper.
    conditional = []
    for row in list(findings):
        if row['kind'] == 'missing_method' and row.get('caller') == 'TaskCardsCLI.commit' and row['method'] == 'managed_trailers' and any(c.__name__ == 'QualityCase' for c in cls.__mro__):
            conditional.append(row); findings.remove(row)
    missing_data = [row for row in missing_data if not (row[0] == 'managed_trailers' and conditional)]
    return {'class': cls.__module__ + '.' + cls.__name__, 'cases': names,
            'instances': len(instances), 'mro': [c.__module__ + '.' + c.__name__ for c in cls.__mro__],
            'visited_methods': sorted(owner.__name__ + '.' + name for owner, name in visited),
            'signature_checks': checks, 'unpacked_calls': expanded,
            'conditional_manual_parent_edge': conditional, 'missing_data_attributes': missing_data, 'findings': findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    modules = {name: importlib.import_module(name) for name in (
        'test_relay_conflict_e2e', 'test_conflict_trailer_proofs', 'test_multiturn_identity_e2e',
        'test_startup_shutdown_e2e', 'test_quality_chain_e2e', 'test_quality_tracer_e2e',
        'test_quality_widen_e2e', 'test_quality_legacy_e2e')}
    relay, proof, identity, shutdown, quality, tracer, wide, legacy = modules.values()
    groups = [
        (relay.RelayConflict, ['test_new_attempt_same_request_id_delivers_once']),
        (proof.ConflictTrailerProofs, ['test_extra_trailers_refused', 'test_hook_trailers_integrate']),
        (identity.MultiTurn, ['test_reclaim_after_receipt_turn', 'test_run_after_receipt_turn',
                            'test_other_native_session_rejected', 'test_other_leader_rejected']),
        (shutdown.StartupShutdown, unittest.defaultTestLoader.getTestCaseNames(shutdown.StartupShutdown)),
        (tracer.Tracer, tracer.CASES), (wide.Widen, [*wide.WIDE_CASES, *wide.REVIEW_RED]),
        (quality.QualityCase, quality.CONTROL_CASES), (legacy.LegacyQuality, legacy.CASES)]
    # Import and instantiate only. No test setUp, host, socket or PTY. Git reads the revision below.
    rows = [inspect_class(cls, names) for cls, names in groups]
    findings = [dict(test_class=row['class'], **finding) for row in rows for finding in row['findings']]
    record = {'status': 'PASS' if not findings else 'INCOMPLETE',
              'scope': 'Python fixture resolution and explicit keyword binding; no test setup or business verdict',
              'argv': sys.argv, 'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'classes': rows, 'findings': findings, 'real_codex_turns': 0,
              'limitations': ['Unpacked argument values and runtime field initialization require separate helper probes or entry tests.',
                              'Data attributes listed as missing require source inspection; this pass does not infer dynamic setattr.']}
    with (args.output / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'status': record['status'], 'classes': len(rows), 'instances': sum(row['instances'] for row in rows),
                      'findings': findings, 'missing_data': {row['class']: row['missing_data_attributes'] for row in rows if row['missing_data_attributes']}}))
    return 0 if not findings else 1


if __name__ == '__main__': raise SystemExit(main())
