from typing import cast, Optional

import yaml
import yatiml

from ymmsl.v0_2.identity import Reference
from ymmsl.v0_2.ports import Ports
from ymmsl.v0_2.supported_settings import SupportedSettings


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
            description: str = 'Please add a description!',
            supported_settings: Optional[SupportedSettings] = None) -> None:
        """Create an Implementation

        Args:
            name: Name of this implementation, must be a valid reference
            ports: The ports this implementation communicates on
            description: Human-readable description of this implementation
            supported_settings: Settings supported by this implementation
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

        self.supported_settings = supported_settings

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if len(node.get_attribute('ports').yaml_node.value) == 0:
            node.remove_attribute('ports')

        descr = node.get_attribute('description')
        if descr.is_scalar(str):
            # output in block style
            ynode = cast(yaml.ScalarNode, descr.yaml_node)
            ynode.style = '|'
            if not ynode.value.endswith('\n'):
                ynode.value += '\n'
