import asyncio
from argparse import ArgumentParser

from async_utils.graceful_shutdown import graceful_main as main
from async_chat import ChatClient

def get_args():
    ap = ArgumentParser('client')
    ap.add_argument('-a', dest='addr', default='localhost')
    ap.add_argument('-p', dest='port', default='4000')
    ap.add_argument('-n', dest='name', default='guest')

    return ap.parse_args()

async def async_main():
    args = get_args()

    await ChatClient(**vars(args)).run()

if __name__ == "__main__":
    main(async_main)
