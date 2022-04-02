"""This module contains all the definitions for yMMSL."""
from typing import Any, List, Optional, cast
from typing import Dict     # noqa

import yatiml

from ymmsl.component import Operator    # noqa
from ymmsl.component import Component
from ymmsl.identity import Identifier, Reference


class Conduit:
    """A conduit transports data between simulation components.

    A conduit has two endpoints, which are references to a port on a
    simulation component. These references must be of one of the
    following forms:

    - component.port
    - namespace.component.port (or several namespace prefixes)

    Attributes:
        sender: The sending port that this conduit is connected to.
        receiver: The receiving port that this conduit is connected to.

    """

    def __init__(self, sender: str, receiver: str) -> None:
        """Create a Conduit.

        Args:
            sender: The sending component and port, as a Reference.
            receiver: The receiving component and port, as a
                    Reference.

        """
        self.sender = Reference(sender)
        self.receiver = Reference(receiver)

        self.__check_reference(self.sender)
        self.__check_reference(self.receiver)

    def __str__(self) -> str:
        """Return a string representation of the object."""
        return 'Conduit({} -> {})'.format(self.sender, self.receiver)

    def __eq__(self, other: Any) -> bool:
        """Returns whether the conduits connect the same ports."""
        if not isinstance(other, Conduit):
            return NotImplemented
        return self.sender == other.sender and self.receiver == other.receiver

    @staticmethod
    def __check_reference(ref: Reference) -> None:
        """Checks an endpoint for validity."""
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
                             ' a component name, a period, and then'
                             ' a port name and optionally a slot. Reference {}'
                             ' is missing either the component or the'
                             ' port'.format(ref))

    def sending_component(self) -> Reference:
        """Returns a reference to the sending component."""
        return cast(Reference, self.__stem(self.sender)[:-1])

    def sending_port(self) -> Identifier:
        """Returns the identity of the sending port."""
        # We've checked that it's an Identifier during construction
        return cast(Identifier, self.__stem(self.sender)[-1])

    def sending_slot(self) -> List[int]:
        """Returns the slot on the sending port.

        If no slot was given, an empty list is returned.

        Returns:
            A list of slot indexes.

        """
        return self.__slot(self.sender)

    def receiving_component(self) -> Reference:
        """Returns a reference to the receiving component."""
        return cast(Reference, self.__stem(self.receiver)[:-1])

    def receiving_port(self) -> Identifier:
        """Returns the identity of the receiving port."""
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

    A model consists of a number of components connected by
    conduits.

    Note that there may be no conduits, if there is only a single
    component. In that case, the conduits argument may be
    omitted when constructing the object, and also from the YAML file;
    the `conduits` attribute will then be set to an empty list.

    Attributes:
        name: The name by which this simulation model is known to
                the system.
        components: A list of components making up the
                model.
        conduits: A list of conduits connecting the components.

    """
    def __init__(self, name: str,
                 components: List[Component],
                 conduits: Optional[List[Conduit]] = None) -> None:
        """Create a Model.

        Args:
            name: Name of this model.
            components: A list of components making up the model.
            conduits: A list of conduits connecting the components.

        """
        super().__init__(name)
        self.components = components

        if conduits is None:
            self.conduits = list()      # type: List[Conduit]
        else:
            self.conduits = conduits

    def update(self, overlay: 'Model') -> None:
        """Overlay another model definition on top of this one.

        This updates the object with the name, components and conduits
        given in the argument. The name is overwritten, and components
        are overwritten if they have the same name as an existing
        argument or else added.

        Conduits are added. If a conduit was already connected to one
        of the endpoints of a conduit in the overlay, the old conduit
        is removed.

        Args:
            overlay: A Model definition to overlay on top of this one.
        """
        self.name = overlay.name
        # update components
        for newc in overlay.components:
            for i, oldc in enumerate(self.components):
                if oldc.name == newc.name:
                    self.components[i] = newc
                    break
            else:
                self.components.append(newc)

        # remove overwritten conduits
        for newt in overlay.conduits:
            for oldt in self.conduits.copy():
                if oldt.sender == newt.sender:
                    self.conduits.remove(oldt)
                if oldt.receiver == newt.receiver:
                    self.conduits.remove(oldt)

        # add new conduits
        self.conduits.extend(overlay.conduits)

    def check_consistent(self) -> None:
        """Checks that the model is internally consistent.

        This checks whether all conduits are connected to existing
        components, and will raise a RuntimeError with an explanation
        if one is not.
        """
        def component_exists(name: Reference) -> bool:
            for comp in self.components:
                if comp.name == name:
                    return True
            return False

        for conduit in self.conduits:
            if not component_exists(conduit.sending_component()):
                raise RuntimeError(
                    'Unknown sending component "{}" of {}'.format(
                        conduit.sending_component(), conduit))

            if not component_exists(conduit.receiving_component()):
                raise RuntimeError(
                    'Unknown receiving component "{}" of {}'.format(
                        conduit.receiving_component(), conduit))

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_mapping()
        node.require_attribute('name')
        node.require_attribute('components')

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.map_attribute_to_seq('components', 'name', 'implementation')
        node.map_attribute_to_seq('conduits', 'sender', 'receiver')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.seq_attribute_to_map('components', 'name', 'implementation')
        if len(node.get_attribute('conduits').seq_items()) == 0:
            node.remove_attribute('conduits')
        node.seq_attribute_to_map('conduits', 'sender', 'receiver')
