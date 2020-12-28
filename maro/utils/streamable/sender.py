
import struct
import socket
import selectors

from multiprocessing import Process, Queue


class DataSender(Process):
    def __init__(self, address: str, port: int, data_queue: Queue, cmd_queue: Queue):
        super(DataSender, self).__init__()

        self._sel = selectors.DefaultSelector()
        self._sock = None
        self._port = port
        self._address = address
        self._data_queue = data_queue
        self._cmd_queue = cmd_queue
        self._should_stop = False

        self._buffer = []

    def run(self):
        while True:
            if self._sock is None:
                self._connect()
            else:
                self._collect()

                self._send()

                if self._should_stop:
                    break

            self._exec_cmd()

    def _connect(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setblocking(False)
            self._sock.connect_ex((self._address, self._port))

            self._sel.register(
                self._sock, selectors.EVENT_WRITE, self._send_data)
        except Exception as ex:
            print(ex)

    def _collect(self):
        for i in range(self._data_queue.qsize()):
            self._buffer.append(self._data_queue.get(timeout=0.1))

    def _exec_cmd(self):
        for i in range(self._cmd_queue.qsize()):
            cmd = self._cmd_queue.get_nowait()

            if cmd == "close":
                self._should_stop = True

    def _send(self):
        events = self._sel.select(timeout=1)

        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

    def _send_data(self, conn: socket.socket, mask):
        # we assume input data is a tuple that can be stringfy
        for item in self._buffer:
            msg = ",".join([str(o) for o in item])
            m = struct.pack(">I", len(msg)) + msg.encode()
            conn.sendall(m)

        self._buffer.clear()
