from abc import ABC, abstractmethod

class FacilityBase(ABC):
    world = None
    id = None
    sku_in_stock = None

    @abstractmethod
    def initialize(self, config: dict):
        """Parse configuration, provide data model information"""
        pass

    def has_sku(self, sku_id: int):
        return sku_id in self.sku_in_stock

    def get_sku(self, sku_id: int):
        return self.sku_in_stock.get(sku_id, None)