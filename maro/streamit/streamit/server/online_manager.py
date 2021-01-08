
import asyncio
import websockets

from typing import List, Union

from ..common import MessageType
from .data_dispatcher import DataDispatcher
from .experiment import Experiment
from .experiment_manager import ExperimentManager


class OnlineManager:
    def __init__(self, experiment_manager: ExperimentManager):
        self._experiment_manager = experiment_manager

        self._current_experiment = self._experiment_manager.new_experiment(enable_dump=True)

    @property
    def live_experiment(self):
        return self._current_experiment

    def request(self, wsock: websockets.WebSocketServerProtocol, categories: List[str]):
        """Client request for a online experiment data"""
        dispatcher = DataDispatcher(wsock, categories)

        self._current_experiment.add_dispatcher(dispatcher)

        # Start dispatching coroutine, that keep pulling and pushing
        asyncio.ensure_future(dispatcher.start())

    async def process(self, data):
        """Process data"""

        msg_type = data[b"type"]
        msg_data = data[b"data"]

        # Used to hold data as 2nd return value
        ret_dat = None

        if msg_type == MessageType.BeginExperiment:
            self._current_experiment.name = msg_data[0].decode()
            self._current_experiment.scenario = msg_data[1].decode()
            self._current_experiment.topology = msg_data[2].decode()
            self._current_experiment.total_episodes = msg_data[3]
            self._current_experiment.durations = msg_data[5]

            self._current_experiment.setup()
        elif msg_type == MessageType.EndExperiment:
            await self._current_experiment.end_experiment()

            self._current_experiment = self._experiment_manager.new_experiment(enable_dump=True)
        elif msg_type == MessageType.BeginEpisode:
            ret_dat = msg_data
        elif msg_type == MessageType.Category:
            category = msg_data[0].decode()
            is_time_depend = msg_data[1]
            data_type = msg_data[2]

            await self._current_experiment.add_category(category, [header.decode()
                                                             for header in msg_data[3:]], is_time_depend, data_type)

            ret_dat = category
        elif msg_type == MessageType.Data:
            await self._current_experiment.put(msg_data)

        return msg_type, ret_dat
