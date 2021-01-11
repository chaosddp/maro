
import os
import struct
import json
import contextlib

from typing import Union
from multiprocessing import Process, Queue

from ..common import MessageType, DataType
from .sender import ExperimentDataSender


class ExperimentDataStream:
    def __init__(self):
        self._sender: ExperimentDataSender = None
        self._data_queue = Queue()
        self._cmd_queue = Queue()

        # Used to mark is current data is time depended
        self._is_time_depend_data = True

        # category name -> is time depend
        self._category_info = {}

        # episode -> tick -> data list
        self._cache = []

        self._cur_episode = 0
        self._cur_tick = 0

    @contextlib.contextmanager
    def experiment(self, name: str, scenario: str, topology: str, total_episodes: int, durations: int, start_tick: int = 0):
        self._send(MessageType.BeginExperiment, (name, scenario,
                                                 topology, total_episodes, start_tick, durations))
        yield self
        self._send(MessageType.EndExperiment, name)

    @contextlib.contextmanager
    def episode(self, episode: int):
        self._cur_episode = episode

        self._send(MessageType.BeginEpisode, episode)

        yield self

        self._send(MessageType.EndEpisode, episode)

    @contextlib.contextmanager
    def tick(self, tick: int):
        self._cur_tick = tick

        yield self

        cached_data = self._cache
        self._cache = []
        self._send(MessageType.Data, (self._cur_episode, tick, cached_data))

    # Add a category with headers
    def category(self, name: str, is_time_depend: bool, data_type: DataType, *args):
        self._send(MessageType.Category,
                   (name, is_time_depend, data_type, *args))

        self._category_info[name] = is_time_depend

    def csv(self, category: str, *args):
        """Send a list of data as csv row"""
        is_time_depend = self._category_info.get(category, True)

        if is_time_depend:
            self._cache.append((category, *args))
        else:
            self._send(MessageType.Data, (self._cur_episode, tick, category, *args))

    def json(self, category: str, jobj: Union[str, object]):
        """Send a object or a json string"""
        is_time_depend = self._category_info.get(category, True)

        json_str = jobj

        if type(jobj) is not str:
            json_str = json.dumps(jobj)

        if is_time_depend:
            self._cache.append((category, json_str))
        else:
            self._send(MessageType.Data, (self._cur_episode, self._cur_tick, [(category, json_str),]))

    def start(self, address="127.0.0.1", port=8889):
        """Connect to server, prepare to send data"""
        self._sender = ExperimentDataSender(
            address, port, self._data_queue, self._cmd_queue)

        self._sender.start()

    def close(self):
        self._data_queue.put_nowait("stop")

        self._sender.join()
        # self._data_queue.close()

    def _send(self, type: MessageType, data):
        try:
            self._data_queue.put_nowait((type, data))
        except Exception as ex:
            # If reach the limitation, then it will exception
            print(ex)

    def __del__(self):
        print("gc collecting")
        if self._sender is not None and self._sender.is_alive:
            print("waiting for close")
            self._sender.terminate()
