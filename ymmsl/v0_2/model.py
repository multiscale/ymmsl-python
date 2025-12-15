from collections import OrderedDict
from typing import Any, cast, List, Optional, Sequence, Union

import yatiml

from ymmsl.v0_1.component import Ports
from ymmsl.v0_1.identity import Identifier, Reference
from ymmsl.v0_2.component import Component
from ymmsl.v0_2.implementation import Implementation


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
        # check that there are no subscripts
        for part in ref:
            if isinstance(part, int):
                raise ValueError(
                        f'Reference {ref} contains a subscript, which is not allowed in'
                        ' conduits.')

        # check that the length is at least 1
        if len(ref) < 1:
            raise ValueError(
                    'Senders and receivers in conduits must have either a port name,'
                    ' or a component name, a period, and then a port name.')

    def sending_component(self) -> Reference:
        """Returns a reference to the sending component."""
        if len(self.sender) == 1:
            return Reference([])
        return cast(Reference, self.sender[:-1])

    def sending_port(self) -> Identifier:
        """Returns the identity of the sending port."""
        # We've checked that it's an Identifier during construction
        return cast(Identifier, self.sender[-1])

    def receiving_component(self) -> Reference:
        """Returns a reference to the receiving component."""
        if len(self.receiver) == 1:
            return Reference([])
        return cast(Reference, self.receiver[:-1])

    def receiving_port(self) -> Identifier:
        """Returns the identity of the receiving port."""
        return cast(Identifier, self.receiver[-1])


class MulticastConduit:
    """Multicast conduits connect multiple input ports to a single output port.

    In yMMSL they are expressed as a mapping:

    .. code-block:: yaml

        sender.port:
        - receiver1.port
        - receiver2.port

    This class is only used in the parsing and storing of the yMMSL file.
    Once parsed and populated in :class:`Model`, a multicast is identified by
    two or more conduits with the same :attr:`Conduit.sender`.
    """

    def __init__(self, sender: str, receiver: List[str]) -> None:
        """Create a Multicast Conduit.

        Args:
            sender: The sending component and port, as a Reference.
            receiver: The receiving components and ports, as a list of
                    References.
        """
        self.sender = sender
        # note: attribute must be called receiver to transparently work with
        # seq_attribute_to_map and map_attribute_to_seq in
        # Model._yatiml_savorize and Model._yatiml_sweeten
        self.receiver = receiver
        self._conduits = [Conduit(sender, recv) for recv in receiver]

    def as_conduits(self) -> List[Conduit]:
        """Retrieve the conduits that are part of this multicast conduit.

        Returns:
            A list of conduits, one conduit for each receiver.
        """
        return self._conduits


AnyConduit = Union[Conduit, MulticastConduit]


class Model(Implementation):
    """Describes a simulation model.

    A model consists of a number of components connected by conduits. It may have ports
    to communicate with models it's embedded in.

    Note that there may be no conduits, if there is only a single component. In that
    case, the conduits argument may be omitted when constructing the object, and also
    from the YAML file; the `conduits` attribute will then be set to an empty list.

    Attributes:
        name: The name by which this simulation model is known to the system.
        ports: Ports through which this model can communicate with other models.
        components: A list of components making up the model.
        conduits: A list of conduits connecting the components.
    """
    def __init__(
            self, name: str, ports: Optional[Ports] = None,
            components: Optional[List[Component]] = None,
            conduits: Optional[Sequence[AnyConduit]] = None) -> None:
        """Create a Model.

        Args:
            name: Name of this model, must be a valid reference
            ports: Ports of this model
            components: A list of components making up the model
            conduits: A list of conduits connecting the components
        """
        super().__init__(name, ports)

        if components is None:
            self.components = []
        else:
            self.components = components

        self.conduits = list()      # type: List[Conduit]
        if conduits:
            for conduit in conduits:
                if isinstance(conduit, Conduit):
                    self.conduits.append(conduit)
                if isinstance(conduit, MulticastConduit):
                    self.conduits.extend(conduit.as_conduits())

    def check_consistent(self) -> None:
        """Check that the model is internally consistent.

        This checks:
            - that no two components have the same name
            - that every conduit is connected to two existing ports on existing
              components, or on the model itself.

        Raises:
            RuntimeError: If an inconsistency was found
        """
        errors: List[str] = list()

        errors.extend(self._check_component_name_conflicts())

        model_receiving_ports = self.ports.f_init + self.ports.s
        model_sending_ports = self.ports.o_i + self.ports.o_f

        for conduit in self.conduits:
            errors.extend(self._check_sending_side(conduit, model_receiving_ports))
            errors.extend(self._check_receiving_side(conduit, model_sending_ports))

        if errors:
            raise RuntimeError(
                    f'One or more errors were found in model {self.name}:\n-'
                    ' {"\n- ".join(errors)}')

    def _check_component_name_conflicts(self) -> List[str]:
        """Check that no two components have the same name.

        Returns a list of errors.
        """
        errors = list()

        for i1, c1 in enumerate(self.components):
            num_conflicts = 0
            for i2 in range(i1-1):
                if c1.name == self.components[i2].name:
                    num_conflicts += 1
            if num_conflicts > 0:
                errors.append(f'There are {num_conflicts + 1} models named {c1.name}.')

        return errors

    def _check_sending_side(
            self, conduit: Conduit, model_receiving_ports: List[Identifier]
            ) -> List[str]:
        """Check the sending side of a conduit."""
        errors = list()
        if not conduit.sending_component():
            # from model input port
            if conduit.sending_port() not in model_receiving_ports:
                errors.append(
                    f'Conduit {conduit} refers to an incoming model port'
                    f' {conduit.sending_port()} that does not exist.')
        else:
            # from component
            snd_cmp = [
                    c for c in self.components
                    if c.name == conduit.sending_component()]
            if not snd_cmp:
                errors.append(
                        f'Conduit {conduit} refers to a component named'
                        f' {conduit.sending_component()}, which is not present in'
                        ' the model.')
            else:
                if len(snd_cmp) == 1:
                    cmp_sending_ports = snd_cmp[0].ports.o_i + snd_cmp[0].ports.o_f
                    if conduit.sending_port() not in cmp_sending_ports:
                        errors.append(
                                f'Conduit {conduit} refers to a sending port named'
                                f' {conduit.sending_port()}, which is not present'
                                f' on sending component {snd_cmp[0].name}, or not'
                                ' an O_I or O_F port.')
        return errors

    def _check_receiving_side(
            self, conduit: Conduit, model_sending_ports: List[Identifier]
            ) -> List[str]:
        """Check the receiving side of a conduit."""
        errors = list()
        if not conduit.receiving_component():
            # to model output port
            if conduit.receiving_port() not in model_sending_ports:
                errors.append(
                    f'Conduit {conduit} refers to an incoming model port'
                    f' {conduit.receiving_port()} that does not exist.')
        else:
            # to component
            rcvng_cmp = [
                    c for c in self.components
                    if c.name == conduit.receiving_component()]
            if not rcvng_cmp:
                errors.append(
                        f'Conduit {conduit} refers to a component named'
                        f' {conduit.receiving_component()}, which is not present in'
                        ' the model.')
            else:
                if len(rcvng_cmp) == 1:
                    rcvr_recv_ports = (
                            rcvng_cmp[0].ports.f_init + rcvng_cmp[0].ports.s +
                            ['muscle_settings_in'])

                    if conduit.receiving_port() not in rcvr_recv_ports:
                        errors.append(
                                f'Conduit {conduit} refers to a receiving port named'
                                f' {conduit.receiving_port()}, which is not present'
                                f' on receiving component {rcvng_cmp[0].name}, or not'
                                ' an F_INIT or S port.')
        return errors

    def _conduits_for_export(self) -> List[AnyConduit]:
        """Process conduits and identify MulticastConduits for exporting.

        Returns:
            A list of Conduits and MulticastConduits.
        """
        cdts_by_sender: OrderedDict[Reference, List[Conduit]] = OrderedDict()
        for conduit in self.conduits:
            cdts_by_sender.setdefault(conduit.sender, []).append(conduit)

        conduit_list = []   # type: List[AnyConduit]
        for sender, conduits in cdts_by_sender.items():
            if len(conduits) == 1:
                conduit_list.append(conduits[0])
            else:
                conduit_list.append(MulticastConduit(
                        str(sender),
                        [str(conduit.receiver) for conduit in conduits]))
        return conduit_list

    def _yatiml_attributes(self) -> OrderedDict:
        return OrderedDict([
            ('name', self.name),
            ('ports', self.ports),
            ('components', self.components),
            ('conduits', self._conduits_for_export())])

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # No ambiguity possible, this gives better error messages
        node.require_mapping()

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.map_attribute_to_seq('components', 'name')
        node.map_attribute_to_seq('conduits', 'sender', 'receiver')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.seq_attribute_to_map('components', 'name',)
        if len(node.get_attribute('conduits').seq_items()) == 0:
            node.remove_attribute('conduits')
        node.seq_attribute_to_map('conduits', 'sender', 'receiver')
