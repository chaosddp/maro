# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


import numpy as np
from functools import partial
from maro.backends.backend import AttributeType
from maro.backends.rlite import FrameLite
from .skuunit import SkuUnit


class SellerUnit(SkuUnit):
    """
    Unit that used to generate product consume demand, and move demand product from current storage.
    """

    data_model_name = "seller"

    data_model_attributes = {
        "product_id": (AttributeType.Int, 1, False, False),
        "id": (AttributeType.Int, 1, False, False),
        "facility_id": (AttributeType.Int, 1, False, False),
        "parent_id": (AttributeType.Int, 1, False, False),

        "gamma": (AttributeType.Int, 1, False, False),
        "sold": (AttributeType.Int, 1, False, False),
        "demand": (AttributeType.Int, 1, False, False),
        "total_sold": (AttributeType.Int, 1, False, False),
    }

    def __init__(self):
        super(SellerUnit, self).__init__()

        self.gamma = 0
        self.durations = 0
        self.demand_distribution = []

        # Attribute cache.
        self.sold = 0
        self.demand = 0
        self.total_sold = 0

    def market_demand(self, tick: int) -> int:
        """Generate market demand for current tick.

        Args:
            tick (int): Current simulator tick.

        Returns:
            int: Demand number.
        """
        return self.demand_distribution[tick]

    def initialize(self):
        super(SellerUnit, self).initialize()

        sku = self.facility.skus[self.product_id]

        unit_price = sku.price
        self.gamma = sku.sale_gamma
        backlog_ratio = sku.backlog_ratio

        self.durations = self.world.durations

        # Generate demand distribution of this episode.
        for _ in range(self.durations):
            self.demand_distribution.append(int(np.random.gamma(self.gamma)))

        super().init_data_model()

    def step(self, tick: int):
        demand = self.market_demand(tick)

        # What seller does is just count down the product number.
        sold_qty = self.facility.storage.take_available(self.product_id, demand)

        self.total_sold += sold_qty
        self.sold = sold_qty
        self.demand = demand

    def flush_states(self):
        if self.sold > 0:
            self.frame.update(self.data_model_name, self.data_model_index, self, "sold", self.sold)
        if self.demand > 0:
            self.frame.update(self.data_model_name, self.data_model_index, self, "demand", self.demand)
        if self.total_sold > 0:
            self.frame.update(self.data_model_name, self.data_model_index, self, "total_sold", self.total_sold)

    def post_step(self, tick: int):
        super(SellerUnit, self).post_step(tick)

        self.sold = 0
        self.demand = 0

    def reset(self):
        super(SellerUnit, self).reset()

        # TODO: regenerate the demand distribution?
        # self.demand_distribution.clear()

        # for _ in range(self.durations):
        #     self.demand_distribution.append(np.random.gamma(self.gamma))