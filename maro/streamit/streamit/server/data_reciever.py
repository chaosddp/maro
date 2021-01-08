
import asyncio
import struct

from ..common import MessageType, parse_message


class DataReciever:
    """Used to recieve data of current live experiment from environment.
    Currently there will only one live experiment at same time, other connections will be refuced."""
    def __init__(self, data_queue: asyncio.Queue):
        # Queue that used to pass data to data service to dispatch.
        self._data_queue = data_queue

        # Name of current live experiment, we will refuse other connection that experiment not same
        self._current_experiment_name: str = None

        # If the recieve service started.
        self._is_started = False


    def start(self, address: str, port: int):
        """Start recieving data from client."""
        if self._is_started:
            return

        loop = asyncio.get_event_loop()

        # Start listening specified port.
        recieve_services = asyncio.start_server(self._on_client_connected, address, port, loop=loop)

        loop.run_until_complete(recieve_services)

        self._is_started = True

        print("Recieving data at: ", address, port)

    async def _on_client_connected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Callback when an client connected."""
        # 1st msg should be MessageType.Experiment, and its name should be same as current one, or reject it
        msg = await self._next_message(reader)

        if msg is None:
            return

        msg_type = msg[b"type"]
        exp_name = msg[b"data"][0].decode()

        if msg_type == MessageType.BeginExperiment:
            if self._current_experiment_name is None:
                self._current_experiment_name = exp_name

            if exp_name != self._current_experiment_name:
                writer.close()
                return
        else:
            # Refuse if first message is not BeginExperiment
            writer.close()
            return

        # Push the msg to dta service to dispatch.
        await self._data_queue.put(msg)

        is_experiment_end = False

        while True:
            msg = await self._next_message(reader)

            if msg is None:
                writer.close()

                # supply an end message if client does not provided
                if not is_experiment_end:
                    await self._data_queue.put({b"type": MessageType.EndExperiment, b"data": True})

                # Wait until all the data being processed
                await self._data_queue.join()

                # Ready for next experiment
                self._current_experiment_name = None

                print("waiting for next experiment")

                break

            msg_type = msg[b"type"]

            is_experiment_end = msg_type == MessageType.EndExperiment

            await self._data_queue.put(msg)

    async def _next_message(self, reader: asyncio.StreamReader) -> dict:
        msg = None
        length = await self._recvall(reader, 4)

        if length is not None:
            length = struct.unpack(">I", length)[0]
            data = await self._recvall(reader, length)

            msg = parse_message(data)

        return msg

    async def _recvall(self, reader: asyncio.StreamReader, n: int) -> bytearray:
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        try:
            while len(data) < n:
                packet = await reader.read(n - len(data))
                if not packet:
                    return None
                data.extend(packet)
        except Exception as ex:
            print(ex)

            data = None

        return data