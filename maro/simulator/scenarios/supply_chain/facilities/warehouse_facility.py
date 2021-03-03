
from collections import namedtuple, defaultdict

from .base import FacilityBase


class WarehouseFacility(FacilityBase):
    Sku = namedtuple("Sku", ("name", "id", "price", "delay_order_penalty"))

    storage = None
    transports = None
    distribution = None

    def initialize(self, config: dict):
        """We expect that the configuration like following:

        WarehouseFacility1:
            class: WarehouseFacility
            configs:
                storage:
                    class: "StorageUnit"
                    capacity: 1000
                    cost_per_unit: 100
                transports:
                    - class: "TransportUnit"
                      patient: 100
                    - class: "AnotherTransportUnit"
                      patient: 100
                distribution:
                    class: "TransportUnit"
                    unit_price: 0
                skus:
                    sku1:
                        price: 100
                        delay_order_penalty: 1000
                    sku2:
                        price: 100
                        delay_order_penalty: 1000


        """
        self.sku_in_stock = {}

        # Construct the sku information of this facility.
        for sku_name, sku_detail in config["skus"].items():
            sku_info = self.world.sku_info[sku_name]

            sku = WarehouseFacility.Sku(
                sku_name,
                sku_info.id,
                sku_detail["price"],
                sku_detail["delay_order_penalty"]
            )

            self.sku_in_stock[sku_info.id] = sku

        self.storage = self.world.build_entity(config["storage"]["class"])

        self.storage.data.initialize(config["storage"])

        self.transports = []

        for transport_detail in config["transports"]:
            transport = self.world.build_entity(transport_detail["class"])

            transport.data.initialize(config["transports"])

            self.transports.append(transport)

        self.distribution = self.world.build_entity(config["storage"]["class"])

        self.distribution.data.initialize(config["storage"])
