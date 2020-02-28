import argparse
import socket

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", dest='addr', default='localhost')
    parser.add_argument("-p", dest='port', default='4000')
    parser.add_argument("-n", dest='name', default='guest')

    return parser.parse_args()

def main():
    args = get_args()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.addr, int(args.port)))

    name = args.name

    s.send(bytes(name, encoding='utf-8'))
    ret_msg = s.recv(1024).decode('utf-8')

    if ret_msg == 'you connected succesfully':
        print('wow, my podklyuchilis')
        for msg in iter(input, None):
            s.send(f'{name}: msg'.encode('utf-8'))
            messages = s.recv(1024)
            print(messages)
        # начинаем чатиться

if __name__ == "__main__":
    main()