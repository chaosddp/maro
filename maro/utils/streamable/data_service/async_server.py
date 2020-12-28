import json
import random
import datetime
import asyncio
import struct
import websockets


DATA_TYPE_CATEGORY = 0
DATA_TYPE_CSV = 1

MSG_MASK_MESSAGE_LENGTH = 4

# data is grouped as:
# experiment name ->  episode -> category -> rows
data_dict = {}

# experiment name ->  category -> meta
category_dict = {}


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    while True:
        length = await recvall(reader, MSG_MASK_MESSAGE_LENGTH)

        if length is None:
            writer.close()
            break

        length = struct.unpack(">I", length)[0]

        data = await recvall(reader, length)

        await dispatch_data(data)


async def recvall(reader: asyncio.StreamReader, n: int):
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


async def dispatch_data(data: bytearray):
    global data_dict

    if data is not None:
        msg = data.decode()

        items = msg.split(",")

        item_type = int(items[0])
        item_experiment = items[1]

        if item_type == DATA_TYPE_CATEGORY:
            item_category = items[2]

            # adding a new category
            if item_experiment not in category_dict:
                category_dict[item_experiment] = {}

            category_dict[item_experiment][item_category] = items[3:]

            await notify_category(item_experiment, item_category, items[3:])
        elif item_type == DATA_TYPE_CSV:
            item_category = items[3]
            item_episode = int(items[2])

            # ensure experiment name and episode exist
            if item_experiment not in data_dict:
                data_dict[item_experiment] = {}

                # notify about new experiment
                await notify_experiments(item_experiment)

            experiment_data = data_dict[item_experiment]

            if item_episode not in experiment_data:
                experiment_data[item_episode] = {}

                # notify about new episode
                await notify_episode(item_experiment, item_episode)

            episode_data = experiment_data[item_episode]

            # ensure category
            if item_category not in episode_data:
                episode_data[item_category] = []

            category_data = episode_data[item_category]

            category_data.append(items[4:])

            await notify_new_row(item_experiment, item_episode, item_category, int(items[4]), items[5:])

# web sockets

connected_clients = []


async def notify_experiments(expmt: str):
    if connected_clients:
        msg = json.dumps({"type": "new_expmt", "data": expmt})
        await asyncio.wait([client.send(msg) for client in connected_clients])


async def notify_episode(expmt: str, ep: int):
    if connected_clients:
        msg = json.dumps({"type": "new_eps", "data": [expmt, ep]})
        await asyncio.wait([client.send(msg) for client in connected_clients])


async def notify_category(expmt: str, category: str, field_names):
    if connected_clients:
        msg = json.dumps({"type": "new_cat", "exmpt": expmt,
                          "cat": category, "data":field_names})
        await asyncio.wait([client.send(msg) for client in connected_clients])


async def notify_new_row(expmt: str, episode, category, tick, data):
    # group data here

    if connected_clients:
        msg = json.dumps({"type": "row", "exmpt": expmt, "ep": episode,
                          "cat": category, "tick": tick, "data": data})
        await asyncio.wait([client.send(msg) for client in connected_clients])


async def wsok_conntected(wsock, path):
    connected_clients.append(wsock)

    try:
        while True:
            # now = datetime.datetime.utcnow().isoformat() + "Z"

            # await wsock.send(now)
            await asyncio.sleep(random.random() * 3)
    finally:
        connected_clients.remove(wsock)


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8888

    loop = asyncio.get_event_loop()

    # start data recieving service
    data_server_coroutine = asyncio.start_server(
        client_connected, host=host, port=port, loop=loop)
    data_server = loop.run_until_complete(data_server_coroutine)

    # start websocket service
    web_socket_server_coroutine = websockets.serve(
        wsok_conntected, "127.0.0.1", 8889)
    web_socket_server = loop.run_until_complete(web_socket_server_coroutine)

    try:
        loop.run_forever()
    except KeyboardInterrupt as ex:
        pass

    data_server.close()
    web_socket_server.close()
    loop.run_until_complete(data_server.wait_closed())
    loop.run_until_complete(web_socket_server.wait_closed())
    loop.close()

    print(data_dict)
    print(category_dict)
