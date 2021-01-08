"""

Used to hold data of an experiment.

"""
import os
import asyncio
import websockets
import aiofiles

from typing import List

from collections import defaultdict


from .data_dispatcher import DataDispatcher
from ..common import DataType


"""

Data of an experiment, experiment will only hold data of one tick, then send to dispatcher
at the end of tick.


"""

import os
import aiofiles
from ..common import DataType

# TODO: override with argv
DATA_DIR = "./data"

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)


class CategoryState:
    file_handler = None
    is_header_write = False
    is_data_write = False
    data_type = DataType.csv
    is_time_depend = True
    cache = []


class Experiment:
    name: str = None
    scenario: str = None
    topology: str = None
    total_episodes: int = 0
    durations: int = 0

    def __init__(self, experiment_manager, enable_dump=False):
        # Categories of current experiment
        self._categories = {}

        # Dispatchers that will dispatch data for current experiment.
        self._dispatchers = []

        # Experiment manager, used to remove current experient
        self._experiment_manager = experiment_manager

        self._is_enable_dump = enable_dump

        # File handlers for each category
        # category name -> state
        self._category_write_state = {}

    def setup(self):
        """Called after BeginExperiment message"""
        if self._is_enable_dump:
            os.mkdir(os.path.join(DATA_DIR, self.name))

    def remove_dispatcher(self, wsock):
        for i in range(len(self._dispatchers)):
            dispatcher = self._dispatchers[i]

            if dispatcher.remote_address == wsock.remote_address:
                # Stop push dispatching
                self._dispatchers.remove(dispatcher)
                dispatcher.stop()

    def add_dispatcher(self, dispatcher: DataDispatcher):
        """Add a dispatcher that want data of current experiment."""
        self._dispatchers.append(dispatcher)

    async def add_category(self, name: str, headers: List[str] = None, is_time_depend=True, data_type=DataType.csv):
        """Add category and its header of current experiment"""
        if self._is_enable_dump and name not in self._categories:
            category_file = os.path.join(DATA_DIR, self.name, f"{name}.txt")
            category_fp = await aiofiles.open(category_file, mode="w+", newline="\n")

            state = CategoryState()
            state.file_handler = category_fp
            state.is_time_depend = is_time_depend
            state.data_type = data_type

            # Write headers if no data writed
            if headers and not state.is_header_write and not state.is_data_write:
                if state.is_time_depend:
                    await category_fp.write(f"episode,tick,")
                await category_fp.write(",".join(headers))
                await category_fp.write("\n")

            self._category_write_state[name] = state

        self._categories[name] = headers

    def get_category(self, name: str) -> List[str]:
        """Get category header by name."""
        return self._categories.get(name)

    def get_category_names(self) -> List[str]:
        return [c for c in self._categories.keys()]

    async def put(self, data: object):
        """Put data into current experiment for dispatch."""
        if self._is_enable_dump:
            epsiode, tick, data_list = data

            for category_data in data_list:
                category = category_data[0].decode()

                if category not in self._category_write_state:
                    self.add_category(category)

                state = self._category_write_state.get(category, None)

                if state is not None:
                    # For csv
                    if state.data_type == DataType.csv:
                        data_to_dump = []
                        if state.is_time_depend:
                            # await state.file_handler.write(f"{epsiode},{tick},")
                            data_to_dump.extend((epsiode, tick))
                        data_to_dump.extend(category_data[1:])

                        state.cache.append(",".join([str(item) for item in data_to_dump]))
                        state.cache.append("\r")

                        if len(state.cache) > 100:
                            await state.file_handler.writelines(state.cache)
                            state.cache.clear()

        await self._send_data(data)

    async def end_experiment(self):
        """End of experiment, push all data to client"""

        # Tell dispatchers we are stopping, but they may not stop immediately, if the queue is not empty
        for dispathcer in self._dispatchers:
            dispathcer.stop()

        # Clear the referentce of dispatchers, make sure there will be gc collected.
        self._dispatchers.clear()

        # Tell experiment buffer remove self
        self._experiment_manager.remove(self)

        for category, state in self._category_write_state.items():
            print("Closing file for category:", category)

            if len(state.cache) > 0:
                await state.file_handler.writelines(state.cache)
                await state.file_handler.close()
                state.cache.clear()

        self._category_write_state.clear()

        # TODO: call post-process scripts that process data of current experiment.

    async def _send_data(self, data):
        """Send data to dispatchers"""
        if data:
            for dispatcher in self._dispatchers:
                await dispatcher.send(data)