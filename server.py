import socket
import argparse
import asyncio

CONN_WAIT_TIME = 0.1
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
            print('got a conn')
            await q.put(conn_addr)
        except socket.timeout: print('no new conns')


# обёртка для того чтобы не работать с исключениями постоянно
def get_info(s: socket.socket):
    ret_val = None
    try:
        ret_val = s.recv(1024)
    except socket.timeout: ...

    return ret_val

async def handler(q: asyncio.Queue, context):
    while True:
        # ждём клиента
        conn, addr = await q.get()

        # как нашёлся клиент, начинаем для него сессию чата
        conn.settimeout(CONN_WAIT_TIME)

        # получаем его ник
        name = get_info(conn)

        if name is None:
            continue

        name = name.decode('utf-8')
        if name in context['connected_users']:
            print(f'old client {name}')
            continue

        print(f'new client {name}')

        # начинаем сессию чата
        conn.send(b'ok')
        context['connected_users'].add(name)
        msg_ptr = 0
        while True:
            # если клиент не видел сообщения, которые есть у нас,
            # отсылаем ему сообщения
            if msg_ptr < len(context['messages']):
                for msg in context['messages'][msg_ptr:]:
                    print('tryna send an msg')
                    conn.send(f'{msg}\n'.encode('utf-8'))
                    print('sent an msg')
                    msg_ptr += 1

                # ждём сообщения от юзера
            user_msgs = get_info(conn)
            if user_msgs:
                for msg in user_msgs.decode('utf-8').split('\n'):
                    context['messages'].append(f'{name}: {msg}')
                    msg_ptr += 1

                # даём время поработать другим хэндлерам/серверу
            await asyncio.sleep(CONN_WAIT_TIME)

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
