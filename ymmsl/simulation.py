"""This module contains all the definitions for yMMSL."""
from typing import List

import yatiml

from ymmsl.identity import Identifier, Reference


class ComputeElementDecl:
    """An object declaring a compute element.

    Compute elements are things like submodels, scale bridges, proxies, \
    and any other program that makes up a simulation. This class \
    represents a declaration of an array of instances of a compute \
    element, and it's used to describe which instances are needed to \
    perform a certain simulation.

    Attributes:
        name: The name of this compute element.
        implementation: A reference to the implementation to use.
        count: The number of instances that execute simultaneously.
    """

    def __init__(self, name: Identifier, implementation: Reference, count: int = 1) -> None:
        self.name = name
        self.implementation = implementation
        self.count = count

        for part in self.implementation.parts:
            if isinstance(part, int):
                raise ValueError('Compute element implementation {} contains a'
                                 ' subscript which is not allowed.'.format(self.name))

    def __str__(self) -> str:
        return '{}[{}]'.format(self.name, self.count)


class Conduit:
    """A conduit transports data between compute elements.

    The references to the sender and receiver must be of one of the \
    following forms:

    - submodel.port
    - namespace.submodel.port (or several namespace prefixes)
    - submodel[3].port (for any value of 3)
    - submodel.port[5] (for any value of 5)

    Or a combination, e.g. namespace.submodel[3].port[4]

    Attributes:
        sender: The sending port that this conduit is connected to. Of \
                the form 'submodel.port_name'.
        receiver: The receiving port that this conduit is connected to. \
                Of the form 'submodel.port_name'.
    """
    def __init__(self, sender: Reference,
                 receiver: Reference) -> None:
        self.sender = sender
        self.receiver = receiver

        self.__check_reference(sender)
        self.__check_reference(receiver)

    def __check_reference(self, ref: Reference) -> None:
        # find last Identifier
        i = len(ref.parts) - 1
        while i >= 0 and isinstance(ref.parts[i], int):
            i -= 1

        # check port subscript, if any
        if len(ref.parts) - 1 - i > 1:
            raise ValueError('In reference {}: Ports can only have a single'
                             ' subscript.'.format(ref))

        # move to before last Identifier
        i -= 1

        # skip model subscripts, if any
        while i >= 0 and isinstance(ref.parts[i], int):
            i -= 1

        if i < 0:
            raise ValueError('Reference {} does not reference any compute'
                             ' element. You need both a compute element part'
                             ' and a port name part.'.format(ref))

        # check that model designator is a list of only identifiers
        while i >= 0:
            if not isinstance(ref.parts[i], Identifier):
                raise ValueError('Reference {} contains a subscript inside the'
                                 ' compute element part.'.format(ref))
            i -= 1

    def sending_compute_element(self) -> Reference:
        """Returns a reference to the sending compute element."""
        return self.__compute_element_part(self.sender)

    def sending_port(self) -> Reference:
        """Returns a reference to the sending port.

        This is either a single Identifier, or an Identifier followed \
        by an int, if a particular slot in the port was referred to.
        """
        return self.__port_name_part(self.sender)

    def receiving_compute_element(self) -> Reference:
        """Returns a reference to the receiving compute element."""
        return self.__compute_element_part(self.receiver)

    def receiving_port(self) -> Reference:
        """Returns the identity of the receiving port.

        This is either a single Identifier, or an Identifier followed \
        by an int, if a particular slot in the port was referred to.
        """
        return self.__port_name_part(self.receiver)

    def __compute_element_part(self, ref: Reference) -> Reference:
        return ref[0:self.__port_name_index(ref)]

    def __port_name_part(self, ref: Reference) -> Reference:
        return ref[self.__port_name_index(ref):]

    def __port_name_index(self, ref: Reference) -> int:
        # last identifier is the port name
        i = len(ref.parts) - 1
        while i >= 0 and isinstance(ref.parts[i], int):
            i -= 1
        return i


class Simulation:
    """Describes a simulation model.

    A model consists of a number of compute elements connected by \
    conduits.

    Attributes:
        name: The name by which this simulation model is known to \
                the system.
        compute_elements: A list of compute elements making up the \
                simulation.
        conduits: A list of conduits connecting the compute elements.
    """
    def __init__(self, name: Identifier,
                 compute_elements: List[ComputeElementDecl],
                 conduits: List[Conduit]) -> None:
        self.name = name
        self.compute_elements = compute_elements
        self.conduits = conduits

    @classmethod
    def yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        pass

    @classmethod
    def yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.map_attribute_to_seq('compute_elements', 'name', 'implementation')
        node.map_attribute_to_seq('conduits', 'sender', 'receiver')

    @classmethod
    def yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.seq_attribute_to_map('compute_elements', 'name', 'implementation')
        node.seq_attribute_to_map('conduits', 'sender', 'receiver')
