# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

#cython: language_level=3
#distutils: language = c++
import numpy as np
cimport numpy as np
cimport cython

from cython cimport view
from cpython cimport bool

from maro.backends.backend cimport (BackendAbc, SnapshotListAbc, INT, UINT, ULONG, IDENTIFIER, NODE_INDEX, SLOT_INDEX,
    ATTR_BYTE, ATTR_SHORT, ATTR_INT, ATTR_LONG, ATTR_FLOAT, ATTR_DOUBLE, raise_get_attr_error)


# Ensure numpy will not crash, as we use numpy as query result
np.import_array()


cdef dict attribute_accessors = {
    "i2": AttributeShortAccessor,
    "i": AttributeIntAccessor,
    "i4": AttributeIntAccessor,
    "i8": AttributeLongAccessor,
    "f": AttributeFloatAccessor,
    "d": AttributeDoubleAccessor,
}


# Helpers used to access attribute with different data type to avoid to much ifelse
cdef class AttributeAccessor:
    cdef:
        IDENTIFIER _attr_id
        RawBackend _raw

    cdef void setup(self, RawBackend raw, IDENTIFIER attr_id):
        self._raw = raw
        self._attr_id = attr_id

    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value):
        pass

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index):
        pass

    def __dealloc__(self):
        self._raw = None


cdef class AttributeShortAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value):
        self._raw._backend.set_attr_value[ATTR_SHORT](self._attr_id, node_index, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index):
        return self._raw._backend.get_short(self._attr_id, node_index, slot_index)


cdef class AttributeIntAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value):
        self._raw._backend.set_attr_value[ATTR_INT](self._attr_id, node_index, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index):
        return self._raw._backend.get_int(self._attr_id, node_index, slot_index)


cdef class AttributeLongAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value):
        self._raw._backend.set_attr_value[ATTR_LONG](self._attr_id, node_index, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index):
        return self._raw._backend.get_long(self._attr_id, node_index, slot_index)


cdef class AttributeFloatAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value):
        self._raw._backend.set_attr_value[ATTR_FLOAT](self._attr_id, node_index, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index):
        return self._raw._backend.get_float(self._attr_id, node_index, slot_index)


cdef class AttributeDoubleAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value):
        self._raw._backend.set_attr_value[ATTR_DOUBLE](self._attr_id, node_index, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index):
        return self._raw._backend.get_double(self._attr_id, node_index, slot_index)


cdef class RawBackend(BackendAbc):
    def __cinit__(self):
        self._node_info = {}
        self._attr_type_dict = {}
        self.snapshots = RawSnapshotList(self)

    cdef IDENTIFIER add_node(self, str name, NODE_INDEX number) except +:
        cdef IDENTIFIER id = self._backend.add_node(name.encode())

        self._backend.set_node_number(id, number)

        self._node_info[id] = {"number": number, "name": name, "attrs":{}}

        return id

    cdef IDENTIFIER add_attr(self, IDENTIFIER node_id, str attr_name, str dtype, SLOT_INDEX slot_num) except +:
        cdef AttrDataType dt = AINT

        # TODO: refactor later
        if dtype == "i" or dtype == "i4":
            dt = AINT
        elif dtype == "i2":
            dt = ASHORT
        elif dtype == "i8":
            dt = ALONG
        elif dtype == "f":
            dt = AFLOAT
        elif dtype == "d":
            dt = ADOUBLE

        cdef IDENTIFIER attr_id = self._backend.add_attr(node_id, attr_name.encode(), dt, slot_num)

        cdef AttributeAccessor acc = attribute_accessors[dtype]()

        acc.setup(self, attr_id)

        self._attr_type_dict[attr_id] = acc

        self._node_info[node_id]["attrs"][attr_id] = {"type": dtype, "slots": slot_num, "name": attr_name}

        return attr_id

    cdef void set_attr_value(self, NODE_INDEX node_index, IDENTIFIER attr_id, SLOT_INDEX slot_index, object value)  except *:
        cdef AttributeAccessor acc = self._attr_type_dict[attr_id]

        acc.set_value(node_index, slot_index, value)

    cdef object get_attr_value(self, NODE_INDEX node_index, IDENTIFIER attr_id, SLOT_INDEX slot_index) except +raise_get_attr_error:
        cdef AttributeAccessor acc = self._attr_type_dict[attr_id]

        return acc.get_value(node_index, slot_index)

    cdef void set_attr_values(self, NODE_INDEX node_index, IDENTIFIER attr_id, SLOT_INDEX[:] slot_index, list value)  except *:
        cdef SLOT_INDEX slot
        cdef int index

        for index, slot in enumerate(slot_index):
            self.set_attr_value(node_index, attr_id, slot, value[index])

    cdef list get_attr_values(self, NODE_INDEX node_index, IDENTIFIER attr_id, SLOT_INDEX[:] slot_indices):
        cdef AttributeAccessor acc = self._attr_type_dict[attr_id]

        cdef SLOT_INDEX slot

        cdef list result = []

        for slot in slot_indices:
            result.append(acc.get_value(node_index, slot))

        return result

    cdef void reset(self) except *:
        self._backend.reset_frame()

    cdef void setup(self, bool enable_snapshot, USHORT total_snapshot, dict options) except *:
        self._backend.setup(enable_snapshot, total_snapshot)

    cdef dict get_node_info(self):
        cdef dict node_info = {}

        for node_id, node in self._node_info.items():
            node_info[node["name"]] = {
                "number": node["number"],
                "attributes": {
                    attr["name"]: {
                        "type": attr["type"],
                        "slots": attr["slots"]
                    } for _, attr in node["attrs"].items()
                }
            }

        return node_info


cdef class RawSnapshotList(SnapshotListAbc):
    def __cinit__(self, RawBackend raw):
        self._raw = raw;

    # Query states from snapshot list
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef query(self, IDENTIFIER node_id, list ticks, list node_index_list, list attr_list):
        cdef int index
        cdef IDENTIFIER attr_id

        # NOTE: format must be changed if NODE_INDEX type changed
        # Node indices parameters passed to raw backend
        cdef NODE_INDEX[:] node_indices = None
        # Tick parameter passed to raw backend
        cdef INT[:] tick_list = None
        # Attribute list cannot be empty, so we just use it to construct parameter
        cdef IDENTIFIER[:] attr_id_list = view.array(shape=(len(attr_list),), itemsize=sizeof(IDENTIFIER), format="H")

        # Check and construct node indices list
        if node_index_list is not None and len(node_index_list) > 0:
            node_indices = view.array(shape=(len(node_index_list),), itemsize=sizeof(NODE_INDEX), format="H")

        cdef USHORT ticks_length = len(ticks)

        # Check ticks, and construct if has value
        if ticks is not None and ticks_length > 0:
            tick_list = view.array(shape=(ticks_length,), itemsize=sizeof(INT), format="i")

            for index in range(ticks_length):
                tick_list[index] = ticks[index]
        else:
            ticks_length = self._raw._backend.get_valid_tick_number()

        for index in range(len(node_index_list)):
            node_indices[index] = node_index_list[index]

        for index in range(len(attr_list)):
            attr_id_list[index] = attr_list[index]

        # Calc 1 frame length
        cdef UINT per_frame_length = self._raw._backend.query_one_tick_length(node_id, &node_indices[0], len(node_indices), &attr_id_list[0], len(attr_id_list))

        # Result holder
        cdef ATTR_FLOAT[:] result = view.array(shape=(per_frame_length * ticks_length, ), itemsize=sizeof(ATTR_FLOAT), format="f")

        # Default result value
        result[:] = 0

        # Do query
        self._raw._backend.query(&result[0], node_id, &tick_list[0], ticks_length, &node_indices[0], len(node_indices), &attr_id_list[0], len(attr_id_list))

        return np.array(result)

    # Record current backend state into snapshot list
    cdef void take_snapshot(self, INT tick) except *:
        self._raw._backend.take_snapshot(tick)

    # List of available frame index in snapshot list
    cdef list get_frame_index_list(self):
        return []

    # Enable history, history will dump backend into files each time take_snapshot called
    cdef void enable_history(self, str history_folder) except *:
        pass

    # Reset internal states
    cdef void reset(self) except *:
        self._raw._backend.reset_snapshots()

    def __len__(self):
        return self._raw._backend.get_max_snapshot_number()
