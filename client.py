import asyncio

from aiostdio import make_stdio
from worker_pool import WorkerPool
from stream_jobs import get_from_stream, send_to_stream
from graceful_shutdown import graceful_main as main

from argparse import ArgumentParser

def get_args():
    ap = ArgumentParser('client')
    ap.add_argument('-a', dest='addr', default='localhost')
    ap.add_argument('-p', dest='port', default='4000')
    ap.add_argument('-n', dest='name', default='guest')

    return ap.parse_args()

async def async_main():
    stdin, stdout, closer = await make_stdio()
    asyncio.create_task(closer())

    conn_reader, conn_writer = await asyncio.open_connection(
        (args := get_args()).addr, args.port)

    # посылаем имя
    conn_writer.write(args.name.encode('utf-8'))
    await conn_writer.drain()

    wp = WorkerPool(4)

    msg_q: asyncio.Queue[str] = asyncio.Queue()
    net_msg_q: asyncio.Queue[str] = asyncio.Queue()

    await wp.add_job(lambda: get_from_stream(msg_q, stdin))
    await wp.add_job(lambda: send_to_stream(msg_q, conn_writer))

    await wp.add_job(lambda: get_from_stream(net_msg_q, conn_reader))
    await wp.add_job(lambda: send_to_stream(net_msg_q, stdout))

    await wp.run()

if __name__ == "__main__":
    main(async_main)
