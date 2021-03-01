from .base import DataModelBase
from maro.backends.frame import node, NodeBase, NodeAttribute
from maro.backends.backend import AttributeType


@node("transport")
class TransportDataModel(DataModelBase):
    # Index of source storage unit
    source = NodeAttribute(AttributeType.UINT)

    # Index of destination storage unit
    destination = NodeAttribute(AttributeType.UINT)

    # Number of product.
    payload = NodeAttribute(AttributeType.UINT)

    # Index of product.
    product_id = NodeAttribute(AttributeType.UINT)

    # Patient to wait for products ready.
    patient = NodeAttribute(AttributeType.UINT)

    # Step to destination.
    step = NodeAttribute(AttributeType.UINT)

    # Current location on the way, equal to step means arrive at destination.
    location = NodeAttribute(AttributeType.UINT)

    def initialize(self, configs):
        pass

    def reset(self):
        pass
