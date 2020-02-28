import socket
import argparse
import asyncio

CONN_WAIT_TIME = 1
MAX_CONNS = 5

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", dest='addr', default='localhost')
    parser.add_argument("-p", dest='port', default='4000')
    parser.add_argument("-w", dest='workers', default='5')

    return parser.parse_args()

async def server(q: asyncio.Queue, addr, port):
    # вся лабуда с сокетом
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((addr, port))
    s.settimeout(CONN_WAIT_TIME)
    s.listen(MAX_CONNS)

    while True:
        await asyncio.sleep(1)
        try:
            conn_addr = s.accept()
            await q.put(conn_addr)
        except socket.timeout: print('no new conns')


async def handler(q: asyncio.Queue, context):

    while True:
        read_messages_ptr = 0

        conn, addr = await q.get()
        name = conn.recv(1024)
        name = name.decode(encoding='utf-8')

        if name not in context['connected_users']:
            context['connected_users'].add(name)
            print(f'{name} connected')
            conn.send(b'you connected succesfully')
            conn.settimeout(CONN_WAIT_TIME)
            # начинаем пересылку сообщений между адресатами
            while True:
                try:
                    messages = conn.recv(1024).decode('utf-8')
                    for msg in messages.split('\n'):
                        print(msg)
                        context['messages'].append(msg)
                        read_messages_ptr += 1

                    if read_messages_ptr != len(context['messages']):
                        for msg in context['messages'][read_messages_ptr:-1]:
                            conn.send((msg + '\n').encode('utf-8'))
                except: ...
                await asyncio.sleep(MAX_CONNS)

        else:
            conn.send(b'go away')

async def async_main():
    args = get_args()

    context = {
        'connected_users': set(),
        'messages': list(),
    }

    q = asyncio.Queue()

    coros = [server(q, args.addr, int(args.port))]
    for _ in range(int(args.workers)):
        coros.append(handler(q, context))

    # запускаем корутины
    await asyncio.gather(*coros)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(async_main())
