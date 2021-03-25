# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


import numpy as np
from functools import partial
from maro.backends.lite import Frame, AttrDataType

from .skuunit import SkuUnit


class SellerUnit(SkuUnit):
    """
    Unit that used to generate product consume demand, and move demand product from current storage.
    """

    data_model_name = "seller"

    def __init__(self):
        super(SellerUnit, self).__init__()

        self.gamma = 0
        self.durations = 0
        self.demand_distribution = []

        # Attribute cache.
        self.sold = 0
        self.demand = 0
        self.total_sold = 0

    @staticmethod
    def register_data_model(frame: Frame):
        register = partial(frame.register_attr, SellerUnit.data_model_name)

        register("product_id", AttrDataType.Int)
        register("id", AttrDataType.Int)
        register("facility_id", AttrDataType.Int)
        register("parent_id", AttrDataType.Int)

        register("gamma", AttrDataType.Int)
        register("sold", AttrDataType.Int)
        register("demand", AttrDataType.Int)
        register("total_sold", AttrDataType.Int)

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

    def step(self, tick: int):
        demand = self.market_demand(tick)

        # What seller does is just count down the product number.
        sold_qty = self.facility.storage.take_available(self.product_id, demand)

        self.total_sold += sold_qty
        self.sold = sold_qty
        self.demand = demand

    def flush_states(self):
        pass

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
