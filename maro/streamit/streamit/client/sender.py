
import asyncio
import warnings

from ..common import build_message
from multiprocessing import Process, Queue


class ExperimentDataSender(Process):
    """Experiment data sending process."""
    def __init__(self, address: str, port: int, data_queue: Queue, cmd_queue: Queue):
        super().__init__()

        self._address = address
        self._port = port
        self._data_queue = data_queue
        self._cmd_queue = cmd_queue

        self._stopping = False

    def run(self):
        loop = asyncio.get_event_loop()

        loop.run_until_complete(self._start())

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()

    async def _start(self):
        reader = None
        writer = None
        loop = asyncio.get_event_loop()
        
        try:
            reader, writer = await asyncio.open_connection(self._address, self._port)
        except ConnectionRefusedError as conn_err:
            warnings.warn(str(conn_err))
            loop.stop()
            return

        while True:
            try:
                while not self._data_queue.empty():
                    try:
                        data = self._data_queue.get(timeout=1)

                        if data == "stop":
                            loop.stop()

                            return

                        msg = build_message(*data)
                    except Exception as ex:
                        print(ex)
                        break

                    try:
                        writer.write(msg)
                        await writer.drain()
                    except Exception as ex:
                        print(ex)
                        self._stopping = True

                if self._stopping:
                    loop.stop()
                    break

                # while not self._cmd_queue.empty():
                #     try:
                #         cmd = self._cmd_queue.get(timeout=1)
                #     except Exception as ex:
                #         print(ex)
                #         break

                #     if cmd == "stop":
                #         self._stopping = True
            except KeyboardInterrupt:
                loop.stop()
                break
