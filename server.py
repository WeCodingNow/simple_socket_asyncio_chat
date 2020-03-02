from typing import List
import asyncio

from worker_pool import WorkerPool
from stream_jobs import get_from_stream, send_to_stream
from graceful_shutdown import graceful_main as main

from argparse import ArgumentParser

def get_args():
    ap = ArgumentParser('server')
    ap.add_argument('-a', dest='addr', default='localhost')
    ap.add_argument('-p', dest='port', default='4000')

    return ap.parse_args()

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

async def chat_session(conn_q, msgs: List[str]):
    reader, writer = await conn_q.get()
    # начинается сессия чатинга одного юзера со всеми другими

    # получаем никнейм
    name = (await reader.read(100)).decode('utf-8')

    msgs_context = {'ptr': 0, 'old_sent': False, 'name': name}

    try:
        await asyncio.gather(
            broadcast_message(reader, msgs, msgs_context),
            send_msgs(writer, msgs, msgs_context),
        )
    # чтобы в случае отключения челика воркер, который обрабатывал
    # это подключение не подыхал, а брался за следующее
    except ConnectionResetError: ...

def make_handler(conn_q):
    async def handler(conn_reader, conn_writer):
        await conn_q.put((conn_reader, conn_writer))

    return handler


async def async_main():
    args = get_args()

    conn_q: asyncio.Queue[Conn] = asyncio.Queue()

    msgs = []
    wp = WorkerPool(5)
    await wp.add_job(lambda: chat_session(conn_q, msgs))
    await wp.add_job(lambda: chat_session(conn_q, msgs))
    await wp.add_job(lambda: chat_session(conn_q, msgs))
    await wp.add_job(lambda: chat_session(conn_q, msgs))
    await wp.add_job(lambda: chat_session(conn_q, msgs))

    await asyncio.start_server(make_handler(conn_q), args.addr, args.port)
    await wp.run()


if __name__ == "__main__":
    main(async_main)
