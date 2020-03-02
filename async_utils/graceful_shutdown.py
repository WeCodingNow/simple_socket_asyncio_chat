from typing import List, Union

import asyncio
import signal

_streams_to_close: List[asyncio.StreamWriter] = []
def stream_closer(stream: asyncio.StreamWriter):
    _streams_to_close.append(stream)

async def shutdown(signal, loop):
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]

    await asyncio.gather(*tasks, return_exceptions=True)

    # закрываем все открытые потоки
    for stream in _streams_to_close:
        stream.close()
        await stream.wait_closed()

    loop.stop()

def graceful_main(async_main):
    loop = asyncio.get_event_loop()

    for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop))
        )

    try:
        loop.create_task(async_main())
        loop.run_forever()
    finally:
        loop.close()
