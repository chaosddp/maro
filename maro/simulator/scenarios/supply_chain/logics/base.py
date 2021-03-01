
from abc import ABC, abstractmethod


class LogicBase(ABC):

    @abstractmethod
    def initialize(self, config):
        pass

    @abstractmethod
    def step(self, tick: int, datamodel: object):
        pass

    @abstractmethod
    def get_metrics(self):
        pass

    @abstractmethod
    def reset(self):
        pass
