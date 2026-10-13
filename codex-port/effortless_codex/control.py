"""Local settings and status. No prompts, responses or credentials are logged."""
import json
import os
from pathlib import Path
import time

def settings_path():
    return Path(os.environ.get('EFFORTLESS_CODEX_CONFIG',str(Path.home()/'.config/effortless-codex/settings.json')))

def load():
    defaults={'auto':False,'judge_model':'gpt-6.1-sol','judge_timeout':12,
              'minimum_confidence':0.85,'resume_revision':0}
    try:value=json.loads(settings_path().read_text())
    except (OSError,ValueError):return defaults
    if not isinstance(value,dict):return defaults
    result={**defaults,**value}
    if not isinstance(result['auto'],bool):result['auto']=False
    if result['judge_model'] not in {'gpt-6.1-sol','gpt-6-luna'}:result['auto']=False
    for key in ['judge_timeout','minimum_confidence']:
        value=result[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not 0<value<=60:
            result[key]=defaults[key];result['auto']=False
    return result

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    temporary=path.with_name(path.name+f'.{os.getpid()}.tmp')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f,indent=2);f.write('\n')
    os.replace(temporary,path)

def update(**changes):
    value=load();value.update(changes)
    value['control_revision']=value.get('control_revision',0)+1
    if changes.get('auto') is True:value['resume_revision']=value.get('resume_revision',0)+1
    atomic_json(settings_path(),value)
    return value

def write_status(value):
    config=load();data=config.get('data_dir')
    if not data:return
    safe={k:v for k,v in value.items() if k in {'outcome','thread','judge','model','effort','pid','parent_pid'}}
    safe['timestamp']=time.time()
    try:atomic_json(Path(data)/'status.json',safe)
    except OSError:pass

def status():
    config=load();latest={}
    try:latest=json.loads((Path(config['data_dir'])/'status.json').read_text())
    except (OSError,ValueError,KeyError):pass
    active=False
    if latest.get('outcome')!='stopped' and latest.get('pid'):
        try:os.kill(latest['pid'],0);active=True
        except (ProcessLookupError,PermissionError):pass
    return {'installed':bool(config.get('managed_by')=='effortless-codex'),
            'auto':config.get('auto',False),'judge':config.get('judge_model'),
            'worker_model':'gpt-6.1-sol','model_switching':False,
            'adapter_active':active,'last_event':latest}
