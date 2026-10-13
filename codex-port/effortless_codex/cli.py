"""Executable override: controls locally, delegates normal CLI commands."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from . import control
from .judge import Judge
from .proxy import run_stdio

def real_binary(config):
    if config.get('real_cli'):return config['real_cli']
    for path in ['/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex',
                 '/Applications/Codex.app/Contents/Resources/codex']:
        if Path(path).is_file():return path
    path=shutil.which('codex')
    if path:return path
    raise RuntimeError('Original Codex executable is unavailable')

def routed_transport(args):
    if 'app-server' not in args or any(x in args for x in ['--help','-h','--version']):return False
    tail=args[args.index('app-server')+1:]
    if tail and tail[0] in {'daemon','proxy','generate-ts','generate-json-schema','help'}:return False
    for ix,arg in enumerate(tail):
        if arg=='--listen' and (ix+1>=len(tail) or tail[ix+1]!='stdio://'):return False
        if arg.startswith('--listen=') and arg!='--listen=stdio://':return False
    return True

def main():
    args=sys.argv[1:]
    if args and args[0]=='status':
        print(json.dumps(control.status(),indent=2));return
    if args and args[0] in {'auto','judge'}:
        p=argparse.ArgumentParser(prog='effortless-codex '+args[0])
        p.add_argument('value',choices=['on','off'] if args[0]=='auto' else ['gpt-6-luna','gpt-6.1-sol'])
        value=p.parse_args(args[1:]).value
        if args[0]=='auto':control.update(auto=value=='on')
        else:control.update(judge_model=value)
        print(json.dumps(control.status(),indent=2));return
    if args and args[0]=='uninstall':
        from .install import uninstall
        uninstall();return
    if args and args[0]=='launch':
        config=control.load()
        subprocess.run(['launchctl','setenv','CODEX_CLI_PATH',config['launcher']],check=True)
        subprocess.run(['open','-a',config['desktop_app'],'--env','CODEX_CLI_PATH='+config['launcher']],check=True)
        print('Desktop launch configured. If the app was already open, quit and reopen it once.');return
    config=control.load();real=real_binary(config)
    if not routed_transport(args):os.execv(real,[real,*args])
    data=Path(config.get('data_dir',Path.home()/'.local/share/effortless-codex'))
    judge=Judge(config.get('judge_cli',real),data/'judge-home',config.get('auth_home',Path.home()/'.codex'))
    try:code=asyncio.run(run_stdio(real,args,control.load,judge,control.write_status))
    except (BrokenPipeError,KeyboardInterrupt):code=0
    sys.exit(code)
