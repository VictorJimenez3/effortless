import json
from pathlib import Path
import sys
import tempfile
import unittest
from effortless_codex.rpc import NativeRPC

class RPCTests(unittest.IsolatedAsyncioTestCase):
    async def test_large_response_and_correlated_requests(self):
        with tempfile.TemporaryDirectory() as td:
            script=Path(td)/'server.py'
            script.write_text('import sys,json\nfor line in sys.stdin:\n d=json.loads(line)\n print(json.dumps({"id":d["id"],"result":{"value":"x"*200000}}),flush=True)\n')
            c=await NativeRPC().start([sys.executable,'-u',str(script)])
            try:
                r=await c.call('test',{})
                self.assertEqual(len(r['value']),200000)
                self.assertEqual(c.pending,{})
            finally:await c.close()

    async def test_dead_backend_fails_request_without_waiting_full_timeout(self):
        c=await NativeRPC().start([sys.executable,'-c','import sys; sys.stdin.readline()'])
        try:
            with self.assertRaises(ConnectionError):await c.call('test',{},timeout=2)
        finally:await c.close()

if __name__=='__main__':unittest.main()
