from .base import DataModelBase, DataModelBuilder

from maro.backends.frame import node, NodeBase, NodeAttribute
from maro.backends.backend import AttributeType


@node("distribution")
class DistributionDataModel(DataModelBase):
    unit_price = NodeAttribute(AttributeType.INT)
    remaining_space = NodeAttribute(AttributeType.INT)
    capacity = NodeAttribute(AttributeType.INT)

    # original stock_levels, used to save proudct and its number
    product_list = NodeAttribute(AttributeType.INT, 1, is_list=True)
    checkin_price = NodeAttribute(AttributeType.INT, 1, is_list=True)
    delay_order_penalty = NodeAttribute(AttributeType.INT, 1, is_list=True)

    def __init__(self):
        self._unit_price = 0
        self._capacity = 0

    def initialize(self, configs: dict):
        if configs is not None:
            self._unit_price = configs.get("unit_price", 0)
            self._capacity = configs.get("capacity", 0)

            self.reset()

    def reset(self):
        self.unit_price = self._unit_price
        self.capacity = self._capacity
