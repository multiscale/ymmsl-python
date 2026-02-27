from collections import OrderedDict
from copy import copy
from enum import Enum
from typing import Any, cast, List, Optional, Sequence, Union

import yatiml

from ymmsl.v0_2.component import Component
from ymmsl.v0_2.identity import Identifier, Reference
from ymmsl.v0_2.implementation import Implementation
from ymmsl.v0_2.ports import Ports
from ymmsl.v0_2.supported_settings import SupportedSettings


class ConduitFilter(Enum):
    """Represent a filter to apply to messages passing through a conduit.

    In multiscale models, scale separation between simulated processes results in a
    communication pattern where a component simulating slow dynamics repeatedly calls a
    component simulating fast dynamics. If the fast dynamics component needs to be
    initialised once on its first run, or needs to send a final result at the end of its
    last run, then the number of sends and receives will not match up, resulting in a
    deadlock.

    Conduit filters solve this problem by telling the conduit to only pass the last sent
    message on to the receiver, or by repeating a single message as often as needed or
    by padding it with null messages to cover subsequent receives.

    Objects of this class represent the different possible filters.
    """
    LAST = 'last'
    """Pass only the last message and drop any preceding ones."""

    REPEAT = 'repeat'
    """Repeat a single message as often as needed."""

    PAD = 'pad'
    """Pass a single message and then generate nil-messages as needed."""

    def is_reducer(self) -> bool:
        """Return whether this filter is a reducer.

        Reducers take one or more sent messages and filter them down to a single one for
        the recipient.
        """
        return self is ConduitFilter.LAST

    def is_repeater(self) -> bool:
        """Return whether this filter is a repeater.

        Repeaters take a single message and turn it into multiple to cover multiple
        receive attempts.
        """
        return self in (ConduitFilter.REPEAT, ConduitFilter.PAD)

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.set_value(ConduitFilter(node.get_value()).name)

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.set_value(ConduitFilter[cast(str, node.get_value())].value)


class Conduit:
    """A conduit transports data between simulation components.

    A conduit has two endpoints, which are references to a port on a
    simulation component. These references must be of one of the
    following forms:

    - component.port
    - namespace.component.port (or several namespace prefixes)

    As a special feature, the receiver may be a whitespace-separated list of words, in
    which case the last of these words is the receiver, and the words before that will
    be interpreted as filters, using the (lowercase) values from ConduitFilter. In this
    case, the filters argument must be absent or empty.

    Attributes:
        sender: The sending port that this conduit is connected to.
        receiver: The receiving port that this conduit is connected to.
        filters: A list of filters, or a string containing space-separated filter names
    """
    def __init__(
            self, sender: str, receiver: str,
            filters: Optional[Union[str, List[ConduitFilter]]] = None) -> None:
        """Create a Conduit.

        Args:
            sender: The sending component and port, as a Reference.
            receiver: The receiving component and port, as a Reference, possibly
                preceded by filters.
            filters: A list of conduit filters to apply
        """
        self.sender = Reference(sender)

        recv_pieces = receiver.rsplit(maxsplit=1)
        if len(recv_pieces) < 2:
            self.receiver = Reference(receiver)
        else:
            if filters:
                raise ValueError(
                        'Cannot specify filters both in receiver and in filters')

            filters = recv_pieces[0]
            self.receiver = Reference(recv_pieces[1])

        if isinstance(filters, list):
            self.filters = filters
        else:
            self.filters = list()
            if isinstance(filters, str):
                for f in filters.split():
                    try:
                        self.filters.append(ConduitFilter(f))
                    except ValueError:
                        raise RuntimeError(f'Invalid conduit filter "{f}"')
        
        # Repeaters must come after reducers
        is_repeating = False
        for filter in self.filters:
            if filter.is_reducer() and is_repeating:
                raise ValueError(
                        f"Invalid conduit filters {self.filters}: reducer filters "
                        "must come before repeater filters.")
            is_repeating = filter.is_repeater()

        self.__check_reference(self.sender)
        self.__check_reference(self.receiver)

    def __str__(self) -> str:
        """Return a string representation of the object."""
        if not self.filters:
            filter_clause = ''
        else:
            filter_clause = ' -> ' + ' '.join([f.value for f in self.filters])
        return f'Conduit({self.sender}{filter_clause} -> {self.receiver})'

    def __eq__(self, other: Any) -> bool:
        """Returns whether the conduits are equal.

        This is the case if they connect the same ports with the same filters.
        """
        if not isinstance(other, Conduit):
            return NotImplemented
        return (
                self.sender == other.sender and self.receiver == other.receiver and
                self.filters == other.filters)

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

    def _filters_receiver(self) -> str:
        """Return the filters + receiver string for YAML.

        Beware! This gets called by Model._conduits_for_export, despite the underscore.
        """
        result = str(self.receiver)

        filter_strs = [f.value for f in self.filters]
        if filter_strs:
            result = ' '.join(filter_strs) + ' ' + result
        return result

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        filters = node.get_attribute('filters')
        filter_strs = [v.value for v in filters.yaml_node.value]

        if filter_strs:
            recv_str = cast(str, node.get_attribute('receiver').get_value())
            node.set_attribute(
                    'receiver', ' '.join(filter_strs) + ' ' + recv_str)

        node.remove_attribute('filters')


class MulticastConduit:
    """Multicast conduits connect multiple input ports to a single output port.

    In yMMSL they are expressed as a mapping, possibly including filters:

    .. code-block:: yaml

        sender.port:
        - receiver1.port
        - last receiver2.port

    This class is only used in the parsing and storing of the yMMSL file.
    Once parsed and populated in :class:`Model`, a multicast is identified by
    two or more conduits with the same :attr:`Conduit.sender`.
    """
    def __init__(self, sender: str, receiver: List[str]) -> None:
        """Create a Multicast Conduit.

        Args:
            sender: The sending component and port, as a Reference.
            receiver: The receiving components and ports, as a list of strings
                containing (optionally) filters and the receiver.
        """
        self.sender = sender
        # note: attribute must be called receiver to transparently work with
        # seq_attribute_to_map and map_attribute_to_seq in
        # Model._yatiml_savorize and Model._yatiml_sweeten
        self.receiver = receiver

    def as_conduits(self) -> List[Conduit]:
        """Retrieve the conduits that are part of this multicast conduit.

        Returns:
            A list of conduits, one conduit for each receiver.
        """
        return [Conduit(self.sender, recv_str) for recv_str in self.receiver]


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
        description: Human-readable description of the model.
        supported_settings: Settings supported by this model.
        components: A list of components making up the model.
        conduits: A list of conduits connecting the components.
    """
    def __init__(
            self, name: str, ports: Optional[Ports] = None,
            description: str = '',
            supported_settings: Optional[SupportedSettings] = None,
            components: Optional[Sequence[Component]] = None,
            conduits: Optional[Sequence[AnyConduit]] = None) -> None:
        """Create a Model.

        Args:
            name: Name of this model, must be a valid reference
            ports: Ports of this model
            description: Human-readable description of the model
            supported_settings: Settings supported by this model
            components: A list of components making up the model
            conduits: A list of conduits connecting the components
        """
        super().__init__(name, ports, description, supported_settings)

        if components is None:
            self.components = {}
        else:
            for i1, c1 in enumerate(components):
                num_conflicts = 0
                for i2 in range(i1-1):
                    if c1.name == components[i2].name:
                        num_conflicts += 1
                if num_conflicts > 0:
                    raise ValueError(
                            f'There are {num_conflicts + 1} components named'
                            f' {c1.name}.')

            self.components = {copy(c.name): c for c in components}

        self.conduits: list[Conduit] = list()
        if conduits:
            for conduit in conduits:
                if isinstance(conduit, Conduit):
                    self.conduits.append(conduit)
                if isinstance(conduit, MulticastConduit):
                    self.conduits.extend(conduit.as_conduits())

    def check_consistent(self) -> List[str]:
        """Check that the model is internally consistent.

        This checks:
            - that every conduit is connected to two existing ports on existing
              components, or on the model itself.

        Returns a list of errors, or an empty list if none were found.
        """
        errors: List[str] = list()

        model_receiving_ports = self.ports.receiving_port_names()
        model_sending_ports = self.ports.sending_port_names()

        for conduit in self.conduits:
            errors.extend(self._check_sending_side(conduit, model_receiving_ports))
            errors.extend(self._check_receiving_side(conduit, model_sending_ports))

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
            if conduit.sending_component() not in self.components:
                errors.append(
                        f'Conduit {conduit} refers to a component named'
                        f' {conduit.sending_component()}, which is not present in'
                        ' the model.')
            else:
                snd_cmp = self.components[conduit.sending_component()]
                cmp_sending_ports = snd_cmp.ports.sending_port_names()
                if conduit.sending_port() not in cmp_sending_ports:
                    errors.append(
                            f'Conduit {conduit} refers to a sending port named'
                            f' {conduit.sending_port()}, which is not present on'
                            f' sending component {snd_cmp.name}, or is not an O_I or'
                            ' O_F port.')
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
            if conduit.receiving_component() not in self.components:
                errors.append(
                        f'Conduit {conduit} refers to a component named'
                        f' {conduit.receiving_component()}, which is not present in'
                        ' the model.')
            else:
                rcvng_cmp = self.components[conduit.receiving_component()]
                rcvr_recv_ports = (
                        rcvng_cmp.ports.receiving_port_names() +
                        ['muscle_settings_in'])

                if conduit.receiving_port() not in rcvr_recv_ports:
                    errors.append(
                            f'Conduit {conduit} refers to a receiving port named'
                            f' {conduit.receiving_port()}, which is not present on'
                            f' receiving component {rcvng_cmp.name}, or is not an'
                            ' F_INIT or S port.')
        return errors

    def _conduits_for_export(self) -> List[AnyConduit]:
        """Process conduits and identify MulticastConduits for exporting.

        Returns:
            A list of Conduits and MulticastConduits.
        """
        cdts_by_sender: OrderedDict[Reference, List[Conduit]] = OrderedDict()
        for conduit in self.conduits:
            cdts_by_sender.setdefault(conduit.sender, []).append(conduit)

        conduit_list: list[AnyConduit] = []
        for sender, conduits in cdts_by_sender.items():
            if len(conduits) == 1:
                conduit_list.append(conduits[0])
            else:
                conduit_list.append(MulticastConduit(
                        str(sender),
                        [str(conduit._filters_receiver()) for conduit in conduits]))
        return conduit_list

    def _yatiml_attributes(self) -> OrderedDict:
        return OrderedDict([
            ('name', self.name),
            ('ports', self.ports),
            ('description', self.description),
            ('supported_settings', self.supported_settings),
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
        node.index_attribute_to_map('components', 'name')

        if len(node.get_attribute('conduits').seq_items()) == 0:
            node.remove_attribute('conduits')

        node.seq_attribute_to_map('conduits', 'sender', 'receiver')
