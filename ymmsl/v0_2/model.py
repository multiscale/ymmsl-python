from collections import OrderedDict
from enum import Enum
from itertools import starmap
from typing import Any, cast, List, Optional, Sequence, Tuple, Union

import yaml
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
            receiver: The receiving component and port, as a Reference.
            filters: A list of conduit filters to apply
        """
        self.sender = Reference(sender)
        self.receiver = Reference(receiver)

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

        self.__check_reference(self.sender)
        self.__check_reference(self.receiver)

    def __str__(self) -> str:
        """Return a string representation of the object."""
        if not self.filters:
            filter_clause = ''
        else:
            filter_clause = ' ->' + ' '.join([f.value for f in self.filters])
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

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        filters = node.get_attribute('filters')
        filter_strs = [v.value for v in filters.yaml_node.value]
        node.set_attribute('filters', ' '.join(filter_strs))


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
    def __init__(
            self, sender: str,
            receiver: Union[List[str], List[Tuple[str, List[ConduitFilter]]]]) -> None:
        """Create a Multicast Conduit.

        Args:
            sender: The sending component and port, as a Reference.
            receiver: The receiving components and ports, as a list of
                    References, or as a list of tuples of receiver Reference and conduit
                    filters.
        """
        self.sender = sender
        # note: attribute must be called receiver to transparently work with
        # seq_attribute_to_map and map_attribute_to_seq in
        # Model._yatiml_savorize and Model._yatiml_sweeten

        def as_recv_string(cmp_port: str, filters: List[ConduitFilter]) -> str:
            result = ' '.join((f.value for f in filters))
            if result:
                result += ' '
            return result + cmp_port

        def as_recv_filters(recv: str) -> Tuple[str, List[ConduitFilter]]:
            parts = recv.split()
            return parts[-1], [ConduitFilter(p) for p in parts[:-1]]

        if isinstance(receiver[0], str):
            self.receiver: List[str] = cast(List[str], receiver)
            self._conduits = [
                    Conduit(self.sender, *as_recv_filters(recv))
                    for recv in self.receiver]
        else:
            recv_list = cast(List[Tuple[str, List[ConduitFilter]]], receiver)
            self.receiver = list(starmap(as_recv_string, recv_list))
            self._conduits = [
                    Conduit(self.sender, cmp_port, filters)
                    for cmp_port, filters in recv_list]

    def _yatiml_init(self, sender: str, receiver: List[str]) -> None:
        MulticastConduit.__init__(self, sender, receiver)

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
        description: Human-readable description of the model.
        supported_settings: Settings supported by this model.
        components: A list of components making up the model.
        conduits: A list of conduits connecting the components.
    """
    def __init__(
            self, name: str, ports: Optional[Ports] = None,
            description: str = '',
            supported_settings: Optional[SupportedSettings] = None,
            components: Optional[List[Component]] = None,
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

    def check_consistent(self) -> List[str]:
        """Check that the model is internally consistent.

        This checks:
            - that no two components have the same name
            - that every conduit is connected to two existing ports on existing
              components, or on the model itself.

        Returns a list of errors, or an empty list if none were found.
        """
        errors: List[str] = list()

        errors.extend(self._check_component_name_conflicts())

        model_receiving_ports = self.ports.receiving_port_names()
        model_sending_ports = self.ports.sending_port_names()

        for conduit in self.conduits:
            errors.extend(self._check_sending_side(conduit, model_receiving_ports))
            errors.extend(self._check_receiving_side(conduit, model_sending_ports))

        return errors

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
                errors.append(
                        f'There are {num_conflicts + 1} components named {c1.name}.')

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
                    cmp_sending_ports = snd_cmp[0].ports.sending_port_names()
                    if conduit.sending_port() not in cmp_sending_ports:
                        errors.append(
                                f'Conduit {conduit} refers to a sending port named'
                                f' {conduit.sending_port()}, which is not present'
                                f' on sending component {snd_cmp[0].name}, or is not'
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
                            rcvng_cmp[0].ports.receiving_port_names() +
                            ['muscle_settings_in'])

                    if conduit.receiving_port() not in rcvr_recv_ports:
                        errors.append(
                                f'Conduit {conduit} refers to a receiving port named'
                                f' {conduit.receiving_port()}, which is not present'
                                f' on receiving component {rcvng_cmp[0].name}, or is'
                                ' not an F_INIT or S port.')
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

        if node.has_attribute('conduits'):
            node.map_attribute_to_seq('conduits', 'sender', 'receiver')
            # receiver now includes any filters
            conduits = node.get_attribute('conduits')
            for conduit_mapping in conduits.yaml_node.value:
                # get this conduit's mapping into a dict for easier working
                entries = {
                        key.value: value.value for key, value in conduit_mapping.value}

                if 'filters' not in entries and 'receiver' in entries:
                    filters, _, receiver = entries['receiver'].rpartition(' ')
                    entries['filters'] = filters
                    entries['receiver'] = receiver

                    # update the list-of-tuples with new receiver value
                    for i, (key_node, value_node) in enumerate(conduit_mapping.value):
                        if key_node.value in entries:
                            value_node.value = entries[key_node.value]

                        # save the location of the filters/receiver text
                        if key_node.value == 'receiver':
                            start_mark = value_node.start_mark
                            end_mark = value_node.end_mark

                    # add new filters key-value pair, pointing to approximately the
                    # right location in the input file in case of error
                    conduit_mapping.value.append((
                        yaml.ScalarNode(
                            'tag:yaml.org,2002:str', 'filters', start_mark, end_mark),
                        yaml.ScalarNode(
                            'tag:yaml.org,2002:str', filters, start_mark, end_mark)))

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.seq_attribute_to_map('components', 'name',)

        if len(node.get_attribute('ports').yaml_node.value) == 0:
            node.remove_attribute('ports')

        if len(node.get_attribute('supported_settings').yaml_node.value) == 0:
            node.remove_attribute('supported_settings')

        if len(node.get_attribute('conduits').seq_items()) == 0:
            node.remove_attribute('conduits')

        # fold conduit filters into the receiver line
        conduits = node.get_attribute('conduits')
        for conduit_node in conduits.yaml_node.value:
            # make key/value dict for easier manipulation
            entries = {
                    key_node.value: val_node.value
                    for key_node, val_node in conduit_node.value}

            if entries['filters'] != '':
                entries['receiver'] = f'{entries["filters"]} {entries["receiver"]}'

            # update the sequence with new values and delete filters
            for key_node, value_node in conduit_node.value:
                value_node.value = entries[key_node.value]

            del conduit_node.value[-1]      # filters is the last attribute

        node.seq_attribute_to_map('conduits', 'sender', 'receiver')
