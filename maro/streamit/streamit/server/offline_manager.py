
import asyncio
import websockets

from typing import List, Union

from .data_dispatcher import DataDispatcher
from .experiment import Experiment
from .experiment_manager import ExperimentManager


class OfflineManager:
    def __init__(self, experiment_manager: ExperimentManager):
        self._experiment_manager = experiment_manager

    async def request(self, wsock: websockets.WebSocketServerProtocol, experiment: str, categories: List[str]):
        pass

    def _start_read_file_task(self, experiment):
        # start a task that read file, and fill its experiment data
        pass