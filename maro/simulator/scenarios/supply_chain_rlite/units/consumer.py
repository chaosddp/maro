# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from functools import partial
import warnings
from collections import Counter, defaultdict

from maro.backends.backend import AttributeType
from maro.backends.rlite import FrameLite

from .order import Order
from .skuunit import SkuUnit


class ConsumerUnit(SkuUnit):
    """Consumer unit used to generate order to purchase from upstream by action."""

    data_model_name = "consumer"

    data_model_attributes = {
        "product_id": (AttributeType.Int, 1, False, False),
        "id": (AttributeType.Int, 1, False, False),
        "facility_id": (AttributeType.Int, 1, False, False),
        "parent_id": (AttributeType.Int, 1, False, False),
        "received": (AttributeType.Int, 1, False, False),
        "purchased": (AttributeType.Int, 1, False, False),
        "order_cost": (AttributeType.Int, 1, False, False),
        "sources": (AttributeType.Int, 1, False, True),
        "total_purchased": (AttributeType.Int, 1, False, False),
        "total_received": (AttributeType.Int, 1, False, False),
        "source_id": (AttributeType.Int, 1, False, False),
        "quantity": (AttributeType.Int, 1, False, False),
        "vlt": (AttributeType.Int, 1, False, False),
        "order_product_cost": (AttributeType.Int, 1, False, False),
    }

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

    def on_order_reception(self, source_id: int, product_id: int, quantity: int, original_quantity: int):
        """Called after order product is received.

        Args:
            source_id (int): Where is the product from (facility id).
            product_id (int): What product we received.
            quantity (int): How many we received.
            original_quantity (int): How many we ordered.
        """
        self.received += quantity
        self.total_received += quantity

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

        super().init_data_model()

    def step(self, tick: int):
        # NOTE: id == 0 means invalid,as our id is 1 based.
        if not self.action or self.action.quantity <= 0 or self.action.product_id <= 0 or self.action.source_id == 0:
            return

        # NOTE: we are using product unit as destination,
        # so we expect the action.source_id is and id of product unit
        self.update_open_orders(self.action.source_id,
                                self.action.product_id, self.action.quantity)

        order = Order(self.facility, self.action.product_id,
                      self.action.quantity, self.action.vlt)

        source_facility = self.world.get_facility_by_id(self.action.source_id)

        self.order_product_cost = source_facility.distribution.place_order(
            order)

        self.purchased = self.action.quantity

        self.total_purchased += self.purchased

    def flush_states(self):
        if self.received > 0:
            self.frame.update(self.data_model_name, self.data_model_index, self, "received", self.received)
            self.frame.update(self.data_model_name, self.data_model_index, self, "total_received", self.total_received)

        if self.purchased > 0:
            self.frame.update(self.data_model_name, self.data_model_index, self, "purchased", self.purchased)
            self.frame.update(self.data_model_name, self.data_model_index, self, "total_purchased", self.total_purchased)

        if self.order_cost > 0:
            self.frame.update(self.data_model_name, self.data_model_index, self, "order_product_cost", self.order_product_cost)

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
