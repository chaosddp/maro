

import asyncio
import json
from collections import defaultdict
from typing import List

import websockets


class DataDispatcher:
    """Dispatch data to related client, one dispatcher to one connection."""

    def __init__(self, wsock: websockets.WebSocketServerProtocol, categories: List[str]):
        # Connection we will send to.
        self._wsock = wsock

        # Categories we interested.
        self._categories = {}

        for category in categories:
            self._categories[category] = True

        # If we need to stop dispatching?
        self._is_stopping = False

        # Queue for pending data, grouped by tick
        self._pending_queue = asyncio.Queue()

        # Plugins to process data
        self._plugins = []

    @property
    def remote_address(self):
        """Remote address this dispatcher related to."""
        return self._wsock.remote_address

    def stop(self):
        """Stop further data dispatching."""
        self._is_stopping = True

        # NOTE: we put a tuple with None, to make "start" coroutine not be blocked by "queue.get", as the method will keep waiting
        # for next item
        self._pending_queue.put_nowait((None, None, None))

    async def start(self):
        """Coroutine to start pull data from pending queue and push it to related connection,
        this coroutine will be called after dispatcher created"""

        print("Start dispatching to", self._wsock.remote_address)

        while not self._wsock.closed:
            # We only stop pushing data after pending queue is empty, or connection closed
            if self._is_stopping and self._pending_queue.qsize() == 0:
                break

            episode, tick, data = await self._pending_queue.get()

            self._pending_queue.task_done()

            # TODO: process through plugin
            # for plugin in self._plugins:

            if data is not None:
                try:
                    await self._wsock.send(json.dumps({"type": "live_data", "data": {"episode": episode, "tick": tick, "data": data}}))
                except Exception as ex:
                    break

        # Clear the data queue before exit
        while not self._pending_queue.empty():
            _ = await self._pending_queue.get()

            self._pending_queue.task_done()

        print("Stopping dispatching to", self._wsock.remote_address)

    async def send(self, data):
        """Dend data to pending queue"""
        if data:
            episode, tick, data_list = data

            accept_data = defaultdict(list)

            for category_data in data_list:
                category = category_data[0].decode()

                if category in self._categories:
                    accept_data[category].append(category_data[1])

            if accept_data is not None and len(accept_data) > 0:
                await self._pending_queue.put((episode, tick, accept_data))
