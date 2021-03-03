from ..world import World

from .base import LogicBase
from ..entity import Entity


class SimpleTransportLogic(LogicBase):
    def __init__(self):
        self.config: dict = None

        # max patient of current one transport
        self.max_patient = None

        # current products' destination
        self.destination = None

    def initialize(self, config):
        self.config = config

    def get_metrics(self):
        pass

    def reset(self):
        self.destination = None
        self.max_patient = None

    def schedule(self, destination: Entity, product_id: int, quantity: int, vlt):
        self.data.destination = destination.id
        self.data.product_id = product_id
        self.data.requested_quantity = quantity
        self.data.vlt = vlt

        self.destination = destination
        # keep the patient, reset it after product unloaded.
        self.max_patient = self.data.patient

        # Find the path from current entity to target.
        # NOTE:
        # destination is a StorageUnit entity.
        path = self.world.find_path(
            self.entity.x, self.entity.y, destination.parent.x, destination.parent.y)

        if self.path is None:
            raise Exception(f"Destination {destination} is unreachable")

        # Steps to destinition.
        self.steps = len(path) // vlt

        # We are waiting for product loading.
        self.data.location = 0

    def try_loading(self, quantity: int):
        if self.facility.storage.try_take_units({self.data.product_id: quantity}):
            self.data.payload = quantity

            return True
        else:
            self.patient -= 1

            return False

    def try_unloading(self):
        unloaded = self.destination.storage.try_add_units(
            {self.data.product_id: self.data.payload}, all_or_nothing=False)

        if len(unloaded) > 0:
            unloaded_units = sum(unloaded.values())

            self.destination.consumer.on_order_reception(
                self.facility.id, self.data.product_id, unloaded_units, self.data.payload)

            # reset the transport's state
            self.data.payload = 0
            self.data.patient = self.max_patient

    def step(self, tick: int):
        # If we have not arrive at destination yet.
        if self.data.steps > 0:
            if self.data.location == 0 and self.data.payload == 0:
                # loading will take one tick.
                if self.try_loading(self.data.requested_quantity):
                    return
                else:
                    # Failed to load, check the patient.
                    if self.patient < 0:
                        self.destination.consumer._update_open_orders(
                            self.facility.id, self.data.product_id, -self.requested_quantity)

                        # reset
                        self.data.steps = 0
                        self.data.location = 0
                        self.data.destination = 0

            # Moving to destinition
            if self.data.payload > 0:
                # Closer to destinition until 0.
                self.data.location += 1
                self.data.steps -= 1
        else:
            # try to unload
            if self.data.payload > 0:
                self.try_unloading()

            # back to source if we unload all
            if self.data.payload == 0:
                self.destination = 0
                self.data.steps = 0
                self.data.location = 0
                self.data.destination = 0
