# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


from collections import namedtuple
from typing import List, Tuple, Union

import networkx as nx

from maro.backends.lite import Frame

from .facilities import FacilityBase
from .parser import FacilityDef, SupplyChainConfiguration, UnitDef
from .units import UnitBase

SkuInfo = namedtuple("SkuInfo", ("name", "id", "bom", "output_units_per_lot"))


class World:
    """Supply chain world contains facilities and grid base map."""

    def __init__(self):
        # Frame for current world configuration.
        self.frame: Frame = None

        # Current configuration.
        self.configs: SupplyChainConfiguration = None

        # Durations of current simulation.
        self.durations = 0

        # All the units in the world.
        self.units = {}

        # All the facilities in this world.
        self.facilities = {}

        # Entity id counter, every unit and facility have unique id.
        self._id_counter = 1

        # Grid of the world
        self._graph: nx.Graph = None

        # Sku id to name mapping, used for querying.
        self._sku_id2name_mapping = {}

        # All the sku in this world.
        self._sku_collection = {}

        # Facility name to id mapping, used for querying.
        self._facility_name2id_mapping = {}

        # Data model class collection, used to collection data model class and their number in frame.
        self._data_class_collection = {}

    def get_sku_by_name(self, name: str) -> SkuInfo:
        """Get sku information by name.

        Args:
            name (str): Sku name to query.

        Returns:
            SkuInfo: General information for sku.
        """
        return self._sku_collection.get(name, None)

    def get_sku_by_id(self, sku_id: int) -> SkuInfo:
        """Get sku information by sku id.

        Args:
            sku_id (int): Id of sku to query.

        Returns:
            SkuInfo: General information for sku.
        """
        return self._sku_collection[self._sku_id2name_mapping[sku_id]]

    def get_facility_by_id(self, facility_id: int) -> FacilityBase:
        """Get facility by id.

        Args:
            facility_id (int): Facility id to query.

        Returns:
            FacilityBase: Facility instance.
        """
        return self.facilities[facility_id]

    def get_facility_by_name(self, name: str):
        """Get facility by name.

        Args:
            name (str): Facility name to query.

        Returns:
            FacilityBase: Facility instance.
        """
        return self.facilities[self._facility_name2id_mapping[name]]

    def get_unit(self, unit_id: int) -> UnitBase:
        """Get an unit by id.

        Args:
            unit_id (int): Id to query.

        Returns:
            UnitBase: Unit instance.
        """
        return self.units[unit_id]

    def find_path(self, start_x: int, start_y: int, goal_x: int, goal_y: int) -> List[Tuple[int, int]]:
        """Find path to specified cell.

        Args:
            start_x (int): Start cell position x.
            start_y (int): Start cell position y.
            goal_x (int): Destination cell position x.
            goal_y (int): Destination cell position y.

        Returns:
            List[Tuple[int, int]]: List of (x, y) position to target.
        """
        return nx.astar_path(self._graph, source=(start_x, start_y), target=(goal_x, goal_y), weight="cost")

    def build(self, configs: SupplyChainConfiguration, snapshot_number: int, durations: int):
        """Build world with configurations.

        Args:
            configs (SupplyChainConfiguration): Configuration of current world.
            snapshot_number (int): Number of snapshots to keep in memory.
            durations (int): Durations of current simulation.
        """
        self.durations = durations
        self.configs = configs

        world_config = configs.world

        # Grab sku information for this world.
        for sku_conf in world_config["skus"]:
            sku = SkuInfo(sku_conf["name"], sku_conf["id"], {}, sku_conf.get("output_units_per_lot", 1))

            self._sku_id2name_mapping[sku.id] = sku.name
            self._sku_collection[sku.name] = sku

        # Collect bom info.
        for sku_conf in world_config["skus"]:
            sku = self._sku_collection[sku_conf["name"]]

            bom = sku_conf.get("bom", {})

            for material_sku_name, units_per_lot in bom.items():
                sku.bom[self._sku_collection[material_sku_name].id] = units_per_lot

        # Construct facilities.
        for facility_conf in world_config["facilities"]:
            facility_class_alias = facility_conf["class"]
            facility_def: FacilityDef = self.configs.facilities[facility_class_alias]
            facility_class_type = facility_def.class_type

            # Instance of facility.
            facility = facility_class_type()

            # Normal properties.
            facility.id = self._gen_id()
            facility.name = facility_conf["name"]
            facility.world = self

            # Parse sku info.
            facility.parse_skus(facility_conf["skus"])

            # Parse config for facility.
            facility.parse_configs(facility_conf.get("config", {}))

            # Build children (units).
            for child_name, child_conf in facility_conf["children"].items():
                setattr(facility, child_name, self.build_unit(facility, None, child_conf))

            self.facilities[facility.id] = facility

            self._facility_name2id_mapping[facility.name] = facility.id

        # Build frame.
        self.frame = Frame(snapshot_number)

        for class_type, number in self._data_class_collection.items():
            if class_type.data_model_name is not None:
                self.frame.register_node(class_type.data_model_name, number)

                # class_type.register_data_model(self.frame)
                for attr_name, attr_def in class_type.data_model_attributes.items():
                    self.frame.register_attr(class_type.data_model_name, attr_name, attr_def[0], attr_def[1], attr_def[2], attr_def[3])

        self.frame.setup()

        # Assign data model instance.
        for unit in self.units.values():
            if unit.data_model_name is not None:
                unit.data_model_index = self.frame.bind(unit.data_model_name, unit)

        # Construct the upstream topology.
        topology = world_config["topology"]

        for cur_facility_name, topology_conf in topology.items():
            facility = self.get_facility_by_name(cur_facility_name)

            facility.upstreams = {}

            for sku_name, source_facilities in topology_conf.items():
                sku = self.get_sku_by_name(sku_name)

                facility.upstreams[sku.id] = [
                    self.get_facility_by_name(source_name) for source_name in source_facilities
                ]

        # Call initialize method for facilities.
        for facility in self.facilities.values():
            facility.initialize()

        # Call initialize method for units.
        for unit in self.units.values():
            unit.initialize()

        # TODO: replace tcod with other lib.
        # Construct the map grid.
        grid_config = world_config["grid"]

        grid_width, grid_height = grid_config["size"]

        # Build our graph base one settings.
        # This will create a full connect graph.
        self._graph = nx.grid_2d_graph(grid_width, grid_height)

        # All edge weight will be 1 by default.
        edge_weights = {e: 1 for e in self._graph.edges()}

        # Facility to cell will have 1 weight, cell to facility will have 4 cost.
        for facility_name, pos in grid_config["facilities"].items():
            facility_id = self._facility_name2id_mapping[facility_name]
            facility = self.facilities[facility_id]
            facility.x = pos[0]
            facility.y = pos[1]
            pos = tuple(pos)

            # Neighbors to facility will have hight cost.
            for npos in ((pos[0] - 1, pos[1]), (pos[0] + 1, pos[1]), (pos[0], pos[1] - 1), (pos[0], pos[1] + 1)):
                if npos[0] >= 0 and npos[0] < grid_width and npos[1] >= 0 and npos[1] < grid_height:
                    edge_weights[(npos, pos)] = 4

        nx.set_edge_attributes(self._graph, edge_weights, "cost")

    def build_unit_by_type(self, unit_type: type, parent: UnitBase, facility: FacilityBase):
        unit = unit_type()

        unit.id = self._gen_id()
        unit.parent = parent
        unit.facility = facility
        unit.world = self

        self.units[unit.id] = unit

        self._register_data_model(unit_type)

        return unit

    def build_unit(self, facility: FacilityBase, parent: UnitBase, config: dict) -> UnitBase:
        """Build an unit by its configuration.

        Args:
            facility (FacilityBase): Facility of this unit belongs to.
            parent (UnitBase): Parent of this unit belongs to, this may be same with facility, if
                this unit is attached to a facility.
            config (dict): Configuration of this unit.

        Returns:
            UnitBase: Unit instance.
        """
        unit_class_alias = config["class"]
        unit_def: UnitDef = self.configs.units[unit_class_alias]

        is_template = config.get("is_template", False)

        # If it is not a template, then just use current configuration to generate unit.
        if not is_template:
            unit_instance = unit_def.class_type()

            # Assign normal properties.
            unit_instance.id = self._gen_id()
            unit_instance.world = self
            unit_instance.facility = facility
            unit_instance.parent = parent

            # Record the id.
            self.units[unit_instance.id] = unit_instance

            # Register the data model, so that it will help to generate related instance index.
            self._register_data_model(unit_def.class_type)

            # Parse the config is there is any.
            unit_instance.parse_configs(config.get("config", {}))

            # Prepare children.
            children_conf = config.get("children", None)

            if children_conf:
                unit_instance.children = []

                for child_name, child_conf in children_conf.items():
                    # If child configuration is a dict, then we add it as a property by name (key).
                    if type(child_conf) == dict:
                        child_instance = self.build_unit(facility, unit_instance, child_conf)

                        setattr(unit_instance, child_name, child_instance)
                        unit_instance.children.append(child_instance)
                    elif type(child_conf) == list:
                        # If child configuration is a list, then will treat it as list property, named same as key.
                        child_list = []
                        for conf in child_conf:
                            child_list.append(self.build_unit(facility, unit_instance, conf))

                        setattr(unit_instance, child_name, child_list)
                        unit_instance.children.extend(child_list)

            return unit_instance
        else:
            # If this is template unit, then will use the class' static method 'generate' to generate sub-units.
            children = unit_def.class_type.generate(facility, config.get("config"))

            for child in children.values():
                child.id = self._gen_id()
                child.world = self
                child.facility = facility
                child.parent = parent

                # Pass the config if there is any.
                child.parse_configs(config.get("config", {}))

                self.units[child.id] = child

            return children

    def get_node_mapping(self):
        """Collect all the entities information.

        Returns:
            dict: A dictionary contains 'mapping' for id to data model index mapping,
                'detail' for detail of units and facilities.
        """
        facility_info_dict = {
            facility_id: facility.get_node_info() for facility_id, facility in self.facilities.items()
        }

        id2index_mapping = {}

        for unit_id, unit in self.units.items():
            if unit.data_model_index is not None:
                id2index_mapping[unit_id] = (unit.data_model_name, unit.data_model_index)
            else:
                id2index_mapping[unit_id] = (None, None)

        return {
            "unit_mapping": id2index_mapping,
            "skus": {sku.name: sku.id for sku in self._sku_collection.values()},
            "facilities": facility_info_dict
        }

    def _register_data_model(self, cls_type: type) -> int:
        """Register a data model alias, used to collect data model used in frame.

        Args:
            cls_type (type): Class alias defined in core.yml.

        Returns:
            int: Specified data model instance index after frame is built.
        """
        if cls_type not in self._data_class_collection:
            self._data_class_collection[cls_type] = 0

        node_index = self._data_class_collection[cls_type]

        self._data_class_collection[cls_type] += 1

        return node_index

    def _gen_id(self):
        """Generate id for entities."""
        nid = self._id_counter

        self._id_counter += 1

        return nid
