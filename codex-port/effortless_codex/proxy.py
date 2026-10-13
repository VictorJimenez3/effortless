"""Transparent desktop JSONL transport and cancellation-aware routing."""
import asyncio
from copy import deepcopy
from collections import defaultdict
import json
import os
import sys
import time
from .policy import State,choose,current_pair,eligible,observe_manual,text_input

class Router:
    def __init__(self,config,judge,send,reply,status):
        self.config=config;self.judge=judge;self.send=send;self.reply=reply;self.status=status
        self.states={};self.catalog={};self.requests={};self.tasks=set()
        self.by_thread=defaultdict(set);self.locks=defaultdict(asyncio.Lock)
        self.manual_events=defaultdict(asyncio.Event);self.task_fields={}
        try:self.resume_revision=config().get('resume_revision',0)
        except (AttributeError,TypeError):self.resume_revision=0

    def state(self,tid):return self.states.setdefault(tid,State())

    def accept(self,message):
        if not isinstance(message,dict) or ('params' in message and not isinstance(message['params'],dict)):
            self.send(message);return
        method=message.get('method');p=message.get('params') or {};tid=p.get('threadId')
        if method=='turn/start' and (not isinstance(p.get('input'),list) or not all(isinstance(x,dict) for x in p['input'])):
            self.send(message);return
        if tid is not None and not isinstance(tid,str):self.send(message);return
        if tid and method in {'turn/interrupt','thread/archive','thread/delete'}:
            for task in list(self.by_thread[tid]):task.cancel()
        if tid and method in {'thread/settings/update','turn/settings/update'}:
            state=self.state(tid);observe_manual(message,state)
            if not state.auto:
                fields={k:p[k] for k in ['model','effort','collaborationMode'] if p.get(k) is not None}
                for task in list(self.by_thread[tid]):
                    self.task_fields[task]=merge_fields(self.task_fields.get(task,{}),fields)
                self.manual_events[tid].set()
                if fields.get('model'):state.model=fields['model']
                if fields.get('effort'):state.effort=fields['effort']
                self.status({'outcome':'manual_override','thread':tid})
        if isinstance(message.get('id'),(str,int)) and method:
            self.requests[message['id']]={'method':method,'threadId':tid}
        if method!='turn/start' or not tid or not isinstance(message.get('id'),(str,int)):
            self.send(message);return
        task=asyncio.create_task(self._turn(message))
        self.tasks.add(task);self.by_thread[tid].add(task)
        task.add_done_callback(self.tasks.discard)
        task.add_done_callback(self.by_thread[tid].discard)
        task.add_done_callback(lambda task:self.task_fields.pop(task,None))

    async def _turn(self,message):
        p=message['params'];tid=p['threadId'];state=self.state(tid);submitted=False
        try:
            async with self.locks[tid]:
                config=self.config()
                revision=config.get('resume_revision',0)
                if revision!=self.resume_revision:
                    for s in self.states.values():s.auto=True;s.last_routed=None
                    self.task_fields.clear()
                    self.resume_revision=revision
                allowed,outcome=eligible(message,state,config)
                decision=None
                if allowed:
                    prompt=text_input(p)
                    previous=state.recent_user
                    reply=state.recent_reply
                    model,effort=current_pair(p,state)
                    profile='sol_low' if effort=='low' else 'sol_xhigh' if effort in {'high','xhigh'} else 'sol_medium'
                    packet={'id':'turn','prompt':prompt[:8000]+('…'+prompt[-4000:] if len(prompt)>12000 else prompt[8000:]),
                            'current_profile':profile,'context':{'previous_user':previous[-1000:],'previous_reply':reply[-1000:]},
                            'current_model':model,'current_effort':effort}
                    event=self.manual_events[tid];event.clear()
                    judge_task=asyncio.create_task(self.judge.decide(packet,config.get('judge_model','gpt-6.1-sol')))
                    manual=asyncio.create_task(event.wait())
                    try:
                        done,_=await asyncio.wait([judge_task,manual],timeout=config.get('judge_timeout',12),return_when=asyncio.FIRST_COMPLETED)
                        if judge_task in done and manual not in done:decision=judge_task.result()
                        elif manual in done:outcome='manual_override'
                        else:outcome='judge_timeout'
                    except Exception:outcome='judge_error'
                    finally:
                        for task in [judge_task,manual]:
                            if not task.done():task.cancel()
                        await asyncio.gather(judge_task,manual,return_exceptions=True)
                # A picker change after submission must not be overwritten by
                # the older pending request when the judge finishes.
                source=message
                task=asyncio.current_task()
                if task in self.task_fields:
                    source=deepcopy(message);fields=self.task_fields.pop(task)
                    source['params']=merge_fields(source['params'],fields)
                    mode=source['params'].get('collaborationMode')
                    if isinstance(mode,dict) and isinstance(mode.get('settings'),dict):
                        if fields.get('model'):mode['settings']['model']=fields['model']
                        if fields.get('effort'):mode['settings']['reasoning_effort']=fields['effort']
                routed,reason=choose(source,state,decision,config,self.catalog or self.judge.catalog)
                self.send(routed);submitted=True
                state.recent_user=text_input(p)[-1000:]
                pair=current_pair(routed['params'],state)
                self.status({'outcome':outcome if outcome in {'judge_error','judge_timeout'} else reason,
                             'thread':tid,'judge':config.get('judge_model'),
                             'model':pair[0],'effort':pair[1],'pid':os.getpid()})
        except Exception:
            if not submitted:self.send(message)
            self.status({'outcome':'routing_error','thread':tid,'pid':os.getpid()})
        except asyncio.CancelledError:
            self.reply({'id':message['id'],'error':{'code':-32000,'message':'Turn cancelled before submission.'}})
            self.requests.pop(message.get('id'),None)

    def observe(self,message):
        p=message.get('params') or {};tid=p.get('threadId');method=message.get('method')
        if 'id' in message and ('result' in message or 'error' in message):
            meta=self.requests.pop(message['id'],{})
            result=message.get('result') or {}
            if meta.get('method')=='model/list':
                for m in result.get('data',[]):
                    self.catalog[m['id']]=[e['reasoningEffort'] for e in m.get('supportedReasoningEfforts',[])]
            if meta.get('method') in {'thread/start','thread/resume','thread/fork'} and result.get('thread'):
                thread=result['thread'];state=self.state(thread['id'])
                source=thread.get('sourceKind') or thread.get('source')
                state.main_thread=not (isinstance(source,dict) and 'subAgent' in source or thread.get('agentRole') or thread.get('agentNickname'))
                state.model=result.get('model') or state.model
                state.effort=result.get('reasoningEffort') or state.effort
                state.provider=result.get('modelProvider') or 'openai'
        if not tid:return
        state=self.state(tid)
        if method=='thread/settings/updated':
            settings=p.get('threadSettings') or {}
            state.model=settings.get('model') or state.model
            state.effort=settings.get('reasoningEffort') or settings.get('effort') or state.effort
        elif method=='item/completed' and p.get('item',{}).get('type')=='agentMessage':
            state.recent_reply=p['item'].get('text','')[-1000:]
        elif method=='thread/tokenUsage/updated':
            usage=p.get('tokenUsage',{}).get('last',{})
            state.tokens=usage.get('inputTokens',0)
            state.cached_tokens=usage.get('cachedInputTokens',0)

    def cancel_all(self):
        for task in list(self.tasks):task.cancel()

    async def drain(self):
        while self.tasks:await asyncio.gather(*list(self.tasks),return_exceptions=True)

async def run_stdio(real_cli,args,config,judge,status):
    env=dict(os.environ,CODEX_CLI_PATH=real_cli)
    process=await asyncio.create_subprocess_exec(real_cli,*args,stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,stderr=None,env=env,limit=64*1024*1024)
    def send(message):
        process.stdin.write((json.dumps(message,ensure_ascii=False)+'\n').encode())
    def reply(message):
        sys.stdout.buffer.write((json.dumps(message,ensure_ascii=False)+'\n').encode());sys.stdout.buffer.flush()
    router=Router(config,judge,send,reply,status)
    async def outputs():
        while line:=await process.stdout.readline():
            sys.stdout.buffer.write(line);sys.stdout.buffer.flush()
            try:router.observe(json.loads(line))
            except (ValueError,KeyError,TypeError):pass
    output_task=asyncio.create_task(outputs())
    reader=asyncio.StreamReader(limit=64*1024*1024)
    transport,_=await asyncio.get_running_loop().connect_read_pipe(lambda:asyncio.StreamReaderProtocol(reader),sys.stdin.buffer)
    status({'outcome':'connected','pid':os.getpid(),'parent_pid':os.getppid()})
    try:
        while True:
            reading=asyncio.create_task(reader.readline())
            done,_=await asyncio.wait([reading,output_task],return_when=asyncio.FIRST_COMPLETED)
            if output_task in done:
                reading.cancel();await asyncio.gather(reading,return_exceptions=True);break
            line=reading.result()
            if not line:break
            try:router.accept(json.loads(line))
            except (ValueError,KeyError,TypeError):process.stdin.write(line)
            await process.stdin.drain()
    finally:
        transport.close();router.cancel_all();await router.drain()
        if not process.stdin.is_closing():process.stdin.close()
        try:await asyncio.wait_for(process.wait(),8)
        except asyncio.TimeoutError:
            process.terminate()
            try:await asyncio.wait_for(process.wait(),4)
            except asyncio.TimeoutError:process.kill();await process.wait()
        await output_task;await judge.close()
        status({'outcome':'stopped','pid':os.getpid()})
    return process.returncode


def merge_fields(original,changes):
    result=deepcopy(original)
    for key,value in changes.items():
        if key=='collaborationMode' and isinstance(value,dict):
            mode=result.get(key)
            mode=deepcopy(mode) if isinstance(mode,dict) else {}
            for field,entry in value.items():
                if field=='settings' and isinstance(entry,dict):
                    mode[field]={**(mode.get(field) or {}),**entry}
                else:mode[field]=deepcopy(entry)
            result[key]=mode
        else:result[key]=deepcopy(value)
    return result
