"""Approval, terminal-frame and readiness facts for P1 scenarios."""
import re
from p1_output import validate_capture


def terminal_text(raw):
    # Same OSC/CSI removal used by the approved native readiness reader.
    plain=re.sub(r'\x1b\][^\x07]*(?:\x07|\x1b\\)','',raw.decode('utf-8'))
    return re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',plain)


def empty_manual_prompt(raw,capture):
    validate_capture(raw,capture)
    # CR/CRLF screen redraws produce blank separator rows. Keep every
    # nonblank row, including any nonempty line of the actual draft.
    text='\n'.join(line for line in terminal_text(raw).splitlines() if line.strip())
    editor=prompt_frame({'terminal':text})
    if not editor['empty']:raise ValueError('readiness_prompt_not_empty')
    footer=text.splitlines()[editor['end_row']+1:]
    if not footer or not re.match(r'^⏸\s*manual\s*mode\s*on(?=\s|·|$)',footer[0].strip()):
        raise ValueError('readiness_manual_mode_required')
    return {'editor':editor,'mode':'manual','mode_row':footer[0],'terminal_text':text}


def action_plan(handling):
    if handling=='simulated-empty-declaration':
        return [{'action':'Escape'},{'action':'clear-restored-draft','key':'Control+C'},
                {'action':'declare-empty-release','truth':'empty'}]
    if handling=='retain-draft-for-block':
        return [{'action':'Escape'},{'action':'retain-restored-draft'},
                {'action':'declare-empty-release','truth':'intentionally-false'}]
    raise ValueError('Unsupported simulated-user scenario')

def validate_actions(approval,consent,handling):
    bound=approval['input']
    if any(consent.get(k)!=bound[k] for k in ['launch','session']) or consent.get('scenario')!=bound['task'].removeprefix('t078-p1-'):
        raise ValueError('Actions approval identity mismatch')
    if consent.get('source')!='test-simulated-user' or consent.get('approved_by')!='executor' or not consent.get('approval_ref') or not consent.get('basis'):
        raise ValueError('Explicit executor approval for automation required')
    actions=consent.get('actions',[])
    plan=[{k:v for k,v in row.items() if k not in ['approved_by','approval_ref','basis']} for row in actions]
    if plan!=action_plan(handling):raise ValueError('Actions approval plan mismatch')
    for row in actions:
        if row.get('approved_by')!='executor' or not row.get('approval_ref') or not row.get('basis'):
            raise ValueError('Each simulated-user action requires approval')

def prompt_frame(view):
    lines=view['terminal'].splitlines()
    def rule(line):
        text=line.strip()
        return len(text)>=10 and set(text)=={'─'}
    starts=[i for i,line in enumerate(lines) if line.lstrip().startswith('❯') and i>0 and rule(lines[i-1])]
    if not starts:raise ValueError('No identifiable prompt editor frame')
    start=starts[-1]
    end=next((i for i in range(start+1,len(lines)) if rule(lines[i])),None)
    if end is None:raise ValueError('Prompt editor frame is incomplete')
    text='\n'.join([lines[start].lstrip()[1:],*lines[start+1:end]])
    return {'start_row':start,'end_row':end,'text':text,'empty':not text.strip()}

def bound_held(view,binding):
    return (view.get('launch')==binding['launch'] and view.get('thread')==binding['thread']
            and view.get('active_dispatch')=='' and view.get('state')=='busy'
            and view.get('lifecycle')=='running' and view.get('input_enabled') is True)
