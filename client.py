import asyncio
import argparse
import socket
import sys

from aioconsole import ainput

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", dest='addr', default='localhost')
    parser.add_argument("-p", dest='port', default='4000')
    parser.add_argument("-n", dest='name', default='guest')

    return parser.parse_args()

def get_info(s: socket.socket):
    ret_val = None
    try:
        ret_val = s.recv(1024)
    except socket.timeout: ...

    return ret_val

CONN_WAIT_TIME = 0.1

async def printer(s: socket.socket):
    while True:
        msgs = get_info(s)
        if msgs:
            msgs = msgs.decode('utf-8')
            for msg in msgs.split('\n'):
                print(msg)
            # sys.stdout.flush()

        await asyncio.sleep(CONN_WAIT_TIME)

# @asyncio.coroutine
async def sender(s: socket.socket):
    while True:
        data = await ainput()
        s.send(data[:-2].encode('utf-8'))


async def async_main():
    args = get_args()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.addr, int(args.port)))

    s.send(args.name.encode('utf-8'))
    ret_msg = s.recv(1024).decode('utf-8')

    if ret_msg == 'ok':
        print('wow, my podklyuchilis')
        s.settimeout(CONN_WAIT_TIME)

        await asyncio.gather(printer(s), sender(s))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(async_main())