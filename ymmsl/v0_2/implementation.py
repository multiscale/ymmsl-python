from typing import Optional

from ymmsl.v0_1.component import Ports
from ymmsl.v0_1.identity import Reference


class Implementation:
    """Describes an implementation of a submodel

    Models consist of connected components, and each component needs to be implemented
    somehow to be able to actually run the simulation. So we have Implementations, which
    can be either a Program, or another Model. This class represents the information
    all implementations need to have to use them as part of a model.

    Attributes:
        name: Name of this implementation, must be a valid Reference
        ports: The ports this implementation has on which it sends and receives messages
    """
    def __init__(self, name: str, ports: Optional[Ports] = None) -> None:
        """Create an Implementation

        Args:
            name: Name of this implementation
            ports: The ports this implementation communicates on
        """
        self.name = Reference(name)

        if ports is None:
            self.ports = Ports()
        else:
            self.ports = ports
