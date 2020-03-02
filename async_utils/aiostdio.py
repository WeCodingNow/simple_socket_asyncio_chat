import asyncio

import os
import sys

# из-за баги, которая описывается в https://bugs.python.org/issue38529
# в питоне 3.8 всё равно приходит сообщение о том,
# что мол мы не закрыли потоки

from .graceful_shutdown import stream_closer

async def make_stdio(limit=asyncio.streams._DEFAULT_LIMIT, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    reader = asyncio.StreamReader(limit=limit, loop=loop)

    reader_transport, reader_protocol = await loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(reader, loop=loop),
        os.fdopen(sys.stdin.fileno(), 'rb'))

    # чтобы убрать надоедливое исключение, которое ни о чём не сообщает
    setattr(reader_transport, 'abort', lambda: ...)

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        lambda: asyncio.streams.FlowControlMixin(loop=loop),
        os.fdopen(sys.stdout.fileno(), 'wb'))

    writer = asyncio.streams.StreamWriter(
        writer_transport, writer_protocol, None, loop)

    # stream_closer(writer)

    return reader, writer