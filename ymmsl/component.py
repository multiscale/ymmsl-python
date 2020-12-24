"""Definitions for describing simulation components."""
from enum import Enum

from ymmsl.identity import Identifier


class Operator(Enum):
    """An operator of a compute element.

    This is a combination of the Submodel Execution Loop operators,
    and operators for other components such as mappers.
    """

    NONE = 0    #: No operator
    F_INIT = 1  #: Initialisation phase, before start of the SEL
    O_I = 2     #: State observation within the model's main loop
    S = 3       #: State update in the model's main loop
    B = 4       #: Boundary conditions update in the model's main loop
    O_F = 5     #: Observation of final state, after the SEL

    def allows_sending(self) -> bool:
        """Whether ports on this operator can send."""
        return self in {
                Operator.NONE,
                Operator.O_I,
                Operator.O_F
        }

    def allows_receiving(self) -> bool:
        """Whether ports on this operator can receive."""
        return self in {
                Operator.NONE,
                Operator.F_INIT,
                Operator.S,
                Operator.B
                }


class Port:
    """A port on a compute element.

    Ports are used by compute elements to send or receive messages
    on. They are connected by conduits to enable communication between
    compute elements.

    Attributes:
        name: The name of the port.
        operator: The MMSL operator in which this port is used.

    """

    def __init__(self, name: Identifier, operator: Operator) -> None:
        """Create a Port.

        Args:
            name: The name of the port.
            operator: The MMSL Operator in which this port is used.

        """
        self.name = name  # type: Identifier
        self.operator = operator  # type: Operator
