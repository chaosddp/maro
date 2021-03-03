from .base import DataModelBase
from maro.backends.frame import node, NodeBase, NodeAttribute
from maro.backends.backend import AttributeType


@node("transport")
class TransportDataModel(DataModelBase):
    # Id of current entity
    source = NodeAttribute(AttributeType.INT)

    # Id of target entity.
    destination = NodeAttribute(AttributeType.INT)

    # Number of product.
    payload = NodeAttribute(AttributeType.INT)

    # Index of product.
    product_id = NodeAttribute(AttributeType.INT)

    requested_quantity = NodeAttribute(AttributeType.INT)

    # Patient to wait for products ready.
    patient = NodeAttribute(AttributeType.INT)

    # Steps to destination.
    steps = NodeAttribute(AttributeType.INT)

    # Current location on the way, equal to step means arrive at destination.
    location = NodeAttribute(AttributeType.INT)

    def __init__(self):
        self._patient = 0

    def initialize(self, configs: dict):
        if configs is not None:
            self._patient = configs.get("patient", 100)

            self.reset()

    def reset(self):
        self.patient = self._patient
