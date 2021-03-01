from .base import DataModelBase
from maro.backends.frame import node, NodeBase, NodeAttribute
from maro.backends.backend import AttributeType


@node("storage")
class StorageDataModel(DataModelBase):
    unit_storage_cost = NodeAttribute(AttributeType.INT)
    capacity = NodeAttribute(AttributeType.INT)
    