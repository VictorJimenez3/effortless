"""Reversible user-scope macOS installation; original Codex stays untouched."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import subprocess
import sys
from .control import atomic_json,load,settings_path

SOURCE=Path(__file__).resolve().parent.parent
SERVICE='local.effortless-codex.environment'

def reject_links(path,home):
    current=Path(path)
    while current!=home and home in current.parents:
        if current.is_symlink():raise FileExistsError('Managed path is a symlink: '+str(current))
        current=current.parent

def tree_hash(path):
    digest=hashlib.sha256()
    for entry in sorted(path.rglob('*')):
        if entry.is_symlink():return None
        if entry.is_file():
            digest.update(str(entry.relative_to(path)).encode());digest.update(b'\0')
            digest.update(entry.read_bytes());digest.update(b'\0')
    return digest.hexdigest()

def install_files(home,python,real_cli,judge_cli,judge_model,previous_override=''):
    home=Path(home);base=home/'.local/share/effortless-codex'
    config=home/'.config/effortless-codex/settings.json'
    launcher=home/'.local/bin/effortless-codex'
    skill=home/'.codex/skills/effortless-codex'
    plist=home/'Library/LaunchAgents'/f'{SERVICE}.plist'
    manifest=base/'install-manifest.json'
    for managed in [base,config,launcher,skill,plist,manifest]:
        reject_links(managed,home)
        if managed.is_dir():
            for entry in managed.rglob('*'):
                if entry.is_symlink():
                    if entry==base/'judge-home/auth.json' and entry.readlink()==home/'.codex/auth.json':continue
                    raise FileExistsError('Symlink inside managed installation: '+str(entry))
    existing={}
    if config.exists():
        existing=json.loads(config.read_text())
        if existing.get('managed_by')!='effortless-codex':raise FileExistsError('Unrelated settings exist')
    if launcher.exists() and 'Managed by Effortless Codex' not in launcher.read_text():
        raise FileExistsError('Unrelated effortless-codex command exists')
    if skill.exists() and not existing:raise FileExistsError('Unrelated effortless-codex skill exists')
    if not existing and manifest.exists():
        old=json.loads(manifest.read_text())
        if old.get('managed_by')=='effortless-codex':existing=old
    if base.exists() and not existing:raise FileExistsError('Unrelated installation directory exists')
    if plist.exists():
        digest=hashlib.sha256(plist.read_bytes()).hexdigest()
        if not existing or digest!=existing.get('service_sha256'):
            raise FileExistsError('Unrelated or edited launch service exists')
    if existing and launcher.exists() and hashlib.sha256(launcher.read_bytes()).hexdigest()!=existing.get('launcher_sha256'):
        raise FileExistsError('Edited launcher exists')
    if existing and skill.exists() and tree_hash(skill)!=existing.get('skill_sha256'):
        raise FileExistsError('Edited controller skill exists')
    base.mkdir(parents=True,exist_ok=True,mode=0o700)
    app=base/'app';app.mkdir(exist_ok=True)
    shutil.copytree(SOURCE/'effortless_codex',app/'effortless_codex',dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (app/'entry.py').write_text('import os,sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).parent))\nos.environ.setdefault("EFFORTLESS_CODEX_CONFIG",'+repr(str(config))+')\nfrom effortless_codex.cli import main\nmain()\n')
    launcher.parent.mkdir(parents=True,exist_ok=True)
    launcher.write_text('#!/bin/sh\n# Managed by Effortless Codex\nexec '+shlex.quote(str(python))+' '+shlex.quote(str(app/'entry.py'))+' "$@"\n')
    launcher.chmod(0o755)
    skill.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(SOURCE/'skills/effortless-codex',skill,dirs_exist_ok=True)
    desktop='/Applications/ChatGPT.app' if Path('/Applications/ChatGPT.app').exists() else '/Applications/Codex.app'
    value={**existing,'managed_by':'effortless-codex','version':'0.1.1','auto':True,
        'judge_model':judge_model,'judge_cli':str(judge_cli),'judge_timeout':12,
        'minimum_confidence':0.85,'real_cli':str(real_cli),'auth_home':str(home/'.codex'),
        'data_dir':str(base),'launcher':str(launcher),'desktop_app':desktop,
        'skill_path':str(skill),'previous_override':existing.get('previous_override',previous_override),
        'control_revision':existing.get('control_revision',0)+1,
        'resume_revision':existing.get('resume_revision',0)+1}
    plist.parent.mkdir(parents=True,exist_ok=True)
    content=plistlib.dumps({'Label':SERVICE,'ProgramArguments':['/bin/launchctl','setenv','CODEX_CLI_PATH',str(launcher)],'RunAtLoad':True})
    plist.write_bytes(content)
    value['service_path']=str(plist);value['service_sha256']=hashlib.sha256(content).hexdigest()
    value['launcher_sha256']=hashlib.sha256(launcher.read_bytes()).hexdigest()
    value['skill_sha256']=tree_hash(skill)
    atomic_json(config,value)
    atomic_json(manifest,value)
    return {'config':str(config),'launcher':str(launcher),'service':str(plist),'skill':str(skill)}

def activate(result):
    target=f'gui/{os.getuid()}'
    subprocess.run(['launchctl','bootout',target+'/'+SERVICE],capture_output=True)
    subprocess.run(['launchctl','bootstrap',target,result['service']],check=True)
    subprocess.run(['launchctl','setenv','CODEX_CLI_PATH',result['launcher']],check=True)

def uninstall():
    config=load()
    if config.get('managed_by')!='effortless-codex':raise RuntimeError('No managed installation')
    target=f'gui/{os.getuid()}'
    service=Path(config['service_path'])
    def owned(path,digest):
        return path.is_file() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==digest
    if owned(service,config.get('service_sha256')):
        subprocess.run(['launchctl','bootout',target+'/'+SERVICE],capture_output=True)
    current=subprocess.run(['launchctl','getenv','CODEX_CLI_PATH'],text=True,capture_output=True).stdout.strip()
    if current==config['launcher']:
        previous=config.get('previous_override','')
        if previous:subprocess.run(['launchctl','setenv','CODEX_CLI_PATH',previous],check=True)
        else:subprocess.run(['launchctl','unsetenv','CODEX_CLI_PATH'],check=True)
    for field,hash_field in [('launcher','launcher_sha256'),('service_path','service_sha256')]:
        path=Path(config[field])
        if owned(path,config.get(hash_field)):path.unlink()
    skill=Path(config['skill_path'])
    if skill.is_dir() and not skill.is_symlink() and tree_hash(skill)==config.get('skill_sha256'):
        shutil.rmtree(skill)
    # Native auth remains in its original library. Remove only the alias.
    alias=Path(config['data_dir'])/'judge-home/auth.json'
    if alias.is_symlink():alias.unlink()
    settings_path().unlink()
    print('Removed unchanged managed configuration. User edits and local runtime files are retained. Quit/reopen the app once.')

def main():
    if sys.version_info<(3,11):raise SystemExit('Python 3.11 or newer is required')
    if sys.platform!='darwin':raise SystemExit('This desktop installer currently supports macOS')
    parser=argparse.ArgumentParser()
    parser.add_argument('--judge',choices=['gpt-6-luna','gpt-6.1-sol'],required=True)
    parser.add_argument('--real-cli');parser.add_argument('--judge-cli')
    args=parser.parse_args()
    from .cli import real_binary
    previous=subprocess.run(['launchctl','getenv','CODEX_CLI_PATH'],text=True,capture_output=True).stdout.strip()
    old=load()
    real=args.real_cli or (old.get('real_cli') if old.get('managed_by')=='effortless-codex' else previous) or real_binary({})
    judge=args.judge_cli or shutil.which('codex') or real
    for path in [real,judge]:
        if not Path(path).is_file() or not os.access(path,os.X_OK):raise SystemExit('Codex executable is unavailable: '+path)
    result=install_files(Path.home(),sys.executable,real,judge,args.judge,previous)
    activate(result)
    print(json.dumps({**result,'auto':True,'judge':args.judge,'activation':'Configured for future desktop launches; quit/reopen an already open app once.'},indent=2))
