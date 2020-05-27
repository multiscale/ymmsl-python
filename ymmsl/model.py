"""This module contains all the definitions for yMMSL."""
from typing import Any, List, Optional, Union, cast

from ruamel import yaml
import yatiml

from ymmsl.identity import Identifier, Reference


class ComputeElement:
    """An object declaring a compute element.

    Compute elements are things like submodels, scale bridges, proxies,
    and any other program that makes up a model. This class
    represents a declaration of a set of instances of a compute
    element, and it's used to describe which instances are needed to
    perform a certain simulation.

    Args:
        name: The name of the compute element; must be a valid
                Reference.
        implementation: The name of the implementation; must be a
                valid Reference.
        multiplicity: An list of ints describing the shape of the
                set of instances.

    Attributes:
        name (ymmsl.Reference): The name of this compute element.
        implementation (ymmsl.Reference): A reference to the
                implementation to use.
        multiplicity (List[int]): The shape of the array of instances
                that execute simultaneously.
    """

    def __init__(self, name: str, implementation: str,
                 multiplicity: Union[None, int, List[int]] = None) -> None:

        if multiplicity is None:
            multiplicity = list()
        elif isinstance(multiplicity, int):
            multiplicity = [multiplicity]

        self.name = Reference(name)
        self.implementation = Reference(implementation)
        if (isinstance(multiplicity, int)):
            multiplicity = [multiplicity]
        self.multiplicity = multiplicity

        for part in self.implementation:
            if isinstance(part, int):
                raise ValueError('Compute element implementation {} contains a'
                                 ' subscript which is not allowed.'.format(self.name))

    def __str__(self) -> str:
        result = str(self.name)
        for dim in self.multiplicity:
            result += '[{}]'.format(dim)
        return result

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_attribute('name', str)
        node.require_attribute('implementation', str)

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.has_attribute('multiplicity'):
            if node.has_attribute_type('multiplicity', int):
                attr = node.get_attribute('multiplicity')
                start_mark = attr.yaml_node.start_mark
                end_mark = attr.yaml_node.end_mark
                new_seq = yaml.nodes.SequenceNode('tag:yaml.org,2002:seq',
                                                  [attr.yaml_node], start_mark, end_mark)
                node.set_attribute('multiplicity', new_seq)

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        multiplicity = node.get_attribute('multiplicity')
        items = multiplicity.seq_items()
        if len(items) == 0:
            node.remove_attribute('multiplicity')
        elif len(items) == 1:
            node.set_attribute('multiplicity', items[0].get_value())


class Conduit:
    """A conduit transports data between compute elements.

    A conduit has two endpoints, which are references to a Port on a
    Compute Element. These references must be of one of the following
    forms:

    - submodel.port
    - namespace.submodel.port (or several namespace prefixes)

    Args:
        sender: The sending compute element and port, as a Reference.
        receiver: The receiving compute element and port, as a
                Reference.

    Attributes:
        sender: The sending port that this conduit is connected to.
        receiver: The receiving port that this conduit is connected to.
    """
    def __init__(self, sender: str, receiver: str) -> None:
        self.sender = Reference(sender)
        self.receiver = Reference(receiver)

        self.__check_reference(self.sender)
        self.__check_reference(self.receiver)

    def __str__(self) -> str:
        return 'Conduit({} -> {})'.format(self.sender, self.receiver)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Conduit):
            return NotImplemented
        return self.sender == other.sender and self.receiver == other.receiver

    @staticmethod
    def __check_reference(ref: Reference) -> None:
        """Checks an endpoint for validity.
        """
        # check that subscripts are at the end
        for i, part in enumerate(ref):
            if isinstance(part, int):
                if (i+1) < len(ref) and isinstance(ref[i+1], Identifier):
                    raise ValueError('Reference {} contains a subscript that'
                                     ' is not at the end, which is not allowed'
                                     ' in conduits.'.format(ref))

        # check that the length is at least 2
        if len(Conduit.__stem(ref)) < 2:
            raise ValueError('Senders and receivers in conduits must have'
                             ' a compute element name, a period, and then'
                             ' a port name and optionally a slot. Reference {}'
                             ' is missing either the compute element or the'
                             ' port'.format(ref))

    def sending_compute_element(self) -> Reference:
        """Returns a reference to the sending compute element.
        """
        return cast(Reference, self.__stem(self.sender)[:-1])

    def sending_port(self) -> Identifier:
        """Returns the identity of the sending port.
        """
        # We've checked that it's an Identifier during construction
        return cast(Identifier, self.__stem(self.sender)[-1])

    def sending_slot(self) -> List[int]:
        """Returns the slot on the sending port.

        If no slot was given, an empty list is returned.

        Returns:
            A list of slot indexes.
        """
        return self.__slot(self.sender)

    def receiving_compute_element(self) -> Reference:
        """Returns a reference to the receiving compute element.
        """
        return cast(Reference, self.__stem(self.receiver)[:-1])

    def receiving_port(self) -> Identifier:
        """Returns the identity of the receiving port.
        """
        return cast(Identifier, self.__stem(self.receiver)[-1])

    def receiving_slot(self) -> List[int]:
        """Returns the slot on the receiving port.

        If no slot was given, an empty list is returned.

        Returns:
            A list of slot indexes.
        """
        return self.__slot(self.receiver)

    @staticmethod
    def __slot(reference: Reference) -> List[int]:
        """Extracts the slot from the given reference.

        The slot is the list of contiguous ints at the end of the
        reference. If the reference does not end in an int, returns
        an empty list.
        """
        result = list()     # type: List[int]
        i = len(reference) - 1
        while isinstance(reference[i], int):
            result.insert(0, cast(int, reference[i]))
            i -= 1
        return result

    @staticmethod
    def __stem(reference: Reference) -> Reference:
        """Extracts the part of the reference before the slot.

        If there is no slot, returns the whole reference.
        """
        i = len(reference)
        while isinstance(reference[i-1], int):
            i -= 1
        return reference[:i]    # type: ignore


class ModelReference:
    """Describes a reference (by name) to a model.

    Attributes:
        name: The name of the simulation model this refers to.
    """
    def __init__(self, name: str) -> None:
        """Create a ModelReference.

        Arguments:
            name: Name of the model to refer to.
        """
        self.name = Identifier(name)


class Model(ModelReference):
    """Describes a simulation model.

    A model consists of a number of compute elements connected by
    conduits.

    Note that there may be no conduits, if there is only a single
    compute element. In that case, the conduits argument may be
    omitted when constructing the object, and also from the YAML file;
    the `conduits` attribute will then be set to an empty list.

    Attributes:
        name: The name by which this simulation model is known to
                the system.
        compute_elements: A list of compute elements making up the
                model.
        conduits: A list of conduits connecting the compute elements.
    """
    def __init__(self, name: str,
                 compute_elements: List[ComputeElement],
                 conduits: Optional[List[Conduit]] = None) -> None:
        """Create a Model.

        Arguments:
            name: Name of this model.
            compute_elements: A list of compute elements making up the
                    model.
            conduits: A list of conduits connecting the compute
                    elements.
        """
        super().__init__(name)
        self.compute_elements = compute_elements

        if conduits is None:
            self.conduits = list()      # type: List[Conduit]
        else:
            self.conduits = conduits

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_mapping()
        node.require_attribute('name')
        node.require_attribute('compute_elements')

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.map_attribute_to_seq('compute_elements', 'name', 'implementation')
        node.map_attribute_to_seq('conduits', 'sender', 'receiver')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.seq_attribute_to_map('compute_elements', 'name', 'implementation')
        if len(node.get_attribute('conduits').seq_items()) == 0:
            node.remove_attribute('conduits')
        node.seq_attribute_to_map('conduits', 'sender', 'receiver')
