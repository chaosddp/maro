# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from functools  import partial
import warnings
from collections import Counter, defaultdict
from maro.backends.lite import AttrDataType, Frame

from .order import Order
from .skuunit import SkuUnit


class ConsumerUnit(SkuUnit):
    """Consumer unit used to generate order to purchase from upstream by action."""

    data_model_name = "consumer"

    def __init__(self):
        super(ConsumerUnit, self).__init__()

        self.open_orders = defaultdict(Counter)

        # States in python side.
        self.received = 0
        self.purchased = 0
        self.order_cost = 0
        self.sources = []

        self.total_purchased = 0
        self.total_received = 0

        self.source_id = 0
        self.quantity = 0
        self.vlt = 0

        self.order_product_cost = 0
        self.facility_id = 0
        self.parent_id = 0

    @staticmethod
    def register_data_model(frame:Frame):
        register = partial(frame.register_attr, ConsumerUnit.data_model_name)

        register("product_id", AttrDataType.Int)
        register("id", AttrDataType.Int)
        register("facility_id", AttrDataType.Int)
        register("parent_id", AttrDataType.Int)
        register("received", AttrDataType.Int)
        register("purchased", AttrDataType.Int)
        register("order_cost", AttrDataType.Int)
        register("sources", AttrDataType.Int, is_list=True)
        register("total_purchased", AttrDataType.Int)
        register("total_received", AttrDataType.Int)
        register("source_id", AttrDataType.Int)
        register("quantity", AttrDataType.Int)
        register("vlt", AttrDataType.Int)
        register("order_product_cost", AttrDataType.Int)

    def on_order_reception(self, source_id: int, product_id: int, quantity: int, original_quantity: int):
        """Called after order product is received.

        Args:
            source_id (int): Where is the product from (facility id).
            product_id (int): What product we received.
            quantity (int): How many we received.
            original_quantity (int): How many we ordered.
        """
        self.received += quantity

        self.update_open_orders(source_id, product_id, -original_quantity)

    def update_open_orders(self, source_id: int, product_id: int, qty_delta: int):
        """Update the order states.

        Args:
            source_id (int): Where is the product from (facility id).
            product_id (int): What product in the order.
            qty_delta (int): Number of product to update (sum).
        """
        if qty_delta > 0:
            # New order for product.
            self.open_orders[source_id][product_id] += qty_delta
        else:
            # An order is completed, update the remaining number.
            self.open_orders[source_id][product_id] += qty_delta

    def initialize(self):
        super(ConsumerUnit, self).initialize()

        sku = self.facility.skus[self.product_id]

        self.order_cost = self.facility.get_config("order_cost", 0)

        if self.facility.upstreams is not None:
            # Construct sources from facility's upstreams.
            sources = self.facility.upstreams.get(self.product_id, None)

            if sources is not None:
                # Is we are a supplier facility?
                is_supplier = self.parent.manufacture is not None

                # Current sku information.
                sku = self.world.get_sku_by_id(self.product_id)

                for source_facility in sources:
                    # We are a supplier unit, then the consumer is used to purchase source materials from upstreams.
                    # Try to find who will provide this kind of material.
                    if is_supplier:
                        if source_facility.products is not None:
                            for source_sku_id in sku.bom.keys():
                                if source_sku_id in source_facility.products:
                                    # This is a valid source facility.
                                    self.sources.append(source_facility.id)
                    else:
                        # If we are not a manufacturing, just check if upstream have this sku configuration.
                        if sku.id in source_facility.skus:
                            self.sources.append(source_facility.id)

            if len(self.sources) == 0:
                warnings.warn(
                    f"No sources for consumer: {self.id}, sku: {self.product_id} in facility: {self.facility.name}.")
                return

    def step(self, tick: int):
        # NOTE: id == 0 means invalid,as our id is 1 based.
        if not self.action or self.action.quantity <= 0 or self.action.product_id <= 0 or self.action.source_id == 0:
            return

        # NOTE: we are using product unit as destination,
        # so we expect the action.source_id is and id of product unit
        self.update_open_orders(self.action.source_id, self.action.product_id, self.action.quantity)

        order = Order(self.facility, self.action.product_id, self.action.quantity, self.action.vlt)

        source_facility = self.world.get_facility_by_id(self.action.source_id)

        self.order_product_cost = source_facility.distribution.place_order(order)

        self.purchased = self.action.quantity

        self.total_purchased += self.purchased

    def flush_states(self):
        pass

    def post_step(self, tick: int):
        # Clear the action states per step.
        self.source_id = 0
        self.quantity = 0
        self.vlt = 0

        # This will set action to None.
        super(ConsumerUnit, self).post_step(tick)

        self.received = 0
        self.purchased = 0
        self.order_product_cost = 0
        self.order_cost = 0

    def reset(self):
        super(ConsumerUnit, self).reset()

        self.open_orders.clear()

    def set_action(self, action: object):
        super(ConsumerUnit, self).set_action(action)

        # record the action
        self.source_id = action.source_id
        self.quantity = action.quantity
        self.vlt = action.vlt
