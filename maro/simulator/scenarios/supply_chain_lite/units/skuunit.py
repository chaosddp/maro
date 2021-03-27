# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


from .unitbase import UnitBase


class SkuUnit(UnitBase):
    """A sku related unit."""

    # Product id (sku id), 0 means invalid.
    product_id: int = 0

    def __init__(self):
        super(SkuUnit, self).__init__().__init__()

    def initialize(self):
        super(SkuUnit, self).initialize()

    def get_unit_info(self) -> dict:
        info = super(SkuUnit, self).get_unit_info()

        info["sku_id"] = self.product_id

        return info
