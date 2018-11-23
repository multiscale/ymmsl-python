from enum import Enum

from ymmsl.identity import Identifier


class Operator(Enum):
    """An operator of a compute element.

    This is a combination of the Submodel Execution Loop operators,
    and operators for other components such as mappers.
    """
    NONE = 0
    F_INIT = 1
    O_I = 2
    S = 3
    B = 4
    O_F = 5
    MAP = 6


class Port:
    """A port on a compute element.

    Ports are used by compute elements to send or receive messages
    on. They are connected by conduits to enable communication between
    compute elements.

    Attributes:
        name: The name of the port.
        operator: The MMSL operator in which this endpoint is used.
    """
    def __init__(self, name: Identifier, operator: Operator) -> None:
        self.name = name  # type: Identifier
        self.operator = operator  # type: Operator
