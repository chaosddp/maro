
import struct

from enum import IntEnum
from msgpack import packb, unpackb


class MessageType(IntEnum):
    BeginExperiment = 0
    EndExperiment = 1
    BeginEpisode = 2
    EndEpisode = 3
    BeginTick = 4
    EndTick = 5
    Data = 6
    Category = 7


class DataType(IntEnum):
    csv = 0
    json = 1
    binary = 2


# build message with specified type and data
# NOTE: the data must can be packb
def build_message(type: MessageType, data):
    data_bin = packb({"type": type, "data": data})

    length = len(data_bin)

    return struct.pack(">I", length) + data_bin


def parse_message(msg: bytearray):
    return unpackb(msg, use_list=False)