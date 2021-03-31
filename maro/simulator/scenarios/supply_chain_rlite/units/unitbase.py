# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from functools import partial
from maro.backends.backend import AttributeType
from maro.backends.rlite import FrameLite

class UnitBase:
    """Base of all unit used to contain related logic.

    Typically one unit instance should bind to a data model instance,
    that used to update states in frame.

    An unit will have following steps to initializing.
    . Create instance with default constructor without parameter, means all unit constructor should not have parameter
        or with default value.
    . Unit.parse_configs is called with configurations from parent or config file.
    . After frame is constructed, Unit.initialize is called to do data model related initializing.
    . At the beginning of business_engine.step, Unit.step is called to go through related logic,
        then after all the agent completed, Unit.flush_state will be called at the end of business_engine.step,
        to tell agents to save their states.
    . Unit.post_step is called in business_engine.post_step after step is finished.
    . Unit.set_action is called when there is any action from out-side.

    """
    # Id of this unit.
    id: int = 0

    # Which this unit belongs to.
    facility = None

    facility_id:int = 0

    # Which world this unit belongs to.
    world = None

    # Parent of this unit, it can be a facility or another unit.
    parent: object = None

    parent_id: int = 0

    # Child units, extended unit can add their own child as property, this is used as a collection.
    children: list = None

    # Data model name in the frame, used to query binding data model instance.
    data_model_name: str = None

    data_model_index: int = None

    # Current action.
    action: object = None

    # Current unit configurations.
    config: dict = None

    frame: FrameLite = None

    # What attribute need to be saved into frame.
    # Expect a dictionary that key is the attribute name, value is a tuple (data type, slot number, is const, is list)
    data_model_attributes: dict = None

    attribute_check_list: dict = None

    def __init__(self):
        self.attribute_check_list = {}

        if self.data_model_attributes is not None:
            for attr_name in self.data_model_attributes.keys():
                self.attribute_check_list[attr_name] = True

    def parse_configs(self, config: dict):
        """Parse configurations from config.

        Args:
            config (dict): Configuration from parent or config file.
        """
        self.config = config

    def step(self, tick: int):
        """Run related logic for current tick.

        Args:
            tick (int): Current simulator tick.
        """
        pass

    def flush_states(self):
        """Flush states into frame for current tick.
        """
        pass

    def post_step(self, tick: int):
        """Post-processing for current step.

        Args:
            tick (int): Current simulator tick.
        """
        self.action = None

    def reset(self):
        """Reset this unit for a new episode."""
        pass

    def initialize(self):
        """Initialize this unit after data model is ready to use.

        NOTE: unit.data_model is available from this step.
        """
        self.facility_id = self.facility.id
        self.parent_id = 0 if self.parent is None else self.parent.id

    def set_action(self, action: object):
        """Set action for this agent.

        Args:
            action (object): Action from outside.
        """
        self.action = action

    def init_data_model(self):
        for attr_name in self.data_model_attributes.keys():
            self.frame.update(self.data_model_name, self.data_model_index, self, attr_name, getattr(self, attr_name))

    def get_unit_info(self) -> dict:
        return {
            "id": self.id,
            "node_name": self.data_model_name,
            "node_index": self.data_model_index,
            "class": type(self),
            "children": None if self.children is None else [c.get_unit_info() for c in self.children]
        }