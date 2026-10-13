import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
import test_proxy as fixtures
turn=fixtures.turn
from test_judge import FakeRPC
from effortless_codex import control
from effortless_codex.judge import Judge
from effortless_codex.install import install_files,uninstall
from effortless_codex.cli import routed_transport

class RoutingRegressions(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=fixtures.ProxyTests.asyncSetUp
    async def test_old_picker_change_does_not_overwrite_later_request(self):
        self.router.accept({'id':2,'method':'thread/settings/update','params':{'threadId':'t','effort':'medium'}})
        self.router.accept(turn());await self.router.drain()
        self.assertEqual(self.sent[-1]['params']['effort'],'high')

    async def test_partial_config_has_safe_fallback(self):
        self.config={'auto':True}
        self.router.accept(turn());await self.router.drain()
        self.assertEqual(len(self.sent),1)

    async def test_judge_change_does_not_resume_manual_override(self):
        self.router.accept(turn());await self.router.drain()
        self.router.accept({'id':2,'method':'thread/settings/update','params':{'threadId':'t','effort':'medium'}})
        self.config.update(judge_model='gpt-6-luna',control_revision=1)
        msg=turn(3);msg['params']['effort']='medium'
        self.router.accept(msg);await self.router.drain()
        self.assertEqual(self.judge.calls,1)
        self.assertEqual(self.sent[-1]['params']['effort'],'medium')

    async def test_auto_on_explicitly_resumes_manual_override(self):
        self.router.accept(turn());await self.router.drain()
        self.router.accept({'id':2,'method':'thread/settings/update','params':{'threadId':'t','effort':'medium'}})
        self.config.update(resume_revision=1)
        self.router.accept(turn(3));await self.router.drain()
        self.assertEqual(self.judge.calls,2)

    async def test_subagent_source_is_not_routed(self):
        self.router.requests[1]={'method':'thread/resume'}
        self.router.observe({'id':1,'result':{'thread':{'id':'t','source':{'subAgent':{'thread_spawn':{'parent_thread_id':'p','depth':1}}}},'model':'gpt-6.1-sol'}})
        self.router.accept(turn(2));await self.router.drain()
        self.assertEqual(self.judge.calls,0)
        self.assertEqual(self.sent[-1]['params']['effort'],'high')

    async def test_confirmation_keeps_previous_routed_effort(self):
        self.router.accept(turn());await self.router.drain()
        self.router.accept(turn(2,'yes'));await self.router.drain()
        self.assertEqual(self.sent[-1]['params']['effort'],'low')
        self.assertTrue(self.router.state('t').auto)

    async def test_pending_manual_merge_preserves_current_mode_fields(self):
        self.judge.block=asyncio.Event()
        msg=turn();msg['params']['collaborationMode']={'mode':'default','settings':{'model':'gpt-6.1-sol','reasoning_effort':'high','developer_instructions':'retain'}}
        self.router.accept(msg);await asyncio.sleep(0)
        self.router.accept({'id':2,'method':'thread/settings/update','params':{'threadId':'t','collaborationMode':{'settings':{'reasoning_effort':'medium'}}}})
        self.judge.block.set();await self.router.drain()
        self.assertEqual(self.sent[-1]['params']['collaborationMode']['settings']['developer_instructions'],'retain')
        self.assertEqual(self.sent[-1]['params']['collaborationMode']['settings']['reasoning_effort'],'medium')

class DelayedRPC(FakeRPC):
    def __init__(self):super().__init__();self.release=asyncio.Event()
    async def call(self,method,params,timeout=20):
        if method=='turn/start':
            self.methods.append(method);self.started.set();await self.release.wait()
            return {'turn':{'id':'v'}}
        return await super().call(method,params,timeout)

class JudgeRegression(unittest.IsolatedAsyncioTestCase):
    async def test_cancel_before_ack_interrupts_late_native_turn(self):
        with tempfile.TemporaryDirectory() as td:
            j=Judge('/unused',td,td);j.rpc=DelayedRPC();j.prepare=AsyncMock();j.catalog={'gpt-6.1-sol':['low']}
            task=asyncio.create_task(j.decide({'id':'turn'},'gpt-6.1-sol'))
            await j.rpc.started.wait();task.cancel();await asyncio.gather(task,return_exceptions=True)
            j.rpc.release.set()
            await asyncio.sleep(0.02)
            self.assertIn('turn/interrupt',j.rpc.methods)
            self.assertEqual(j.turns,{})

class LocalRegression(unittest.TestCase):
    def test_config_non_object_is_safe(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'settings.json';p.write_text('[]')
            with patch.dict('os.environ',{'EFFORTLESS_CODEX_CONFIG':str(p)}):
                self.assertIsInstance(control.load(),dict)
                self.assertFalse(control.load()['auto'])

    def test_all_transport_flags_must_be_stdio(self):
        self.assertFalse(routed_transport(['app-server','--listen','stdio://','--listen','tcp://127.0.0.1:99']))

    def test_dangling_launcher_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);p=home/'.local/bin/effortless-codex';p.parent.mkdir(parents=True)
            target=home/'outside';p.symlink_to(target)
            with self.assertRaises(FileExistsError):install_files(home,'/python','/main','/judge','gpt-6.1-sol')
            self.assertFalse(target.exists())

    def test_dangling_service_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);p=home/'Library/LaunchAgents/local.effortless-codex.environment.plist';p.parent.mkdir(parents=True)
            target=home/'outside';p.symlink_to(target)
            with self.assertRaises(FileExistsError):install_files(home,'/python','/main','/judge','gpt-6.1-sol')
            self.assertFalse(target.exists())

    def test_uninstall_preserves_edited_skill_and_new_environment(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);result=install_files(home,'/python','/main','/judge','gpt-6.1-sol')
            skill=Path(result['skill']);(skill/'personal.md').write_text('keep me')
            from subprocess import CompletedProcess
            calls=[]
            def run(args,**kwargs):
                calls.append(args);return CompletedProcess(args,0,stdout='/new-user-choice\n',stderr='')
            with patch.dict('os.environ',{'EFFORTLESS_CODEX_CONFIG':result['config']}),patch('subprocess.run',side_effect=run):uninstall()
            self.assertTrue(skill.exists())
            self.assertFalse(any(x[1] in {'setenv','unsetenv'} for x in calls))

class AdditionalRegression(unittest.IsolatedAsyncioTestCase):
    async def test_backend_exit_closes_wrapper_without_waiting_for_client_input(self):
        import os,sys
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);backend=root/'fake-codex';backend.write_text('#!/bin/sh\nexit 0\n');backend.chmod(0o755)
            config=root/'settings.json';config.write_text(json.dumps({'real_cli':str(backend),'auto':False,'data_dir':td}))
            entry=Path(__file__).resolve().parents[1]/'entry.py'
            child=await asyncio.create_subprocess_exec(sys.executable,str(entry),'app-server','--stdio',stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,env=dict(os.environ,EFFORTLESS_CODEX_CONFIG=str(config)))
            try:self.assertEqual(await asyncio.wait_for(child.wait(),3),0)
            finally:
                if child.returncode is None:child.kill();await child.wait()

class InstallationRegression(unittest.TestCase):
    def test_reinstall_accepts_only_its_auth_alias(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);args=(home,'/python','/main','/judge','gpt-6.1-sol')
            install_files(*args)
            alias=home/'.local/share/effortless-codex/judge-home/auth.json'
            alias.parent.mkdir();alias.symlink_to(home/'.codex/auth.json')
            install_files(*args)
            alias.unlink();alias.symlink_to(home/'unrelated')
            with self.assertRaises(FileExistsError):install_files(*args)

    def test_parent_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);outside=home/'outside';outside.mkdir()
            (home/'.local').symlink_to(outside)
            with self.assertRaises(FileExistsError):install_files(home,'/python','/main','/judge','gpt-6.1-sol')
            self.assertEqual(list(outside.iterdir()),[])

    def test_uninstall_restores_prior_environment_and_removes_unchanged_files(self):
        from subprocess import CompletedProcess
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);result=install_files(home,'/python','/main','/judge','gpt-6.1-sol','/prior')
            calls=[]
            def run(args,**kwargs):
                calls.append(args);return CompletedProcess(args,0,stdout=result['launcher']+'\n',stderr='')
            with patch.dict('os.environ',{'EFFORTLESS_CODEX_CONFIG':result['config']}),patch('subprocess.run',side_effect=run):uninstall()
            self.assertIn(['launchctl','setenv','CODEX_CLI_PATH','/prior'],calls)
            for key in ['launcher','skill','service','config']:self.assertFalse(Path(result[key]).exists())
            install_files(home,'/python','/main','/judge','gpt-6.1-sol')

class AttachmentRegression(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=fixtures.ProxyTests.asyncSetUp
    async def test_image_input_keeps_original_effort_without_text_only_judge(self):
        msg=turn();msg['params']['input'].append({'type':'image','url':'data:image/png;base64,example'})
        self.router.accept(msg);await self.router.drain()
        self.assertEqual(self.judge.calls,0)
        self.assertEqual(self.sent,[msg])
