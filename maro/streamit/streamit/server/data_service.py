
import os
import json
import asyncio
import websockets

from .experiment_manager import ExperimentManager
from .offline_manager import OfflineManager
from .online_manager import OnlineManager

from ..common import MessageType


class DataService:
    """Data service used to provide data clients via websockets, it support online and offline modes via command.
    For online mode, clients will not recieve any data, without command set_live_source to select interested categories.
    For offline mode, clients must provide an exist experiment name under data folder, then set_offline_source with categories.

    Commands we supported:
        1. set_live_source: {"type": "set_live_source", "categories": ["categires interested"]}
        2. set_offline_source: { "type": "set_offline_source", "experiment": "name of experiment", "categories": ["categires interested"]}
        3. cancel: {"type": "cancel"}, cancel current data recieving.
        4. experiments: {"type": "experiments"}, get all experiments under data folder with details
        5. experiment: {"type": "experiment", "experiment":"experiment name"}, get detail of an experiment
    """

    def __init__(self, data_queue: asyncio.Queue):
        # Manage all experiments that need to dispatch data
        self._experiment_manager = ExperimentManager()

        # Used to process request to recieve live data
        self._online_manager = OnlineManager(self._experiment_manager)

        # Used to process request that recieve offline data
        self._offline_manager = OfflineManager(self._experiment_manager)

        # Queue to recieve data from DataReciever
        self._data_queue = data_queue

        # All available connections
        self._connections = []

    def start(self, address: str, port: int):
        """Start data service to recieve data from reciever and dispatch data to client"""
        # Start listening
        loop = asyncio.get_event_loop()

        wsock_server = websockets.serve(
            self._on_client_connected, address, port)
        loop.run_until_complete(wsock_server)

        # Start task to collect online data.
        loop.run_until_complete(self._collect_online_data())

    async def _collect_online_data(self):
        """Task to keep recieving data from data queue"""
        while True:
            data = await self._data_queue.get()

            self._data_queue.task_done()

            msg_type, ret_data = await self._online_manager.process(data)

            # Force push to all connections
            if msg_type == MessageType.BeginExperiment:
                await self._send_msg_to_all({
                    "type": "live_experiment",
                    "data": {
                            "name": self._online_manager.live_experiment.name,
                            "scenario": self._online_manager.live_experiment.scenario,
                            "topology": self._online_manager.live_experiment.topology,
                            "durations": self._online_manager.live_experiment.durations,
                            "total_episodes": self._online_manager.live_experiment.total_episodes
                    }
                })
            elif msg_type == MessageType.BeginEpisode:
                await self._send_msg_to_all({
                    "type": "live_episode",
                    "data": ret_data
                })
            elif msg_type == MessageType.BeginTick:
                await self._send_msg_to_all({
                    "type": "live_tick",
                    "data": ret_data
                })
            elif msg_type == MessageType.Category:
                category = self._online_manager.live_experiment.get_category(
                    ret_data)

                await self._send_msg_to_all({
                    "type": "live_category",
                    "data": {
                        "name": ret_data,
                        "type": category.data_type,
                        "is_time_depend": category.is_time_depend,
                        "headers": category.headers,
                    }
                })

    async def _on_client_connected(self, wsock: websockets.WebSocketServerProtocol, path):
        """Keep recieving and processing cmd from client"""
        print("Connection from:", wsock.remote_address)

        self._connections.append(wsock)

        try:
            while True:
                cmd = await wsock.recv()

                self._process_cmd(cmd, wsock)
        except Exception as ex:
            print(ex)
        finally:
            await wsock.close()

            self._connections.remove(wsock)

            print("Connection closed from:", wsock.remote_address)

    async def _send_msg_to_all(self, msg: object):
        """Send message to all available connections"""
        if msg is not None:
            msg = json.dumps(msg)

            # We do not care about if any connection failed to recieve
            await asyncio.gather(*[conn.send(msg) for conn in self._connections])

    def _process_cmd(self, cmd: str, wsock: websockets.WebSocketServerProtocol):
        cmd = json.loads(cmd)

        cmd_type = cmd["type"]

        if cmd_type == "set_live_source":
            # online mode
            # {
            #  "type": "set_live_source"
            #  "categories": ["category 1", "category 2"]
            #  "episodes": [0, 99]
            # }
            self._online_manager.request(
                wsock, cmd["categories"], cmd["episodes"], cmd.get("delay", 0))
        elif cmd_type == "set_offline_source":
            # offline mode
            # {
            #  "type": "set_offline_source"
            #  "experiment": "experiment name"
            #  "categories": ["", ""]
            #  "episodes": [0, 99]
            # }
            print(cmd)
            self._offline_manager.request(
                wsock, cmd["experiment"], cmd["categories"], cmd["episodes"], cmd.get("delay", 0))
        elif cmd_type == "cancel":
            # cancel recieving data of current connection
            self._experiment_manager.cancel(wsock)
        elif cmd_type == "experiments":
            pass
        elif cmd_type == "experiment":
            pass
