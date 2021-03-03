
from collections import dqueue, defaultdict

from ..world import World

from .base import LogicBase
from ..entity import Entity

from typing import Dict


class Order:
    destination = None
    product_id = None
    quantity = None
    vlt = None


class DistributionLogic(LogicBase):
    def __init__(self):
        self.config: dict = None

        # TODO: find a way to save it to snapshot
        self.order_queue = dqueue()

        # used to map from product id to slot index
        self.product_index_mapping: Dict[int, int] = {}

    def initialize(self, config):
        self.config = config

        for index, product_id in self.data.product_list:
            self.product_index_mapping[product_id] = index

    def step(self, tick: int):
        for vechicle in self.facility.transports:
            # if we have vechicle not enroute and pending order
            if len(self.order_queue) > 0 and vechicle.data.location == 0:
                order = self.order_queue.popleft()

                vechicle.schedule(order.destination,
                                  order.product_id, order.quantity, order.vlt)

        # NOTE: we moved delay_order_penalty from facility to sku, is this ok?
        for order in self.order_queue:
            sku = self.facility.get_sku(order.product_id)
            product_index = self.product_index_mapping[order.product_id]

            self.data.delay_order_penalty[product_index] += sku.delay_order_penalty

    def get_metrics(self):
        pass

    def reset(self):
        self.order_queue.clear()

    def get_pending_order(self):
        counter = defaultdict(int)

        for order in self.order_queue:
            counter[order.product_id] += order.quantity

        return counter

    def place_order(self, order):
        if order.quantity > 0:
            sku = self.facility.get_sku(order.product_id)

            if sku is not None:
                self.order_queue.append(order)

                product_index = self.product_index_mapping[order.product_id]
                order_total_price = sku.price * order.quantity

                self.data.checkin_price[product_index] += order_total_price

                return order_total_price

        return 0
