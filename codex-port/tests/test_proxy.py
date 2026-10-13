import asyncio
import json
import unittest
from effortless_codex.proxy import Router
from effortless_codex.policy import State

CATALOG={'gpt-6.1-sol':['low','medium','high','xhigh']}

class FakeJudge:
    catalog=CATALOG
    def __init__(self):self.block=None;self.calls=0;self.error=None
    async def decide(self,packet,model):
        self.calls+=1
        if self.block:await self.block.wait()
        if self.error:raise self.error
        return {'id':'turn','profile':'sol_low','action':'route','confidence':0.95,'reason':'Test.'}
    async def close(self):pass

def turn(ident=1,text='Implement the function.'):
    return {'id':ident,'method':'turn/start','params':{'threadId':'t','model':'gpt-6.1-sol','effort':'high','input':[{'type':'text','text':text}],'sandboxPolicy':{'type':'readOnly'}}}

class ProxyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.sent=[];self.client=[];self.judge=FakeJudge()
        self.config={'auto':True,'judge_model':'gpt-6.1-sol','judge_timeout':0.05}
        self.router=Router(lambda:self.config,self.judge,self.sent.append,self.client.append,lambda x:None)
        self.router.catalog=CATALOG

    async def test_real_request_is_changed_only_after_judge(self):
        self.router.accept(turn())
        await self.router.drain()
        self.assertEqual(self.sent[0]['params']['effort'],'low')
        self.assertEqual(self.sent[0]['params']['sandboxPolicy'],{'type':'readOnly'})

    async def test_timeout_forwards_original(self):
        self.judge.block=asyncio.Event()
        msg=turn();self.router.accept(msg);await self.router.drain()
        self.assertEqual(self.sent,[msg])

    async def test_interrupt_cancels_pending_turn_and_is_never_delayed(self):
        self.judge.block=asyncio.Event()
        self.router.accept(turn());await asyncio.sleep(0)
        interrupt={'id':2,'method':'turn/interrupt','params':{'threadId':'t','turnId':'pending'}}
        self.router.accept(interrupt);await self.router.drain()
        self.assertEqual(self.sent,[interrupt])
        self.assertEqual(self.client[0]['id'],1)
        self.assertIn('error',self.client[0])

    async def test_permission_response_is_not_delayed(self):
        self.judge.block=asyncio.Event()
        self.router.accept(turn());await asyncio.sleep(0)
        answer={'id':'approval-1','result':{'decision':'accept'}}
        self.router.accept(answer)
        self.assertEqual(self.sent,[answer])
        self.router.cancel_all();await self.router.drain()

    async def test_manual_picker_change_cancels_stale_judge_without_losing_prompt(self):
        self.judge.block=asyncio.Event()
        msg=turn();self.router.accept(msg);await asyncio.sleep(0)
        manual={'id':2,'method':'thread/settings/update','params':{'threadId':'t','effort':'medium'}}
        self.router.accept(manual)
        self.judge.block.set();await self.router.drain()
        self.assertEqual(self.sent[0],manual)
        self.assertEqual(self.sent[1]['params']['effort'],'medium')
        self.assertFalse(self.router.states['t'].auto)

    async def test_same_thread_prompt_order_preserved(self):
        self.router.accept(turn(1));self.router.accept(turn(2,'Implement another function.'))
        await self.router.drain()
        self.assertEqual([x['id'] for x in self.sent],[1,2])

    async def test_auto_disabled_skips_judge(self):
        self.config['auto']=False
        self.router.accept(turn());await self.router.drain()
        self.assertEqual(self.judge.calls,0)
        self.assertEqual(self.sent,[turn()])

    async def test_settings_notifications_update_effective_state(self):
        self.router.observe({'method':'thread/settings/updated','params':{'threadId':'t','threadSettings':{'model':'gpt-6.1-sol','reasoningEffort':'low'}}})
        self.assertEqual(self.router.states['t'].effort,'low')

    async def test_large_prompt_is_not_truncated_for_worker(self):
        msg=turn(text='x'*200000)
        self.router.accept(msg);await self.router.drain()
        self.assertEqual(self.sent[0]['params']['input'][0]['text'],'x'*200000)

    async def test_judge_exception_forwards_original(self):
        self.judge.error=ValueError('invalid JSON')
        msg=turn();self.router.accept(msg);await self.router.drain()
        self.assertEqual(self.sent,[msg])

    async def test_malformed_client_messages_go_to_backend_without_crashing(self):
        for msg in [None,[],{'method':'turn/start','params':'bad'},
                    {'id':1,'method':'turn/start','params':{'threadId':'t','input':'bad'}}]:
            self.router.accept(msg)
            self.assertEqual(self.sent[-1],msg)

if __name__=='__main__':unittest.main()
