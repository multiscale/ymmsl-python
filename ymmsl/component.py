"""Definitions for describing simulation components."""
from enum import Enum
import logging
from typing import Dict, Iterable, List, Optional

import yatiml

from ymmsl.identity import Identifier


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
        self.f_init = f_init if f_init else list()
        self.o_i = o_i if o_i else list()
        self.s = s if s else list()
        self.o_f = o_f if o_f else list()

        all_names = sorted(self.port_names())
        for i in range(len(all_names) - 1):
            if all_names[i] == all_names[i+1]:
                raise RuntimeError(
                        'Invalid ports specification: port "{}" is specified'
                        ' more than once. Port names must be unique within'
                        ' the component.')

    def port_names(self) -> Iterable[str]:
        """Returns an iterable containing the names of all ports."""
        return self.f_init + self.o_i + self.s + self.o_f

    def all_ports(self) -> Iterable[Port]:
        """Returns an iterable containing all ports."""
        return (
                [Port(Identifier(n), Operator.F_INIT) for n in self.f_init] +
                [Port(Identifier(name), Operator.O_I) for name in self.o_i] +
                [Port(Identifier(name), Operator.S) for name in self.s] +
                [Port(Identifier(name), Operator.O_F) for name in self.o_f])

    def operator(self, port_name: str) -> Operator:
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
