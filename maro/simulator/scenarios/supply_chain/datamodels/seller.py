# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


from maro.backends.backend import AttributeType
from maro.backends.frame import NodeAttribute, node

from .extend import ExtendDataModel


@node("seller")
class SellerDataModel(ExtendDataModel):
    """Data model for seller unit."""
    demand = NodeAttribute(AttributeType.UInt)
    sold = NodeAttribute(AttributeType.UInt)

    total_demand = NodeAttribute(AttributeType.UInt)
    total_sold = NodeAttribute(AttributeType.UInt)

    price = NodeAttribute(AttributeType.Float, is_const=True)
    backlog_ratio = NodeAttribute(AttributeType.Float, is_const=True)

    def __init__(self):
        super(SellerDataModel, self).__init__()
        self._price = 0
        self._backlog_ratio = 0

    def initialize(self, price: int, backlog_ratio: float):
        self._price = price
        self._backlog_ratio = backlog_ratio

        self.reset()

    def reset(self):
        super(SellerDataModel, self).reset()

        self.backlog_ratio = self._backlog_ratio
        self.price = self._price
