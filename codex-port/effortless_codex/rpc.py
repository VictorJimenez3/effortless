"""Native Codex JSONL client; no direct provider API or copied credentials."""
import asyncio
import json

class NativeRPC:
    def __init__(self,notify=None):
        self.notify=notify or (lambda x:None);self.pending={};self.counter=0
        self.process=None;self.reader=None

    async def start(self,command,env=None,cwd=None,stderr=None):
        self.process=await asyncio.create_subprocess_exec(*command,env=env,cwd=cwd,
            stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,
            stderr=stderr,limit=64*1024*1024)
        self.reader=asyncio.create_task(self._read())
        return self

    async def send(self,message):
        if self.process.returncode is not None:raise ConnectionError('Native Codex server exited')
        self.process.stdin.write((json.dumps(message)+'\n').encode())
        await self.process.stdin.drain()

    async def call(self,method,params,timeout=20):
        self.counter+=1;ident=self.counter
        future=asyncio.get_running_loop().create_future();self.pending[ident]=future
        try:
            await self.send({'id':ident,'method':method,'params':params})
            return await asyncio.wait_for(future,timeout)
        finally:self.pending.pop(ident,None)

    async def _read(self):
        try:
            while line:=await self.process.stdout.readline():
                try:data=json.loads(line)
                except ValueError:continue
                if not isinstance(data,dict):continue
                if 'id' in data and ('result' in data or 'error' in data):
                    future=self.pending.get(data['id'])
                    if future is not None and not future.done():
                        if 'error' in data:future.set_exception(RuntimeError(data['error'].get('message','Native RPC failed')))
                        else:future.set_result(data['result'])
                else:self.notify(data)
        finally:
            for future in list(self.pending.values()):
                if not future.done():future.set_exception(ConnectionError('Native Codex connection closed'))

    async def close(self):
        if not self.process:return
        if not self.process.stdin.is_closing():self.process.stdin.close()
        try:await asyncio.wait_for(self.process.wait(),5)
        except asyncio.TimeoutError:
            self.process.terminate()
            try:await asyncio.wait_for(self.process.wait(),3)
            except asyncio.TimeoutError:self.process.kill();await self.process.wait()
        if self.reader:
            await asyncio.gather(self.reader,return_exceptions=True)
