from typing import List, Tuple
from maro.backends.frame import NodeBase, FrameBase, FrameNode


class NodeInfo:
    number
    arguments

    def __init__(self):
        self.number = 0
        self.arguments = {}

    def add_argument(self, name: str, value: int):
        if name in self.arguments:
            # leave max value.
            self.arguments[name] = max(self.arguments[name], value)


class FrameBuilder:
    def __init__(self):
        self.node_info_collection = {}

    def add_node_info(self, name: str, arguments: dict = None):
        if name not in self.node_info:
            self.node_info_collection[name] = NodeInfo()

        node_info = self.node_info_collection[name]

        node_index = node_info.number

        node_info.number += 1

        if arguments is not None:
            for name, value in arguments.items():
                node_info.add_argument(name, value)

        return node_index


class NodeDefWrapper:
    builder: FrameBuilder

    def __init__(self, name: str, arguments: dict):
        self.node_name = name
        self.node_index = self.builder.add_node_info(name, arguments)

    def get_instance(self, frame):
        pass

def build_frame(enable_snapshot: bool, total_snapshots: int, nodes: List[Tuple[NodeBase, name, int]]):
    class Frame(FrameBase):
        def __init__(self):
            # Inject the node definition to frame to support add node dynamically.
            for node_cls, name, number in nodes.items():
                setattr(Frame, name, FrameNode(node_cls, number))

            super().__init__(enable_snapshot=enable_snapshot, total_snapshot=total_snapshots)

    return Frame()
