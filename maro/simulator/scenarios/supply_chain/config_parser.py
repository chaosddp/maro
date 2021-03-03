
"""
    Parse the configuration files, and output the result.

"""

from enum import Enum
from typing import Dict, List, Union
from yaml import safe_load


class BuilderDefinition:
    class_name: str = None
    module_path: str = None
    arguments: list = None

    def __init__(self, class_name: str, module_path: str):
        self.class_name = class_name
        self.module_path = module_path
        self.arguments = []

    def add_argument(self, arg_name: int):
        self.arguments.append(arg_name)


class ClassDefinition:
    """Dynamic class definition from configuration file.
    """

    # Default configurations of this definition.
    configs: dict = None

    # Class name of the definition.
    class_name: str = None

    # Class module path, used for dynamic loading.
    module_path: str = None

    module_name: str = None

    builder: BuilderDefinition = None

    def __init__(self, class_name, module_name, module_path, configs):
        self.configs = configs
        self.class_name = class_name
        self.module_path = module_path
        self.module_name = module_name
        self.builder = None

    def __str__(self):
        return f"(ClassDefinition class:{self.class_name}, module: {self.module_path}, configs: {self.configs})"

    def __repr__(self):
        return self.__str__()


class CoreParser:
    def parse(self, config_path: str) -> dict:
        result = {}

        with open(config_path, "rt") as fp:
            core_content = safe_load(fp)

            for data_type, type_detail in core_content.items():
                class_collection = {}

                for module_name, module_detail in type_detail.items():
                    module_path = module_detail["path"]

                    for alias, definition in module_detail["definitions"].items():
                        class_def = ClassDefinition(
                            definition["class"],
                            module_name,
                            module_path,
                            definition.get("configs", None)
                        )

                        builder_detail = definition.get("builder", None)

                        if builder_detail is not None:
                            builder = BuilderDefinition(builder_detail["class"], module_path)

                            for arg in builder_detail["arguments"]:
                                builder.add_argument(arg)

                            class_def.builder = builder

                        class_collection[alias] = class_def

                result[data_type] = class_collection

        return result


class ItemDefinition:
    class_name: str = None
    configs: dict = None
    type: str = ""

    def __init__(self, class_name: str, configs: dict, type: str):
        self.class_name = class_name
        self.configs = configs
        self.type = type

    @staticmethod
    def from_config(config: dict):
        if config is None:
            return None

        return ItemDefinition(config.get("class", None), config.get("configs", None), config.get("type", None))

    def __str__(self):
        return f"(ItemDefinition class:{self.class_name}, type:{self.type}, configs:{self.configs})"

    def __repr__(self):
        return self.__str__()


class EntityDefinition:
    # Alias in in datamodels.
    data_model: ItemDefinition = None

    # Alias in logics.
    logic: ItemDefinition = None

    # Configuration of this entity
    configs: dict = None

    # Children definition.
    children: dict = None

    def __init__(self, data_model: str, logic: str, configs: dict = None):
        self.data_model = data_model
        self.logic = logic
        self.configs = configs
        self.children = {}

    def add_child(self, field_name: str, class_name: str, configs: dict = None, type: str = None):
        self.children[field_name] = ItemDefinition(class_name, configs, type)


class EntityParser:
    def parse(self, config_path: str):
        result = {}

        with open(config_path, "rt") as fp:
            config_content: dict = safe_load(fp)

            for entity_name, entity_detail in config_content.items():
                entity_def = EntityDefinition(
                    ItemDefinition.from_config(entity_detail.get("data_model", None)),
                    ItemDefinition.from_config(entity_detail.get("logic", None)),
                    entity_detail.get("configs", None))

                children_definitions = entity_detail.get("children", None)

                if children_definitions is not None:
                    for field_name, child_def in children_definitions.items():
                        entity_def.add_child(field_name, child_def["class"], child_def.get("configs", None), child_def.get("type", None))

                result[entity_name] = entity_def

        return result


class ConfigParser:
    def __init__(self):
        pass

    def parse(self, config_path: str):
        pass

    def _parse_core(self):
        pass

    def _parse_entity(self):
        pass


if __name__ == "__main__":
    core_paser = CoreParser()

    core_definitions = core_paser.parse(
        "D:/projects/python/maro/maro/simulator/scenarios/supply_chain/topologies/sample/core.yaml")

    print(core_definitions)

    entity_parser = EntityParser()

    entity_definitions = entity_parser.parse(
        "D:/projects/python/maro/maro/simulator/scenarios/supply_chain/topologies/sample/entities.yaml"
    )

    print(entity_definitions)