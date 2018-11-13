from enum import Enum

from ymmsl.identity import Reference


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


class Endpoint:
    """An endpoint on a compute element.

    Endpoints are used by compute elements to send or receive messages
    on. They are connected by conduits to enable communication between
    compute elements.

    Attributes:
        name: The name of the endpoint.
        operator: The MMSL operator in which this endpoint is used.
    """
    def __init__(self, name: Reference, operator: Operator) -> None:
        self.name = name  # type: Reference
        self.operator = operator  # type: Operator
