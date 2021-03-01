
from abc import abstractmethod
from maro.backends.frame import NodeBase


class DataModelBase(NodeBase):
    @abstractmethod
    def initialize(self, configs):
        pass

    @abstractmethod
    def reset(self):
        pass