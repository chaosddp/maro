# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from functools import partial
from maro.backends.backend import AttributeType
from maro.backends.rlite import FrameLite

from .product import ProductUnit
from .unitbase import UnitBase


class VehicleUnit(UnitBase):
    """Unit used to move production from source to destination by order."""

    data_model_name = "vehicle"

    data_model_attributes = {
        "id": (AttributeType.Int, 1, False, False),
        "facility_id": (AttributeType.Int, 1, False, False),
        "parent_id": (AttributeType.Int, 1, False, False),
        "position": (AttributeType.Int, 2, False, False),
        "unit_transport_cost": (AttributeType.Int, 1, False, False),
        "requested_quantity": (AttributeType.Int, 1, False, False),
        "destination_id": (AttributeType.Int, 1, False, False),
        "source": (AttributeType.Int, 1, False, False),
        "patient": (AttributeType.Int, 1, False, False),
        "quantity": (AttributeType.Int, 1, False, False),
        "velocity": (AttributeType.Int, 1, False, False),
        "payload": (AttributeType.Int, 1, False, False),
        "steps": (AttributeType.Int, 1, False, False),
        "product_id": (AttributeType.Int, 1, False, False),
    }

    def __init__(self):
        super(VehicleUnit, self).__init__()

        # Max patient of current vehicle.
        self.max_patient: int = None

        # Current products' destination.
        self.destination: ProductUnit = None

        # Path to destination.
        self.path: list = None

        # Product to load
        self.product_id = 0

        # Steps to arrive destination.
        self.steps = 0

        # Payload on vehicle.
        self.payload = 0

        # Which product unit current product related to.
        self.product: ProductUnit = None

        # Current location in the path.
        self.location = 0

        # Velocity.
        self.velocity = 0
        self.quantity = 0
        self.patient = 0
        self.source = 0

        # Id of target entity.
        self.destination_id = 0

        self.requested_quantity = 0

        self.unit_transport_cost = 0

        self.position = [-1, -1]

    def schedule(self, destination: object, product_id: int, quantity: int, vlt: int):
        """Schedule a job for this vehicle.

        Args:
            destination (FacilityBase): Destination facility.
            product_id (int): What load from storage.
            quantity (int): How many to load.
            vlt (int): Velocity of vehicle.
        """
        # Keep these in states, we will not update it until we reach the destination or cancelled.
        self.source = self.facility.id
        self.destination_id = destination.id
        self.product_id = product_id
        self.requested_quantity = quantity
        self.velocity = vlt

        # Cache.
        self.product_id = product_id
        self.destination = destination
        self.quantity = quantity

        # Find the path from current entity to target.
        self.path = self.world.find_path(
            self.facility.x,
            self.facility.y,
            destination.x,
            destination.y
        )

        if self.path is None:
            raise Exception(f"Destination {destination} is unreachable")

        # Steps to destination.
        self.steps = len(self.path) // vlt

        # We are waiting for product loading.
        self.location = 0

        self.patient = self.max_patient

    def try_load(self, quantity: int) -> bool:
        """Try to load specified number of scheduled product.

        Args:
            quantity (int): Number to load.
        """
        if self.facility.storage.try_take_products({self.product_id: quantity}):
            self.payload = quantity

            # Write to frame, as we do not need to update it per tick.
            self.payload = quantity

            return True
        else:
            return False

    def try_unload(self):
        """Try unload products into destination's storage."""
        unloaded = self.destination.storage.try_add_products(
            {self.product_id: self.payload},
            all_or_nothing=False
        )

        # Update order if we unloaded any.
        if len(unloaded) > 0:
            unloaded_units = sum(unloaded.values())

            self.destination.products[self.product_id].consumer.on_order_reception(
                self.facility.id,
                self.product_id,
                unloaded_units,
                self.payload
            )

            self.payload -= unloaded_units

    def initialize(self):
        super(VehicleUnit, self).initialize()

        self.max_patient = self.config.get("patient", 100)
        self.unit_transport_cost = self.config.get("unit_transport_cost", 1)
        self.patient = self.max_patient

        super().init_data_model()

    def step(self, tick: int):
        # If we have not arrive at destination yet.
        if self.steps > 0:
            # if we still not loaded enough productions yet.
            if self.location == 0 and self.payload == 0:
                # then try to load by requested.

                if self.try_load(self.quantity):
                    # NOTE: here we return to simulate loading
                    return
                else:
                    self.patient -= 1

                    # Failed to load, check the patient.
                    if self.patient < 0:
                        self.destination.products[self.product_id].consumer.update_open_orders(
                            self.facility.id,
                            self.product_id,
                            -self.quantity
                        )

                        self._reset_internal_states()

            # Moving to destination
            if self.payload > 0:
                # Closer to destination until 0.

                self.location += self.velocity
                self.steps -= 1

                if self.location >= len(self.path):
                    self.location = len(self.path) - 1

                self.position[:] = self.path[self.location]
        else:
            # Avoid update under idle state.
            if self.location > 0:
                # try to unload
                if self.payload > 0:
                    self.try_unload()

                # back to source if we unload all
                if self.payload == 0:
                    self._reset_internal_states()

    def flush_states(self):
        if self.payload > 0:
            self.frame.update(self.data_model_name, self.data_model_index, self, "payload", self.payload)

        # Flush if we have an order.
        if self.quantity > 0:
            self.frame.update(self.data_model_name, self.data_model_index, self, "patient", self.patient)

    def reset(self):
        super(VehicleUnit, self).reset()

        self._reset_internal_states()

    def _reset_internal_states(self):
        self.destination = None
        self.path = None
        self.payload = 0
        self.product_id = 0
        self.steps = 0
        self.location = 0
        self.quantity = 0
        self.velocity = 0
        self.patient = self.max_patient
        self.position = [-1, -1]
        self.requested_quantity = 0
        self.source = 0
        self.destination_id = 0
