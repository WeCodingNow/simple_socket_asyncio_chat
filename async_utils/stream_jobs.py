import asyncio
import worker_pool

# поставляет сообщения из потока в очередь сообщений
async def get_from_stream(msg_q: asyncio.Queue, stream_in: asyncio.StreamReader):
    msg = await stream_in.read(100)

    if msg == b'':
        raise worker_pool.WorkerPool.StopWork

    await msg_q.put(msg)

# записывает новые сообщения из очереди сообщений в поток
async def send_to_stream(msg_q: asyncio.Queue, stream_out: asyncio.StreamWriter):
    msg = await msg_q.get()
    stream_out.write(msg)
    await stream_out.drain()

# async def time_printer(interval: int = 1):
#     await asyncio.sleep(interval)
#     print(datetime.datetime.now())
