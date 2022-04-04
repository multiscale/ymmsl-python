"""Definitions for describing simulation components."""
from enum import Enum
import logging
from typing import Dict, Iterable, List, Optional, Union

import ruamel.yaml as yaml
import yatiml

from ymmsl.identity import Identifier, Reference


_logger = logging.getLogger(__name__)


class Operator(Enum):
    """An operator of a compute element.

    This is a combination of the Submodel Execution Loop operators,
    and operators for other components such as mappers.
    """

    NONE = 0    #: No operator
    F_INIT = 1  #: Initialisation phase, before start of the SEL
    O_I = 2     #: State observation within the model's main loop
    S = 3       #: State update in the model's main loop
    O_F = 5     #: Observation of final state, after the SEL

    def allows_sending(self) -> bool:
        """Whether ports on this operator can send."""
        return self in {Operator.NONE, Operator.O_I, Operator.O_F}

    def allows_receiving(self) -> bool:
        """Whether ports on this operator can receive."""
        return self in {Operator.NONE, Operator.F_INIT, Operator.S}


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


class Ports:
    """Ports declaration for a component.

    Ports objects compare for equality by value.

    Attributes:
        f_init: The ports associated with the F_INIT operator.
        o_i: The ports associated with the O_I operator
        s: The ports associated with the S operator.
        o_f: The ports associated with the O_F operator
    """
    def __init__(
            self, f_init: Optional[List[str]] = None,
            o_i: Optional[List[str]] = None, s: Optional[List[str]] = None,
            o_f: Optional[List[str]] = None) -> None:
        """Create a Ports declaration.

        Args:
            f_init: The ports associated with the F_INIT operator.
            o_i: The ports associated with the O_I operator
            s: The ports associated with the S operator.
            o_f: The ports associated with the O_F operator
        """
        self.f_init = list(map(Identifier, f_init)) if f_init else list()
        self.o_i = list(map(Identifier, o_i)) if o_i else list()
        self.s = list(map(Identifier, s)) if s else list()
        self.o_f = list(map(Identifier, o_f)) if o_f else list()

        all_names = sorted(self.port_names())
        for i in range(len(all_names) - 1):
            if all_names[i] == all_names[i+1]:
                raise RuntimeError(
                        'Invalid ports specification: port "{}" is specified'
                        ' more than once. Port names must be unique within'
                        ' the component.')

    def port_names(self) -> Iterable[Identifier]:
        """Returns an iterable containing the names of all ports."""
        return self.f_init + self.o_i + self.s + self.o_f

    def all_ports(self) -> Iterable[Port]:
        """Returns an iterable containing all ports."""
        return (
                [Port(n, Operator.F_INIT) for n in self.f_init] +
                [Port(name, Operator.O_I) for name in self.o_i] +
                [Port(name, Operator.S) for name in self.s] +
                [Port(name, Operator.O_F) for name in self.o_f])

    def operator(self, port_name: Identifier) -> Operator:
        """Looks up the operator for a given port.

        Args:
            port_name: Name of the port to look up.

        Return:
            The operator for that port.

        Raises:
            KeyError: If no port with this name was found.
        """
        if port_name in self.f_init:
            return Operator.F_INIT

        if port_name in self.o_i:
            return Operator.O_I

        if port_name in self.s:
            return Operator.S

        if port_name in self.o_f:
            return Operator.O_F

        raise KeyError('No port named "{}" was found'.format(port_name))

    _yatiml_defaults = {
            'f_init': [],
            'o_i': [],
            's': [],
            'o_f': []}  # type: Dict[str, Optional[List[str]]]

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.remove_attributes_with_default_values(cls)


class Component:
    """An object declaring a simulation component.

    Simulation components are things like submodels, scale bridges,
    proxies, and any other program that makes up a model. This class
    represents a declaration of a set of instances of a simulation
    component, and it's used to describe which instances are needed to
    perform a certain simulation.

    Attributes:
        name (ymmsl.Reference): The name of this component.
        implementation (ymmsl.Reference): A reference to the
                implementation to use.
        multiplicity (List[int]): The shape of the array of instances
                that execute simultaneously.
        ports (Optional[Ports]): The ports of this component,
                organised by operator. None if not specified.

    """

    def __init__(self, name: str, implementation: Optional[str] = None,
                 multiplicity: Union[None, int, List[int]] = None,
                 ports: Optional[Ports] = None) -> None:
        """Create a Component.

        Args:
            name: The name of the component; must be a valid
                    Reference.
            implementation: The name of the implementation; must be a
                    valid Reference.
            multiplicity: A list of ints describing the shape of the
                    set of instances.
            ports: The ports used by this component to communicate,
                    organised by operator.

        """
        self.name = Reference(name)
        if implementation is None:
            self.implementation = None      # type: Optional[Reference]
        else:
            self.implementation = Reference(implementation)
            for part in self.implementation:
                if isinstance(part, int):
                    raise ValueError('Component implementation {} contains a'
                                     ' subscript, which is not'
                                     ' allowed.'.format(self.name))

        if multiplicity is None:
            self.multiplicity = list()
        elif isinstance(multiplicity, int):
            self.multiplicity = [multiplicity]
        else:
            self.multiplicity = multiplicity

        self.ports = ports

    def __str__(self) -> str:
        """Returns a string representation of the object."""
        result = str(self.name)
        for dim in self.multiplicity:
            result += '[{}]'.format(dim)
        return result

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_attribute('name', str)

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.has_attribute('multiplicity'):
            if node.has_attribute_type('multiplicity', int):
                attr = node.get_attribute('multiplicity')
                start_mark = attr.yaml_node.start_mark
                end_mark = attr.yaml_node.end_mark
                new_seq = yaml.nodes.SequenceNode(
                        'tag:yaml.org,2002:seq', [attr.yaml_node], start_mark,
                        end_mark)
                node.set_attribute('multiplicity', new_seq)

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        multiplicity = node.get_attribute('multiplicity')
        items = multiplicity.seq_items()
        if len(items) == 0:
            node.remove_attribute('multiplicity')
        elif len(items) == 1:
            node.set_attribute('multiplicity', items[0].get_value())

        ports_node = node.get_attribute('ports').yaml_node
        if len(ports_node.value) == 0:
            node.remove_attribute('ports')
