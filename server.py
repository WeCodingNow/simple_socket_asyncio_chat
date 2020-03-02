import asyncio
from argparse import ArgumentParser

from async_utils.graceful_shutdown import graceful_main as main
from async_chat import ChatServer

def get_args():
    ap = ArgumentParser('server')
    ap.add_argument('-a', dest='addr', default='localhost')
    ap.add_argument('-p', dest='port', default=4000)
    ap.add_argument('-m', dest='max_sessions', default=5)

    return ap.parse_args()

async def async_main():
    args = get_args()

    await ChatServer(**vars(args)).run()

if __name__ == "__main__":
    main(async_main)
