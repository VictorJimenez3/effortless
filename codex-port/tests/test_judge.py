import asyncio
import tempfile
import unittest
from unittest.mock import AsyncMock
from effortless_codex.judge import Judge

class FakeRPC:
    def __init__(self):self.methods=[];self.started=asyncio.Event()
    async def call(self,method,params,timeout=20):
        self.methods.append(method)
        if method=='thread/start':return {'thread':{'id':'t'}}
        if method=='turn/start':self.started.set();return {'turn':{'id':'v'}}
        return {}

class JudgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_judge_interrupts_native_turn(self):
        with tempfile.TemporaryDirectory() as td:
            j=Judge('/unused',td,td);j.rpc=FakeRPC()
            j.prepare=AsyncMock();j.catalog={'gpt-6.1-sol':['low']}
            task=asyncio.create_task(j.decide({'id':'turn','prompt':'A task'},'gpt-6.1-sol'))
            await j.rpc.started.wait();task.cancel()
            await asyncio.gather(task,return_exceptions=True)
            self.assertIn('turn/interrupt',j.rpc.methods)
            self.assertEqual(j.turns,{})

if __name__=='__main__':unittest.main()
