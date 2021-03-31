#cython: language_level=3
#distutils: language = c++
#distutils: define_macros=NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION

import numpy as np
cimport numpy as np
cimport cython

from cython cimport view
from cython.operator cimport dereference as deref

from cpython cimport bool
from libcpp cimport bool as cppbool
from libcpp.map cimport map

from maro.backends.backend cimport (AttributeType,
    INT, UINT, ULONG, NODE_TYPE, ATTR_TYPE, NODE_INDEX, SLOT_INDEX,
    ATTR_CHAR, ATTR_UCHAR, ATTR_SHORT, ATTR_USHORT, ATTR_INT, ATTR_UINT,
    ATTR_LONG, ATTR_ULONG, ATTR_FLOAT, ATTR_DOUBLE, USHORT)

np.import_array()


cdef dict attribute_accessors = {
    AttributeType.Byte: AttributeCharAccessor,
    AttributeType.UByte: AttributeUCharAccessor,
    AttributeType.Short: AttributeShortAccessor,
    AttributeType.UShort: AttributeUShortAccessor,
    AttributeType.Int: AttributeIntAccessor,
    AttributeType.UInt: AttributeUIntAccessor,
    AttributeType.Long: AttributeLongAccessor,
    AttributeType.ULong: AttributeULongAccessor,
    AttributeType.Float: AttributeFloatAccessor,
    AttributeType.Double: AttributeDoubleAccessor,
}



cdef map[string, AttrDataType] attr_type_mapping

attr_type_mapping[AttributeType.Byte] = ACHAR
attr_type_mapping[AttributeType.UByte] = AUCHAR
attr_type_mapping[AttributeType.Short] = ASHORT
attr_type_mapping[AttributeType.UShort] = AUSHORT
attr_type_mapping[AttributeType.Int] = AINT
attr_type_mapping[AttributeType.UInt] = AUINT
attr_type_mapping[AttributeType.Long] = ALONG
attr_type_mapping[AttributeType.ULong] = AULONG
attr_type_mapping[AttributeType.Float] = AFLOAT
attr_type_mapping[AttributeType.Double] = ADOUBLE


cdef class AttrDef:
    cdef:
        str name
        bytes data_type
        SLOT_INDEX slots
        bool is_const
        bool is_list
        ATTR_TYPE attr_type

cdef class BindingPair:
    cdef:
        object object
        NODE_TYPE node_type
        NODE_INDEX index


# Helpers used to access attribute with different data type to avoid to much if-else.
cdef class AttributeAccessor:
    cdef:
        ATTR_TYPE _attr_type
        FrameLite _backend

    cdef void setup(self, FrameLite frame, ATTR_TYPE attr_type):
        self._backend = frame
        self._attr_type = attr_type

    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        pass

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        pass

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        pass

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        pass

    def __dealloc__(self):
        self._backend = None


cdef class FrameLite:
    def __cinit__(self, USHORT total_snapshots):
        self._node_counter = {}
        self._node_type_mapping = {}
        self._node_attr_defs = {}
        self._attr_type_quick_mapping = {}

        self._bind_pairs = {}
        self._attr_type_dict = {}
        self._snapshots.setup(&self._frame)
        self._snapshots.set_max_size(total_snapshots)

    def register_node(self, node_name: str, number: int):
        cdef str _node_name = node_name
        cdef NODE_INDEX _number = number
        cdef NODE_TYPE node_type = self._frame.add_node(_node_name.encode(), _number)

        self._node_type_mapping[_node_name] = node_type
        self._node_counter[node_type] = 0
        self._node_attr_defs[node_type] = {}
        self._attr_type_quick_mapping[node_type] = {}

    def register_attr(self, node_name: str, attr_name: str, data_type: bytes, slot_number: int=1, is_const: bool=False, is_list: bool=False):
        cdef AttrDataType dt = AINT

        cdef map[string, AttrDataType].iterator attr_pair = attr_type_mapping.find(data_type)

        if attr_pair != attr_type_mapping.end():
            dt = deref(attr_pair).second;
        
        cdef str _node_name = node_name
        cdef str _attr_name = attr_name
        cdef SLOT_INDEX _slot_number = slot_number
        cdef bool _is_const = is_const
        cdef bool _is_list = is_list
        
        cdef NODE_TYPE node_type = self._node_type_mapping[_node_name]
        cdef ATTR_TYPE attr_type = self._frame.add_attr(node_type, _attr_name.encode(), dt, _slot_number, _is_const, _is_list)

        cdef dict attr_def_list = self._node_attr_defs[node_type]

        cdef AttrDef attr_def = AttrDef()
        
        attr_def.name = _attr_name
        attr_def.data_type = data_type
        attr_def.slots = _slot_number
        attr_def.is_const = _is_const
        attr_def.is_list = _is_list
        attr_def.attr_type = attr_type

        attr_def_list[attr_name] = attr_def

        self._attr_type_quick_mapping[node_type][attr_name] = attr_type
        
        cdef AttributeAccessor acc = attribute_accessors[data_type]()

        acc.setup(self, attr_type)

        self._attr_type_dict[attr_type] = acc

    def bind(self, node_name:str , obj: object):
        cdef str _node_name = node_name

        cdef NODE_TYPE node_type = self._node_type_mapping[_node_name]
        cdef NODE_INDEX index = self._node_counter[node_type]

        cdef BindingPair pair = BindingPair()

        pair.object = obj
        pair.node_type = node_type
        pair.index = index

        self._bind_pairs[(node_name, index)] = pair

        self._node_counter[node_type] += 1

        return index

    def update(self, node_name: str, node_index: int, obj: object, attr_name: str, value: object):
        cdef BindingPair pair
        cdef NODE_INDEX _node_index = node_index
        cdef NODE_TYPE node_type

        cdef AttrDef attr_def
        cdef AttributeAccessor attr_acc
        cdef ATTR_TYPE attr_type
        cdef bool is_list
        cdef bool is_const
        cdef SLOT_INDEX slots
        cdef SLOT_INDEX slot_index
        cdef int item_index = 0

        pair = self._bind_pairs[(node_name, node_index)]
        node_type = pair.node_type

        attr_def= self._node_attr_defs[node_type][attr_name]

        is_list = attr_def.is_list
        is_const = attr_def.is_const
        attr_type = attr_def.attr_type

        attr_acc = self._attr_type_dict[attr_type]

        slots = self._frame.get_slot_number(node_index, attr_type)

        if not is_list and slots == 1:
            attr_acc.set_value(node_index, 0, value)
        else:
            slot_index = 0

            for item_index, item in enumerate(value):
                if is_list:
                    if slot_index >= slots:
                        attr_acc.append_value(node_index, item)

                        slots = self._frame.get_slot_number(node_index, attr_type)
                        slot_index += 1
                        
                        continue

                attr_acc.set_value(node_index, slot_index, item)

                slot_index += 1

    def collect_states(self):
        cdef BindingPair pair
        cdef object obj
        cdef NODE_INDEX node_index
        cdef NODE_TYPE node_type
        cdef list attr_def_list
        cdef str attr_name
        cdef ATTR_TYPE attr_type
        cdef bytes data_type
        cdef bool is_list
        cdef bool is_const
        cdef SLOT_INDEX slots
        cdef AttrDef attr_def
        cdef SLOT_INDEX slot_index
        cdef AttributeAccessor attr_acc
        cdef dict attribute_check_list

        for pair in self._bind_pairs:
            obj = pair.object
            node_index = pair.index
            node_type = pair.node_type
            attr_def_list = self._node_attr_defs[node_type]
            attribute_check_list = obj.attribute_check_list

            for attr_def in attr_def_list:
                attr_name = attr_def.name
                attr_type = attr_def.attr_type
                data_type = attr_def.data_type
                is_list = attr_def.is_list
                is_const = attr_def.is_const

                if not attribute_check_list[attr_name]:
                    continue

                attribute_check_list[attr_name] = False

                slots = self._frame.get_slot_number(node_index, attr_type)
                attr_acc = self._attr_type_dict[attr_type]

                target_attr = getattr(obj, attr_name)

                if not is_list and slots == 1:
                    attr_acc.set_value(node_index, 0, target_attr)
                else:
                    slot_index = 0

                    for item_index, item in enumerate(target_attr):
                        if is_list:
                            if slot_index >= slots:
                                attr_acc.append_value(node_index, item)

                                slots = self._frame.get_slot_number(node_index, attr_type)
                                slot_index += 1
                                
                                continue
                        
                        if type(target_attr) != list:
                            if not target_attr.is_all_changed and item_index in target_attr:
                                continue
                
                        attr_acc.set_value(node_index, slot_index, item)

                        slot_index += 1

    def setup(self):
        self._frame.setup()

    def reset(self):
        self._frame.reset()
        self._snapshots.reset()

    def take_snapshot(self, tick: int):
        cdef int _tick = tick
        self._snapshots.take_snapshot(tick)

    def get_node_info(self):
        return {}


cdef class AttributeCharAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_CHAR](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_CHAR](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_CHAR](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_CHAR](node_index, self._attr_type, slot_index, value)


cdef class AttributeUCharAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_UCHAR](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_UCHAR](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_UCHAR](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_UCHAR](node_index, self._attr_type, slot_index, value)


cdef class AttributeShortAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_SHORT](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_SHORT](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_SHORT](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_SHORT](node_index, self._attr_type, slot_index, value)


cdef class AttributeUShortAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_USHORT](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_USHORT](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_USHORT](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_USHORT](node_index, self._attr_type, slot_index, value)


cdef class AttributeIntAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_INT](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_INT](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_INT](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_INT](node_index, self._attr_type, slot_index, value)


cdef class AttributeUIntAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_UINT](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_UINT](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_UINT](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_UINT](node_index, self._attr_type, slot_index, value)


cdef class AttributeLongAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_LONG](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_LONG](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_LONG](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_LONG](node_index, self._attr_type, slot_index, value)


cdef class AttributeULongAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_ULONG](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_ULONG](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_ULONG](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_ULONG](node_index, self._attr_type, slot_index, value)


cdef class AttributeFloatAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_FLOAT](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_FLOAT](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_FLOAT](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_FLOAT](node_index, self._attr_type, slot_index, value)


cdef class AttributeDoubleAccessor(AttributeAccessor):
    cdef void set_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.set_value[ATTR_DOUBLE](node_index, self._attr_type, slot_index, value)

    cdef object get_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index) except +:
        return self._backend._frame.get_value[ATTR_DOUBLE](node_index, self._attr_type, slot_index)

    cdef void append_value(self, NODE_INDEX node_index, object value) except +:
        self._backend._frame.append_to_list[ATTR_DOUBLE](node_index, self._attr_type, value)

    cdef void insert_value(self, NODE_INDEX node_index, SLOT_INDEX slot_index, object value) except +:
        self._backend._frame.insert_to_list[ATTR_DOUBLE](node_index, self._attr_type, slot_index, value)
