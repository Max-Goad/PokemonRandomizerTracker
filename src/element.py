import abc
from   typing import List, TypeVar

class Element(metaclass=abc.ABCMeta):
    T = TypeVar("T")

    @abc.abstractmethod
    def update(self, obj : T):
        pass

    @abc.abstractmethod
    def layout(self) -> List:
        pass
