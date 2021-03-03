from .base import DataModelBase, DataModelBuilder

from maro.backends.frame import node, NodeBase, NodeAttribute
from maro.backends.backend import AttributeType


@node("storage")
class StorageDataModel(DataModelBase):
    unit_storage_cost = NodeAttribute(AttributeType.INT)
    remaining_space = NodeAttribute(AttributeType.INT)
    capacity = NodeAttribute(AttributeType.INT)

    # original stock_levels, used to save proudct and its number
    product_list = NodeAttribute(AttributeType.INT, 1, is_list=True)
    product_number = NodeAttribute(AttributeType.INT, 1, is_list=True)

    def __init__(self):
        self._unit_storage_cost = 0
        self._capacity = 0

    def initialize(self, configs):
        if configs is not None:
            self._unit_storage_cost = configs.get("unit_storage_cost", 0)
            self._capacity = configs.get("capacity", 0)

            self.reset()

    def reset(self):
        self.unit_storage_cost = self._unit_storage_cost
        self.capacity = self._capacity

        self.remaining_space = self._capacity

        self.product_number[:] = 0
