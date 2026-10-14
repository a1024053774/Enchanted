"""Check only archive helpers with new local fixtures; never run the disposal entry point."""
import argparse, ast, json, os, stat, tarfile, tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir()
source=Path(__file__).with_name('dispose-draft-09a2.py').read_text(encoding='utf-8');tree=ast.parse(source)
helpers=ast.Module(body=[v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name in ['inventory','archive_and_verify']],type_ignores=[])
namespace={'stat':stat,'os':os,'tarfile':tarfile}
exec(compile(helpers,'archive-helpers','exec'),namespace)
checks=[]
with tempfile.TemporaryDirectory(prefix='t078-draft-archive-probe-',dir='/tmp') as directory:
    temporary=Path(directory);fixture=temporary/'fixture';fixture.mkdir()
    (fixture/'value.txt').write_bytes(b'fixture data\n')
    target=temporary/'public-target.txt';target.write_bytes(b'public symlink target fixture\n')
    (fixture/'link').symlink_to(target)
    result=namespace['archive_and_verify'](fixture,a.output/'good.tar.gz')
    with tarfile.open(a.output/'good.tar.gz') as arc:
        assert arc.getmember('fixture/link').issym()
        assert arc.extractfile('fixture/value.txt').read()==b'fixture data\n'
    checks.append({'name':'archive_readback_preserves_link_without_copying_target','status':'PASS','source_preserved':fixture.exists()})
    bad=ast.parse(source.replace("tarfile.open(destination,'x:gz',dereference=False)","tarfile.open(destination,'x:gz',dereference=True)"))
    bad_helpers=ast.Module(body=[v for v in bad.body if isinstance(v,ast.FunctionDef) and v.name in ['inventory','archive_and_verify']],type_ignores=[])
    other={'stat':stat,'os':os,'tarfile':tarfile};exec(compile(bad_helpers,'mutant-follow-links','exec'),other)
    rejected=False
    try:other['archive_and_verify'](fixture,a.output/'mutant.tar.gz')
    except AssertionError:rejected=True
    with tarfile.open(a.output/'mutant.tar.gz') as arc:
        copied=arc.getmember('fixture/link').isfile() and arc.extractfile('fixture/link').read()==target.read_bytes()
    assert rejected and copied
    checks.append({'name':'known_bad_follow_links_actually_copies_target_and_is_rejected','status':'PASS','forbidden_result_observed':copied,'source_preserved':fixture.exists()})
report={'status':'PASS','argv':__import__('sys').argv,'checks':checks,'scope':'Archive functions only, temporary public target; no retained-root/slot access, deletion, ps, process signals or model starts'}
with (a.output/'result.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False))
