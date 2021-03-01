
from typing import Union

from .logics.base import LogicBase
from .datamodels.base import DataModelBase


class EntityChildren:
    def __init__(self, entity):
        pass

    def from_configs(self, config: dict):
        pass

    def __getitem__(self, name: str):
        # Provide a way to get child entity easily.
        pass

    def __iter__(self):
        pass

    def __next__(self):
        pass


class Entity:
    # Current world instance.
    world = None
    # Parent entity
    parent = None
    id = None

    def __init__(self, name: str, datamodel: DataModelBase, logic: LogicBase):
        self.name = name
        self.logic = logic
        self.datamodel = datamodel
        self.children = EntityChildren(self)

    def step(self, tick: int):
        # If logic provided, then use it replace default one,
        # so it should make sure the children can be updated.
        if self.logic is not None:
            self.logic.step(tick, self)
        else:
            for child in self.children:
                child.step(tick)

    def get_metrics(self):
        return {
            self.name: None if self.logic is None else self.logic.get_metrics(),
            "children": {c.name: c.get_metrics() for c in self.children}
        }

    def _parse_config(self, config: object):
        pass
