import asyncio

from async_utils.aiostdio import make_stdio
from async_utils.worker_pool import WorkerPool
from async_utils.stream_jobs import get_from_stream, send_to_stream

from argparse import ArgumentParser

class ChatClient:
    def __init__(self, addr, port, name):
        self.addr = addr
        self.port = port
        self.name = name

        self.wp = WorkerPool(4)

        self.msg_q: asyncio.Queue[str] = asyncio.Queue()
        self.net_msg_q: asyncio.Queue[str] = asyncio.Queue()
    
    async def _net_msg_handler(self, stdout):
        try:
            msg = await self.net_msg_q.get()
            stdout.write(msg)
            await stdout.drain()
        except EOFError:
            self.wp.close()

    async def run(self):
        stdin, stdout = await make_stdio()

        conn_reader, conn_writer = await asyncio.open_connection(
            self.addr, self.port)

        # посылаем имя
        conn_writer.write(self.name.encode('utf-8'))
        await conn_writer.drain()

        await self.wp.add_job(lambda: get_from_stream(self.msg_q, stdin))
        await self.wp.add_job(lambda: send_to_stream(self.msg_q, conn_writer))

        await self.wp.add_job(lambda: get_from_stream(self.net_msg_q, conn_reader))
        await self.wp.add_job(lambda: self._net_msg_handler(stdout))
        # await self.wp.add_job(lambda: send_to_stream(self.net_msg_q, stdout))

        await self.wp.run()
