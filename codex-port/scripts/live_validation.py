"""Real Codex backend verification through the desktop adapter."""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import argparse
import shutil

SOURCE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(SOURCE))
from effortless_codex.rpc import NativeRPC
from effortless_codex.control import atomic_json

parser=argparse.ArgumentParser(description='Live native routing smoke test. Uses your existing ChatGPT sign-in and synthetic prompts.')
parser.add_argument('--adapter',help='Installed launcher to verify; defaults to the source entry point')
parser.add_argument('--output',help='Save JSON results here')
OPTIONS=parser.parse_args()
SCRATCH=tempfile.TemporaryDirectory(prefix='effortless-codex-validation-')
ROOT=Path(SCRATCH.name)
from effortless_codex.cli import real_binary
from effortless_codex import control
NATIVE=real_binary(control.load())

async def main():
    ROOT.mkdir(exist_ok=True)
    home=ROOT/'main-home';home.mkdir(exist_ok=True)
    auth=home/'auth.json'
    if not auth.exists():auth.symlink_to(Path.home()/'.codex/auth.json')
    config=ROOT/'settings.json'
    settings={'auto':True,'judge_model':'gpt-6.1-sol','judge_timeout':12,
              'real_cli':NATIVE,
              'judge_cli':shutil.which('codex') or NATIVE,'data_dir':str(ROOT),
              'auth_home':str(Path.home()/'.codex'),'control_revision':1}
    atomic_json(config,settings)
    states={}
    def notify(d):
        p=d.get('params',{});state=states.get(p.get('threadId'))
        if not state:return
        if d.get('method')=='turn/completed' and not state.done():state.set_result(p['turn'])
    log=(ROOT/'main-stderr.log').open('a')
    command=[OPTIONS.adapter] if OPTIONS.adapter else [sys.executable,str(SOURCE/'entry.py')]
    c=await NativeRPC(notify).start([*command,
        'app-server','--stdio','-c','features.hooks=false','-c','features.plugins=false',
        '-c','features.multi_agent=false','-c','features.skip_host_skill_discovery=true'],
        env=dict(os.environ,EFFORTLESS_CODEX_CONFIG=str(config),CODEX_HOME=str(home)),stderr=log)
    findings=[]
    try:
        await c.call('initialize',{'clientInfo':{'name':'effortless_proxy_validation','version':'0.1.0'},'capabilities':{'experimentalApi':True}})
        await c.send({'method':'initialized'})
        await c.call('model/list',{'includeHidden':False})
        async def new_thread():
            r=await c.call('thread/start',{'model':'gpt-6.1-sol','cwd':str(ROOT),
                'ephemeral':False,'approvalPolicy':'never','sandbox':'read-only',
                'baseInstructions':'Answer the synthetic task only. Do not use tools.',
                'config':{'model_reasoning_effort':'high'}})
            return r['thread']['id']
        async def turn(tid,text,effort='high'):
            states[tid]=asyncio.get_running_loop().create_future()
            await c.call('turn/start',{'threadId':tid,'model':'gpt-6.1-sol','effort':effort,
                'collaborationMode':{'mode':'default','settings':{'model':'gpt-6.1-sol','reasoning_effort':effort,'developer_instructions':None}},
                'input':[{'type':'text','text':text}]},timeout=25)
            done=await asyncio.wait_for(states[tid],90)
            assert done['status']=='completed',done
            snap=await c.call('thread/resume',{'threadId':tid})
            return {'model':snap['model'],'effort':snap['reasoningEffort'],
                    'approvalPolicy':snap['approvalPolicy'],'sandbox':snap['sandbox']}
        tid=await new_thread()
        result=await turn(tid,'Extract only the status value from "status: pending".')
        assert result['effort']=='low',result
        assert result['model']=='gpt-6.1-sol',result
        assert result['approvalPolicy']=='never',result
        assert result['sandbox']['type']=='readOnly',result
        findings.append({'probe':'actual_routing_with_collaboration_mode','pass':True,'settings':result})
        result=await turn(tid,'yes')
        assert result['effort']=='low',result
        findings.append({'probe':'confirmation_keeps_active_effort','pass':True,'settings':result})
        await c.call('thread/settings/update',{'threadId':tid,'effort':'medium'})
        result=await turn(tid,'Return only the integer 4.','medium')
        assert result['effort']=='medium',result
        findings.append({'probe':'manual_picker_wins','pass':True,'settings':result})
        settings.update(judge_timeout=0.001,control_revision=2)
        atomic_json(config,settings)
        result=await turn(await new_thread(),'Compute 37 times 41 exactly.')
        assert result['effort']=='high',result
        findings.append({'probe':'forced_judge_timeout_preserves_original','pass':True,'settings':result})
    finally:
        await c.close();log.close()
    if OPTIONS.output:Path(OPTIONS.output).write_text(json.dumps(findings,indent=2)+'\n')
    SCRATCH.cleanup()
    print(json.dumps(findings,indent=2))

if __name__=='__main__':asyncio.run(main())
