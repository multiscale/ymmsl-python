from collections import OrderedDict
from typing import Any, cast, Iterator, List, Optional, overload, Sequence, Union

from ymmsl.v0_1.component import Operator   # also the v0.2 version, import from here
from ymmsl.v0_2.identity import Identifier, Reference


class Timeline:
    """Identify a timeline on which a port sends or receives.

    Timeline objects describe when a port sends or receives, either relative to a parent
    timeline that calls the component they're a part of, or by describing the whole list
    of components calling each other from the root timeline down.

    A component c1 that is not called by any other component will have its F_INIT and
    O_F ports (if any) on the root timeline, which is represented by ':'. If c1's
    implementation has a loop in which it sends on an O_I port and receives on an S
    port, then those ports are on a subtimeline, which is named after the component by
    default, ':c1'.

    If we add a component c2 and connect its F_INIT and O_F to those ports, then we
    create a macro-micro type coupling. The F_INIT and O_F ports of c2 will then be on
    timeline ':c1', because they'll receive and send at the exact points in simulated
    time that c1's O_I and S ports send and receive.

    If c2 has its own O_I and S ports, then those will be on timeline ':c1:c2', this
    being the concatenation of the parent timeline and the relative timeline within c2.

    Some implementations may have more than one set of O_I/S ports, on which they
    communicate at different rates. In that case, each port should be given a local
    relative timeline explicitly. In the above example, if c1's O_I and S ports were
    specified to be on local relative timeline 'tl1', then their full relative timeline
    is 'c1.tl' and their absolute timeline is ':c1.tl`, putting c2's O_I and S ports on
    ':c1.tl:c2' unless they too have an explicit timeline designation.

    Timelines have a technical representation as a list of References, and a string
    representation in which those References are joined using colons.
    """
    @overload
    def __init__(self, timeline: str) -> None: ...

    @overload
    def __init__(
            self, timeline: Sequence[Union[str, Reference]], absolute: bool = True
            ) -> None: ...

    def __init__(
            self, timeline: Union[str, Sequence[Union[str, Reference]]],
            absolute: bool = True) -> None:
        """Create a Timeline.

        The argument is either a string describing the timeline, or a list of components
        that are each a string that is also a valid Reference.
        """
        def make_new_reference(x: Union[str, Reference]) -> Reference:
            return Reference(str(x))

        if isinstance(timeline, str):
            if timeline == '':
                self.absolute = False
                parts = []  # type: Sequence[Union[str, Reference]]
            elif timeline == ':':
                self.absolute = True
                parts = []
            else:
                self.absolute = False
                if timeline[0] == ':':
                    self.absolute = True
                    timeline = timeline[1:]

                parts = timeline.split(':')

            self._parts = list(map(make_new_reference, parts))

        elif isinstance(timeline, list):
            self.absolute = absolute
            self._parts = list(map(make_new_reference, timeline))

    def __eq__(self, other: Any) -> bool:
        """Compare with another Timeline or a string for equality."""
        if isinstance(other, str):
            return str(self) == other
        elif isinstance(other, Timeline):
            return self.absolute == other.absolute and self._parts == other._parts
        return NotImplemented

    def __hash__(self) -> int:
        """Make this hashable so we can make sets of Timelines."""
        return hash(str(self))

    def __str__(self) -> str:
        """Return the string representation of this Timeline."""
        anchor = ':' if self.absolute else ''
        return anchor + ':'.join(map(str, self._parts))

    def __repr__(self) -> str:
        """Return a representation of the object."""
        return f'Timeline({self.__str__()})'

    def __len__(self) -> int:
        """Return the number of parts in the Timeline."""
        return len(self._parts)

    def __getitem__(self, index: int) -> Reference:
        """Return the index'th item in the timeline."""
        return self._parts[index]

    def __add__(self, other: Any) -> 'Timeline':
        """Concatenate this timeline with another (relative!) Timeline."""
        if isinstance(other, Timeline):
            if other.absolute:
                raise ValueError(
                        'Cannot concatenate an absolute Timeline onto another one')
            return Timeline(self._parts + other._parts, self.absolute)
        return NotImplemented


class Port:
    """A port on a component.

    Ports are used by component to send or receive messages on. They are
    connected by conduits to enable communication between components.

    Attributes:
        name: The name of the port
        operator: The MMSL operator in which this port is used
        timeline: The timeline this port is on, relative to its component.
    """
    def __init__(
            self, name: Identifier, operator: Operator,
            timeline: Optional[Timeline] = None) -> None:
        """Create a Port.

        Args:
            name: The name of the port
            operator: The MMSL Operator in which this port is used
            timeline: The Timeline this port is on. If None or omitted, an empty
                timeline will be set.
        """
        self.name = name
        self.operator = operator
        if timeline is None:
            timeline = Timeline('')
        self.timeline = timeline

    def __eq__(self, other: Any) -> bool:
        """Compare Port objects by value."""
        if isinstance(other, Port):
            return (
                    self.name == other.name and self.operator == other.operator and
                    self.timeline == other.timeline)

        return NotImplemented


_PortsSubAttrs = OrderedDict[str, Union[str, List[str]]]


_PortsAttrs = OrderedDict[
        str, Union[str, List[str], _PortsSubAttrs]]


def _ensure_identifier(port_name: Union[str, Identifier]) -> Identifier:
    if isinstance(port_name, str):
        port_name = Identifier(port_name)
    return port_name


class Ports:
    """Ports declaration for a component or implementation.

    In YAML, ports on the default timelines are organised by operator, as follows:

    .. code:: yaml

        ports:
          f_init:   # list of names
          - a
          - b
          o_f: d e  # on one line, space-separated
          o_i: c    # single port

    Note that operators for which there are no ports may be omitted. If there are O_I
    and/or S ports that are on a non-default timeline, then they can be described like
    this:

    .. code:: yaml

        ports:
          f_init: a
          o_f: b
          +timeline1:
            o_i: c d
            s: e
          +timeline2:
            o_i: f
            s: g h

    Note that the + symbol is not a part of the timeline name, it's just there to
    make it a bit easier to distinguish timelines from operators.

    On the Python side, this class acts like a dictionary mapping port names to Port
    objects.
    """
    @overload
    def __init__(
            self, f_init: Union[None, str, List[str]] = None,
            o_i: Union[None, str, List[str]] = None,
            s: Union[None, str, List[str]] = None,
            o_f: Union[None, str, List[str]] = None) -> None: ...

    @overload
    def __init__(self, f_init: List[Port]) -> None: ...

    def __init__(
            self, f_init: Union[None, str, List[str], List[Port]] = None,
            o_i: Union[None, str, List[str]] = None,
            s: Union[None, str, List[str]] = None,
            o_f: Union[None, str, List[str]] = None) -> None:
        """Create a Ports declaration.

        This can be called in two ways, either with four sets of ports, or with a single
        argument that is a list of Port objects.

        Args:
            ports: A list of port objects

            or:

            f_init: The ports associated with the F_INIT operator
            o_i: The ports associated with the O_I operator
            s: The ports associated with the S operator
            o_f: The ports associated with the O_F operator
        """
        # Bit of a tricky detection of which signature was intended
        is_empty_list = False
        is_port_list = False
        others_none = o_i is None and s is None and o_f is None

        if isinstance(f_init, list):
            is_empty_list = len(f_init) == 0
            is_port_list = not is_empty_list and isinstance(f_init[0], Port)

        if is_port_list or (is_empty_list and others_none):
            if not others_none:
                raise ValueError(
                        'Both a list of ports and per-operator ports were given. Please'
                        ' use either, not both.')

            self._ports = {p.name: p for p in cast(List[Port], f_init)}
        else:
            self._ports = dict()

            self._add_ports(Operator.F_INIT, cast(Union[None, str, List[str]], f_init))
            self._add_ports(Operator.O_I, o_i)
            self._add_ports(Operator.S, s)
            self._add_ports(Operator.O_F, o_f)

    def __len__(self) -> int:
        return len(self._ports)

    def __contains__(self, port_name: Union[str, Identifier]) -> bool:
        return _ensure_identifier(port_name) in self._ports

    def __getitem__(self, port_name: Union[str, Identifier]) -> Port:
        return self._ports[_ensure_identifier(port_name)]

    def __setitem__(self, port_name: Union[str, Identifier], port: Port) -> None:
        self._ports[_ensure_identifier(port_name)] = port

    def __iter__(self) -> Iterator[Identifier]:
        """Iterate through the ports' names."""
        for port_name in self._ports:
            yield port_name

    def sending_port_names(self) -> List[Identifier]:
        """Return the names of all the sending ports.

        These are ports associated with O_I or O_F operators.
        """
        return [
                p.name for p in self._ports.values()
                if p.operator in (Operator.O_I, Operator.O_F)]

    def receiving_port_names(self) -> List[Identifier]:
        """Return the names of all the receiving ports.

        These are ports associated with F_INIT or S operators.
        """
        return [
                p.name for p in self._ports.values()
                if p.operator in (Operator.F_INIT, Operator.S)]

    def _add_ports(
            self, op: Operator, ports: Union[None, str, List[str]],
            timeline: str = '') -> None:
        """Add the described ports to self._ports, helper function"""
        if ports is None:
            name_list = []
        elif isinstance(ports, str):
            name_list = ports.split()
        else:
            name_list = ports

        for name in name_list:
            if name in self._ports:
                raise RuntimeError(
                        f'Invalid ports specification: port "{name}" is'
                        ' specified more than once. Port names must be unique'
                        ' within the object they are on.')

            try:
                port_id = Identifier(name)
            except ValueError as e:
                raise ValueError(
                        f'Port name "{name}" is not a valid identifier. {e}')

            self._ports[port_id] = Port(port_id, op, Timeline(timeline))

    def _yatiml_init(
            self,
            _yatiml_extra: OrderedDict,
            f_init: Union[None, str, List[str]] = None,
            o_i: Union[None, str, List[str]] = None,
            s: Union[None, str, List[str]] = None,
            o_f: Union[None, str, List[str]] = None
            ) -> None:
        """Alternative initialisation when loading from YAML."""
        self._ports = dict()
        self._add_ports(Operator.F_INIT, f_init)
        self._add_ports(Operator.O_F, o_f)
        self._add_ports(Operator.O_I, o_i)
        self._add_ports(Operator.S, s)

        for tl_tag, tl_ports in _yatiml_extra.items():
            if not tl_tag.startswith('+'):
                raise RuntimeError(
                        f'Invalid operator "{tl_tag}". Please use f_init, o_i, s, or'
                        ' o_f, or prepend a + to the timeline name.')

            if 'o_i' in tl_ports:
                self._add_ports(Operator.O_I, tl_ports['o_i'], tl_tag[1:])

            if 's' in tl_ports:
                self._add_ports(Operator.S, tl_ports['s'], tl_tag[1:])

            additional_keys = set(tl_ports.keys()) - {'o_i', 's'}
            if additional_keys:
                raise RuntimeError(
                        f'Found additional keys {",".join(additional_keys)} under'
                        f' timeline {tl_tag}. Only o_i and s can be specified here.')

    def _yatiml_attributes(self) -> OrderedDict:
        def add_ports(
                attrs: OrderedDict, op: Operator, key: str, timeline: Timeline) -> None:
            op_ports = [
                    p for p in self._ports.values()
                    if p.operator == op and p.timeline == timeline]
            names = [str(p.name) for p in op_ports]
            if len(names) > 5 or len(' '.join(names)) > 60:
                attrs[key] = names
            elif names:
                attrs[key] = ' '.join(names)

        def unique(timelines: List[Timeline]) -> List[Timeline]:
            result = list()     # keeps the order
            seen = set()        # fast lookup
            for timeline in timelines:
                if timeline not in seen:
                    result.append(timeline)
                    seen.add(timeline)
            return result

        attrs = OrderedDict()       # type: _PortsAttrs
        add_ports(attrs, Operator.F_INIT, 'f_init', Timeline(''))

        timelines = [p.timeline for p in self._ports.values() if p.timeline != '']
        if not timelines:
            add_ports(attrs, Operator.O_I, 'o_i', Timeline(''))
            add_ports(attrs, Operator.S, 's', Timeline(''))
        else:
            for timeline in unique(timelines):
                timeline_attrs = OrderedDict()  # type: _PortsSubAttrs
                add_ports(timeline_attrs, Operator.O_I, 'o_i', timeline)
                add_ports(timeline_attrs, Operator.S, 's', timeline)
                attrs[f'+{timeline}'] = timeline_attrs

        add_ports(attrs, Operator.O_F, 'o_f', Timeline(''))
        return attrs
