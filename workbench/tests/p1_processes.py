"""Pure process-identity parsing and cleanup verdict; the runner owns ps I/O."""
import re

def identity_from_ps(pid, code, stdout, stderr):
    if stderr.strip() or code not in (0, 1):raise ValueError('process_readback_failed')
    if code == 1:
        if stdout.strip():raise ValueError('ambiguous_process_exit')
        return None
    lines=[line.strip() for line in stdout.splitlines() if line.strip()]
    if len(lines)!=1:raise ValueError('ambiguous_process_readback')
    parts=lines[0].split(maxsplit=6)
    if len(parts)!=7 or int(parts[0])!=pid:raise ValueError('process_identity_mismatch')
    started=' '.join(parts[1:6])
    if not re.fullmatch(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]{1,2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}',started):
        raise ValueError('process_locale_protocol_mismatch')
    return {'pid':pid,'started':started,'command':parts[6]}

def cli_exit_verdict(attempted, manifest, observed):
    if not attempted:return {'status':'PASS','reason':'no_controller_launch_attempt'}
    if not manifest or not manifest.get('cli'):
        return {'status':'BLOCKED','reason':'cli_process_manifest_missing'}
    identity=manifest['cli'];pid=identity.get('pid')
    if type(pid) is not int or pid<=0 or not identity.get('started') or not identity.get('command') or pid not in observed:
        return {'status':'BLOCKED','reason':'cli_process_exit_unverified'}
    current=observed[pid]
    if current is None:return {'status':'PASS','reason':'recorded_cli_exited','pid':pid}
    if current['pid']!=pid or current['started']!=identity['started']:
        return {'status':'BLOCKED','reason':'cli_process_identity_changed','pid':pid}
    # This is an exit observation, not permission to signal a process. ps can
    # change comm during shutdown without changing the process lifetime (#153).
    # Keep waiting for actual absence; never call a changed command "exited".
    return {'status':'BLOCKED','reason':'recorded_cli_still_alive','pid':pid,
            'command_changed':current['command']!=identity['command'],'observed_command':current['command']}
