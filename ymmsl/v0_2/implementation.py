from typing import Optional

from ymmsl.v0_2.ports import Ports
from ymmsl.v0_2.identity import Reference


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
    def __init__(
            self, name: str, ports: Optional[Ports] = None,
            description: str = 'Please add a description!') -> None:
        """Create an Implementation

        Args:
            name: Name of this implementation, must be a valid reference
            ports: The ports this implementation communicates on
            description: Human-readable description of this implementation
        """
        if not isinstance(name, Reference):
            self.name = Reference(name)
        else:
            self.name = name

        if ports is None:
            self.ports = Ports()
        else:
            self.ports = ports

        self.description = description
