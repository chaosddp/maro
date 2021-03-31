# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from maro.backends.backend import AttributeType
from maro.backends.rlite import FrameLite
from maro.simulator.scenarios.supply_chain_lite.actions import ManufactureAction
from functools import partial

from .skuunit import SkuUnit


class ManufactureUnit(SkuUnit):
    """Unit that used to produce certain product(sku) with consume specified source skus.

    One manufacture unit per sku.
    """

    data_model_name = "manufacture"

    data_model_attributes = {
        "product_id": (AttributeType.Int, 1, False, False),
        "id": (AttributeType.Int, 1, False, False),
        "facility_id": (AttributeType.Int, 1, False, False),
        "parent_id": (AttributeType.Int, 1, False, False),
        "output_units_per_lot": (AttributeType.Int, 1, False, False),
        "input_units_per_lot": (AttributeType.Int, 1, False, False),
        "manufacture_number": (AttributeType.Int, 1, False, False),
        "storage_id": (AttributeType.Int, 1, False, False),
        "product_unit_cost": (AttributeType.Int, 1, False, False),
        "production_rate": (AttributeType.Int, 1, False, False),
    }

    def __init__(self):
        super(ManufactureUnit, self).__init__()
        # Source material sku and related number per produce cycle.
        self.bom = None

        # How many production unit each produce cycle.
        self.output_units_per_lot = 1

        # How many unit we will consume each produce cycle.
        self.input_units_per_lot = 1

        # How many we procedure per current step.
        self.manufacture_number = 0
        self.storage_id = 0

        # Cost to produce one output production.
        self.product_unit_cost = 0

        self.production_rate = 0

    def initialize(self):
        super(ManufactureUnit, self).initialize()

        self.storage_id = self.facility.storage.id
        facility_sku_info = self.facility.skus[self.product_id]

        self.product_unit_cost = facility_sku_info.product_unit_cost

        global_sku_info = self.world.get_sku_by_id(self.product_id)

        self.bom = global_sku_info.bom
        self.output_units_per_lot = global_sku_info.output_units_per_lot

        if len(self.bom) > 0:
            self.input_units_per_lot = sum(self.bom.values())
        super().init_data_model()

    def step(self, tick: int):
        # Try to produce production if we have positive rate.
        if self.action is not None and self.action.production_rate > 0:
            sku_num = len(self.facility.skus)
            unit_num_upper_bound = self.facility.storage.capacity // sku_num

            # Compare with avg storage number.
            current_product_number = self.facility.storage.get_product_number(self.product_id)
            max_number_to_procedure = min(
                unit_num_upper_bound - current_product_number,
                self.action.production_rate * self.output_units_per_lot,
                self.facility.storage.remaining_space
            )

            if max_number_to_procedure > 0:
                space_taken_per_cycle = self.output_units_per_lot - self.input_units_per_lot

                # Consider about the volume, we can produce all if space take per cycle <=1.
                if space_taken_per_cycle > 1:
                    max_number_to_procedure = max_number_to_procedure // space_taken_per_cycle

                source_sku_to_take = {}
                # Do we have enough source material?
                for source_sku_id, source_sku_cost_number in self.bom.items():
                    source_sku_available_number = self.facility.storage.get_product_number(source_sku_id)

                    max_number_to_procedure = min(
                        source_sku_available_number // source_sku_cost_number,
                        max_number_to_procedure
                    )

                    if max_number_to_procedure <= 0:
                        break

                    source_sku_to_take[source_sku_id] = max_number_to_procedure * source_sku_cost_number

                if max_number_to_procedure > 0:
                    self.manufacture_number = max_number_to_procedure
                    self.facility.storage.try_take_products(source_sku_to_take)
                    self.facility.storage.try_add_products({self.product_id: self.manufacture_number})
        else:
            self.manufacture_number = 0

    def flush_states(self):
        if self.manufacture_number > 0:
            self.frame.update(self.data_model_name, self.data_model_index, self, "manufacture_number", self.manufacture_number)

    def post_step(self, tick: int):
        self.manufacture_number = 0

        self.production_rate = 0

        super(ManufactureUnit, self).post_step(tick)

    def set_action(self, action: ManufactureAction):
        super(ManufactureUnit, self).set_action(action)

        self.production_rate = action.production_rate