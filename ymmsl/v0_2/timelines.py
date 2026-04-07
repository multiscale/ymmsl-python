from ymmsl.v0_2 import (
    Component,
    Conduit,
    Model,
    Operator,
    Port,
    Reference,
    Timeline,
    Identifier,
)


class TimelineTree:
    """Determines timelines and nesting for a given yMMSL model"""

    def __init__(self, model: Model) -> None:
        self.model = model
        """yMMSL model that this TimelineTree belongs to."""
        self.root = TimelineNode(Timeline(":"), None)
        """Timeline node of the root timeline."""

        self.component_timeline: dict[Reference, TimelineNode] = {}
        """Map of component names to the TimelineNode they are part of."""
        self.conduits_by_receiver: dict[Reference, Conduit] = {
            conduit.receiver: conduit for conduit in self.model.conduits
        }
        """Map of conduits by their receiving port"""
        self.all_ports: dict[Reference, Port] = {
            component.name + port_name: port
            for component in self.model.components.values()
            for port_name, port in component.ports.items()
        }
        """Map of Port objects by their full reference"""

        # Ports may only have relative timeline annotations of size 1
        for port in self.all_ports.values():
            if port.timeline.absolute or len(port.timeline) > 1:
                # FIXME?
                raise ValueError(
                    f"Invalid timeline annotation for {port.name}: {port.timeline}"
                )

        # Assign components to timelines
        for component in self.model.components.values():
            if component.name in self.component_timeline:
                continue
            self._assign_component(component, [])

    def _f_init_conduits_for_component(self, component: Component) -> list[Conduit]:
        """Get conduits that are connected to an F_INIT port on the component"""
        result = []
        for port in component.ports.values():
            if port.operator is Operator.F_INIT:
                conduit = self.conduits_by_receiver.get(component.name + port.name)
                if conduit is not None:
                    result.append(conduit)
        return result

    def _assign_component(self, component: Component, seen: list[Component]) -> None:
        """Recursive component assignment, uses "seen" list for cycle detection."""
        if component in seen:
            # TODO: better error message
            idx = seen.index(component)
            cycle_list = seen[idx:] + [component]
            cycle = " -> ".join(str(component.name) for component in cycle_list)
            raise RuntimeError(f"Cycle detected in model '{self.model.name}': {cycle}")
        f_init_conduits = self._f_init_conduits_for_component(component)

        # Ensure we know the timelines of the components attached to our F_INIT
        seen.append(component)
        for conduit in f_init_conduits:
            sender = conduit.sending_component()
            if sender not in self.component_timeline:
                self._assign_component(self.model.components[sender], seen)
        seen.pop()

        # Now we can determine our timeline
        repeater_conduits: list[Conduit] = []
        incoming_timelines: list[TimelineNode] = []
        for conduit in f_init_conduits:
            if any(filter.is_repeater() for filter in conduit.filters):
                repeater_conduits.append(conduit)
                continue
            timeline = self.timeline_for_sending_port(conduit.sender)
            for filter in conduit.filters:
                assert filter.is_reducer()
                if timeline.parent is None:
                    raise ValueError("Too many reducer filters")
                timeline = timeline.parent
            incoming_timelines.append(timeline)

        determined_timeline = self.root
        if incoming_timelines:
            determined_timeline = incoming_timelines[0]
        if not all(tl is determined_timeline for tl in incoming_timelines):
            # TODO: better error message
            raise ValueError(f"Inconsistent timelines {incoming_timelines}")

        # Check consistency of conduits with repeaters
        for conduit in repeater_conduits:
            timeline1 = self.timeline_for_sending_port(conduit.sender)
            timeline2 = determined_timeline
            for filter in conduit.filters:
                if timeline1 is determined_timeline:
                    raise ValueError(
                        "repeater after reducer cannot be in same timeline"
                    )
                if filter.is_reducer():
                    if timeline1.parent is None:
                        raise ValueError("Too many reducer filters")
                    timeline1 = timeline1.parent
                if filter.is_repeater():
                    if timeline2.parent is None:
                        raise ValueError("Too many repeater filters")
                    timeline2 = timeline2.parent
            if timeline1 is not timeline2:
                raise ValueError("Inconsistent timelines")

        # Done: register timeline for component
        self.component_timeline[component.name] = determined_timeline
        determined_timeline.add(component)

    def timeline_for_sending_port(self, port_name: Reference) -> "TimelineNode":
        component = port_name[:-1]
        if len(component) == 0:
            # Connected to a model port
            model_port = port_name[-1]
            assert isinstance(model_port, Identifier)
            port = self.model.ports[model_port]
            if port.operator is Operator.F_INIT:
                return self.root
            else:
                raise NotImplementedError()  # FIXME?
        timeline = self.component_timeline[component]
        port = self.all_ports[port_name]
        if port.operator is Operator.O_F:
            return timeline
        assert port.operator is Operator.O_I
        subtimeline = port.timeline
        if len(port.timeline) == 0:
            # No explicit label attached to the timeline, so we take the component name
            subtimeline = Timeline(str(component))
        return timeline.get(subtimeline)


class TimelineNode:
    """Node in the timeline tree.

    Corresponds to a single timeline in a yMMSL model, and keeps track of components
    that are in that timeline.
    """

    def __init__(self, timeline: Timeline, parent: "TimelineNode | None") -> None:
        """Initialize timeline node for a given timeline"""

        self.name = timeline
        """Name of this timeline."""
        self.parent = parent
        """Parent node of this node."""
        self.children: dict[Reference, TimelineNode] = {}
        """Child timeline nodes."""
        self.components: list[Component] = []
        """List of components that are part of this timeline."""

    def get(self, subtimeline: Timeline) -> "TimelineNode":
        """Get a sub-timeline of this timeline, creating a new one if required."""
        assert not subtimeline.absolute
        assert len(subtimeline) == 1
        child = self.children.get(subtimeline[0])
        if child is None:
            child = TimelineNode(self.name + subtimeline, self)
            self.children[subtimeline[0]] = child
        return child

    def add(self, component: Component) -> None:
        """Add component to this timeline."""
        self.components.append(component)

    def __repr__(self) -> str:
        return f"TimelineNode({self.name})"
