"""This module contains all the definitions for yMMSL."""
from typing import cast, List

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

    A conduit has two endpoints, which are references to a Port on a
    Compute Element. These references must be of one of the following
    forms:

    - submodel.port
    - namespace.submodel.port (or several namespace prefixes)

    Attributes:
        sender: The sending port that this conduit is connected to.
        receiver: The receiving port that this conduit is connected to.
    """
    def __init__(self, sender: Reference,
                 receiver: Reference) -> None:
        self.sender = sender
        self.receiver = receiver

        self.__check_reference(sender)
        self.__check_reference(receiver)

    def __check_reference(self, ref: Reference) -> None:
        """Checks an endpoint for validity."""
        # check that there are no subscripts
        for part in ref.parts:
            if not isinstance(part, Identifier):
                raise ValueError('Reference {} contains a subscript, which'
                                 ' is not allowed in conduits.'.format(ref))

        # check that the length is at least 2
        if len(ref.parts) < 2:
            raise ValueError('Senders and receivers in conduits must have'
                             ' a compute element name, a period, and then'
                             ' a port name. Reference {} is missing either'
                             ' the compute element or the port'.format(ref))

    def sending_compute_element(self) -> Reference:
        """Returns a reference to the sending compute element.
        """
        return self.sender[:-1]

    def sending_port(self) -> Identifier:
        """Returns the identity of the sending port.
        """
        # We've checked that it's an Identifier during construction
        return cast(Identifier, self.sender.parts[-1])

    def receiving_compute_element(self) -> Reference:
        """Returns a reference to the receiving compute element.
        """
        return self.receiver[:-1]

    def receiving_port(self) -> Identifier:
        """Returns the identity of the receiving port.
        """
        return cast(Identifier, self.receiver.parts[-1])


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
