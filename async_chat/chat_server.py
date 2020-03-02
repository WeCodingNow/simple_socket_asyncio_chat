from typing import List, Tuple
import asyncio

from async_utils.worker_pool import WorkerPool
from async_utils.stream_jobs import get_from_stream, send_to_stream
from async_utils.graceful_shutdown import stream_closer

# types for linter
Conn = Tuple[asyncio.StreamReader, asyncio.StreamWriter]

# корутина, которая рассылает сообщения от пользователя
# другим пользователям
async def broadcast_message(reader, msgs, msgs_context):
    # сначала ждём, пока пользователь получит все старые сообщения
    while not msgs_context['old_sent']:
        await asyncio.sleep(0.1)

    name = msgs_context['name']
    while True:
        msg = await reader.readline()
        if msg == b'':
            break

        msgs.append(f"{name}: {msg.decode('utf-8').rstrip()}")
        msgs_context['ptr'] += 1

# корутина, которая посылате пользователю
# сообщения других пользователей
async def send_msgs(writer, msgs, msgs_context):
    while True:
        while msgs_context['ptr'] < len(msgs):
            writer.write((msgs[msgs_context['ptr']] + '\n').encode('utf-8'))
            msgs_context['ptr'] += 1

        if not msgs_context['old_sent']:
            msgs_context['old_sent'] = True

        await writer.drain()
        await asyncio.sleep(0.1)

class ChatServer:
    def __init__(self, max_sessions, addr, port):
        self.max_sessions = max_sessions
        self.addr = addr
        self.port = port

        self.wp = WorkerPool(max_sessions)

        self.conn_q: asyncio.Queue[Conn] = asyncio.Queue()
        self.msgs = []

    async def _handler(self, conn_reader, conn_writer):
        await self.conn_q.put((conn_reader, conn_writer))

    async def _chat_session(self):
        reader, writer = await self.conn_q.get()
        stream_closer(writer)
        # начинается сессия чатинга одного юзера со всеми другими

        # получаем никнейм
        name = (await reader.read(100)).decode('utf-8')

        msgs_context = {'ptr': 0, 'old_sent': False, 'name': name}

        try:
            await asyncio.gather(
                broadcast_message(reader, self.msgs, msgs_context),
                send_msgs(writer, self.msgs, msgs_context),
            )
        # чтобы в случае отключения челика воркер, который обрабатывал
        # это подключение не подыхал, а брался за следующее
        except ConnectionResetError: closer_task.cancel()

    async def _init_workers(self):
        await self.wp.add_job(self._chat_session)
        await self.wp.add_job(self._chat_session)
        await self.wp.add_job(self._chat_session)
        await self.wp.add_job(self._chat_session)
        await self.wp.add_job(self._chat_session)

    async def run(self):
        await self._init_workers()
        await asyncio.start_server(self._handler, self.addr, self.port)
        await self.wp.run()
