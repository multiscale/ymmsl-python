from typing import cast, List, Optional, Union

import yaml
import yatiml

from ymmsl.v0_2.ports import Ports
from ymmsl.v0_2.identity import Reference


class Component:
    """Describes a simulation component

    Simulation components are the abstract boxes that models consist of. Components are
    implemented by an implementation, which describes how to do the calculations needed
    for this component, they have a multiplicity, which describes how many copies of
    that implementation need to be started (for e.g. ensembles), and they have ports,
    which are used to connect components to each other.

    Components may be optional. If a component is optional, then a missing
    implementation in the final configuration that is run is valid, and will result in
    the component and all connected conduits being removed from the simulation. If a
    component is not optional, then trying to run a simulation with a component that
    does not have an implementation will result in an error.

    Attributes:
        name: The name of this component
        ports: The ports by which this component can be connected to others
        description: A human-readable description of this component
        implementation: A Model or Program implementing this component
        optional: Whether this component is optional
        multiplicity: The shape of the set of instances
    """
    def __init__(
            self, name: str, ports: Ports,
            description: str, implementation: Optional[str] = None,
            optional: bool = False,
            multiplicity: Union[None, int, List[int]] = None) -> None:
        """Create a Component

        Args:
            name: The name of the component, must be a valid Identifier
            ports: Ports on this component that can be used to connect it
            description: Human-readable description of this component
            implementation: The name of the implementation, must be a valid Reference
            optional: Whether this component is optional.
            multiplicity: The shape of the set of instances, or a number describing the
                size of a 1D set of them, or None to have a single instance.
        """
        self.name = Reference(name)
        self.ports = ports
        self.description = description
        self.optional = optional

        if implementation is not None:
            self.implementation: Optional[Reference] = Reference(implementation)
            for part in self.implementation:
                if isinstance(part, int):
                    raise ValueError('Component implementation {} contains a'
                                     ' subscript, which is not'
                                     ' allowed.'.format(self.name))
        else:
            self.implementation = None

        if multiplicity is None:
            self.multiplicity = list()
        elif isinstance(multiplicity, int):
            self.multiplicity = [multiplicity]
        else:
            self.multiplicity = multiplicity

    def __str__(self) -> str:
        """Returns a string representation of the object."""
        result = str(self.name)
        for dim in self.multiplicity:
            result += '[0:{}]'.format(dim)
        return result

    def __repr__(self) -> str:
        """Returns a string representation of the object."""
        return 'Component({})'.format(self.name)

    def instances(self) -> List[Reference]:
        """Creates a list of instances needed.

        Returns:
            A list with one Reference for each instance of this
            component.
        """
        def increment(index: List[int], dims: List[int]) -> None:
            # assumes index and dims are the same length > 0
            # modifies index argument
            i = len(index) - 1
            index[i] += 1
            while index[i] == dims[i]:
                index[i] = 0
                i -= 1
                if i == -1:
                    break
                index[i] += 1

        def generate_indices(multiplicity: List[int]) -> List[List[int]]:
            # n-dimensional counter
            indices: list[list[int]] = list()

            index = [0] * len(multiplicity)
            indices.append(index.copy())
            increment(index, multiplicity)
            while sum(index) > 0:
                indices.append(index.copy())
                increment(index, multiplicity)
            return indices

        result: list[Reference] = list()

        if len(self.multiplicity) == 0:
            result.append(self.name)
        else:
            for index in generate_indices(self.multiplicity):
                result.append(self.name + index)

        return result

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_attribute('name', str)

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        ports_node = node.get_attribute('ports').yaml_node
        if ports_node.tag == 'tag:yaml.org,2002:null':
            node.remove_attribute('ports')

        descr = node.get_attribute('description')
        if descr.is_scalar(str):
            # output in block style
            ynode = cast(yaml.ScalarNode, descr.yaml_node)
            ynode.style = '|'
            if not ynode.value.endswith('\n'):
                ynode.value += '\n'

        multiplicity = node.get_attribute('multiplicity')
        items = multiplicity.seq_items()
        if len(items) == 0:
            node.remove_attribute('multiplicity')
        elif len(items) == 1:
            node.set_attribute('multiplicity', items[0].get_value())

        node.remove_attributes_with_default_values(cls)
