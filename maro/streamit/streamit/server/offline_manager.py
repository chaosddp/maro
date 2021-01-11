
import os
import asyncio
import aiofiles
import websockets
import simplejson as json

from typing import List, Union

from .data_dispatcher import DataDispatcher
from .experiment import Experiment
from .experiment_manager import ExperimentManager

from ..common import DataType, DATA_DIR


class OfflineManager:
    def __init__(self, experiment_manager: ExperimentManager):
        self._experiment_manager = experiment_manager

    def request(self, wsock: websockets.WebSocketServerProtocol, experiment_name: str, categories: List[str], episodes: List[int], delay=0):
        asyncio.ensure_future(self._start_read_file_task(wsock, experiment_name, categories, episodes, delay))

    async def _start_read_file_task(self, wsock, experiment_name, categories: List[str], episodes: List[int], delay):
        # start a task that read file, and fill its experiment data by tick
        experiment_path = os.path.join(DATA_DIR, experiment_name)

        if not os.path.exists(experiment_path):
            return

        experiment = self._experiment_manager.new_experiment()
        dispatcher = DataDispatcher(wsock, categories, episodes, delay)

        asyncio.ensure_future(dispatcher.start())

        experiment.add_dispatcher(dispatcher)

        if not os.path.exists(experiment_path):
            return

        category_states = {}

        # read meta
        meta_path = os.path.join(experiment_path, "meta.json")

        async with aiofiles.open(meta_path, mode="r") as fp:
            meta = json.loads(await fp.read())

            experiment.name = meta["name"]
            experiment.scenario = meta["scenario"]
            experiment.topology = meta["topology"]
            experiment.duration = meta["durations"]
            experiment.total_episodes = meta["total_episodes"]

            for category, category_conf in meta["categories"].items():
                category_states[category] = await experiment.add_category(
                    category,
                    category_conf["headers"],
                    category_conf["is_time_depend"],
                    DataType(category_conf["data_type"])
                )

        # open files fore interested category
        for cname, state in category_states.items():
            ext = ".txt"

            if state.data_type == DataType.csv:
                ext = ".csv"
            elif state.data_type == DataType.json:
                ext = ".json"

            state.file_handler = await aiofiles.open(os.path.join(experiment_path, f"{cname}{ext}"))

            if state.data_type == DataType.csv:
                # read the header
                await state.file_handler.readline()

        # send data that not time depend
        for cname, state in category_states.items():
            if not state.is_time_depend:
                content = await state.file_handler.read()

                await experiment.put((None, None, (cname, content)), False)

        last_episode = 0
        last_tick = 0

        for episode in range(experiment.total_episodes):
            for tick in range(durations):
                data_to_send = []
                for cname, state in category_states.items():
                    line_episode = None
                    line_tick = None

                    if state.is_time_depend:
                        async for line in state.file_handler:
                            if state.data_type == DataType.csv:
                                data = json.loads(f"[{line}]") # parse to a list

                                line_episode = data[0]
                                line_tick = data[1]
                                
                            elif state.data_type == DataType.json:
                                data = json.loads(line)

                                line_episode = data["episode"]
                                line_tick = data["tick"]

                            if line_episode == episode and line_tick == tick:
                                state.cache.append(data)
                            else:
                                data_to_send.append(data)

                            state.cache = [data]

                if len(data_to_send) > 0:
                    await experiment.put((last_episode, last_tick, data_to_send))

                last_tick = tick
            last_episode = episode

        for cname, state in category_states.items():
            print("Offline: closing category ->", cname)

            await state.file_handler.close()
