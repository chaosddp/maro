from typing import List, Tuple
from maro.backends.frame import NodeBase, FrameBase, FrameNode


def build_frame(enable_snapshot: bool, total_snapshots: int, nodes: List[Tuple[NodeBase, name, int]]):
    class Frame(FrameBase):
        def __init__(self):
            # Inject the node definition to frame to support add node dynamically.
            for node_cls, name, number in node.items():
                setattr(Frame, name, FrameNode(node_cls, number))

            super().__init__(enable_snapshot=enable_snapshot, total_snapshot=total_snapshots)

    return Frame()