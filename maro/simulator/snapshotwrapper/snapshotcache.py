
from abc import ABC, abstractmethod
from typing import List
from maro.simulator import AbsEnv
from collections import defaultdict


class _CacheAttrDef:
    def __init__(self, offset: int, slots: int):
        self.offset = offset
        self.slots = slots


class SnapshotCacheABC(ABC):
    def __init__(self):
        self._env = None
        # current cache tick
        self._current_cache_frame_index = None

        # attribute list for querying
        self._node_query_attrs = {}
        # node name -> attribute name -> _CacheAttrDef(attr offset, slots)
        self._node_attrs = defaultdict(dict)

    def init(self, env: AbsEnv, node_def: dict):
        self._env = env

        for node_name, attrs in node_def.items():
            list_attr_list = []
            normal_attr_list = []

            offset = 0

            for attr in attrs:
                if attr.is_list:
                    list_attr_list.append(attr.name)
                else:
                    normal_attr_list.append(attr.name)

                    self._node_attrs[node_name][attr.name] = _CacheAttrDef(offset, attr.slots)
                    offset += attr.slots

            self._node_query_attrs[node_name] = {
                "normal": normal_attr_list,
                "list": list_attr_list
            }

    @abstractmethod
    def get_attribute(self, node_name: str, node_index: int, attr_name: str):
        """Get latest (current tick) attribute value"""
        pass

    @abstractmethod
    def get_attribute_range(self, node_name: str, node_index: int, attr_name: str, ticks: List[int]):
        """Get attribute value for specified tick range."""
        pass


class PerInstanceSnapshotCache(SnapshotCacheABC):
    def __init__(self):
        super(PerInstanceSnapshotCache, self).__init__()

        # TODO: key is node name, value is np array: tick, attribute value array
        # NOW: key is node name and node index, value attribute value list
        self._normal_cache = {}

        # TODO: normal dict: key is tick, attribute dict: key is attribute name, value is attribute value
        # key is node name and node_index, value is dict: key if attr name, value is value list
        self._list_cache = defaultdict(dict)

    def get_attribute(self, node_name: str, node_index: int, attr_name: str):
        self._update_cache(node_name, node_index)

        key = (node_name, node_index)

        if attr_name not in self._node_attrs[node_name]:
            # list attribute
            return self._list_cache[key][attr_name]
        else:
            attr = self._node_attrs[node_name][attr_name]

            return self._normal_cache[key][attr.offset: attr.offset+attr.slots]

    def get_attribute_range(self, node_name: str, node_index: int, attr_name: str, ticks: List[int]):
        ss = self._env.snapshot_list[node_name]

        if attr_name in self._node_attrs[node_name]:
            return ss[ticks:node_index:attr_name].flatten()
        else:
            # combine one by one
            values = []
            for tick in ticks:
                values.append(ss[tick:node_index:attr_name].flatten())

            return values

    def _update_cache(self, node_name: str, node_index: int):
        key = (node_name, node_index)

        # update cache if frame index not match, or key not exist
        if self._current_cache_frame_index != self._env.frame_index or \
            (key not in self._normal_cache and key not in self._list_cache):
            self._current_cache_frame_index = self._env.frame_index

            ss = self._env.snapshot_list[node_name]
            key = (node_name, node_index)

            node_def = self._node_query_attrs[node_name]
            frame_index = self._env.frame_index

            # cache normal attribute
            self._normal_cache[key] = ss[frame_index:node_index:node_def["normal"]].flatten()

            # cache list attribute
            for attr in node_def["list"]:
                self._list_cache[key][attr] = ss[frame_index:node_index:attr].flatten()


class PerTypeSnapshotCache(SnapshotCacheABC):
    def __init__(self):
        super(PerInstanceSnapshotCache, self).__init__()

        self._cache = {}

    def get_attribute(self, node_name: str, node_index: int, attr_name: str):
        pass

    def get_attribute_range(self, node_name: str, node_index: int, attr_name: str, ticks: List[int]):
        pass
