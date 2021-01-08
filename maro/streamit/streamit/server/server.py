
import asyncio

from .data_reciever import DataReciever
from .data_service import DataService


class Server:
    def start(self, address="127.0.0.1", recieve_port=8889, service_port=8890):
        loop = asyncio.get_event_loop()

        # Queue used to pass data
        data_queue = asyncio.Queue()

        data_reciever = DataReciever(data_queue)
        data_service = DataService(data_queue)

        print(f"starting data reciever at port {recieve_port}")

        data_reciever.start("127.0.0.1", recieve_port)

        print(f"start data service at port {service_port}")

        data_service.start("127.0.0.1", service_port)

        try:
            loop.run_forever()
        except KeyboardInterrupt as ex:
            pass
