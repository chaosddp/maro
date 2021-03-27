# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from functools import partial
from maro.backends.backend import AttributeType
from maro.backends.rlite import FrameLite
from typing import Dict

from .attr_list import AttributeList
from .unitbase import UnitBase


class StorageUnit(UnitBase):
    """Unit that used to store skus."""

    data_model_name = "storage"

    data_model_attributes = {
        "id": (AttributeType.Int, 1, False, False),
        "facility_id": (AttributeType.Int, 1, False, False),
        "parent_id": (AttributeType.Int, 1, False, False),
        "product_number": (AttributeType.Int, 1, False, True),
        "product_list": (AttributeType.Int, 1, False, True),
        "capacity": (AttributeType.Int, 1, False, False),
        "remaining_space": (AttributeType.Int, 1, False, False),
        "unit_storage_cost": (AttributeType.Int, 1, False, False),
    }

    def __init__(self):
        super(StorageUnit, self).__init__()

        # We use these variables to hold changes at python side, flash to frame before taking snapshot.
        self.product_number = AttributeList([])
        self.product_list = AttributeList([])

        # Used to map from product id to slot index.
        self.product_index_mapping: Dict[int, int] = {}
        self.capacity = 0
        self.remaining_space = 0
        self.unit_storage_cost = 0

    def try_add_products(self, product_quantities: Dict[int, int], all_or_nothing=True) -> dict:
        """Try to add products into storage.

        Args:
            product_quantities (Dict[int, int]): Dictionary of product id and quantity need to add to storage.
            all_or_nothing (bool): Failed if all product cannot be added, or add as many as it can. Default is True.

        Returns:
            dict: Dictionary of product id and quantity success added.
        """
        if all_or_nothing and self.remaining_space < sum(product_quantities.values()):
            return {}

        unloaded_quantities = {}

        for product_id, quantity in product_quantities.items():
            unload_quantity = min(self.remaining_space, quantity)

            product_index = self.product_index_mapping[product_id]
            self.product_number[product_index] += unload_quantity
            unloaded_quantities[product_id] = unload_quantity

            self.remaining_space -= unload_quantity

        return unloaded_quantities

    def try_take_products(self, product_quantities: Dict[int, int]) -> bool:
        """Try to take specified number of product.

        Args:
            product_quantities (Dict[int, int]): Dictionary of product id and quantity to take from storage.

        Returns:
            bool: Is success to take?
        """
        # Check if we can take all kinds of products?
        for product_id, quantity in product_quantities.items():
            product_index = self.product_index_mapping[product_id]

            if self.product_number[product_index] < quantity:
                return False

        # TODO: refactoring for dup code
        # Take from storage.
        for product_id, quantity in product_quantities.items():
            product_index = self.product_index_mapping[product_id]

            self.product_number[product_index] -= quantity

            self.remaining_space += quantity

        return True

    def take_available(self, product_id: int, quantity: int) -> int:
        """Take as much as available specified product from storage.

        Args:
            product_id (int): Product to take.
            quantity (int): Max quantity to take.

        Returns:
            int: Actual quantity taken.
        """
        product_index = self.product_index_mapping[product_id]
        available = self.product_number[product_index]
        actual = min(available, quantity)

        self.product_number[product_index] -= actual

        self.remaining_space += actual

        return actual

    def get_product_number(self, product_id: int) -> int:
        """Get product number in storage.

        Args:
            product_id (int): Product to check.

        Returns:
            int: Available number of product.
        """
        product_index = self.product_index_mapping[product_id]

        return self.product_number[product_index]

    def initialize(self):
        super(StorageUnit, self).initialize()

        self.capacity = self.config.get("capacity", 100)
        self.unit_storage_cost = self.config.get("unit_storage_cost", 1)
        self.remaining_space = self.capacity

        for sku in self.facility.skus.values():
            self.product_index_mapping[sku.id] = len(self.product_list)
            self.product_list.append(sku.id)
            self.product_number.append(sku.init_stock)

            self.remaining_space -= sku.init_stock

    def flush_states(self):
        pass

    def reset(self):
        super(StorageUnit, self).reset()

        self.product_number.clear()

        self.remaining_space = self.capacity

        for sku in self.facility.skus.values():
            self.product_number.append(sku.init_stock)

            self.remaining_space -= sku.init_stock
