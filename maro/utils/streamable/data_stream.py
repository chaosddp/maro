"""
Client interface
"""

import os
import time

from multiprocessing import Queue

from .sender import DataSender

DATA_TYPE_CATEGORY = 0
DATA_TYPE_CSV = 1

class DataStream:
    def __init__(self, address: str, port: int):
        self._address = address
        self._port = port
        self._data_queue = Queue()
        self._cmd_queue = Queue()

        self._experiment_name = "Default experiment"
        self._episode = 0
        self._tick = 0
        self._sender = None

    def start(self, experiment_name: str):
        self._sender = DataSender(self._address, self._port, self._data_queue, self._cmd_queue)

        self._sender.start()

        self._experiment_name = experiment_name

    def episode(self, episode: int):
        self._episode = episode

    def tick(self, tick: int):
        self._tick = tick

    def csv(self, category: str, *args):

        data = (DATA_TYPE_CSV, self._experiment_name, self._episode, category, self._tick, *args)

        self._data_queue.put_nowait(data)

    def csv_object(self, obj):
        #data = obj._get_stream_data()

        #self._data_queue.put_nowait((DATA_TYPE_CSV, self._experiment_name, self._episode, data[0],  self._tick, *data[1:]))
        pass

    def category(self, name: str, *args):
        data = (DATA_TYPE_CATEGORY, self._experiment_name, name, *args)

        self._data_queue.put_nowait(data)

    def stop(self):
        if self._sender and self._sender.is_alive():
            self._cmd_queue.put("close")

            self._sender.join()

    def __del__(self):
        self.stop()

# The only interface to send data for whole program

# Check if streamable enabled
is_streamable_enabled: bool = bool(os.environ.get("MARO_STREAMABLE_ENABLED", False))

stream: DataStream = None

if not is_streamable_enabled:

    def dummy(self, *args, **kwargs):
        pass

    class StreamableDummy:
        def __getattr__(self, name):
            return dummy

    stream = StreamableDummy()
else:
    address: str = os.environ.get("MARO_STREAMABLE_DATA_SERVER_ADDRESS", None)
    port: str = os.environ.get("MARO_STREAMABLE_DATA_SERVER_PORT", None)

    if address is not None and port is not None:
        stream = DataStream(address, int(port))
        #stream.start()

