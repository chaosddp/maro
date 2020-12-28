"""

A simple python server that used to recieve csv files from exposed port,
and do:

1. save to file by experiment/episode/category
2. push to connected client via web socket.


for each message, it is format must be:

1. start with 4 bytes to identify length of this message
2. following 2 bytes to identify type: 0: greeting, 1. data (csv row)

2.1 if type is 0 (greeting), then it contains:
    experiment name
2.2 if type is 1 (data), it contains:
    episode number (4 bytes)
    category name,
    row/header seperated by ','

"""

from conf import conf

import struct
import socket
import selectors
import time


# dup from streamable
DATA_TYPE_CATEGORY = 0
DATA_TYPE_CSV = 1


MSG_MASK_MESSAGE_LENGTH = 4


def accept(sock: socket.socket, mask):
    conn, addr = sock.accept()

    print("accepted", conn, "from", addr)

    conn.setblocking(False)

    # ready for recv
    sel.register(conn, selectors.EVENT_READ, read)


def read(conn: socket.socket, mask):
    # read the message length
    length = recvall(conn, MSG_MASK_MESSAGE_LENGTH)

    if not length:
        sel.unregister(conn)
        conn.close()

        return

    length = struct.unpack(">I", length)[0]

    data = recvall(conn, length)

    dispatch_data(data)


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    try:
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
    except Exception as ex:
        print(ex)

        data = None
    return data


def dispatch_data(data: bytearray):
    if data is not None:
        msg = data.decode()

        items = msg.split(",")

        item_type = int(items[0])

        if item_type == DATA_TYPE_CATEGORY:
            # adding a new category
            print("adding category: ", items[1], " with fields: ", items[2:])
        elif item_type == DATA_TYPE_CSV:
            print("add data for category: ", items[1], " with data: ", items[2:])




async def time(websocket, path):
    while True:
        now = datetime.datetime.utcnow().isoformat() + "Z"
        await websocket.send(now)
        await asyncio.sleep(random.random() * 3)

start_server = websockets.serve(time, "127.0.0.1", 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    sel = selectors.DefaultSelector()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((conf["address"], conf["port"]))
    sock.listen()
    sock.setblocking(False)

    sel.register(sock, selectors.EVENT_READ, accept)

    while True:
        events = sel.select(timeout=1)

        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
