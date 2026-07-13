from abc import ABC, abstractmethod


class Document(ABC):
    """Base class for ymmsl documents of all versions"""

    @abstractmethod
    def __init__(self) -> None:
        pass
